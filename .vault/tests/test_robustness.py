"""Tests for input normalisation, cost guards and failure handling (no API key).

Covers CRLF/BOM notes, YAML frontmatter parsing, skipping empty and unchanged
unfileable notes, per-note API error isolation, and the push retry. The model is
replaced by a scripted fake client, so these are deterministic.
"""

from __future__ import annotations

from types import SimpleNamespace

import git
import httpx
from anthropic import APIConnectionError

RESOURCE_DECISION = {
    "status": "filed", "reason": "Reference.", "target_path": "Resources/x.md",
    "domain": "networking", "tags": ["tcp"], "para": "Resources",
    "project": None, "wikilinks": [],
}
UNFILEABLE_DECISION = {"status": "unfileable", "reason": "Too vague."}


class FakeClient:
    """Stands in for `Anthropic()`: returns scripted decisions (or raises)."""

    def __init__(self, *results):
        self.results = list(results)
        self.calls = 0
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **_kwargs):
        self.calls += 1
        result = self.results.pop(0)
        if isinstance(result, Exception):
            raise result
        block = SimpleNamespace(type="tool_use", name="file_note", input=result)
        return SimpleNamespace(content=[block])


def _api_error():
    return APIConnectionError(request=httpx.Request("POST", "https://api.test"))


def _run(vault, client):
    notes = sorted(p for p in vault.inbox.glob("*.md") if p.is_file())
    return vault.module.process_notes(client, "system", notes, "2026-10-03")


# --- CRLF / BOM ----------------------------------------------------------------

def test_crlf_note_keeps_a_single_frontmatter_block(vault):
    note = vault.drop_note("TCP.md", "")
    note.write_bytes(b"---\r\ntags: [proto]\r\n---\r\nHandshake.\r\n")

    outcome = vault.module.apply_filed(note, dict(RESOURCE_DECISION),
                                       vault.read_index(), "2026-10-03")

    written = (vault.root / outcome["target_path"]).read_text(encoding="utf-8")
    assert written.startswith("---\ntags: [proto]\ndomain: networking\n")
    assert written.count("---\n") == 2
    assert "## tags" not in written and "\r" not in written


def test_bom_note_frontmatter_is_detected(vault):
    note = vault.drop_note("TCP.md", "")
    note.write_bytes("﻿---\ndomain: transport\n---\nBody.\n".encode("utf-8"))

    index = vault.read_index()
    vault.module.apply_filed(note, dict(RESOURCE_DECISION), index, "2026-10-03")

    assert index["notes"][-1]["domain"] == "transport"


# --- YAML frontmatter ------------------------------------------------------------

def test_quoted_values_are_unquoted(vault):
    _, values = vault.module.parse_frontmatter('domain: "go"\ntags: ["a", \'b\']')
    assert values == {"domain": "go", "tags": ["a", "b"]}


def test_yaml_dates_become_iso_strings(vault):
    _, values = vault.module.parse_frontmatter("date: 2026-06-04\nstruggled: true")
    assert values["date"] == "2026-06-04"


def test_invalid_yaml_falls_back_to_lenient_parser(vault):
    keys, values = vault.module.parse_frontmatter('domain: "go"\nbad: a: b: [')
    assert keys == ["domain", "bad"]
    assert values["domain"] == "go"


# --- Cost guards -----------------------------------------------------------------

def test_empty_note_is_skipped_without_api_call(vault):
    vault.drop_note("blank.md", "---\ntags: []\n---\n\n  \n")
    client = FakeClient()

    assert _run(vault, client) == []
    assert client.calls == 0
    assert (vault.inbox / "blank.md").exists()


def test_unchanged_unfileable_note_is_not_resent(vault):
    vault.drop_note("vague.md", "asdf\n")

    first = _run(vault, FakeClient(UNFILEABLE_DECISION))
    assert first[0]["status"] == "unfileable"

    client = FakeClient()
    assert _run(vault, client) == []
    assert client.calls == 0


def test_edited_unfileable_note_is_retried(vault):
    note = vault.drop_note("vague.md", "asdf\n")
    _run(vault, FakeClient(UNFILEABLE_DECISION))

    note.write_text("TCP three-way handshake: SYN, SYN-ACK, ACK.\n", encoding="utf-8")
    client = FakeClient(dict(RESOURCE_DECISION))
    outcomes = _run(vault, client)

    assert client.calls == 1
    assert outcomes[0]["status"] == "filed"
    assert vault.module.load_unfileable_state() == {}


def test_rejected_decision_is_cached_like_unfileable(vault):
    vault.drop_note("x.md", "Some content.\n")
    bad = dict(RESOURCE_DECISION, domain=None)

    outcomes = _run(vault, FakeClient(bad))

    assert outcomes[0]["reason"] == "rejected: model omitted domain"
    assert "x.md" in vault.module.load_unfileable_state()


def test_state_is_pruned_when_note_leaves_inbox(vault):
    note = vault.drop_note("vague.md", "asdf\n")
    _run(vault, FakeClient(UNFILEABLE_DECISION))
    note.unlink()

    assert vault.module.prune_unfileable_state() is True
    assert vault.module.load_unfileable_state() == {}


# --- API errors -------------------------------------------------------------------

def test_api_error_on_one_note_does_not_lose_the_others(vault):
    vault.drop_note("a.md", "First note.\n")
    vault.drop_note("b.md", "Second note.\n")

    outcomes = _run(vault, FakeClient(_api_error(), dict(RESOURCE_DECISION)))

    assert [o["status"] for o in outcomes] == ["error", "filed"]
    assert (vault.inbox / "a.md").exists()
    # Errors are transient: never cached, so the next push retries the note.
    assert "a.md" not in vault.module.load_unfileable_state()


def test_main_fails_the_job_on_api_error(vault, monkeypatch):
    vault.drop_note("a.md", "First note.\n")
    monkeypatch.setattr(vault.module, "Anthropic", lambda: FakeClient(_api_error()))

    assert vault.module.main(commit=False) == 1


# --- Push retry -------------------------------------------------------------------

def test_rejected_push_is_rebased_and_retried(git_vault, tmp_path):
    gv = git_vault
    # Someone else pushes while the run is in progress.
    other = git.Repo.clone_from(gv.remote_path, tmp_path / "other")
    other.git.config("user.name", "user")
    other.git.config("user.email", "user@example.com")
    (tmp_path / "other" / "Inbox" / "new.md").write_text("New.\n", encoding="utf-8")
    other.git.add(A=True)
    other.git.commit("-m", "add notes")
    other.git.push()

    (gv.root / "Resources" / "idea.md").write_text("Idea.\n", encoding="utf-8")
    assert gv.module.commit_and_push(gv.repo, "chore(llm): organize idea") is True

    files = gv.remote_files()
    assert "Resources/idea.md" in files and "Inbox/new.md" in files


def test_unreachable_remote_reports_failure(git_vault, tmp_path):
    gv = git_vault
    gv.repo.git.remote("set-url", "origin", str(tmp_path / "missing.git"))
    (gv.root / "Resources" / "idea.md").write_text("Idea.\n", encoding="utf-8")

    assert gv.module.commit_and_push(gv.repo, "chore(llm): organize idea") is False
