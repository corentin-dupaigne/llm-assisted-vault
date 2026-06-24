"""End-to-end tests against the real Claude API.

Each test drops one or more real Markdown notes into an isolated temporary
vault, runs the actual classification + filing pipeline (`process_notes`) with a
live `claude-haiku-4-5-20251001` call, and asserts on the result.

The suite is skipped automatically when `ANTHROPIC_API_KEY` is absent. Because a
real model is involved, assertions favour *invariants and contracts* (valid
frontmatter, lowercase-hyphenated metadata, file actually moved, index updated)
over brittle expectations of an exact wording, and only assert a specific PARA
bucket where the note leaves essentially no room for interpretation.

Run with:  .venv/bin/python -m pytest tests/ -v
"""

from __future__ import annotations

import re
from datetime import date

import pytest

# Every test in this module makes a real Claude API call.
pytestmark = pytest.mark.api

SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
PARA_ROOTS = {"Projects", "Areas", "Resources", "Archive"}


# --- helpers -----------------------------------------------------------------

def parse_frontmatter(text: str) -> tuple[dict, str]:
    """Parse the leading `--- ... ---` YAML block into a dict, return (meta, body).

    Deliberately tiny: only handles the flat scalar/list fields this vault emits.
    """
    assert text.startswith("---\n"), "note must start with a frontmatter block"
    end = text.index("\n---\n", 4)
    block = text[4:end]
    body = text[end + len("\n---\n"):]

    meta: dict = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        key, _, raw = line.partition(":")
        key, raw = key.strip(), raw.strip()
        if raw.startswith("[") and raw.endswith("]"):
            inner = raw[1:-1].strip()
            meta[key] = [t.strip() for t in inner.split(",") if t.strip()] if inner else []
        elif raw == "null":
            meta[key] = None
        else:
            meta[key] = raw
    return meta, body


def assert_valid_filed_note(vault, outcome: dict, *, expected_para: str | None = None):
    """Assert the structural contract of a successfully filed note."""
    assert outcome["status"] == "filed"

    dest = vault.root / outcome["target_path"]
    assert dest.exists(), f"filed note missing at {outcome['target_path']}"
    assert not (vault.inbox / outcome["filename"]).exists(), "note still in Inbox"

    top = outcome["target_path"].split("/", 1)[0]
    assert top in PARA_ROOTS, f"filed outside PARA roots: {outcome['target_path']}"

    meta, _ = parse_frontmatter(dest.read_text(encoding="utf-8"))
    for key in ("domain", "tags", "date", "para", "project"):
        assert key in meta, f"frontmatter missing '{key}'"

    assert meta["para"] == top, "para must match the destination folder"
    assert SLUG_RE.match(meta["domain"]), f"domain not lowercase-hyphenated: {meta['domain']!r}"
    for tag in meta["tags"]:
        assert SLUG_RE.match(tag), f"tag not lowercase-hyphenated: {tag!r}"
    assert meta["domain"] not in meta["tags"], "domain must not duplicate a tag"
    assert meta["date"] == date.today().isoformat()

    if top == "Projects":
        assert meta["project"], "Projects note must name a project"
    else:
        assert meta["project"] is None, "non-Projects note must have null project"

    if expected_para is not None:
        assert meta["para"] == expected_para, (
            f"expected {expected_para}, got {meta['para']} — reason: {outcome.get('target_path')}"
        )

    # Index side effects.
    index = vault.read_index()
    titles = [n["path"] for n in index["notes"]]
    assert outcome["target_path"] in titles, "filed note absent from index notes"
    assert meta["domain"] in index["domains"], "domain not registered in index"
    for tag in meta["tags"]:
        assert tag in index["tags"], f"tag {tag!r} not registered in index"


# --- tests -------------------------------------------------------------------

def test_reference_note_filed_to_resources(vault):
    """A purely encyclopedic note with no project ties belongs in Resources."""
    vault.drop_note(
        "tcp-handshake.md",
        "# The TCP Three-Way Handshake\n\n"
        "TCP establishes a connection with SYN, SYN-ACK, and ACK packets. "
        "The client sends SYN, the server replies SYN-ACK, the client confirms "
        "with ACK. This is foundational networking reference knowledge with no "
        "deadline and no associated project.\n",
    )

    outcomes = vault.run()

    assert len(outcomes) == 1
    assert_valid_filed_note(vault, outcomes[0], expected_para="Resources")


