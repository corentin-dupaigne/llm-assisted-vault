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

import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import date, datetime
from pathlib import Path

import git
import mdformat
import yaml
from anthropic import Anthropic, APIError

# --- Paths and constants -----------------------------------------------------

# This script lives at `.vault/scripts/`, so its grandparent is `.vault/` (the
# machinery dir) and the vault root one level up holds the PARA folders + `.git`.
VAULT_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = VAULT_DIR.parent
INBOX_DIR = REPO_ROOT / "Inbox"
PROJECTS_DIR = REPO_ROOT / "Projects"
AREAS_DIR = REPO_ROOT / "Areas"
ATLAS_DIR = REPO_ROOT / "Atlas"
MOC_TEMPLATE_PATH = REPO_ROOT / "Templates" / "moc.md"

# Notes placed directly in these folders (not via the Inbox) are enriched in
# place when they carry no `domain`. Archive is left alone: enriching inactive
# notes is not worth an API call.
ENRICH_ROOTS = ("Projects", "Areas", "Resources")
# Cap per run so a large backlog (e.g. an imported vault) is spread over pushes.
ENRICH_MAX_PER_RUN = int(os.environ.get("VAULT_ENRICH_MAX_PER_RUN") or 20)
# A domain with at least this many notes and no MOC in Atlas/ gets one.
MOC_MIN_NOTES = int(os.environ.get("VAULT_MOC_MIN_NOTES") or 5)
INDEX_PATH = VAULT_DIR / "vault.index.json"
# Content hashes of Inbox notes the last run could not file, so an unchanged
# unfileable note is not re-sent to the API on every push (controlled cost).
UNFILEABLE_STATE_PATH = VAULT_DIR / "unfileable.json"
SYSTEM_PROMPT_PATH = VAULT_DIR / "prompts" / "system.md"
# Optional `{"variant": "canonical"}` map applied to the model's domain and tags.
ALIASES_PATH = VAULT_DIR / "aliases.json"

# Overridable for experiments (e.g. `VAULT_MODEL=claude-haiku-4-5`); see
# `.vault/scripts/eval.py` to measure a model against the vault history first.
MODEL = os.environ.get("VAULT_MODEL") or "claude-sonnet-4-6"
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
                "description": "Full destination path including a readable "
                               "filename (the note's title, with spaces), e.g. "
                               "'Resources/Contains Duplicate.md'.",
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
            "area": {
                "type": ["string", "null"],
                "description": "Area name when para is 'Areas' and one of the listed "
                               "areas fits, otherwise null.",
            },
            "wikilinks": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Links to relevant existing notes, built from each "
                               "note's title (which is its filename), e.g. "
                               "'[[Contains Duplicate]]'. Use the exact title as "
                               "it appears in the index.",
            },
        },
        "required": ["status", "reason"],
        "additionalProperties": False,
    },
}

# Models that reject a forced tool call (`tool_choice` `tool`/`any` is a 400).
# For them `file_note` is offered with `tool_choice: auto` and a strict schema,
# the prompt asks for the call, and a reply without one is retried once. They
# think by default, so they run at `low` effort with room for that thinking, and
# opt into server-side fallback on a policy decline.
AUTO_TOOL_MODELS = ("claude-sonnet-5-5", "claude-opus-5-5", "claude-fable-5-1")
AUTO_TOOL_MAX_TOKENS = 8000
FALLBACK_BETA = "server-side-fallback-2026-07-01"


def forces_tool_call(model: str) -> bool:
    return not model.startswith(AUTO_TOOL_MODELS)

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


# --- Unfileable state --------------------------------------------------------

def load_unfileable_state() -> dict:
    """``{inbox filename: {"sha256", "reason", "date"}}`` for notes left in the
    Inbox by a previous run. Missing file means no state yet."""
    if not UNFILEABLE_STATE_PATH.is_file():
        return {}
    with UNFILEABLE_STATE_PATH.open(encoding="utf-8") as fh:
        return json.load(fh)


def save_unfileable_state(state: dict) -> None:
    with UNFILEABLE_STATE_PATH.open("w", encoding="utf-8") as fh:
        json.dump(state, fh, indent=2, ensure_ascii=False, sort_keys=True)
        fh.write("\n")


def prune_unfileable_state() -> bool:
    """Drop state for notes that are gone (filed, renamed or deleted by hand).
    Keys are Inbox filenames, or repo-relative paths for notes enriched in
    place. Returns ``True`` if the state file changed."""
    state = load_unfileable_state()
    kept = {name: entry for name, entry in state.items()
            if (INBOX_DIR / name).is_file() or (REPO_ROOT / name).is_file()}
    if kept == state:
        return False
    save_unfileable_state(kept)
    return True


def content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# --- Project and area detection ---------------------------------------------

def detect_folders(root: Path) -> list[str]:
    """Immediate subfolders of ``root``, sorted for a stable, diff-friendly index.

    One subfolder per active project (``Projects/``) or area of responsibility
    (``Areas/``) is the on-disk convention (see CLAUDE.md), so the folder listing
    is the source of truth.
    """
    if not root.is_dir():
        return []
    return sorted(p.name for p in root.iterdir() if p.is_dir())


def detect_projects() -> list[str]:
    """Active project names = the immediate subfolders of ``Projects/``."""
    return detect_folders(PROJECTS_DIR)


def detect_areas() -> list[str]:
    """Area names = the immediate subfolders of ``Areas/``."""
    return detect_folders(AREAS_DIR)


