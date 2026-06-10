"""Tests for the Markdown formatting + wikilink resolution steps (no API, no git).

`format_markdown` normalizes a filed note's body before it is written, and
`resolve_wikilinks` rewrites the model's title-based links into
Obsidian-resolvable basename links. These tests pin the properties that matter:
the body is reformatted, `[[wikilinks]]` survive formatting, and links resolve to
real files. They use only the `vault` fixture's loaded module — no Claude call.
"""

from __future__ import annotations


def _index_with_notes():
    return {
        "notes": [
            {"title": "Contains Duplicate", "path": "Projects/neetcode-150/contains-duplicate.md"},
            {"title": "Two Sum", "path": "Projects/neetcode-150/two-sum.md"},
        ]
    }


def test_format_markdown_normalizes_body(vault):
    """Headings, runaway whitespace and list markers are normalized."""
    messy = "#   Title\n\n\nSome   text.\n*  one\n*  two\n"
    out = vault.module.format_markdown(messy)

    assert "# Title\n" in out, "heading whitespace not collapsed"
    assert "Some text." in out, "inline whitespace not collapsed"
    assert "- one\n- two\n" in out, "list markers not normalized to '-'"
    assert "\n\n\n" not in out, "blank-line runs not collapsed"


def test_format_markdown_preserves_wikilinks(vault):
    """`[[wikilinks]]` must pass through unescaped (the `wikilink` extension)."""
    body = "Body text.\n\n## Links\n\n- [[Existing Note Title]]\n- [[Another Note]]\n"
    out = vault.module.format_markdown(body)

    assert "[[Existing Note Title]]" in out
    assert "[[Another Note]]" in out
    assert "\\[" not in out, "brackets were escaped — wikilinks broken"


def test_resolve_wikilinks_validates_basename_and_canonical_alias(vault):
    """A filename-based link is kept; the alias is re-derived from the index title."""
    out = vault.module.resolve_wikilinks(
        ["[[contains-duplicate|whatever the model wrote]]"], _index_with_notes()
    )
    assert out == ["[[contains-duplicate|Contains Duplicate]]"]


def test_resolve_wikilinks_normalizes_path_and_extension(vault):
    """A bare stem, a full path, or a name with .md all reduce to the basename."""
    idx = _index_with_notes()
    assert vault.module.resolve_wikilinks(["[[two-sum]]"], idx) == ["[[two-sum|Two Sum]]"]
    assert vault.module.resolve_wikilinks(["[[two-sum.md]]"], idx) == ["[[two-sum|Two Sum]]"]
    assert vault.module.resolve_wikilinks(
        ["[[Projects/neetcode-150/two-sum]]"], idx
    ) == ["[[two-sum|Two Sum]]"]


def test_resolve_wikilinks_drops_unknown_and_dedupes(vault):
    """Links whose basename matches no indexed note are dropped; dupes collapse."""
    out = vault.module.resolve_wikilinks(
        ["[[contains-duplicate]]", "[[nonexistent-note]]", "[[contains-duplicate]]"],
        _index_with_notes(),
    )
    assert out == ["[[contains-duplicate|Contains Duplicate]]"]
