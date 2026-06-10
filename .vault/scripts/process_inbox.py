#!/usr/bin/env python3
"""LLM-assisted PARA filing for the vault Inbox.

Reads every Markdown note dropped in ``Inbox/``, asks Claude to classify and
enrich it according to the PARA method using ``vault.index.json`` as the sole
source of truth, then files the note, updates the index, and commits the run.

Invariants (see CLAUDE.md):
- Only files inside ``Inbox/`` are ever moved or modified.
- ``Atlas/``, ``Templates/`` and ``Attachments/`` are never touched.
- Nothing is ever deleted; links are only added from the new note outward.
- No API call is made when the Inbox is empty (controlled cost).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import git
import mdformat
from anthropic import Anthropic

# --- Paths and constants -----------------------------------------------------

# This script lives at `.vault/scripts/`, so its grandparent is `.vault/` (the
# machinery dir) and the vault root one level up holds the PARA folders + `.git`.
VAULT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = VAULT_DIR.parent
INBOX_DIR = REPO_ROOT / "Inbox"
PROJECTS_DIR = REPO_ROOT / "Projects"
INDEX_PATH = VAULT_DIR / "vault.index.json"
SYSTEM_PROMPT_PATH = VAULT_DIR / "prompts" / "system.md"

MODEL = "claude-sonnet-4-6"
MAX_TOKENS = 1024

# Structured output is forced via tool use: the model must call `file_note`, and
# its `input` is returned already parsed and conforming to this schema. This is
# model-agnostic (works on models that reject assistant prefill, e.g. sonnet 4.6)
# and removes any chance of prose, ```json fences, or unparseable text.
CLASSIFY_TOOL = {
    "name": "file_note",
    "description": (
        "Record the PARA classification and enrichment decision for the note. "
        "Provide every field when status is 'filed'; provide only status and "
        "reason when status is 'unfileable'."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["filed", "unfileable"]},
            "reason": {"type": "string", "description": "Short justification."},
            "target_path": {
                "type": "string",
                "description": "Full destination path including filename, "
                               "e.g. 'Resources/note-filename.md'.",
            },
            "domain": {
                "type": "string",
                "description": "Single primary subject, lowercase hyphen-separated.",
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Secondary subjects, lowercase hyphen-separated.",
            },
            "para": {"type": "string", "enum": ["Projects", "Areas", "Resources", "Archive"]},
            "project": {
                "type": ["string", "null"],
                "description": "Project name when para is 'Projects', otherwise null.",
            },
            "wikilinks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Links to relevant existing notes, built from each "
                               "note's FILENAME (its 'path' basename without the "
                               "'.md'), with the note's title as the display "
                               "alias: '[[file-stem|Note Title]]'. E.g. for a note "
                               "at 'Resources/contains-duplicate.md' titled "
                               "'Contains Duplicate', emit "
                               "'[[contains-duplicate|Contains Duplicate]]'.",
            },
        },
        "required": ["status", "reason"],
    },
}

# Destinations the LLM is allowed to file into. Atlas/Templates/Attachments and
# Inbox itself are deliberately excluded — filing there is forbidden.
ALLOWED_PARA_ROOTS = {"Projects", "Areas", "Resources", "Archive"}


# --- Index helpers -----------------------------------------------------------

def load_index() -> dict:
    with INDEX_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_index(index: dict) -> None:
    with INDEX_PATH.open("w", encoding="utf-8") as fh:
        json.dump(index, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


# --- Project detection -------------------------------------------------------

def detect_projects() -> list[str]:
    """Active project names = the immediate subfolders of ``Projects/``.

    One subfolder per active project is the on-disk convention (see CLAUDE.md),
    so the folder listing is the source of truth. Returned sorted for a stable,
    diff-friendly index.
    """
    if not PROJECTS_DIR.is_dir():
        return []
    return sorted(p.name for p in PROJECTS_DIR.iterdir() if p.is_dir())


def sync_projects(index: dict) -> bool:
    """Refresh ``index['projects']`` from the ``Projects/`` folder listing.

    Returns ``True`` if the index changed, so the caller can decide whether to
    persist it. The folder listing is authoritative: projects whose folder no
    longer exists are dropped, newly created folders are added.
    """
    detected = detect_projects()
    if index.get("projects") != detected:
        index["projects"] = detected
        return True
    return False


# --- Note helpers ------------------------------------------------------------

def extract_title(content: str, fallback_stem: str) -> str:
    """Title of a note: its first H1 heading, else a humanized filename stem."""
    for line in content.splitlines():
        match = re.match(r"^#\s+(.+?)\s*$", line)
        if match:
            return match.group(1).strip()
    return fallback_stem.replace("-", " ").replace("_", " ").strip().title()


# The metadata every filed note must carry. Order is the canonical layout used
# when a field has to be added; existing fields keep their own position.
MANDATORY_FIELDS = ("domain", "tags", "date", "para", "project")

# A leading YAML frontmatter block, and a `key:` line within one.
_FRONTMATTER_RE = re.compile(r"^---\n(.*?)\n---\n?", re.DOTALL)
_FM_KEY_RE = re.compile(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$")
_FM_LIST_ITEM_RE = re.compile(r"^\s*-\s+(.*)$")


def split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split a leading YAML frontmatter block from the body.

    Returns ``(inner, body)`` where ``inner`` is the block's content *without*
    the ``---`` delimiters (``None`` when the note has no frontmatter) and
    ``body`` is everything after it.
    """
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return None, text
    return match.group(1), text[match.end():]


