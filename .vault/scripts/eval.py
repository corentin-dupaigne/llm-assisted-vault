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

Results land in ``.e2e-output/eval/<model>-<timestamp>/`` (gitignored):
``cases.jsonl`` (one line per case) and ``summary.json``.
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


def projects_at(commit: git.Commit) -> list[str]:
    try:
        return sorted(t.name for t in (commit.tree / "Projects").trees)
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
                "projects": projects_at(parent),
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
                "id": f"{commit.hexsha[:7]}:{filename}",
                "filename": filename,
                "content": content.replace("\r\n", "\n").lstrip("﻿"),
                "index": index,
                "bot_target": target,
                "expected": {
                    "path": final,
                    "para": parts[0],
                    "project": parts[1] if parts[0] == "Projects" and len(parts) > 2 else None,
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
        response = client.messages.create(**request)
    except APIError as exc:
        return {"id": case["id"], "error": f"{type(exc).__name__}: {exc}"[:300]}
    return score_case(case, pi.decision_from_response(response), {
        "seconds": round(time.monotonic() - start, 2),
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    })


def score_case(case: dict, raw_decision: dict, meta: dict) -> dict:
    """What the pipeline would file for this decision, next to the reference."""
    content, index = case["content"], case["index"]
    inner, _ = pi.split_frontmatter(content)
    preset = pi.parse_frontmatter(inner)[1] if inner else {}
    decision = pi.normalize_decision(raw_decision)
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

    para, project = pi.reconcile_placement(content, decision.get("para"),
                                           decision.get("project"))
    placement = pi.build_target_path(para, project, "x.md")
    if pi.unknown_model_project(content, para, project, index):
        placement = None
    preset_tags = preset.get("tags") if isinstance(preset.get("tags"), list) else []
    result["got"] = {
        "valid": bool(decision.get("domain")) and placement is not None,
        "para": para,
        "project": project,
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


def summarize(model: str, results: list[dict], skipped: list[str]) -> dict:
    ok = [r for r in results if "error" not in r]
    filed = [r for r in ok if r["got"]]
    valid = [r for r in filed if r["got"]["valid"]]

    def rate(hits: int, total: int) -> dict:
        return {"hits": hits, "total": total,
                "rate": round(hits / total, 3) if total else None}

    placement = [r for r in valid
                 if (r["got"]["para"], r["got"]["project"])
                 == (r["expected"]["para"], r["expected"]["project"])]
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
            {"id": r["id"], "expected": f"{r['expected']['para']}/{r['expected']['project'] or ''}",
             "got": f"{r['got']['para']}/{r['got']['project'] or ''}"}
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
        "tokens": {"input": tokens_in, "output": tokens_out,
                   "input_per_case": round(tokens_in / len(ok)) if ok else None},
        "cost_usd": round(cost, 4) if cost is not None else None,
        "seconds_median": sorted(r["seconds"] for r in ok)[len(ok) // 2] if ok else None,
        "history_placements_corrected_by_hand": [
            {"id": r["id"], "bot": r["bot_target"], "now": r["expected"]["path"]}
            for r in corrected],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--model", default=pi.MODEL)
    parser.add_argument("--rev", default="HEAD", help="history to replay (default HEAD)")
    parser.add_argument("--limit", type=int, help="replay only the N most recent cases")
    parser.add_argument("--workers", type=int, default=4)
    parser.add_argument("--out", type=Path, help="output directory")
    parser.add_argument("--rescore", type=Path, metavar="DIR",
                        help="re-score the decisions saved in DIR/cases.jsonl with the "
                             "current code (no API calls); writes DIR/summary.json")
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
        results = [r if "error" in r else score_case(
                       by_id[r["id"]], r["decision"],
                       {k: r[k] for k in ("seconds", "input_tokens", "output_tokens")})
                   for r in saved if r["id"] in by_id]
        args.model, out = model, args.rescore
    else:
        system_prompt = pi.SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        client = Anthropic(max_retries=5)
        with ThreadPoolExecutor(max_workers=args.workers) as pool:
            results = list(pool.map(
                lambda c: replay(client, system_prompt, args.model, c), cases))
        out = args.out or (pi.REPO_ROOT / ".e2e-output" / "eval"
                           / f"{args.model}-{datetime.now():%Y%m%d-%H%M%S}")

    summary = summarize(args.model, results, skipped)
    out.mkdir(parents=True, exist_ok=True)
    with (out / "cases.jsonl").open("w", encoding="utf-8") as fh:
        for r in results:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
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