def sync_projects(index: dict) -> bool:
    """Refresh ``index['projects']`` and ``index['areas']`` from the folders.

    Returns ``True`` if the index changed, so the caller can decide whether to
    persist it. The folder listing is authoritative: entries whose folder no
    longer exists are dropped, newly created folders are added. ``areas`` is only
    written once an area folder exists, so a vault without areas keeps its index.
    """
    changed = False
    detected = detect_projects()
    if index.get("projects") != detected:
        index["projects"] = detected
        changed = True
    areas = detect_areas()
    if areas != (index.get("areas") or []):
        index["areas"] = areas
        changed = True
    return changed


# --- Note helpers ------------------------------------------------------------

def read_note(path: Path) -> str:
    """Read a note normalised to LF line endings, without a UTF-8 BOM.

    Notes written on Windows or by some mobile editors use CRLF; the frontmatter
    regex only matches ``---\\n``, so an un-normalised note would get a second
    frontmatter block stacked on top and its own turned into body text.
    """
    text = path.read_text(encoding="utf-8-sig")
    return text.replace("\r\n", "\n").replace("\r", "\n")


def title_from_stem(stem: str) -> str:
    """A filed note's title is its filename stem — the human-readable name the
    user gave the capture. Used verbatim (only trimmed) so acronyms and casing
    are preserved (``ArgoCD``, ``CRDs``, ``PV, PVC``). The note body — including
    any heading — is never inspected; titles come from the filename alone."""
    return stem.strip()


# Characters forbidden in (or hostile to) a note filename: the OS/Obsidian-illegal
# set plus the wikilink-significant `# ^ [ ]` and the alias pipe `|`.
_FILENAME_FORBIDDEN_RE = re.compile(r'[:?*"<>|#^\[\]]')
_FILENAME_SLASH_RE = re.compile(r"[\\/]+")
_FILENAME_WS_RE = re.compile(r"\s+")


def title_to_filename(title: str) -> str:
    """Turn a note's human title into a readable, Obsidian-safe filename.

    Deliberately *not* slugging: spaces and case are preserved so the filename
    reads as the title (``ArgoCD Helm Install No CRDs.md``) and resolves as a
    bare ``[[wikilink]]``. Only the characters that are illegal in a filename or
    that break wikilinks are removed/replaced — the minimal cleanup Obsidian
    itself does (``TCP/IP`` -> ``TCP-IP``, ``What is REST?`` -> ``What is REST``).
    """
    name = _FILENAME_SLASH_RE.sub("-", title)
    name = _FILENAME_FORBIDDEN_RE.sub("", name)
    name = _FILENAME_WS_RE.sub(" ", name).strip(" .")
    return f"{name or 'untitled'}.md"


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


def _plain_value(value):
    """Map a YAML-loaded value onto the JSON-friendly shapes the index stores:
    dates become ISO strings, list items and other scalars become strings."""
    if value is None or isinstance(value, str):
        return value
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, list):
        return [_plain_value(v) for v in value if v is not None]
    if isinstance(value, dict):
        return value
    return str(value)


def parse_frontmatter(inner: str) -> tuple[list[str], dict]:
    """Parse a frontmatter block into ``(ordered_keys, values)``.

    Uses a real YAML parser so quoted values (``domain: "go"``), nested and
    multi-line values read correctly. Falls back to a lenient line parser when
    the block is not valid YAML (hand-written notes often are not). Used only to
    read existing values; the original lines are preserved verbatim when
    re-emitting.
    """
    try:
        data = yaml.safe_load(inner)
    except yaml.YAMLError:
        data = None
    if isinstance(data, dict):
        keys = [str(k) for k in data]
        return keys, {str(k): _plain_value(v) for k, v in data.items()}
    return _parse_frontmatter_lenient(inner)


def _unquote(raw: str) -> str:
    """Strip whitespace and one pair of matching surrounding quotes."""
    raw = raw.strip()
    if len(raw) >= 2 and raw[0] == raw[-1] and raw[0] in "\"'":
        return raw[1:-1]
    return raw


def _parse_frontmatter_lenient(inner: str) -> tuple[list[str], dict]:
    """Line-based fallback for frontmatter that is not valid YAML.

    Supports the scalar, flow-list (`[a, b]`) and block-list (`- a`) forms that
    appear in hand-written and templated notes.
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
                items.append(_unquote(_FM_LIST_ITEM_RE.match(lines[j]).group(1)))
                j += 1
            if items:
                values[key] = items
                i = j
                continue
            values[key] = None
        elif raw.startswith("[") and raw.endswith("]"):
            body = raw[1:-1].strip()
            values[key] = [_unquote(t) for t in body.split(",") if t.strip()] if body else []
        elif raw in ("null", "~"):
            values[key] = None
        else:
            values[key] = _unquote(raw)
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
                      para: str, project: str | None,
                      area: str | None = None) -> tuple[str, str, dict]:
    """Merge the mandatory metadata into a note's existing frontmatter.

    Captured notes may already carry frontmatter (e.g. Obsidian/Dataview
    templates). Existing fields — mandatory or not — are kept **verbatim** and
    never overridden; only the mandatory fields that are *missing* are appended,
    so the result is always a single frontmatter block. ``area`` is not
    mandatory: it is only added for a note filed into an area subfolder. Returns
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
    if area and "area" not in existing_keys:
        lines.append(f"area: {area}")

    frontmatter = "---\n" + "\n".join(lines) + "\n---\n"

    effective = {
        key: existing_values[key] if key in existing_keys else computed[key]
        for key in MANDATORY_FIELDS
    }
    effective["area"] = existing_values.get("area") or area
    return frontmatter, body, effective