def parse_frontmatter(inner: str) -> tuple[list[str], dict]:
    """Parse a frontmatter block into ``(ordered_keys, values)``.

    Supports the scalar, flow-list (`[a, b]`) and block-list (`- a`) forms that
    appear in hand-written and templated notes. Used only to read existing
    values; the original lines are preserved verbatim when re-emitting.
    """
    keys: list[str] = []
    values: dict = {}
    lines = inner.splitlines()
    i = 0
    while i < len(lines):
        match = _FM_KEY_RE.match(lines[i])
        if not match:
            i += 1
            continue
        key, raw = match.group(1), match.group(2).strip()
        keys.append(key)
        if raw == "":
            items, j = [], i + 1
            while j < len(lines) and _FM_LIST_ITEM_RE.match(lines[j]):
                items.append(_FM_LIST_ITEM_RE.match(lines[j]).group(1).strip())
                j += 1
            if items:
                values[key] = items
                i = j
                continue
            values[key] = None
        elif raw.startswith("[") and raw.endswith("]"):
            body = raw[1:-1].strip()
            values[key] = [t.strip() for t in body.split(",") if t.strip()] if body else []
        elif raw in ("null", "~"):
            values[key] = None
        else:
            values[key] = raw
        i += 1
    return keys, values


def render_field(key: str, value) -> str:
    """Render one mandatory field as a frontmatter line."""
    if key == "tags":
        return f"tags: [{', '.join(value or [])}]"
    if key == "project":
        return f"project: {value if value else 'null'}"
    return f"{key}: {value}"


def merge_frontmatter(original: str, *, domain: str, tags: list[str], date: str,
                      para: str, project: str | None) -> tuple[str, str, dict]:
    """Merge the mandatory metadata into a note's existing frontmatter.

    Captured notes may already carry frontmatter (e.g. Obsidian/Dataview
    templates). Existing fields — mandatory or not — are kept **verbatim** and
    never overridden; only the mandatory fields that are *missing* are appended,
    so the result is always a single frontmatter block. Returns
    ``(frontmatter, body, effective)`` where ``effective`` holds the
    authoritative mandatory values (existing wins) for the index.
    """
    inner, body = split_frontmatter(original)
    computed = {"domain": domain, "tags": tags, "date": date,
                "para": para, "project": project}

    if inner:
        existing_keys, existing_values = parse_frontmatter(inner)
        lines = [inner]
    else:
        existing_keys, existing_values = [], {}
        lines = []

    for key in MANDATORY_FIELDS:
        if key not in existing_keys:
            lines.append(render_field(key, computed[key]))

    frontmatter = "---\n" + "\n".join(lines) + "\n---\n"

    effective = {
        key: existing_values[key] if key in existing_keys else computed[key]
        for key in MANDATORY_FIELDS
    }
    return frontmatter, body, effective


def resolve_wikilinks(raw_links: list[str], index: dict) -> list[str]:
    """Validate the model's filename-based wikilinks against the index.

    Obsidian resolves a wikilink by the target file's *basename*, not by its
    frontmatter title — so the model is asked to build each link from the note's
    filename (the `path` basename), producing `[[file-stem|Title]]`. This is a
    safety net over that contract: each link's target is matched against the
    indexed note basenames, and the alias is re-derived from the index `title`
    so the display text is always canonical. A link whose basename matches no
    indexed note (a hallucinated target) is dropped rather than written broken —
    that is what would otherwise spawn a stray note at the vault root.
    """
    by_stem: dict[str, str] = {}
    for note in index.get("notes", []):
        title, path = note.get("title"), note.get("path")
        if title and path:
            by_stem[Path(path).stem] = title

    resolved: list[str] = []
    seen: set[str] = set()
    for raw in raw_links:
        # Accept whatever the model emitted ([[stem]], [[stem|Alias]], a path,
        # or a name with .md) and reduce it to the bare basename to match on.
        target = raw.strip().strip("[]").split("|", 1)[0].strip()
        stem = Path(target).stem
        title = by_stem.get(stem)
        if title and stem not in seen:
            resolved.append(f"[[{stem}|{title}]]")
            seen.add(stem)
    return resolved


