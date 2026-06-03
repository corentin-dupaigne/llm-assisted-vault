"""Tests for Step 3 — the real git commit + push.

These exercise `commit_and_push` / `main(commit=True)` against a throwaway local
repo wired to a *bare local remote* (see the `git_vault` fixture). They prove
that filing results actually reach the remote: the new file is added, the moved
note's old path is deleted, and the commit message is correct — the piece the
pipeline-only tests deliberately skip.

The first two tests are deterministic and need no API key. The last runs the
full loop (real API + real push) and carries the `api` marker.
"""

from __future__ import annotations

import re

import pytest


def test_commit_and_push_publishes_move_to_remote(git_vault):
    """A filed note (new file + deleted Inbox source) reaches the bare remote."""
    gv = git_vault

    # A captured note already tracked and pushed to the remote.
    note = gv.drop_note("idea.md", "# Idea\n\nA captured thought.\n")
    gv.repo.git.add(A=True)
    gv.repo.git.commit("-m", "capture idea")
    gv.repo.git.push()
    assert "Inbox/idea.md" in gv.remote_files()

    # Simulate the pipeline's result: the note is enriched, written to its PARA
    # destination, and removed from the Inbox (a move).
    dest = gv.root / "Resources" / "idea.md"
    dest.write_text(
        "---\ndomain: misc\ntags: []\ndate: 2026-06-04\npara: Resources\nproject: null\n---\n"
        "# Idea\n\nA captured thought.\n",
        encoding="utf-8",
    )
    note.unlink()

    message = gv.module.build_commit_message([
        {"status": "filed", "filename": "idea.md", "target_path": "Resources/idea.md"}
    ])
    gv.module.commit_and_push(gv.repo, message)

    files = gv.remote_files()
    assert "Resources/idea.md" in files, "filed note did not reach the remote"
    assert "Inbox/idea.md" not in files, "moved note's old path still on the remote"
    assert gv.remote_message().strip() == "chore(llm): organize idea.md → Resources/idea.md"


def test_commit_and_push_is_noop_when_nothing_changed(git_vault):
    """The Step 3 guard: a clean tree produces no new commit on the remote."""
    gv = git_vault
    before = gv.remote_head_sha()

    gv.module.commit_and_push(gv.repo, "chore(llm): should not be committed")

    assert gv.remote_head_sha() == before, "an empty run must not push a commit"


@pytest.mark.api
def test_full_loop_files_note_and_pushes_commit(git_vault):
    """End-to-end: real classification + real commit + real push to the remote."""
    gv = git_vault
    gv.drop_note(
        "photosynthesis.md",
        "# Photosynthesis\n\n"
        "Plants convert light, water and carbon dioxide into glucose and oxygen "
        "via chlorophyll in their chloroplasts. General reference knowledge with "
        "no associated project and no deadline.\n",
    )
    before = gv.remote_head_sha()

    rc = gv.run_main()
    assert rc == 0

    # A new commit was actually pushed.
    assert gv.remote_head_sha() != before, "no commit reached the remote"
    message = gv.remote_message()
    assert message.startswith("chore(llm): organize photosynthesis.md →"), message

    # The destination named in the commit message exists on the remote, and the
    # note is no longer sitting in the Inbox there.
    target = message.split("→", 1)[1].strip().splitlines()[0].strip()
    files = gv.remote_files()
    assert target in files, f"filed note {target!r} missing from the remote"
    assert not any(re.fullmatch(r"Inbox/photosynthesis\.md", f) for f in files)
    # The index update was committed alongside the note.
    assert "vault.index.json" in files
