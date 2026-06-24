"""Tests for the Markdown formatting + wikilink resolution steps (no API, no git).

`format_markdown` normalizes a filed note's body before it is written, and
`resolve_wikilinks` validates the model's links against the index and re-emits
them as bare, resolvable `[[Note Title]]` links (the filename is the title now).
These tests pin the properties that matter: the body is reformatted,
`[[wikilinks]]` survive formatting, and links resolve to real files. They use
only the `vault` fixture's loaded module — no Claude call.
"""

from __future__ import annotations


def _index_with_notes():
    return {
        "notes": [
            {"title": "Contains Duplicate", "path": "Projects/neetcode-150/Contains Duplicate.md"},
            {"title": "Two Sum", "path": "Projects/neetcode-150/Two Sum.md"},
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


def test_resolve_wikilinks_matches_by_title_and_strips_alias(vault):
    """A title-based link is kept as a bare `[[Title]]`; any alias is dropped."""
    out = vault.module.resolve_wikilinks(
        ["[[Contains Duplicate|whatever the model wrote]]"], _index_with_notes()
    )
    assert out == ["[[Contains Duplicate]]"]


def test_resolve_wikilinks_normalizes_path_and_extension(vault):
    """A bare title, a full path, or a name with .md all resolve to the basename."""
    idx = _index_with_notes()
    assert vault.module.resolve_wikilinks(["[[Two Sum]]"], idx) == ["[[Two Sum]]"]
    assert vault.module.resolve_wikilinks(["[[Two Sum.md]]"], idx) == ["[[Two Sum]]"]
    assert vault.module.resolve_wikilinks(
        ["[[Projects/neetcode-150/Two Sum]]"], idx
    ) == ["[[Two Sum]]"]


def test_resolve_wikilinks_matches_sanitized_title_to_basename(vault):
    """A title with illegal chars resolves to its sanitized on-disk basename."""
    idx = {"notes": [{"title": "TCP/IP", "path": "Resources/TCP-IP.md"}]}
    assert vault.module.resolve_wikilinks(["[[TCP/IP]]"], idx) == ["[[TCP-IP]]"]


def test_resolve_wikilinks_drops_unknown_and_dedupes(vault):
    """Links matching no indexed note are dropped; dupes collapse."""
    out = vault.module.resolve_wikilinks(
        ["[[Contains Duplicate]]", "[[Nonexistent Note]]", "[[Contains Duplicate]]"],
        _index_with_notes(),
    )
    assert out == ["[[Contains Duplicate]]"]
