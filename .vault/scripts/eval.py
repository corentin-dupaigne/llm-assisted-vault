#!/usr/bin/env python3
"""Replay past Inbox filings through a model and score it against the vault.

Every ``organize <note> → <path>`` line of a ``chore(llm):`` commit is one test
case. Each case is replayed the way the pipeline saw it at the time:

- the note content is the Inbox file as it was in the commit's parent;
- the index is the commit's index minus the notes filed by that run, plus the
  ones the run had filed *before* this note (the pipeline files in order), with
  projects taken from the ``Projects/`` folders of the parent commit;
- the system prompt, tool schema and index rendering are the *current* ones, so
  this measures the pipeline as it is now.

The reference is the note as it lives at ``--rev`` today: its location (the bot's
placement as kept or corrected by hand), its ``domain``/``tags`` frontmatter and
its ``## Links``. Domain and tag scores only count notes whose captured
frontmatter did not already set the field (otherwise the model's answer is
ignored by the pipeline and the match is free). Link scores measure agreement
with the links the vault kept, which were picked by the previous model — not an
absolute truth.

Usage (from the repo root; reads the key from ``.vault/.env``)::

    .venv/bin/python .vault/scripts/eval.py --model claude-haiku-4-5
    .venv/bin/python .vault/scripts/eval.py --model claude-sonnet-4-6 --rev my-notes --limit 10

Results land in ``.vault/benchmarks/<date>-<model>/`` — tracked, so runs are
kept in the repo (see ``.vault/benchmarks/README.md``):
``cases.jsonl`` (one line per case) and ``summary.json``. ``--rescore`` writes
``cases.rescored.jsonl`` / ``summary.rescored.json`` next to them.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import git
from anthropic import Anthropic, APIError

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_inbox as pi  # noqa: E402

# USD per million tokens (input, output), for the cost estimate only.
PRICES = {
    "claude-haiku-4-5": (1.0, 5.0),
    "claude-sonnet-4-6": (3.0, 15.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-opus-5-5": (4.0, 20.0),
}

_ORGANIZE_RE = re.compile(r"organize (.+?) → (.+)$")
_LINK_RE = re.compile(r"\[\[([^\]|#]+)")
INDEX_PATHS = (".vault/vault.index.json", "vault.index.json")


# --- Building cases from history ---------------------------------------------

def show(repo: git.Repo, rev: str, path: str) -> str | None:
    try:
        return repo.git.show(f"{rev}:{path}")
    except git.GitCommandError:
        return None


def index_at(repo: git.Repo, rev: str) -> dict | None:
    for path in INDEX_PATHS:
        text = show(repo, rev, path)
        if text is not None:
            return json.loads(text)
    return None


def folders_at(commit: git.Commit, root: str) -> list[str]:
    try:
        return sorted(t.name for t in (commit.tree / root).trees)
    except KeyError:
        return []


def final_path(repo: git.Repo, sha: str, target: str, rev: str) -> str | None:
    """Where the note filed at ``target`` by ``sha`` lives at ``rev`` (follows
    renames/moves made since); ``None`` if it was deleted."""
    if show(repo, rev, target) is not None:
        return target
    out = repo.git.diff("-M", "--name-status", sha, rev)
    for line in out.splitlines():
        parts = line.split("\t")
        if parts[0].startswith("R") and len(parts) == 3 and parts[1] == target:
            return parts[2]
    return None


def links_in(text: str) -> list[str]:
    _, _, links_section = text.partition("\n## Links\n")
    return sorted({m.strip() for m in _LINK_RE.findall(links_section)})


def case_id(commit: git.Commit, filename: str) -> str:
    return f"{commit.authored_datetime.isoformat()}:{filename}"


def build_cases(repo: git.Repo, rev: str) -> tuple[list[dict], list[str]]:
    cases: list[dict] = []
    skipped: list[str] = []
    commits = [c for c in repo.iter_commits(rev) if c.message.startswith("chore(llm):")]
    for commit in reversed(commits):  # oldest first
        filed = [m.groups() for line in commit.message.splitlines()
                 if (m := _ORGANIZE_RE.search(line))]
        if not filed or not commit.parents:
            continue
        parent = commit.parents[0]
        post = index_at(repo, commit.hexsha)
        if post is None:
            skipped.append(f"{commit.hexsha[:7]}: no index")
            continue
        run_targets = [target for _, target in filed]
        by_path = {n.get("path"): n for n in post.get("notes", [])}
        base = [n for n in post.get("notes", []) if n.get("path") not in run_targets]

        for k, (filename, target) in enumerate(filed):
            content = show(repo, parent.hexsha, f"Inbox/{filename}")
            final = final_path(repo, commit.hexsha, target, rev)
            if content is None or final is None:
                skipped.append(f"{commit.hexsha[:7]} {filename}: "
                               f"{'source missing' if content is None else 'note since deleted'}")
                continue
            earlier = [by_path[t] for t in run_targets[:k] if t in by_path]
            notes = base + earlier
            index = {
                "projects": folders_at(parent, "Projects"),
                "areas": folders_at(parent, "Areas"),
                "domains": pi.collect_canonical(post.get("domains", []),
                                                [n["domain"] for n in notes if n.get("domain")]),
                "tags": pi.collect_canonical(post.get("tags", []),
                                             [t for n in notes for t in n.get("tags") or []]),
                "notes": notes,
            }
            final_text = show(repo, rev, final)
            inner, _ = pi.split_frontmatter(final_text)
            final_fm = pi.parse_frontmatter(inner)[1] if inner else {}
            parts = Path(final).parts
            cases.append({
                # Author date + name survive a rebase (the SHA does not), so
                # saved results stay comparable after history is rewritten.
                "id": case_id(commit, filename),
                "filename": filename,
                "content": content.replace("\r\n", "\n").lstrip("﻿"),
                "index": index,
                "bot_target": target,
                "expected": {
                    "path": final,
                    "para": parts[0],
                    "project": parts[1] if parts[0] == "Projects" and len(parts) > 2 else None,
                    "area": parts[1] if parts[0] == "Areas" and len(parts) > 2 else None,
                    "domain": final_fm.get("domain"),
                    "tags": sorted(final_fm.get("tags") or []),
                    "links": links_in(final_text),
                },
            })
    return cases, skipped


# --- Replaying ---------------------------------------------------------------

def replay(client: Anthropic, system_prompt: str, model: str, case: dict) -> dict:
    """Classify one case with the model and score it. The raw decision is kept
    so ``--rescore`` can re-apply the current code-side checks later."""
    request = pi.build_classification_request(system_prompt, case["content"],
                                              case["index"], model=model)
    start = time.monotonic()
    try:
        decision, responses = pi.run_classification(client, request)
    except APIError as exc:
        return {"id": case["id"], "error": f"{type(exc).__name__}: {exc}"[:300]}
    return score_case(case, decision, {
        "seconds": round(time.monotonic() - start, 2),
        "calls": len(responses),
        "input_tokens": sum(r.usage.input_tokens for r in responses),
        "output_tokens": sum(r.usage.output_tokens for r in responses),
    })


def score_case(case: dict, raw_decision: dict, meta: dict) -> dict:
    """What the pipeline would file for this decision, next to the reference."""
    content, index = case["content"], case["index"]
    inner, _ = pi.split_frontmatter(content)
    preset = pi.parse_frontmatter(inner)[1] if inner else {}
    decision = pi.canonicalize_labels(pi.normalize_decision(raw_decision), index)
    result = {
        "id": case["id"],
        **meta,
        "decision": raw_decision,
        "domain_preset": "domain" in preset,
        "tags_preset": "tags" in preset,
        "expected": case["expected"],
        "bot_target": case["bot_target"],
        "got": None,
    }
    if decision.get("status") != "filed":
        return result

    para, project, area = pi.reconcile_placement(
        content, decision.get("para"), decision.get("project"), decision.get("area"))
    placement = pi.build_target_path(para, project, "x.md", area)
    if pi.invented_folder(content, para, project, area, index):
        placement = None
    preset_tags = preset.get("tags") if isinstance(preset.get("tags"), list) else []
    result["got"] = {
        "valid": bool(decision.get("domain")) and placement is not None,
        "para": para,
        "project": project,
        "area": area,
        "domain": preset.get("domain") or decision.get("domain"),
        "tags": sorted(preset_tags if "tags" in preset else decision.get("tags") or []),
        "links": sorted(link.strip("[]") for link in
                        pi.resolve_wikilinks(decision.get("wikilinks") or [], index)),
    }
    return result


# --- Scoring -----------------------------------------------------------------

def jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    return 1.0 if not sa and not sb else len(sa & sb) / len(sa | sb)


def place(p: dict) -> str:
    """``para/subfolder`` of a placement (runs saved before areas have none)."""
    return f"{p['para']}/{p.get('project') or p.get('area') or ''}"


def summarize(model: str, results: list[dict], skipped: list[str]) -> dict:
    ok = [r for r in results if "error" not in r]
    filed = [r for r in ok if r["got"]]
    valid = [r for r in filed if r["got"]["valid"]]

    def rate(hits: int, total: int) -> dict:
        return {"hits": hits, "total": total,
                "rate": round(hits / total, 3) if total else None}

    placement = [r for r in valid
                 if place(r["got"]) == place(r["expected"])]
    dom_cases = [r for r in valid if not r["domain_preset"]]
    tag_cases = [r for r in valid if not r["tags_preset"]]
    link_tp = sum(len(set(r["got"]["links"]) & set(r["expected"]["links"])) for r in valid)
    link_got = sum(len(r["got"]["links"]) for r in valid)
    link_exp = sum(len(r["expected"]["links"]) for r in valid)
    tokens_in = sum(r["input_tokens"] for r in ok)
    tokens_out = sum(r["output_tokens"] for r in ok)
    price_in, price_out = PRICES.get(model, (None, None))
    cost = (tokens_in * price_in + tokens_out * price_out) / 1e6 if price_in else None
    corrected = [r for r in ok if r["bot_target"] != r["expected"]["path"]]

    return {
        "model": model,
        "cases": len(results),
        "api_errors": len(results) - len(ok),
        "skipped_cases": skipped,
        "filed_valid": rate(len(valid), len(ok)),
        "unfileable_or_rejected": [r["id"] for r in ok if r not in valid],
        "placement_exact": rate(len(placement), len(valid)),
        "placement_misses": [
            {"id": r["id"], "expected": place(r["expected"]), "got": place(r["got"])}
            for r in valid if r not in placement],
        "domain_exact_model_decided": rate(
            sum(r["got"]["domain"] == r["expected"]["domain"] for r in dom_cases), len(dom_cases)),
        "domain_misses": [
            {"id": r["id"], "expected": r["expected"]["domain"], "got": r["got"]["domain"]}
            for r in dom_cases if r["got"]["domain"] != r["expected"]["domain"]],
        "tags_jaccard_model_decided": round(
            sum(jaccard(r["got"]["tags"], r["expected"]["tags"]) for r in tag_cases)
            / len(tag_cases), 3) if tag_cases else None,
        "links": {
            "agreed": link_tp, "proposed": link_got, "kept_in_vault": link_exp,
            "precision": round(link_tp / link_got, 3) if link_got else None,
            "recall": round(link_tp / link_exp, 3) if link_exp else None,
        },
        "retries_without_tool_call": sum(r.get("calls", 1) - 1 for r in ok),
        "tokens": {"input": tokens_in, "output": tokens_out,
                   "input_per_case": round(tokens_in / len(ok)) if ok else None},
        "cost_usd": round(cost, 4) if cost is not None else None,
        "seconds_median": sorted(r["seconds"] for r in ok)[len(ok) // 2] if ok else None,
        "history_placements_corrected_by_hand": [
            {"id": r["id"], "bot": r["bot_target"], "now": r["expected"]["path"]}
            for r in corrected],
    }


def new_run_dir(model: str) -> Path:
    """``.vault/benchmarks/<date>-<model>``, suffixed if that run already
    exists, so a new run never overwrites a saved one."""
    base = pi.VAULT_DIR / "benchmarks" / f"{datetime.now():%Y-%m-%d}-{model}"
    out, n = base, 2
    while out.exists():
        out, n = base.with_name(f"{base.name}-{n}"), n + 1
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", default=pi.MODEL)
    parser.add_argument("--rev", default="HEAD", help="history to replay (default HEAD)")
    parser.add_argument("--limit", type=int, help="replay only the N most recent cases")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, help="output directory")
    parser.add_argument("--rescore", type=Path, metavar="DIR",
                        help="re-score the decisions saved in DIR/cases.jsonl with the "
                             "current code (no API calls); writes DIR/summary.rescored.json")
    args = parser.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv(pi.VAULT_DIR / ".env")
    except ImportError:
        pass

    repo = git.Repo(pi.REPO_ROOT)
    cases, skipped = build_cases(repo, args.rev)
    if args.limit:
        cases = cases[-args.limit:]
    print(f"{len(cases)} cases from {args.rev} ({len(skipped)} skipped)")

    if args.rescore:
        saved = [json.loads(line) for line in
                 (args.rescore / "cases.jsonl").read_text(encoding="utf-8").splitlines()]
        by_id = {case["id"]: case for case in cases}
        model = json.loads((args.rescore / "summary.json").read_text())["model"]
        missing = [r["id"] for r in saved if r["id"] not in by_id]
        if missing:
            print(f"! {len(missing)} saved cases no longer match the history "
                  f"(e.g. {missing[0]}); nothing written.", file=sys.stderr)
            return 1
        results = [r if "error" in r else score_case(
                       by_id[r["id"]], r["decision"],
                       {k: r[k] for k in ("seconds", "calls", "input_tokens",
                                          "output_tokens") if k in r})
                   for r in saved]
        args.model, out = model, args.rescore
    else:
        system_prompt = pi.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        client = Anthropic(max_retries=5)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(
                lambda c: replay(client, system_prompt, args.model, c), cases))
        if results and all("error" in r for r in results):
            print(f"! Every call failed, nothing written: {results[0]['error']}",
                  file=sys.stderr)
            return 1
        out = args.out or new_run_dir(args.model)

    summary = summarize(args.model, results, skipped)
    out.mkdir(parents=True, exist_ok=True)
    # A rescore never overwrites the raw run: its results go to their own files.
    suffix = ".rescored" if args.rescore else ""
    with (out / f"cases{suffix}.jsonl").open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / f"summary{suffix}.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
                                      encoding="utf-8")

    for key in ("filed_valid", "placement_exact", "domain_exact_model_decided"):
        print(f"{key:28} {summary[key]['hits']}/{summary[key]['total']} ({summary[key]['rate']})")
    print(f"{'tags_jaccard_model_decided':28} {summary['tags_jaccard_model_decided']}")
    print(f"{'links':28} {summary['links']}")
    print(f"{'tokens':28} {summary['tokens']}  cost ${summary['cost_usd']}")
    print(f"Wrote {out}")
    return 1 if summary["api_errors"] else 0


if __name__ == "__main__":
    sys.exit(main())