def resolve_wikilinks(raw_links: list[str], index: dict) -> list[str]:
    """Validate the model's wikilinks against the index, as bare ``[[Title]]``.

    Filenames are the readable title now, so Obsidian resolves a link by its
    basename directly — the model is asked to build each link from the target
    note's title (``[[ArgoCD Helm Install No CRDs]]``). This is a safety net over
    that contract: each link is matched against the indexed notes by title *or*
    basename and re-emitted as the canonical basename, so it always resolves. A
    link matching no indexed note (a hallucinated target) is dropped rather than
    written broken — that is what would otherwise spawn a stray note.
    """
    by_title: dict[str, str] = {}   # title -> file basename
    by_stem: set[str] = set()       # known file basenames
    for note in index.get("notes", []):
        path = note.get("path")
        if not path:
            continue
        stem = Path(path).stem
        by_stem.add(stem)
        if note.get("title"):
            by_title[note["title"]] = stem

    resolved: list[str] = []
    seen: set[str] = set()
    for raw in raw_links:
        # Accept whatever the model emitted ([[Title]], [[Title|alias]], a name
        # with .md, or a path) and reduce it to the target text to match on.
        target = raw.strip().strip("[]").split("|", 1)[0].strip()
        if target.endswith(".md"):
            target = target[:-3]
        stem = by_title.get(target)
        if stem is None:
            cand = target.rsplit("/", 1)[-1]  # last path component, if any
            stem = cand if cand in by_stem else (target if target in by_stem else None)
        if stem and stem not in seen:
            resolved.append(f"[[{stem}]]")
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


def placement_of(rel_path: str) -> tuple[str, str | None, str | None]:
    """``(para, project, area)`` implied by a note's repo-relative location."""
    parts = Path(rel_path).parts
    para = parts[0]
    project = parts[1] if para == "Projects" and len(parts) > 2 else None
    area = parts[1] if para == "Areas" and len(parts) > 2 else None
    return para, project, area


def entry_from_file(rel_path: str, path: Path, existing: dict | None) -> dict:
    """Build an index entry from a filed note's current on-disk state.

    ``para``/``project`` are derived from the file's *location* (authoritative
    for where the note physically lives, so a hand-moved note self-corrects);
    ``domain``/``tags``/``date`` are read from its frontmatter and ``title`` is
    its filename. A missing ``date`` falls back to the note's existing index
    entry, so a hand-written note without one does not churn the index.
    """
    text = read_note(path)
    inner, _ = split_frontmatter(text)
    values = parse_frontmatter(inner)[1] if inner else {}

    para, project, area = placement_of(rel_path)

    tags = values.get("tags")
    if not isinstance(tags, list):
        tags = [tags] if tags else []

    entry = {
        "title": title_from_stem(path.stem),
        "path": rel_path,
        "domain": values.get("domain"),
        "tags": tags,
        "para": para,
        "project": project,
        "date": values.get("date") or (existing or {}).get("date"),
    }
    if area:  # only for notes in an area subfolder, so older entries don't churn
        entry["area"] = area
    return entry


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


