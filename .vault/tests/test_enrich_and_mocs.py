"""Tests for in-place enrichment of hand-filed notes and automatic MOCs (no API).

A note put straight into a PARA folder without a `domain` is enriched where it
is: missing frontmatter added, links appended, body untouched, never moved.
A domain that reaches `MOC_MIN_NOTES` notes gets a MOC rendered from the user's
template, created once and never overwritten.
"""

from __future__ import annotations

import pytest

from test_robustness import FakeClient

DECISION = {
    "status": "filed", "reason": "Enriched.", "target_path": "Resources/x.md",
    "domain": "computer-vision", "tags": ["slam"], "para": "Projects",
    "project": "research", "wikilinks": ["[[Pose Estimation]]", "[[Pipeline]]"],
}


def _write(vault, rel, text):
    path = vault.root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _index_with(vault, *titles_and_paths):
    vault.seed_index(notes=[{"title": t, "path": p, "domain": "computer-vision",
                             "tags": [], "para": p.split("/")[0], "project": None}
                            for t, p in titles_and_paths])


# --- Detection -----------------------------------------------------------------------

def test_only_unprocessed_notes_in_enrich_roots_are_found(vault):
    _write(vault, "Projects/research/Pipeline.md", "Raw notes.\n")
    _write(vault, "Resources/Done.md", "---\ndomain: go\n---\nBody.\n")
    _write(vault, "Resources/Skip.md", "---\nllm: skip\n---\nBody.\n")
    _write(vault, "Resources/Empty.md", "---\ntags: []\n---\n\n")
    _write(vault, "Archive/Old.md", "Old notes.\n")

    found = [p.relative_to(vault.root).as_posix() for p in vault.module.find_unenriched()]

    assert found == ["Projects/research/Pipeline.md"]


# --- Enrichment ----------------------------------------------------------------------

def test_note_is_enriched_where_it_is(vault):
    body = "# Pipeline\n\n* step   one\n* step two\n"
    path = _write(vault, "Projects/research/Pipeline.md", "---\nstatus: draft\n---\n" + body)
    _index_with(vault, ("Pose Estimation", "Resources/Pose Estimation.md"),
                ("Pipeline", "Projects/research/Pipeline.md"))

    outcome = vault.module.apply_in_place(path, dict(DECISION), vault.read_index(), "2026-10-03")

    text = path.read_text(encoding="utf-8")
    assert outcome == {"status": "enriched", "filename": "Projects/research/Pipeline.md"}
    assert text.startswith("---\nstatus: draft\ndomain: computer-vision\ntags: [slam]\n"
                           "date: 2026-10-03\npara: Projects\nproject: research\n---\n")
    assert body in text                            # body untouched, not reformatted
    assert text.endswith("## Links\n\n- [[Pose Estimation]]\n")   # no self-link
    assert not (vault.root / "Resources" / "x.md").exists()       # never moved


def test_location_wins_and_disagreement_becomes_a_hint(vault):
    path = _write(vault, "Resources/Pipeline.md", "Notes.\n")

    outcome = vault.module.apply_in_place(path, dict(DECISION), vault.read_index(), "2026-10-03")

    assert "para: Resources\nproject: null" in path.read_text(encoding="utf-8")
    assert outcome["hint"] == "model would have filed it under Projects/research"


def test_existing_links_section_is_not_duplicated(vault):
    path = _write(vault, "Resources/Pipeline.md", "Notes.\n\n## Links\n\n- [[Mine]]\n")
    _index_with(vault, ("Pose Estimation", "Resources/Pose Estimation.md"))

    vault.module.apply_in_place(path, dict(DECISION), vault.read_index(), "2026-10-03")

    assert path.read_text(encoding="utf-8").count("## Links") == 1