def build_links_section(wikilinks: list[str]) -> str:
    lines = "\n".join(f"- {link}" for link in wikilinks)
    return f"\n## Links\n\n{lines}\n"


def format_markdown(text: str) -> str:
    """Normalize the Markdown body's formatting before it is filed.

    The `wikilink` extension keeps `[[Obsidian links]]` intact (mdformat would
    otherwise escape the brackets). The YAML frontmatter is deliberately *not*
    passed through here — it is built canonically and reattached verbatim, so
    the formatter never rewrites `project: null` or reorders keys.
    """
    return mdformat.text(text, extensions={"wikilink"})


# --- Path safety -------------------------------------------------------------

def resolve_safe_target(target_path: str) -> Path | None:
    """Resolve ``target_path`` and confirm it lands inside an allowed PARA root.

    Returns the absolute path, or ``None`` if the path is malformed, escapes the
    repo, or points at a forbidden area. Defensive: protects against the model
    returning a path into Atlas/Templates/Attachments/Inbox or outside the vault.
    """
    if not target_path or not target_path.endswith(".md"):
        return None

    rel = Path(target_path)
    if rel.is_absolute():
        return None

    candidate = (REPO_ROOT / rel).resolve()
    try:
        relative = candidate.relative_to(REPO_ROOT)
    except ValueError:
        return None  # escapes the repo via ../

    if not relative.parts or relative.parts[0] not in ALLOWED_PARA_ROOTS:
        return None

    return candidate


def unique_destination(dest: Path) -> Path:
    """Never overwrite an already-filed note (immutability). Add a suffix."""
    if not dest.exists():
        return dest
    stem, suffix, parent = dest.stem, dest.suffix, dest.parent
    counter = 2
    while True:
        candidate = parent / f"{stem}-{counter}{suffix}"
        if not candidate.exists():
            return candidate
        counter += 1


# --- LLM call ----------------------------------------------------------------

def classify_note(client: Anthropic, system_prompt: str, content: str,
                  index: dict) -> dict:
    """Call Claude with forced tool use and return the decision dict.

    The model is required to call `file_note`; its already-parsed `input` is the
    decision. If, exceptionally, no tool call comes back, the note is treated as
    unfileable.
    """
    user_message = (
        "## Note content\n\n"
        f"{content}\n\n"
        "## Vault index\n\n"
        f"{json.dumps(index, ensure_ascii=False)}"
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=MAX_TOKENS,
        system=system_prompt,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": CLASSIFY_TOOL["name"]},
        messages=[{"role": "user", "content": user_message}],
    )

    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == CLASSIFY_TOOL["name"]:
            return dict(block.input)

    print("  ! Model returned no tool_use decision.", file=sys.stderr)
    return {
        "status": "unfileable",
        "reason": "Model did not return a structured classification decision.",
    }


# --- Filing ------------------------------------------------------------------

