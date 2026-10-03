"""Tests for the compact index sent to the model and the history replay (no API).

`render_index_for_prompt` must keep everything the model uses (projects,
vocabulary, every title, the placement precedent) while dropping per-note fields
it does not. `eval.build_cases` must rebuild the index exactly as the pipeline
saw it when each note was filed — no note from later in the same run — and take
the reference from where the note lives today.
"""

from __future__ import annotations

import importlib.util
import json

from conftest import VAULT_DIR

INDEX = {
    "projects": ["neetcode-150"],
    "domains": ["leetcode", "networking"],
    "tags": ["hashmap"],
    "notes": [
        {"title": "Two Sum", "path": "Projects/neetcode-150/Two Sum.md", "domain": "leetcode",
         "tags": ["hashmap"], "para": "Projects", "project": "neetcode-150", "date": "2026-06-04"},
        {"title": "TCP/IP", "path": "Resources/TCP-IP.md", "domain": "networking",
         "tags": [], "para": "Resources", "project": None, "date": "2026-06-04"},
        {"title": "Valid Anagram", "path": "Projects/neetcode-150/Valid Anagram.md",
         "domain": "leetcode", "tags": [], "para": "Projects", "project": "neetcode-150",
         "date": "2026-06-05"},
    ],
}


def test_render_groups_titles_by_domain_and_location(vault):
    text = vault.module.render_index_for_prompt(INDEX)

    assert "Active projects: neetcode-150" in text
    assert "Domains in use: leetcode, networking" in text
    assert "Tags in use: hashmap" in text
    assert "leetcode @ Projects/neetcode-150: Two Sum | Valid Anagram" in text
    assert "networking @ Resources: TCP/IP" in text
    # Fields the model does not use are gone.
    assert "2026-06-04" not in text and ".md" not in text


def test_render_is_much_smaller_than_json(vault):
    big = dict(INDEX, notes=INDEX["notes"] * 20)
    assert len(vault.module.render_index_for_prompt(big)) < len(json.dumps(big)) / 4


def test_render_empty_index_and_legacy_project_objects(vault):
    text = vault.module.render_index_for_prompt(
        {"projects": [{"name": "site", "description": "x"}], "notes": []})
    assert "Active projects: site" in text
    assert "(no notes yet)" in text


def test_request_carries_compact_index_and_model(vault):
    request = vault.module.build_classification_request(
        "system", "Body.", INDEX, model="claude-haiku-4-5")
    assert request["model"] == "claude-haiku-4-5"
    assert "leetcode @ Projects/neetcode-150" in request["messages"][0]["content"]
    assert request["tool_choice"] == {"type": "tool", "name": "file_note"}


# --- History replay ----------------------------------------------------------

def _load_eval():
    spec = importlib.util.spec_from_file_location("vault_eval", VAULT_DIR / "scripts" / "eval.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _commit(gv, message):
    gv.repo.git.add(A=True)
    gv.repo.git.commit("-m", message)


def test_build_cases_replays_index_as_seen_at_filing_time(git_vault):
    gv = git_vault
    ev = _load_eval()
    gv.drop_note("a.md", "Alpha.\n")
    gv.drop_note("b.md", "Beta.\n")
    _commit(gv, "add notes")

    # A two-note run: A then B are filed and both reach the index.
    for name, title in (("a.md", "A"), ("b.md", "B")):
        (gv.inbox / name).unlink()
        (gv.root / "Resources" / f"{title}.md").write_text(
            f"---\ndomain: misc\ntags: [t{title}]\n---\nBody.\n\n## Links\n\n- [[A]]\n",
            encoding="utf-8")
    entry = lambda t: {"title": t, "path": f"Resources/{t}.md", "domain": "misc",  # noqa: E731
                       "tags": [f"t{t}"], "para": "Resources", "project": None}
    gv.index_path.write_text(json.dumps({
        "projects": [], "domains": ["misc"], "tags": ["tA", "tB"],
        "notes": [entry("A"), entry("B")]}), encoding="utf-8")
    _commit(gv, "chore(llm): process 2 inbox notes\n\n"
                "- organize a.md → Resources/A.md\n- organize b.md → Resources/B.md")

    # The user later disagrees and archives B by hand.
    (gv.root / "Archive").mkdir(exist_ok=True)
    gv.repo.git.mv("Resources/B.md", "Archive/B.md")
    _commit(gv, "archive B")

    cases, skipped = ev.build_cases(gv.repo, "HEAD")

    assert skipped == []
    first, second = cases
    assert first["content"] == "Alpha."
    assert first["index"]["notes"] == []           # nothing filed yet in this run
    assert first["index"]["tags"] == []            # vocabulary from earlier notes only
    assert [n["title"] for n in second["index"]["notes"]] == ["A"]  # never B itself
    assert second["bot_target"] == "Resources/B.md"
    assert second["expected"]["path"] == "Archive/B.md"   # follows the hand move
    assert second["expected"]["para"] == "Archive"
    assert second["expected"]["links"] == ["A"]
    assert second["expected"]["tags"] == ["tB"]


def test_new_run_dir_never_reuses_a_saved_run(vault, monkeypatch, tmp_path):
    ev = _load_eval()
    monkeypatch.setattr(ev.pi, "VAULT_DIR", tmp_path)
    first = ev.new_run_dir("m")
    first.mkdir(parents=True)
    second = ev.new_run_dir("m")
    assert second != first and second.name == f"{first.name}-2"
