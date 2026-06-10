"""Tests for the Markdown formatting step (no API, no git).

`format_markdown` normalizes a filed note's body before it is written. These
tests pin the two properties that matter: the body is actually reformatted, and
Obsidian `[[wikilinks]]` survive (mdformat would otherwise escape the brackets).
They use only the `vault` fixture's loaded module — no Claude call is made.
"""

from __future__ import annotations


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
