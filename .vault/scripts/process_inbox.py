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


# --- Index reconciliation ----------------------------------------------------

def scan_filed_notes() -> dict[str, Path]:
    """Map every filed note's repo-relative path to its file, across PARA roots.

    Walks the four PARA roots recursively (only ``Projects/`` nests, one level
    deep). ``Atlas/``, ``Templates/``, ``Attachments/`` and ``Inbox/`` are
    deliberately not scanned — they are never part of the index.
    """
    found: dict[str, Path] = {}
    for root in sorted(ALLOWED_PARA_ROOTS):
        base = REPO_ROOT / root
        if not base.is_dir():
            continue
        for path in base.rglob("*.md"):
            if path.is_file():
                found[path.relative_to(REPO_ROOT).as_posix()] = path
    return found


def entry_from_file(rel_path: str, path: Path, existing: dict | None) -> dict:
    """Build an index entry from a filed note's current on-disk state.

    ``para``/``project`` are derived from the file's *location* (authoritative
    for where the note physically lives, so a hand-moved note self-corrects);
    ``domain``/``tags``/``date`` are read from its frontmatter and ``title`` from
    its first H1. A missing ``date`` falls back to the note's existing index
    entry, so a hand-written note without one does not churn the index.
    """
    text = path.read_text(encoding="utf-8")
    inner, body = split_frontmatter(text)
    values = parse_frontmatter(inner)[1] if inner else {}

    parts = Path(rel_path).parts
    para = parts[0]
    project = parts[1] if para == "Projects" and len(parts) > 2 else None

    tags = values.get("tags")
    if not isinstance(tags, list):
        tags = [tags] if tags else []

    return {
        "title": extract_title(body, path.stem),
        "path": rel_path,
        "domain": values.get("domain"),
        "tags": tags,
        "para": para,
        "project": project,
        "date": values.get("date") or (existing or {}).get("date"),
    }


def collect_canonical(existing: list[str], in_use: list[str]) -> list[str]:
    """Canonical list of the values actually in use, stable for diffs.

    Keeps the existing entries that are still in use in their current order (so
    the file does not churn), then appends any newly seen values in order of
    first appearance. Values no note uses any more are dropped — the list is
    defined as the domains/tags currently *in use*.
    """
    in_use_set = set(in_use)
    result: list[str] = []
    seen: set[str] = set()
    for value in [*existing, *in_use]:
        if value in in_use_set and value not in seen:
            result.append(value)
            seen.add(value)
    return result


def reconcile_index(index: dict) -> bool:
    """Re-derive the index entries from the vault's filed notes on disk.

    The index is the LLM's only source of truth, but a user may edit a filed
    note's frontmatter or rename its title by hand — and the filing pipeline,
    which only ever writes the *new* note it just filed, would never propagate
    those edits. This refreshes every indexed note from its file, drops entries
    whose file is gone, adds notes that appeared on disk, and recomputes the
    ``domains``/``tags`` canonical lists from actual usage. Returns ``True`` if
    anything changed, so the caller can persist and commit the correction.
    """
    on_disk = scan_filed_notes()
    old_notes = index.get("notes", [])

    notes: list[dict] = []
    seen: set[str] = set()
    # Refresh notes already in the index in their current order (diff-friendly);
    # drop any whose file no longer exists.
    for note in old_notes:
        rel = note.get("path")
        if rel in on_disk and rel not in seen:
            notes.append(entry_from_file(rel, on_disk[rel], note))
            seen.add(rel)
    # Append notes present on disk but never indexed (created or moved in by
    # hand), sorted for a stable order.
    for rel in sorted(on_disk):
        if rel not in seen:
            notes.append(entry_from_file(rel, on_disk[rel], None))
            seen.add(rel)

    domains = collect_canonical(index.get("domains", []),
                                [n["domain"] for n in notes if n["domain"]])
    tags = collect_canonical(index.get("tags", []),
                             [t for n in notes for t in n["tags"]])

    if (notes == old_notes and domains == index.get("domains", [])
            and tags == index.get("tags", [])):
        return False

    index["notes"], index["domains"], index["tags"] = notes, domains, tags
    return True


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


