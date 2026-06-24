"""Tests for readable-filename derivation (`title_to_filename`).

A filed note's filename is its human-readable title, not a slug — spaces and
capitalisation are kept so the note reads as its title across Obsidian and
resolves as a bare `[[wikilink]]`. Only filename-illegal / wikilink-breaking
characters are stripped or replaced. No API, no git.
"""

from __future__ import annotations

import pytest


@pytest.mark.parametrize("title, expected", [
    ("Contains Duplicate", "Contains Duplicate.md"),       # the common case: verbatim
    ("ArgoCD Helm Install No CRDs", "ArgoCD Helm Install No CRDs.md"),
    ("PV, PVC, StorageClass", "PV, PVC, StorageClass.md"),  # commas are legal
    ("TCP/IP", "TCP-IP.md"),                                # slash -> hyphen
    ("What is REST?", "What is REST.md"),                   # illegal char dropped
    ('A "quoted" title: part', "A quoted title part.md"),   # quotes + colon dropped
    ("Tags #1 and [brackets]", "Tags 1 and brackets.md"),   # wikilink-hostile dropped
    ("Spaced   out\ttitle", "Spaced out title.md"),         # whitespace collapsed
    ("  trim me .", "trim me.md"),                          # surrounding space/dot trimmed
])
def test_title_to_filename(vault, title, expected):
    assert vault.module.title_to_filename(title) == expected


def test_title_to_filename_empty_falls_back(vault):
    """A title that sanitises to nothing yields a safe placeholder, never '.md'."""
    assert vault.module.title_to_filename("???") == "untitled.md"
