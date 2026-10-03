"""Tests for area subfolders under `Areas/` (no API, no git).

Areas mirror projects: the subfolders of `Areas/` are detected into the index,
the model may only file into a listed area (or the `Areas/` root), a note's own
`area:` frontmatter wins, and the index/frontmatter/location stay consistent.
"""

from __future__ import annotations

DECISION = {
    "status": "filed", "reason": "Ongoing responsibility.",
    "target_path": "Areas/x.md", "domain": "personal-finance", "tags": [],
    "para": "Areas", "project": None, "area": "finances", "wikilinks": [],
}


def _area(vault, name):
    (vault.root / "Areas" / name).mkdir(parents=True)


def test_area_folders_are_detected_into_the_index(vault):
    _area(vault, "health")
    _area(vault, "finances")
    index = vault.read_index()

    assert vault.module.sync_projects(index) is True
    assert index["areas"] == ["finances", "health"]


def test_no_area_folders_leaves_the_index_untouched(vault):
    index = vault.read_index()
    assert vault.module.sync_projects(index) is False
    assert "areas" not in index


def test_note_is_filed_into_a_listed_area(vault):
    _area(vault, "finances")
    vault.seed_index(areas=["finances"])
    note = vault.drop_note("Budget.md", "Monthly budget rules.\n")
    index = vault.read_index()

    outcome = vault.module.apply_filed(note, dict(DECISION), index, "2026-10-03")

    assert outcome["target_path"] == "Areas/finances/Budget.md"
    written = (vault.root / outcome["target_path"]).read_text(encoding="utf-8")
    assert "para: Areas" in written and "area: finances" in written
    assert index["notes"][-1]["area"] == "finances"


def test_no_fitting_area_files_at_the_areas_root(vault):
    vault.seed_index(areas=["finances"])
    note = vault.drop_note("Routine.md", "Morning routine.\n")
    index = vault.read_index()

    outcome = vault.module.apply_filed(note, dict(DECISION, area=None), index, "2026-10-03")

    assert outcome["target_path"] == "Areas/Routine.md"
    written = (vault.root / outcome["target_path"]).read_text(encoding="utf-8")
    assert "area:" not in written
    assert "area" not in index["notes"][-1]


def test_model_cannot_invent_an_area(vault):
    vault.seed_index(areas=["health"])
    note = vault.drop_note("Budget.md", "Monthly budget rules.\n")

    outcome = vault.module.apply_filed(note, dict(DECISION), vault.read_index(), "2026-10-03")

    assert outcome["reason"] == "rejected: model chose unknown area 'finances'"
    assert note.exists() and not (vault.root / "Areas" / "finances").exists()


def test_user_declared_area_is_allowed(vault):
    note = vault.drop_note("Budget.md", "---\npara: Areas\narea: finances\n---\nRules.\n")

    outcome = vault.module.apply_filed(note, dict(DECISION, area=None),
                                       vault.read_index(), "2026-10-03")

    assert outcome["target_path"] == "Areas/finances/Budget.md"


def test_rerouting_away_from_areas_drops_the_area(vault):
    vault.seed_index(areas=["finances"])
    note = vault.drop_note("Budget.md", "---\npara: Resources\n---\nReference.\n")

    outcome = vault.module.apply_filed(note, dict(DECISION), vault.read_index(), "2026-10-03")

    assert outcome["target_path"] == "Resources/Budget.md"


def test_reconcile_derives_area_from_location(vault):
    _area(vault, "health")
    (vault.root / "Areas" / "health" / "Sleep.md").write_text(
        "---\ndomain: health\ntags: []\n---\nBody.\n", encoding="utf-8")
    (vault.root / "Areas" / "Routine.md").write_text(
        "---\ndomain: habits\ntags: []\n---\nBody.\n", encoding="utf-8")
    index = vault.read_index()

    vault.module.reconcile_index(index)

    by_path = {n["path"]: n for n in index["notes"]}
    assert by_path["Areas/health/Sleep.md"]["area"] == "health"
    assert "area" not in by_path["Areas/Routine.md"]


def test_render_lists_areas_and_their_notes(vault):
    text = vault.module.render_index_for_prompt({
        "areas": ["health"],
        "notes": [{"title": "Sleep", "domain": "health", "para": "Areas", "area": "health"}],
    })
    assert "Areas: health" in text
    assert "health @ Areas/health: Sleep" in text
    assert "Areas: (none" in vault.module.render_index_for_prompt({})