def build_target_path(para: str, project: str | None, filename: str) -> str | None:
    """Compose a repo-relative target path from placement fields + filename.

    ``Projects`` notes live one subfolder deep (``Projects/<project>/file.md``);
    the other PARA roots are flat. Returns a POSIX path string, or ``None`` when
    the inputs are inconsistent (an unknown root, a missing filename, or
    ``para == "Projects"`` with no project). Path *safety* — escapes, forbidden
    roots — is still enforced afterwards by ``resolve_safe_target``.
    """
    if para not in ALLOWED_PARA_ROOTS or not filename:
        return None
    if para == "Projects":
        if not project:
            return None
        return f"Projects/{project}/{filename}"
    return f"{para}/{filename}"


def reconcile_placement(original: str, model_para: str,
                        model_project: str | None) -> tuple[str, str | None]:
    """Let a note's own frontmatter override the model's placement.

    Returns the ``(para, project)`` that win. A note captured with an explicit
    ``para`` (and optionally ``project``) is filed where it says, not where the
    model guessed — this is the deterministic, opt-in escape hatch for the cases
    where the human disagrees with the classifier (e.g. durable reference that
    relates to an active project but belongs in ``Resources``). Rules:

    - an explicit valid ``para`` in the note wins;
    - rerouting to a *different* root than the model chose drops the model's
      project association — a flat root (Areas/Resources/Archive) carries none;
    - an explicit ``project`` in the note wins over the model's.

    A non-``Projects`` root is forced to ``project = None``; the caller rejects
    the incoherent ``Projects``-without-a-project case.
    """
    inner, _ = split_frontmatter(original)
    user_fm = parse_frontmatter(inner)[1] if inner else {}

    para, project = model_para, model_project
    user_para = user_fm.get("para")
    if user_para in ALLOWED_PARA_ROOTS:
        para = user_para
        if user_para != model_para:
            project = None
    if "project" in user_fm:
        project = user_fm["project"] or None
    if para != "Projects":
        project = None
    return para, project


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

    # Capture-time placement override: a note's own frontmatter wins over the
    # model for where it is filed. Reconcile para/project *before* merging so the
    # written frontmatter, the physical destination and the index all agree.
    # Rules: an explicit `para`/`project` in the note overrides the model's; a
    # reroute to a *different* root drops the model's project (a flat root carries
    # none); and `Projects` without a project is incoherent → rejected below.
    para, project = reconcile_placement(original, para, project)

    placement = build_target_path(para, project, dest.name)
    if placement is None:
        print(f"  ! Rejected {md_file.name}: inconsistent placement override "
              f"(para={para!r}, project={project!r}). Left in Inbox.")
        return None
    dest = resolve_safe_target(placement)
    if dest is None:
        print(f"  ! Rejected placement '{placement}' for {md_file.name}: outside "
              f"allowed PARA roots. Left in Inbox.")
        return None

    # Merge the mandatory metadata into any frontmatter the note already carries
    # (templated notes bring their own); existing fields are kept verbatim, only
    # missing mandatory ones are added — so we never stack two `---` blocks. The
    # reconciled para/project are passed in so a freshly added project field is
    # coherent with the chosen root.
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
    processing_date = date.today().isoformat()

    # Step 0 — Verify the index against the vault, every push. Sync the active
    # projects from the Projects/ folder and reconcile every filed note's entry
    # with its on-disk frontmatter, title and location, so manual edits reach the
    # index even when the Inbox is empty (no API call is made here). process_notes
    # reloads the index from disk per note, so persist the correction first.
    index = load_index()
    index_changed = sync_projects(index)
    index_changed |= reconcile_index(index)
    if index_changed:
        save_index(index)
        print("Index verified and updated to match the vault's on-disk state.")

    # Step 1–2 — File the Inbox. Guarded: an empty Inbox means no work and no API
    # call (controlled cost), but the reconciliation above still ran.
    inbox_notes = sorted(p for p in INBOX_DIR.glob("*.md") if p.is_file())
    outcomes: list[dict] = []
    if inbox_notes:
        system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
        print(f"Processing {len(inbox_notes)} note(s) from Inbox...")
        outcomes = process_notes(client, system_prompt, inbox_notes, processing_date)
    else:
        print("Inbox is empty. Nothing to file.")

    # Step 3 — Commit and push the whole run as one record. When nothing was
    # filed, only the index correction (if any) is recorded; commit_and_push is a
    # no-op when the tree is clean, so a fully in-sync vault pushes nothing.
    if commit:
        repo = git.Repo(REPO_ROOT)
        message = (build_commit_message(outcomes) if outcomes
                   else "chore(llm): reconcile vault index")
        commit_and_push(repo, message)
    return 0


if __name__ == "__main__":
    sys.exit(main())
