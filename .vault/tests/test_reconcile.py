"""Tests for the index reconciliation step (issue #10).

The filing pipeline only ever writes the index entry for the note it just filed,
so editing a filed note's frontmatter or renaming it by hand leaves
`vault.index.json` stale forever. `reconcile_index` re-derives the index from the
notes actually on disk; these tests prove a frontmatter edit, a rename (which
re-titles, since the title *is* the filename), a deletion and a hand-added note
all reach the index, and that an already-in-sync vault is a no-op.

These are deterministic and need no API key — they drive `reconcile_index`
directly against an isolated vault.
"""

from __future__ import annotations


def _file(vault, rel_path, body):
    path = vault.root / rel_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _note(*, domain, tags, para, project="null", date="2026-06-04",
          body="Reference content.\n"):
    tags_line = "[" + ", ".join(tags) + "]"
    return (
        f"---\ndomain: {domain}\ntags: {tags_line}\ndate: {date}\n"
        f"para: {para}\nproject: {project}\n---\n{body}"
    )


def _reconcile(vault):
    """Run reconcile against the on-disk index and return (changed, index)."""
    index = vault.module.load_index()
    changed = vault.module.reconcile_index(index)
    return changed, index


def test_edited_frontmatter_reaches_the_index(vault):
    """Hand-editing a filed note's frontmatter refreshes its index entry; the
    title follows the filename (the body is never inspected)."""
    _file(vault, "Resources/Photosynthesis.md",
          _note(domain="botany", tags=["plants", "energy"], para="Resources"))
    vault.seed_index(notes=[{
        "title": "Photosynthesis", "path": "Resources/Photosynthesis.md",
        "domain": "biology", "tags": ["plants"], "para": "Resources",
        "project": None, "date": "2026-06-04",
    }], domains=["biology"], tags=["plants"])

    changed, index = _reconcile(vault)

    assert changed is True
    entry = index["notes"][0]
    assert entry["title"] == "Photosynthesis"   # from the filename
    assert entry["domain"] == "botany"
    assert entry["tags"] == ["plants", "energy"]
    # The canonical lists track actual usage: 'biology' is dropped, 'energy' added.
    assert index["domains"] == ["botany"]
    assert index["tags"] == ["plants", "energy"]


def test_renamed_file_changes_the_indexed_title(vault):
    """The title is the filename, so renaming the file re-titles its index entry
    (the stale path drops out, the new one is added)."""
    _file(vault, "Resources/Krebs Cycle.md",
          _note(domain="biology", tags=["metabolism"], para="Resources"))
    vault.seed_index(notes=[{
        "title": "Citric Acid Cycle", "path": "Resources/Citric Acid Cycle.md",
        "domain": "biology", "tags": ["metabolism"], "para": "Resources",
        "project": None, "date": "2026-06-04",
    }], domains=["biology"], tags=["metabolism"])

    changed, index = _reconcile(vault)

    assert changed is True
    assert [n["path"] for n in index["notes"]] == ["Resources/Krebs Cycle.md"]
    assert index["notes"][0]["title"] == "Krebs Cycle"


def test_deleted_note_is_pruned_with_its_orphaned_metadata(vault):
    """A note whose file is gone leaves the index, and so do tags only it used."""
    _file(vault, "Resources/Kept.md",
          _note(domain="general", tags=["shared"], para="Resources"))
    vault.seed_index(
        notes=[
            {"title": "Kept", "path": "Resources/Kept.md", "domain": "general",
             "tags": ["shared"], "para": "Resources", "project": None,
             "date": "2026-06-04"},
            {"title": "Gone", "path": "Resources/Gone.md", "domain": "obsolete",
             "tags": ["shared", "dead"], "para": "Resources", "project": None,
             "date": "2026-06-04"},
        ],
        domains=["general", "obsolete"], tags=["shared", "dead"],
    )

    changed, index = _reconcile(vault)

    assert changed is True
    assert [n["path"] for n in index["notes"]] == ["Resources/Kept.md"]
    assert index["domains"] == ["general"]
    assert index["tags"] == ["shared"]


def test_hand_added_note_gets_indexed_with_location_derived_placement(vault):
    """A note created directly under a PARA root is picked up; para/project come
    from its location and the title from its filename."""
    _file(vault, "Projects/cka/Etcd Backup.md",
          _note(domain="kubernetes", tags=["etcd"], para="Projects", project="cka"))

    changed, index = _reconcile(vault)

    assert changed is True
    entry = index["notes"][0]
    assert entry["path"] == "Projects/cka/Etcd Backup.md"
    assert entry["title"] == "Etcd Backup"
    assert entry["para"] == "Projects"
    assert entry["project"] == "cka"
    assert entry["domain"] == "kubernetes"


def test_in_sync_vault_is_a_noop(vault):
    """When the index already matches disk, reconcile reports no change."""
    _file(vault, "Areas/Health.md",
          _note(domain="wellbeing", tags=["habits"], para="Areas"))
    vault.seed_index(notes=[{
        "title": "Health", "path": "Areas/Health.md", "domain": "wellbeing",
        "tags": ["habits"], "para": "Areas", "project": None,
        "date": "2026-06-04",
    }], domains=["wellbeing"], tags=["habits"])

    changed, index = _reconcile(vault)

    assert changed is False
    assert index["notes"][0]["title"] == "Health"