def test_process_in_place_updates_index_and_caches_unfileable(vault):
    _write(vault, "Resources/A.md", "Alpha.\n")
    _write(vault, "Resources/B.md", "Beta.\n")
    paths = vault.module.find_unenriched()
    client = FakeClient(dict(DECISION, para="Resources", project=None),
                        {"status": "unfileable", "reason": "Too vague."})

    outcomes = vault.module.process_in_place(client, "system", paths, "2026-10-03")

    assert [o["status"] for o in outcomes] == ["enriched", "unfileable"]
    assert "## Location" in client.requests[0]["messages"][0]["content"]
    index = vault.read_index()
    assert {n["path"]: n["domain"] for n in index["notes"]}["Resources/A.md"] == "computer-vision"
    assert "Resources/B.md" in vault.module.load_unfileable_state()
    # Unchanged and cached: no second call.
    again = FakeClient()
    assert vault.module.process_in_place(again, "system", [paths[1]], "2026-10-03") == []
    assert again.calls == 0


def test_commit_message_lines_for_new_outcomes(vault):
    message = vault.module.build_commit_message([
        {"status": "enriched", "filename": "Resources/A.md",
         "hint": "model would have filed it under Projects/x"},
        {"status": "moc", "filename": "go", "target_path": "Atlas/Go MOC.md"},
    ])
    assert message.startswith("chore(llm): 2 vault updates\n\n")
    assert "- enrich Resources/A.md in place — model would have filed it under Projects/x" in message
    assert "- create MOC Atlas/Go MOC.md" in message


# --- MOCs ------------------------------------------------------------------------------

def _notes(domain, n):
    return [{"title": f"{domain}-{i}", "path": f"Resources/{domain}-{i}.md",
             "domain": domain, "tags": [], "para": "Resources", "project": None}
            for i in range(n)]


TEMPLATER_MOC = """<%*
const title = await tp.system.prompt("MOC title?")
await tp.file.rename(title + " MOC")
_%>
---
type: moc
theme: <% theme %>
created: <% tp.date.now("YYYY-MM-DD") %>
---
# <% title %> — Map of Content

```dataview
LIST
WHERE domain = this.theme
```
"""

CORE_MOC = """---
type: moc
theme: 
created: {{date}}
---
# {{title}} — Map of Content

```dataview
LIST
WHERE domain = this.theme
```
"""


@pytest.mark.parametrize("template", [TEMPLATER_MOC, CORE_MOC], ids=["templater", "core"])
def test_moc_created_from_user_template_at_threshold(vault, template):
    _write(vault, "Templates/moc.md", template)
    index = {"notes": _notes("computer-vision", 5) + _notes("travel", 4)}

    outcomes = vault.module.create_mocs(index, "2026-10-03")

    assert [o["target_path"] for o in outcomes] == ["Atlas/Computer Vision MOC.md"]
    text = (vault.root / "Atlas" / "Computer Vision MOC.md").read_text(encoding="utf-8")
    assert text.startswith("---\ntype: moc\ntheme: computer-vision\ncreated: 2026-10-03\n---\n"
                           "# Computer Vision — Map of Content")
    assert "<%" not in text and "WHERE domain = this.theme" in text
    assert index["generated_mocs"] == ["computer-vision"]


def test_builtin_moc_without_template(vault):
    vault.module.create_mocs({"notes": _notes("go", 5)}, "2026-10-03")
    text = (vault.root / "Atlas" / "Go MOC.md").read_text(encoding="utf-8")
    assert "theme: go" in text and "# Go — Map of Content" in text


def test_existing_or_deleted_mocs_are_never_recreated(vault):
    _write(vault, "Atlas/My Go map.md", "---\ntype: moc\ntheme: go\n---\nMine.\n")
    index = {"notes": _notes("go", 6) + _notes("rust", 6), "generated_mocs": ["rust"]}

    assert vault.module.create_mocs(index, "2026-10-03") == []
    assert (vault.root / "Atlas" / "My Go map.md").read_text(encoding="utf-8").endswith("Mine.\n")
    assert not (vault.root / "Atlas" / "Rust MOC.md").exists()