def test_project_note_filed_under_active_project(vault):
    """A note clearly about an active project is filed under Projects/<project>/."""
    vault.seed_index(projects=[
        {"name": "website-redesign",
         "description": "Rebuild the company marketing website on a new stack."}
    ])
    vault.drop_note(
        "redesign-homepage-todo.md",
        "# Homepage hero section\n\n"
        "For the website redesign project: finalize the new homepage hero copy, "
        "pick the hero image, and ship the responsive layout before the launch "
        "deadline next week.\n",
    )

    outcomes = vault.run()

    assert len(outcomes) == 1
    out = outcomes[0]
    assert_valid_filed_note(vault, out, expected_para="Projects")
    assert out["target_path"].startswith("Projects/website-redesign/"), (
        f"expected filing under the active project, got {out['target_path']}"
    )


def test_french_note_gets_english_metadata(vault):
    """A French note is handled, and its domain/tags are emitted in English slugs."""
    vault.drop_note(
        "fermentation-pain.md",
        "# La fermentation du pain au levain\n\n"
        "Le levain est une culture de levures sauvages et de bactéries lactiques. "
        "La fermentation lente développe les arômes et améliore la digestibilité "
        "du pain. Connaissance de référence, sans projet ni échéance.\n",
    )

    outcomes = vault.run()

    assert len(outcomes) == 1
    out = outcomes[0]
    # French content is allowed; if filed, metadata must still be valid slugs.
    if out["status"] == "filed":
        assert_valid_filed_note(vault, out)
        meta, _ = parse_frontmatter((vault.root / out["target_path"]).read_text(encoding="utf-8"))
        assert meta["domain"].isascii(), f"domain should be an ASCII slug: {meta['domain']!r}"
    else:
        # Unfileable is acceptable, but then the note must remain in the Inbox.
        assert (vault.inbox / "fermentation-pain.md").exists()


def test_wikilinks_reference_existing_titles_only(vault):
    """Any wikilinks returned must point at notes that exist in the index."""
    vault.seed_index(
        domains=["kubernetes"],
        tags=["networking"],
        notes=[{
            "title": "Kubernetes Cluster Networking",
            "path": "Resources/Kubernetes Cluster Networking.md",
            "domain": "kubernetes",
            "tags": ["networking"],
            "para": "Resources",
            "project": None,
            "date": "2026-01-01",
        }],
    )
    vault.drop_note(
        "k8s-service-mesh.md",
        "# Service Meshes in Kubernetes\n\n"
        "A service mesh like Istio manages service-to-service traffic inside a "
        "Kubernetes cluster, building directly on cluster networking primitives. "
        "Reference knowledge.\n",
    )

    outcomes = vault.run()
    out = outcomes[0]

    if out["status"] != "filed":
        pytest.skip("model returned unfileable; wikilink contract not exercised")

    dest = vault.root / out["target_path"]
    body = dest.read_text(encoding="utf-8")
    notes = vault.read_index()["notes"]
    existing_stems = {n["path"].rsplit("/", 1)[-1].removesuffix(".md") for n in notes}

    # Links are emitted as bare [[Note Title]] — the filename is the title now, so
    # the link must name a real note's basename and carry no alias.
    links = re.findall(r"\[\[([^\]]+)\]\]", body)
    for link in links:
        assert "|" not in link, f"wikilink [[{link}]] should be bare (no alias)"
        assert link in existing_stems, (
            f"wikilink [[{link}]] does not match any existing note filename"
        )
    # The "## Links" section exists iff at least one wikilink was injected.
    assert ("## Links" in body) == bool(links)


def test_unfileable_note_stays_in_inbox(vault):
    """The unfileable contract: nothing moved, index untouched, file preserved.

    A contentless fragment gives the model strong grounds to decline. Whatever it
    decides, the relevant invariant for that branch must hold.
    """
    before = vault.read_index()
    vault.drop_note("fragment.md", "asdf\n")

    outcomes = vault.run()
    out = outcomes[0]

    if out["status"] == "unfileable":
        assert (vault.inbox / "fragment.md").exists(), "unfileable note must stay in Inbox"
        assert vault.read_index() == before, "index must be untouched on unfileable"
    else:
        # If the model chose to file it, the standard filed contract still holds.
        assert_valid_filed_note(vault, out)