def build_target_path(para: str, project: str | None, filename: str,
                      area: str | None = None) -> str | None:
    """Compose a repo-relative target path from placement fields + filename.

    ``Projects`` notes live one subfolder deep (``Projects/<project>/file.md``);
    ``Areas`` notes in their area's subfolder when they have one
    (``Areas/<area>/file.md``), else at the ``Areas/`` root; the other PARA
    roots are flat. Returns a POSIX path string, or ``None`` when
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
    if para == "Areas" and area:
        return f"Areas/{area}/{filename}"
    return f"{para}/{filename}"


def reconcile_placement(original: str, model_para: str,
                        model_project: str | None,
                        model_area: str | None = None
                        ) -> tuple[str, str | None, str | None]:
    """Let a note's own frontmatter override the model's placement.

    Returns the ``(para, project, area)`` that win. A note captured with an
    explicit ``para`` (and optionally ``project``/``area``) is filed where it
    says, not where the model guessed — this is the deterministic, opt-in escape
    hatch for the cases where the human disagrees with the classifier (e.g.
    durable reference that relates to an active project but belongs in
    ``Resources``). Rules:

    - an explicit valid ``para`` in the note wins;
    - rerouting to a *different* root than the model chose drops the model's
      project and area association;
    - an explicit ``project``/``area`` in the note wins over the model's.

    Only ``Projects`` carries a project and only ``Areas`` an area; the caller
    rejects the incoherent ``Projects``-without-a-project case.
    """
    inner, _ = split_frontmatter(original)
    user_fm = parse_frontmatter(inner)[1] if inner else {}

    para, project, area = model_para, model_project, model_area
    user_para = user_fm.get("para")
    if user_para in ALLOWED_PARA_ROOTS:
        para = user_para
        if user_para != model_para:
            project = area = None
    if "project" in user_fm:
        project = user_fm["project"] or None
    if "area" in user_fm:
        area = user_fm["area"] or None
    if para != "Projects":
        project = None
    if para != "Areas":
        area = None
    return para, project, area


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

def render_index_for_prompt(index: dict) -> str:
    """Render the index as the compact text the model actually needs.

    The model uses the index for two things only: the project/domain/tag
    vocabulary (to classify) and the existing note titles (to pick wikilinks).
    Per-note `path`, `date`, `para` and the repeated JSON keys carry nothing the
    model uses — the code rebuilds the path and resolves links from titles — so
    notes are listed as titles grouped by domain and location, e.g.::

        leetcode @ Projects/neetcode-150: Two Sum | Valid Anagram

    The location keeps the placement precedent ("notes like this went to that
    project") for a few characters per group.
    """
    projects = [p["name"] if isinstance(p, dict) else p
                for p in index.get("projects") or []]
    areas = index.get("areas") or []
    groups: dict[tuple[str, str], list[str]] = {}
    for note in index.get("notes", []):
        project, area = note.get("project"), note.get("area")
        location = (f"Projects/{project}" if project
                    else f"Areas/{area}" if area else (note.get("para") or "?"))
        key = (note.get("domain") or "(no domain)", location)
        groups.setdefault(key, []).append(note.get("title") or "")

    lines = [
        "Active projects: " + (", ".join(projects) or "(none)"),
        "Areas: " + (", ".join(areas) or "(none — Areas notes go to the Areas/ root)"),
        "Domains in use: " + (", ".join(index.get("domains") or []) or "(none)"),
        "Tags in use: " + (", ".join(index.get("tags") or []) or "(none)"),
        "",
        "Existing notes as `domain @ location: title | title | ...`:",
    ]
    lines += [f"{domain} @ {location}: " + " | ".join(titles)
              for (domain, location), titles in groups.items()]
    if not groups:
        lines.append("(no notes yet)")
    return "\n".join(lines)


def build_classification_request(system_prompt: str, content: str, index: dict,
                                 model: str = MODEL,
                                 location: str | None = None) -> dict:
    """The `messages.create` arguments for classifying one note.

    ``location`` is set for a note the user already filed by hand: the model is
    told the placement is decided and only enriches it.
    """
    placed = (
        "## Location\n\n"
        f"The user already filed this note at `{location}`. Do not reclassify "
        "it: set `para`, `project` and `area` to match this location, use "
        "`status: filed`, and provide the domain, tags and wikilinks. Never "
        "link the note to itself.\n\n"
    ) if location else ""
    user_message = (
        "## Note content\n\n"
        f"{content}\n\n"
        f"{placed}"
        "## Vault index\n\n"
        f"{render_index_for_prompt(index)}"
    )
    request = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "system": system_prompt,
        "tools": [CLASSIFY_TOOL],
        "tool_choice": {"type": "tool", "name": CLASSIFY_TOOL["name"]},
        "messages": [{"role": "user", "content": user_message}],
    }
    if not forces_tool_call(model):
        request.update(
            max_tokens=AUTO_TOOL_MAX_TOKENS,
            tools=[{**CLASSIFY_TOOL, "strict": True}],
            tool_choice={"type": "auto"},
            output_config={"effort": "low"},
            betas=[FALLBACK_BETA],
            extra_body={"fallbacks": "default"},
        )
    return request


def send_request(client: Anthropic, request: dict):
    """Send through the beta endpoint when the request carries beta flags."""
    if "betas" in request:
        return client.beta.messages.create(**request)
    return client.messages.create(**request)


def tool_call_input(response) -> dict | None:
    """The `file_note` input of a response, or ``None`` if it made no call.
    Blocks are matched by type, so leading `thinking` blocks are skipped."""
    for block in response.content:
        if getattr(block, "type", None) == "tool_use" and block.name == CLASSIFY_TOOL["name"]:
            return dict(block.input)
    return None


def run_classification(client: Anthropic, request: dict) -> tuple[dict, list]:
    """Send the request and return ``(raw decision, responses)``.

    A policy decline (`stop_reason == "refusal"`) leaves the note unfileable
    with the category as reason. In `auto` tool mode a reply without the tool
    call is retried once. All responses are returned so callers can account
    for usage.
    """
    responses = []
    attempts = 1 if request["tool_choice"]["type"] == "tool" else 2
    for _ in range(attempts):
        response = send_request(client, request)
        responses.append(response)
        if getattr(response, "stop_reason", None) == "refusal":
            details = getattr(response, "stop_details", None)
            category = getattr(details, "category", None) or "unspecified"
            return ({"status": "unfileable",
                     "reason": f"model declined the note (refusal: {category})"}, responses)
        decision = tool_call_input(response)
        if decision is not None:
            return decision, responses

    print("  ! Model returned no tool_use decision.", file=sys.stderr)
    return ({"status": "unfileable",
             "reason": "Model did not return a structured classification decision."},
            responses)


def _as_str_list(value) -> list[str]:
    """Coerce a model-supplied list field to a list of non-empty strings. The
    tool schema is not strictly enforced, and a model may answer ``"devops"``
    or ``"[a, b]"`` where a list is expected — which would otherwise be iterated
    character by character (``tags: [d, e, v, o, p, s]``)."""
    if isinstance(value, str):
        value = value.strip().strip("[]").split(",")
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _label(value: str) -> str:
    """Force a domain/tag into the naming convention: lowercase, hyphen-separated,
    ``[a-z0-9-]`` only (drops stray brackets/quotes a model may leave)."""
    value = re.sub(r"[\s_]+", "-", value.strip().lower())
    value = re.sub(r"[^a-z0-9-]", "", value)
    return re.sub(r"-{2,}", "-", value).strip("-")


def normalize_decision(decision: dict) -> dict:
    """Return the decision with its fields coerced to the expected shapes:
    list fields as lists of strings, domain and tags as convention labels."""
    decision = dict(decision)
    if "wikilinks" in decision:
        decision["wikilinks"] = _as_str_list(decision["wikilinks"])
    if "tags" in decision:
        tags = [_label(t) for t in _as_str_list(decision["tags"])]
        decision["tags"] = list(dict.fromkeys(t for t in tags if t))
    if isinstance(decision.get("domain"), str):
        decision["domain"] = _label(decision["domain"]) or None
    return decision


def label_key(label: str) -> str:
    """Spelling-insensitive key for spotting near-duplicate labels: hyphens are
    ignored and each word loses its trailing ``s`` (``arrays-hashing``,
    ``array-hashing`` and ``arrayhashing`` share a key; so do ``dev-ops`` and
    ``devops``)."""
    return "".join(word.rstrip("s") for word in label.split("-"))


def load_aliases() -> dict[str, str]:
    if not ALIASES_PATH.is_file():
        return {}
    with ALIASES_PATH.open(encoding="utf-8") as fh:
        return {_label(k): _label(v) for k, v in json.load(fh).items()}


def canonicalize_labels(decision: dict, index: dict,
                        aliases: dict[str, str] | None = None) -> dict:
    """Keep the model's domain and tags inside the vault's existing vocabulary.

    Applied after ``normalize_decision``, in this order: an alias from
    ``aliases.json`` wins; otherwise a label that is a near-duplicate of one
    already in use (see ``label_key``) is rewritten to the existing spelling (or
    that spelling's alias) — a domain prefers existing domains, a tag existing
    tags; then tags are
    de-duplicated and the domain is removed from them (a note's domain is never
    also its tag). Only the model's values pass through here; a note's own
    frontmatter is kept verbatim by ``merge_frontmatter``.
    """
    aliases = load_aliases() if aliases is None else aliases
    domains = index.get("domains") or []
    tags = index.get("tags") or []

    def canonical(label: str, first: list[str], second: list[str]) -> str:
        if label in aliases:
            return aliases[label]
        key = label_key(label)
        for existing in [*first, *second]:
            if label_key(existing) == key:
                return aliases.get(existing, existing)  # never snap back to an alias
        return label

    decision = dict(decision)
    domain = decision.get("domain")
    if domain:
        decision["domain"] = domain = canonical(domain, domains, tags)
    if "tags" in decision:
        canon = [canonical(t, tags, domains) for t in decision["tags"]]
        decision["tags"] = [t for t in dict.fromkeys(canon) if t != domain]
    return decision


def known_projects(index: dict) -> set[str]:
    return {p["name"] if isinstance(p, dict) else p for p in index.get("projects") or []}


def invented_folder(original: str, para: str, project: str | None,
                    area: str | None, index: dict) -> str | None:
    """Why the note would go to a project or area the model made up, else ``None``.

    The model may only file into an existing project or area (one folder under
    ``Projects/`` or ``Areas/``); without this check an invented name would
    silently create a new folder. A project or area the user declared in the
    note's own frontmatter is their decision and is always allowed.
    """
    inner, _ = split_frontmatter(original)
    declared = parse_frontmatter(inner)[1] if inner else {}
    if (para == "Projects" and project and project not in known_projects(index)
            and project != declared.get("project")):
        return f"model chose unknown project {project!r}"
    if (para == "Areas" and area and area not in (index.get("areas") or [])
            and area != declared.get("area")):
        return f"model chose unknown area {area!r}"
    return None


def classify_note(client: Anthropic, system_prompt: str, content: str,
                  index: dict, location: str | None = None) -> dict:
    """Call Claude and return the normalized decision dict.

    The model is made (forced tool use) or asked (`auto` on models that reject
    forcing) to call `file_note`; its already-parsed `input` is the decision. If
    no tool call comes back, or the model declines, the note is unfileable.
    """
    request = build_classification_request(system_prompt, content, index,
                                           location=location)
    decision, _ = run_classification(client, request)
    return canonicalize_labels(normalize_decision(decision), index)


# --- Filing ------------------------------------------------------------------

def _rejected(md_file: Path, reason: str) -> dict:
    """Outcome for a filing decision refused by the code-side checks. The note
    stays in the Inbox and the specific reason reaches the commit message."""
    print(f"  ! Rejected {md_file.name}: {reason}. Left in Inbox.")
    return {
        "status": "unfileable",
        "filename": md_file.name,
        "reason": f"rejected: {reason}",
    }


def apply_filed(md_file: Path, decision: dict, index: dict,
                processing_date: str) -> dict:
    """Enrich and move a filed note; update the index in place.

    Returns the outcome dict for the commit message: ``status == "filed"`` on
    success, or ``"unfileable"`` with the rejection reason when the decision
    fails a safety check (in which case the note is left in the Inbox and the
    index is untouched).
    """
    domain = decision.get("domain")
    para = decision.get("para")
    target_path = decision.get("target_path")

    missing = [name for name, value in (("domain", domain),
                                        ("target_path", target_path)) if not value]
    if missing:
        return _rejected(md_file, f"model omitted {', '.join(missing)}")
    if para not in ALLOWED_PARA_ROOTS:
        return _rejected(md_file, f"invalid para {para!r} from model")

    tags = decision.get("tags") or []
    project = decision.get("project")
    area = decision.get("area")
    # Validate the model's links against the index and reduce them to bare,
    # resolvable [[Title]] wikilinks (the filename is the readable title now).
    wikilinks = resolve_wikilinks(decision.get("wikilinks") or [], index)

    original = read_note(md_file)

    # The note's human-readable name is its Inbox filename. The destination
    # filename is derived from it — kept readable and Obsidian-safe rather than
    # slugified — so the note reads as its title across Obsidian and resolves as a
    # bare [[wikilink]]. The model's target_path is only a completeness signal;
    # the actual filename is taken from the title in code.
    title = title_from_stem(md_file.stem)
    filename = title_to_filename(title)

    # Capture-time placement override: a note's own frontmatter wins over the
    # model for where it is filed. Reconcile para/project *before* composing the
    # destination so the written frontmatter, the physical location and the index
    # all agree. Rules: an explicit `para`/`project` in the note overrides the
    # model's; a reroute to a *different* root drops the model's project (a flat
    # root carries none); and `Projects` without a project is incoherent → below.
    para, project, area = reconcile_placement(original, para, project, area)

    invented = invented_folder(original, para, project, area, index)
    if invented:
        return _rejected(md_file, invented)
    placement = build_target_path(para, project, filename, area)
    if placement is None:
        return _rejected(md_file, f"inconsistent placement (para={para!r}, "
                                  f"project={project!r})")
    dest = resolve_safe_target(placement)
    if dest is None:
        return _rejected(md_file, f"placement {placement!r} is outside the "
                                  f"allowed PARA roots")

    # Merge the mandatory metadata into any frontmatter the note already carries
    # (templated notes bring their own); existing fields are kept verbatim, only
    # missing mandatory ones are added — so we never stack two `---` blocks. The
    # reconciled para/project are passed in so a freshly added project field is
    # coherent with the chosen root.
    frontmatter, note_body, effective = merge_frontmatter(
        original, domain=domain, tags=tags, date=processing_date,
        para=para, project=project, area=area,
    )

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
        **({"area": effective["area"]} if effective["area"] else {}),
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


# --- In-place enrichment ----------------------------------------------------

def needs_enrichment(path: Path) -> bool:
    """A note the user put straight into a PARA folder and that was never
    processed: it has content but no ``domain``. Once enriched it has one, so it
    is never touched again. ``llm: skip`` in its frontmatter opts it out."""
    inner, body = split_frontmatter(read_note(path))
    values = parse_frontmatter(inner)[1] if inner else {}
    if values.get("domain") or not body.strip():
        return False
    return str(values.get("llm") or "").lower() != "skip"


def find_unenriched() -> list[Path]:
    """Notes needing enrichment across ``ENRICH_ROOTS``, in a stable order."""
    found: list[Path] = []
    for root in ENRICH_ROOTS:
        base = REPO_ROOT / root
        if base.is_dir():
            found += [p for p in sorted(base.rglob("*.md"))
                      if p.is_file() and needs_enrichment(p)]
    return found


_LINKS_HEADING_RE = re.compile(r"^## Links\s*$", re.MULTILINE)


def apply_in_place(path: Path, decision: dict, index: dict,
                   processing_date: str) -> dict:
    """Add the missing metadata and links to a note filed by hand.

    The location is the user's decision: the note is never moved, and
    ``para``/``project``/``area`` come from its folder. Only missing frontmatter
    fields are added and a ``## Links`` section is appended (unless the note has
    one); the body is otherwise left byte-for-byte as written — no reformatting,
    since the user may still be editing it. If the model would have placed the
    note elsewhere, that is returned as a hint for the commit message only.
    """
    rel = path.relative_to(REPO_ROOT).as_posix()
    domain = decision.get("domain")
    if not domain:
        return {"status": "unfileable", "filename": rel,
                "reason": "rejected: model omitted domain"}
    para, project, area = placement_of(rel)
    original = read_note(path)
    frontmatter, body, _ = merge_frontmatter(
        original, domain=domain, tags=decision.get("tags") or [],
        date=processing_date, para=para, project=project, area=area)

    links = [link for link in resolve_wikilinks(decision.get("wikilinks") or [], index)
             if link != f"[[{path.stem}]]"]
    if links and not _LINKS_HEADING_RE.search(body):
        body = body.rstrip("\n") + "\n" + build_links_section(links)
    path.write_text(frontmatter + body, encoding="utf-8")

    outcome = {"status": "enriched", "filename": rel}
    model_place = (decision.get("para"), decision.get("project") or None,
                   decision.get("area") or None)
    if model_place[0] and model_place != (para, project, area):
        where = "/".join(part for part in model_place if part)
        outcome["hint"] = f"model would have filed it under {where}"
    print(f"  ✓ Enriched {rel} in place")
    return outcome


def process_in_place(client: Anthropic, system_prompt: str, paths: list[Path],
                     processing_date: str) -> list[dict]:
    """Enrich notes filed by hand (see ``apply_in_place``). Same cost guards as
    the Inbox: a note unchanged since it came back unfileable is skipped, and an
    API error is recorded without stopping the run. The index is refreshed from
    disk afterwards."""
    outcomes: list[dict] = []
    state = load_unfileable_state()
    state_before = dict(state)

    for path in paths:
        rel = path.relative_to(REPO_ROOT).as_posix()
        print(f"- {rel} (in place)")
        content = read_note(path)
        digest = content_hash(content)
        if state.get(rel, {}).get("sha256") == digest:
            print("  · Skipped: unchanged since it was found unfileable.")
            continue

        index = load_index()
        try:
            decision = classify_note(client, system_prompt, content, index,
                                     location=rel)
        except APIError as exc:
            reason = f"API error: {type(exc).__name__}: {exc}"[:200]
            print(f"  ! {reason}", file=sys.stderr)
            outcomes.append({"status": "error", "filename": rel, "reason": reason})
            continue

        if decision.get("status") == "filed":
            outcome = apply_in_place(path, decision, index, processing_date)
        else:
            outcome = {"status": "unfileable", "filename": rel,
                       "reason": decision.get("reason", "No reason provided.")}
            print(f"  · Not enriched: {outcome['reason']}")

        if outcome["status"] == "unfileable":
            state[rel] = {"sha256": digest, "reason": outcome["reason"],
                          "date": processing_date}
        else:
            state.pop(rel, None)
            index = load_index()
            if reconcile_index(index):
                save_index(index)
        outcomes.append(outcome)

    if state != state_before:
        save_unfileable_state(state)
    return outcomes


# --- Maps of Content -----------------------------------------------------------

_TEMPLATER_BLOCK_RE = re.compile(r"<%\*.*?%>\n?", re.DOTALL)

DEFAULT_MOC = """---
type: moc
theme: {theme}
created: {created}
---
# {title} — Map of Content

## Primary notes

```dataview
LIST
FROM "Projects" OR "Areas" OR "Resources" OR "Archive"
WHERE domain = this.theme
SORT date DESC
```

## Related notes

```dataview
LIST
FROM "Projects" OR "Areas" OR "Resources" OR "Archive"
WHERE contains(tags, this.theme) AND domain != this.theme
SORT date DESC
```
"""


def moc_title(domain: str) -> str:
    return " ".join(word.capitalize() for word in domain.split("-"))


def render_moc(domain: str, created: str) -> str:
    """The MOC for ``domain``, rendered from the user's ``Templates/moc.md``.

    Both template syntaxes are filled in: Templater (``<% title %>``,
    ``<% theme %>``, ``<% tp.date.now("YYYY-MM-DD") %>``, with its prompt block
    dropped) and Obsidian core templates (``{{title}}``, ``{{date}}``). The
    frontmatter ``theme:`` is always set to the domain. Editing the template
    therefore changes every future MOC. Falls back to a built-in layout when the
    template is missing or still has unknown placeholders.
    """
    title = moc_title(domain)
    if MOC_TEMPLATE_PATH.is_file():
        text = _TEMPLATER_BLOCK_RE.sub("", read_note(MOC_TEMPLATE_PATH))
        for placeholder, value in (("<% title %>", title), ("<% theme %>", domain),
                                   ('<% tp.date.now("YYYY-MM-DD") %>', created),
                                   ("{{title}}", title), ("{{date}}", created)):
            text = text.replace(placeholder, value)
        inner, body = split_frontmatter(text)
        if inner is not None:
            lines = [line for line in inner.splitlines() if not line.startswith("theme:")]
            text = "---\n" + "\n".join([*lines[:1], f"theme: {domain}", *lines[1:]]) \
                + "\n---\n" + body
        if "<%" not in text and "{{" not in text:
            return text
    return DEFAULT_MOC.format(theme=domain, title=title, created=created)


def existing_moc_themes() -> set[str]:
    themes: set[str] = set()
    if ATLAS_DIR.is_dir():
        for path in ATLAS_DIR.glob("*.md"):
            inner, _ = split_frontmatter(read_note(path))
            theme = parse_frontmatter(inner)[1].get("theme") if inner else None
            if theme:
                themes.add(str(theme))
    return themes


def create_mocs(index: dict, created: str) -> list[dict]:
    """Create a MOC in ``Atlas/`` for each domain with ``MOC_MIN_NOTES`` notes or
    more and no MOC yet (matched by the MOC's ``theme``). No API call.

    Only new files are created — an existing MOC is never modified — and every
    generated theme is remembered in ``index["generated_mocs"]``, so a MOC the
    user deletes is not recreated.
    """
    counts = Counter(n["domain"] for n in index.get("notes", []) if n.get("domain"))
    have = existing_moc_themes() | set(index.get("generated_mocs") or [])
    outcomes: list[dict] = []
    for domain, count in sorted(counts.items()):
        if count < MOC_MIN_NOTES or domain in have:
            continue
        path = ATLAS_DIR / title_to_filename(f"{moc_title(domain)} MOC")
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(render_moc(domain, created), encoding="utf-8")
        index.setdefault("generated_mocs", []).append(domain)
        rel = path.relative_to(REPO_ROOT).as_posix()
        print(f"  ✓ Created MOC {rel} ({count} {domain} notes)")
        outcomes.append({"status": "moc", "filename": domain, "target_path": rel})
    return outcomes


# --- Commit message ----------------------------------------------------------

def format_outcome_line(outcome: dict) -> str:
    if outcome["status"] == "filed":
        return f"organize {outcome['filename']} → {outcome['target_path']}"
    if outcome["status"] == "error":
        return f"error {outcome['filename']} — {outcome['reason']}"
    if outcome["status"] == "enriched":
        hint = f" — {outcome['hint']}" if outcome.get("hint") else ""
        return f"enrich {outcome['filename']} in place{hint}"
    if outcome["status"] == "moc":
        return f"create MOC {outcome['target_path']}"
    return f"unfileable {outcome['filename']} — {outcome['reason']}"


def build_commit_message(outcomes: list[dict]) -> str:
    if len(outcomes) == 1:
        return f"chore(llm): {format_outcome_line(outcomes[0])}"

    inbox_only = all(o["status"] in ("filed", "unfileable", "error")
                     and "/" not in o["filename"] for o in outcomes)
    header = (f"chore(llm): process {len(outcomes)} inbox notes" if inbox_only
              else f"chore(llm): {len(outcomes)} vault updates")
    body = "\n".join(f"- {format_outcome_line(o)}" for o in outcomes)
    return f"{header}\n\n{body}"


# --- Git ---------------------------------------------------------------------

def commit_and_push(repo: git.Repo, message: str) -> bool:
    """Commit the run and push it. Returns ``False`` if the push never landed.

    A push is typically rejected because the user pushed while the run was in
    progress; the run's commit is then rebased onto the new remote head and
    pushed once more. If that fails too, the caller must fail the job — a green
    run whose work never reached the remote would be silently lost.
    """
    repo.git.add(A=True)
    if not repo.git.diff("--cached", "--name-only").strip():
        print("No changes to commit.")
        return True
    repo.git.commit("-m", message)
    try:
        repo.git.push()
        print("Pushed changes to remote.")
        return True
    except git.GitCommandError as exc:
        print(f"! Push rejected, rebasing onto the remote and retrying: {exc}",
              file=sys.stderr)

    try:
        repo.git.pull("--rebase")
    except git.GitCommandError as exc:
        print(f"! Rebase onto the remote failed: {exc}", file=sys.stderr)
        try:
            repo.git.rebase("--abort")
        except git.GitCommandError:
            pass  # no rebase in progress (e.g. the fetch itself failed)
        return False
    try:
        repo.git.push()
        print("Pushed changes to remote (after rebase).")
        return True
    except git.GitCommandError as exc:
        print(f"! Push failed after rebase: {exc}", file=sys.stderr)
        return False


# --- Main --------------------------------------------------------------------

def process_notes(client: Anthropic, system_prompt: str,
                  inbox_notes: list[Path], processing_date: str) -> list[dict]:
    """Classify, enrich and file each Inbox note. Returns per-note outcomes.

    This is the pure pipeline (Steps 1–2): no git side effects, so it can be
    driven directly by tests against an isolated vault.

    Notes are skipped without an API call when they are empty or when they are
    byte-for-byte what a previous run already found unfileable; editing such a
    note makes it eligible again. An API failure on one note is recorded as an
    ``error`` outcome (not cached) so the rest of the run still lands.
    """
    outcomes: list[dict] = []
    state = load_unfileable_state()
    state_before = dict(state)

    for md_file in inbox_notes:
        print(f"- {md_file.name}")
        content = read_note(md_file)

        if not split_frontmatter(content)[1].strip():
            print("  · Skipped: empty note (no API call).")
            continue
        digest = content_hash(content)
        if state.get(md_file.name, {}).get("sha256") == digest:
            print("  · Skipped: unchanged since it was found unfileable "
                  "(edit the note to retry).")
            continue

        index = load_index()
        try:
            decision = classify_note(client, system_prompt, content, index)
        except APIError as exc:
            reason = f"API error: {type(exc).__name__}: {exc}"[:200]
            print(f"  ! {reason}", file=sys.stderr)
            outcomes.append({"status": "error", "filename": md_file.name,
                             "reason": reason})
            continue

        if decision.get("status") == "filed":
            outcome = apply_filed(md_file, decision, index, processing_date)
            if outcome["status"] == "filed":
                save_index(index)
        else:
            # Step 2 (unfileable) — leave the note in Inbox, print the reason.
            reason = decision.get("reason", "No reason provided.")
            print(f"  · Unfileable: {reason}")
            outcome = {"status": "unfileable", "filename": md_file.name,
                       "reason": reason}

        if outcome["status"] == "unfileable":
            state[md_file.name] = {"sha256": digest, "reason": outcome["reason"],
                                   "date": processing_date}
        else:
            state.pop(md_file.name, None)
        outcomes.append(outcome)

    if state != state_before:
        save_unfileable_state(state)
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
    if prune_unfileable_state():
        print("Dropped unfileable state for notes no longer in the Inbox.")

    # Step 1–2 — File the Inbox, then enrich notes filed by hand. Guarded: with
    # nothing to do there is no API call (controlled cost), but the
    # reconciliation above still ran.
    inbox_notes = sorted(p for p in INBOX_DIR.glob("*.md") if p.is_file())
    to_enrich = find_unenriched()
    outcomes: list[dict] = []
    if inbox_notes or to_enrich:
        system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        client = Anthropic()  # reads ANTHROPIC_API_KEY from the environment
    if inbox_notes:
        print(f"Processing {len(inbox_notes)} note(s) from Inbox...")
        outcomes = process_notes(client, system_prompt, inbox_notes, processing_date)
    else:
        print("Inbox is empty. Nothing to file.")
    if to_enrich:
        batch = to_enrich[:ENRICH_MAX_PER_RUN]
        later = len(to_enrich) - len(batch)
        print(f"Enriching {len(batch)} note(s) filed by hand"
              + (f" ({later} more on later runs)..." if later else "..."))
        outcomes += process_in_place(client, system_prompt, batch, processing_date)

    # Step 2b — Maps of Content for domains that grew enough (no API call).
    index = load_index()
    moc_outcomes = create_mocs(index, processing_date)
    if moc_outcomes:
        save_index(index)
        outcomes += moc_outcomes

    # Step 3 — Commit and push the whole run as one record. When nothing was
    # filed, only the index correction (if any) is recorded; commit_and_push is a
    # no-op when the tree is clean, so a fully in-sync vault pushes nothing.
    if commit:
        repo = git.Repo(REPO_ROOT)
        message = (build_commit_message(outcomes) if outcomes
                   else "chore(llm): reconcile vault index")
        if not commit_and_push(repo, message):
            return 1

    # Fail the job (after committing what did succeed) when a note hit an API
    # error, so the failure is visible; the note stays in the Inbox for a retry.
    if any(o["status"] == "error" for o in outcomes):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
