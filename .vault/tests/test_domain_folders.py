"""Tests for domain-foldered placement in Resources/ and Areas/ (issue #12).

Resources and Areas notes are grouped one folder deep by their `domain`
(`Resources/<domain>/note.md`) so the roots stay browsable; Projects groups by
project and Archive stays flat. Placement is decided in code (`build_target_path`
is authoritative — it only borrows the basename from the model), so these are
deterministic and need no API key.
"""

from __future__ import annotations

import pytest


# --- build_target_path (pure) ------------------------------------------------

@pytest.mark.parametrize("para, project, domain, expected", [
    ("Resources", None, "golang", "Resources/golang/arrays.md"),
    ("Areas", None, "health", "Areas/health/routine.md"),
    ("Archive", None, "old-stuff", "Archive/done.md"),            # flat
    ("Projects", "cka", "kubernetes", "Projects/cka/etcd.md"),    # by project
    ("Resources", None, None, None),   # domain-foldered root needs a domain
    ("Projects", None, "x", None),     # Projects needs a project
])
def test_build_target_path_groups_by_domain(vault, para, project, domain, expected):
    filename = expected.rsplit("/", 1)[1] if expected else "note.md"
    assert vault.module.build_target_path(para, project, filename, domain) == expected


# --- apply_filed (integration, no API) ---------------------------------------

def _decision(**over):
    base = {
        "status": "filed", "reason": "x", "domain": "golang", "tags": ["arrays"],
        "para": "Resources", "project": None, "wikilinks": [],
        "target_path": "Resources/golang-arrays.md",
    }
    base.update(over)
    return base


def test_resource_note_is_filed_under_its_domain_folder(vault):
    note = vault.drop_note("golang-arrays.md", "# Golang Arrays\n\nReference.\n")
    index = vault.read_index()

    outcome = vault.module.apply_filed(note, _decision(), index, "2026-06-24")

    assert outcome["target_path"] == "Resources/golang/golang-arrays.md"
    assert (vault.root / "Resources" / "golang" / "golang-arrays.md").exists()
    # The index path agrees with the on-disk location.
    assert index["notes"][-1]["path"] == "Resources/golang/golang-arrays.md"


def test_archive_note_stays_flat(vault):
    note = vault.drop_note("retro.md", "# Retro\n\nDone.\n")
    decision = _decision(para="Archive", domain="project-retros",
                         target_path="Archive/retro.md")
    index = vault.read_index()

    outcome = vault.module.apply_filed(note, decision, index, "2026-06-24")

    assert outcome["target_path"] == "Archive/retro.md"
    assert (vault.root / "Archive" / "retro.md").exists()


def test_domain_folder_follows_effective_domain_from_frontmatter(vault):
    """When the note's own frontmatter defines the domain, the folder uses that
    effective value (existing wins over the model), so file and index agree."""
    note = vault.drop_note(
        "caffeine.md",
        "---\ndomain: pharmacology\n---\n# Caffeine\n\nReference.\n",
    )
    # The model proposes a different domain; the note's own must win.
    index = vault.read_index()
    outcome = vault.module.apply_filed(
        note, _decision(domain="biohacking", target_path="Resources/caffeine.md"),
        index, "2026-06-24",
    )

    assert outcome["target_path"] == "Resources/pharmacology/caffeine.md"
    assert index["notes"][-1]["domain"] == "pharmacology"


def test_reconcile_reads_nested_resource_note(vault):
    """A domain-foldered note on disk reconciles with para from its location."""
    path = vault.root / "Resources" / "golang" / "loops.md"
    path.parent.mkdir(parents=True)
    path.write_text(
        "---\ndomain: golang\ntags: [control-flow]\ndate: 2026-06-24\n"
        "para: Resources\nproject: null\n---\n# Golang Loops\n\nReference.\n",
        encoding="utf-8",
    )

    index = vault.module.load_index()
    assert vault.module.reconcile_index(index) is True

    entry = index["notes"][0]
    assert entry["path"] == "Resources/golang/loops.md"
    assert entry["para"] == "Resources"
    assert entry["project"] is None
    assert entry["domain"] == "golang"
