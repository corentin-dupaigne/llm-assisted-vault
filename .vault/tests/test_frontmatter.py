"""Tests for frontmatter merging (no API, no git).

`merge_frontmatter` folds the mandatory metadata into whatever frontmatter a
captured note already has: existing fields are kept verbatim (mandatory ones are
never overridden), missing mandatory fields are added, and the result is always
a single `---` block. These tests pin that contract using only the `vault`
fixture's loaded module — no Claude call.
"""

from __future__ import annotations

MANDATORY = ("domain", "tags", "date", "para", "project")


def _kwargs(**over):
    base = dict(domain="leetcode", tags=["golang", "array-hashing"],
               date="2026-06-10", para="Projects", project="neetcode-150")
    base.update(over)
    return base


def test_no_frontmatter_adds_all_mandatory(vault):
    """A plain note gets a single block with every mandatory field."""
    fm, body, eff = vault.module.merge_frontmatter(
        "# Plain\n\nText.\n", **_kwargs(tags=["k3s"], para="Resources", project=None)
    )
    assert fm == (
        "---\n"
        "domain: leetcode\n"
        "tags: [k3s]\n"
        "date: 2026-06-10\n"
        "para: Resources\n"
        "project: null\n"
        "---\n"
    )
    assert body == "# Plain\n\nText.\n"
    assert eff["project"] is None


def test_existing_mandatory_fields_are_not_overridden(vault):
    """Templated note: existing fields stay verbatim, only missing ones are added."""
    original = (
        "---\n"
        "difficulty: easy\n"
        "tags: []\n"
        "neetcode_section: Array & Hashing\n"
        "struggled: false\n"
        "project: neetcode-150\n"
        "domain: leetcode\n"
        "---\n"
        "\n# Two Sum\n\nNotes.\n"
    )
    fm, body, eff = vault.module.merge_frontmatter(original, **_kwargs())

    # Exactly one frontmatter block.
    assert fm.count("---\n") == 2
    # Non-mandatory fields preserved.
    assert "difficulty: easy" in fm
    assert "neetcode_section: Array & Hashing" in fm
    assert "struggled: false" in fm
    # Existing mandatory fields kept as-is (not the model's values).
    assert "tags: []" in fm
    assert "tags: [golang, array-hashing]" not in fm
    # Only the genuinely missing mandatory fields were appended.
    assert "date: 2026-06-10" in fm
    assert "para: Projects" in fm
    # Body is preserved after the block.
    assert body == "\n# Two Sum\n\nNotes.\n"
    # Effective values: existing wins for present fields, computed for the rest.
    assert eff["tags"] == []
    assert eff["domain"] == "leetcode"
    assert eff["para"] == "Projects"


def test_no_duplicate_mandatory_keys(vault):
    """Every mandatory key appears exactly once in the merged block."""
    original = "---\ndomain: x\nproject: p\n---\nBody\n"
    fm, _, _ = vault.module.merge_frontmatter(original, **_kwargs())
    for key in MANDATORY:
        assert fm.count(f"{key}:") == 1, f"{key} duplicated in merged frontmatter"


def test_existing_block_list_tags_are_read(vault):
    """Block-style YAML lists in existing frontmatter are parsed for the index."""
    original = "---\ntags:\n  - one\n  - two\n---\nBody\n"
    _, _, eff = vault.module.merge_frontmatter(original, **_kwargs())
    assert eff["tags"] == ["one", "two"]


def test_apply_filed_merges_templated_note_end_to_end(vault):
    """Full filing path (no API): templated note → one block, index uses effective values."""
    note = vault.drop_note(
        "two-sum.md",
        "---\n"
        "tags: []\n"
        "neetcode_section: Array & Hashing\n"
        "project: neetcode-150\n"
        "domain: leetcode\n"
        "---\n"
        "\n# Two Sum\n\nNotes.\n",
    )
    decision = {
        "status": "filed",
        "reason": "Project note.",
        "target_path": "Projects/neetcode-150/two-sum.md",
        "domain": "leetcode",
        "tags": ["golang", "array-hashing"],  # should NOT win over existing tags: []
        "para": "Projects",
        "project": "neetcode-150",
        "wikilinks": [],
    }
    index = vault.read_index()

    outcome = vault.module.apply_filed(note, decision, index, "2026-06-10")
    assert outcome["status"] == "filed"

    written = (vault.root / outcome["target_path"]).read_text(encoding="utf-8")
    # Exactly one frontmatter block, with the template fields preserved and the
    # missing mandatory fields added.
    assert written.count("\n---\n") == 1
    assert "neetcode_section: Array & Hashing" in written
    assert "tags: []" in written and "tags: [golang, array-hashing]" not in written
    assert "date: 2026-06-10" in written and "para: Projects" in written

    # The index mirrors the effective values (existing tags: [] wins).
    entry = index["notes"][-1]
    assert entry["tags"] == []
    assert entry["domain"] == "leetcode"
    assert "golang" not in index["tags"]