def apply_filed(md_file: Path, decision: dict, index: dict,
                processing_date: str) -> dict | None:
    """Enrich and move a filed note; update the index in place.

    Returns an outcome dict for the commit message, or ``None`` if the decision
    had to be rejected (in which case the note is left in the Inbox).
    """
    domain = decision.get("domain")
    para = decision.get("para")
    target_path = decision.get("target_path")

    if not domain or para not in ALLOWED_PARA_ROOTS or not target_path:
        print(f"  ! Rejected decision for {md_file.name}: incomplete or invalid "
              f"fields. Left in Inbox.")
        return None

    dest = resolve_safe_target(target_path)
    if dest is None:
        print(f"  ! Rejected target_path '{target_path}' for {md_file.name}: "
              f"outside allowed PARA roots. Left in Inbox.")
        return None

    tags = decision.get("tags") or []
    project = decision.get("project")
    # Resolve the model's title-based links to Obsidian-resolvable basename links.
    wikilinks = resolve_wikilinks(decision.get("wikilinks") or [], index)

    original = md_file.read_text(encoding="utf-8")

    # Merge the mandatory metadata into any frontmatter the note already carries
    # (templated notes bring their own); existing fields are kept verbatim, only
    # missing mandatory ones are added — so we never stack two `---` blocks.
    frontmatter, note_body, effective = merge_frontmatter(
        original, domain=domain, tags=tags, date=processing_date,
        para=para, project=project,
    )
    title = extract_title(note_body, md_file.stem)

    # Format the Markdown body (captured content + generated Links section) but
    # keep the merged frontmatter out of the formatter, then reattach it.
    markdown_body = note_body
    if wikilinks:
        markdown_body += build_links_section(wikilinks)
    markdown_body = format_markdown(markdown_body)

    body = frontmatter + markdown_body

    dest = unique_destination(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(body, encoding="utf-8")
    md_file.unlink()  # remove from Inbox only — the source we just relocated

    rel_dest = dest.relative_to(REPO_ROOT).as_posix()

    # --- Index update --------------------------------------------------------
    # Mirror the note's effective metadata (existing frontmatter wins over the
    # model's values for any field the note already defined) into the index.
    eff_domain = effective["domain"] or domain
    eff_tags = effective["tags"] or []
    index.setdefault("notes", []).append({
        "title": title,
        "path": rel_dest,
        "domain": eff_domain,
        "tags": eff_tags,
        "para": effective["para"],
        "project": effective["project"],
        "date": effective["date"],
    })

    domains = index.setdefault("domains", [])
    if eff_domain and eff_domain not in domains:
        domains.append(eff_domain)

    index_tags = index.setdefault("tags", [])
    for tag in eff_tags:
        if tag not in index_tags:
            index_tags.append(tag)

    print(f"  ✓ Filed {md_file.name} → {rel_dest}")
    return {
        "status": "filed",
        "filename": md_file.name,
        "target_path": rel_dest,
    }


# --- Commit message ----------------------------------------------------------

def format_outcome_line(outcome: dict) -> str:
    if outcome["status"] == "filed":
        return f"organize {outcome['filename']} → {outcome['target_path']}"
    return f"unfileable {outcome['filename']} — {outcome['reason']}"


def build_commit_message(outcomes: list[dict]) -> str:
    if len(outcomes) == 1:
        return f"chore(llm): {format_outcome_line(outcomes[0])}"

    header = f"chore(llm): process {len(outcomes)} inbox notes"
    body = "\n".join(f"- {format_outcome_line(o)}" for o in outcomes)
    return f"{header}\n\n{body}"


# --- Git ---------------------------------------------------------------------

def commit_and_push(repo: git.Repo, message: str) -> None:
    repo.git.add(A=True)
    if not repo.git.diff("--cached", "--name-only").strip():
        print("No changes to commit.")
        return
    repo.git.commit("-m", message)
    try:
        repo.git.push()
        print("Pushed changes to remote.")
    except git.GitCommandError as exc:
        print(f"! Push failed: {exc}", file=sys.stderr)


# --- Main --------------------------------------------------------------------

def process_notes(client: Anthropic, system_prompt: str,
                  inbox_notes: list[Path], processing_date: str) -> list[dict]:
    """Classify, enrich and file each Inbox note. Returns per-note outcomes.

    This is the pure pipeline (Steps 1–2): no git side effects, so it can be
    driven directly by tests against an isolated vault.
    """
    outcomes: list[dict] = []

    for md_file in inbox_notes:
        print(f"- {md_file.name}")
        content = md_file.read_text(encoding="utf-8")
        index = load_index()

        decision = classify_note(client, system_prompt, content, index)
        status = decision.get("status")

        if status == "filed":
            outcome = apply_filed(md_file, decision, index, processing_date)
            if outcome is not None:
                save_index(index)
                outcomes.append(outcome)
            else:
                # Decision rejected for safety; record as unfileable, keep file.
                reason = "Filing decision rejected by safety checks."
                print(f"  · Unfileable: {reason}")
                outcomes.append({
                    "status": "unfileable",
                    "filename": md_file.name,
                    "reason": reason,
                })
        else:
            # Step 2 (unfileable) — leave the note in Inbox, print the reason.
            reason = decision.get("reason", "No reason provided.")
            print(f"  · Unfileable: {reason}")
            outcomes.append({
                "status": "unfileable",
                "filename": md_file.name,
                "reason": reason,
            })

    return outcomes


def main(commit: bool = True) -> int:
    # Step 0 — Guard: no Inbox notes means no work and no API call.
    inbox_notes = sorted(p for p in INBOX_DIR.glob("*.md") if p.is_file())
    if not inbox_notes:
        print("Inbox is empty. Nothing to process.")
        return 0

    processing_date = date.today().isoformat()
    system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
    client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment

    # Sync the active-project list from the Projects/ folder before filing, so
    # the LLM classifies against the projects that actually exist on disk. Each
    # note in process_notes reloads the index from disk, so persist the change.
    index = load_index()
    if sync_projects(index):
        save_index(index)
        print(f"Detected projects: {index['projects'] or '(none)'}")

    print(f"Processing {len(inbox_notes)} note(s) from Inbox...")
    outcomes = process_notes(client, system_prompt, inbox_notes, processing_date)

    # Step 3 — Commit and push the whole run as one record.
    if commit:
        repo = git.Repo(REPO_ROOT)
        commit_and_push(repo, build_commit_message(outcomes))
    return 0


if __name__ == "__main__":
    sys.exit(main())
