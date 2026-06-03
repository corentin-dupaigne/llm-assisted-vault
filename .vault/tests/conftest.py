"""Shared fixtures for the end-to-end test suite.

Two kinds of tests live here:

* **API tests** (marker `api`) hit the real Claude API
  (model `claude-haiku-4-5-20251001`) and are skipped when `ANTHROPIC_API_KEY`
  is unavailable.
* **Git-step tests** exercise the real commit/push (Step 3) against a throwaway
  local repo and a *bare local remote* — no network, no real remote. These run
  regardless of the API key.

Neither kind ever touches the real vault: each test runs against a temporary
vault and the production module's path constants are redirected at it.
"""

from __future__ import annotations

import importlib.util
import json
import os
import shutil
import sys
from datetime import date
from pathlib import Path

import git
import pytest
from dotenv import load_dotenv

# This file lives at `.vault/tests/`, so its grandparent is the `.vault/` dir
# that holds the machinery (the script, system prompt and .env).
VAULT_DIR = Path(__file__).resolve().parent.parent
SCRIPT_PATH = VAULT_DIR / "scripts" / "process_inbox.py"
REAL_SYSTEM_PROMPT = VAULT_DIR / "prompts" / "system.md"

# Load .env from the .vault/ dir so the real key is available locally without
# exporting it by hand. CI provides ANTHROPIC_API_KEY via the environment.
load_dotenv(VAULT_DIR / ".env")

PARA_ROOTS = ["Projects", "Areas", "Resources", "Archive"]
EMPTY_INDEX = {"projects": [], "domains": [], "tags": [], "notes": []}


# --- pytest hooks ------------------------------------------------------------

def pytest_configure(config):
    config.addinivalue_line("markers", "api: test makes a real Claude API call")


def pytest_collection_modifyitems(config, items):
    """Skip only API-marked tests when no key is set; git-step tests still run."""
    if os.environ.get("ANTHROPIC_API_KEY"):
        return
    skip = pytest.mark.skip(reason="ANTHROPIC_API_KEY not set (.env or environment)")
    for item in items:
        if "api" in item.keywords:
            item.add_marker(skip)


# --- vault construction ------------------------------------------------------

def _load_process_module():
    """Import scripts/process_inbox.py as a fresh module named `process_inbox`."""
    spec = importlib.util.spec_from_file_location("process_inbox", SCRIPT_PATH)
    module = importlib.util.module_from_spec(spec)
    sys.modules["process_inbox"] = module
    spec.loader.exec_module(module)
    return module


def _build_vault_tree(root: Path, *, gitkeep: bool = False) -> Path:
    """Create the PARA folder layout, system prompt and empty index under `root`."""
    (root / "Inbox").mkdir(parents=True)
    for para in PARA_ROOTS:
        (root / para).mkdir()
    (root / "prompts").mkdir()
    shutil.copy(REAL_SYSTEM_PROMPT, root / "prompts" / "system.md")

    index_path = root / "vault.index.json"
    index_path.write_text(json.dumps(EMPTY_INDEX), encoding="utf-8")

    if gitkeep:
        # Git can't track empty dirs; keep them so PARA roots exist on the remote.
        for folder in ["Inbox", *PARA_ROOTS]:
            (root / folder / ".gitkeep").write_text("", encoding="utf-8")
    return index_path


def _redirect_module_paths(monkeypatch, module, root: Path, index_path: Path):
    monkeypatch.setattr(module, "REPO_ROOT", root)
    monkeypatch.setattr(module, "INBOX_DIR", root / "Inbox")
    monkeypatch.setattr(module, "INDEX_PATH", index_path)
    monkeypatch.setattr(module, "SYSTEM_PROMPT_PATH", root / "prompts" / "system.md")


# --- helper objects ----------------------------------------------------------

class _VaultBase:
    def __init__(self, module, root: Path, index_path: Path):
        self.module = module
        self.root = root
        self.inbox = root / "Inbox"
        self.index_path = index_path

    def seed_index(self, **fields):
        data = json.loads(self.index_path.read_text(encoding="utf-8"))
        data.update(fields)
        self.index_path.write_text(json.dumps(data), encoding="utf-8")

    def read_index(self):
        return json.loads(self.index_path.read_text(encoding="utf-8"))

    def drop_note(self, name: str, content: str) -> Path:
        path = self.inbox / name
        path.write_text(content, encoding="utf-8")
        return path


class Vault(_VaultBase):
    """Isolated vault for the pure pipeline (no git)."""

    def run(self):
        notes = sorted(p for p in self.inbox.glob("*.md") if p.is_file())
        client = self.module.Anthropic()
        system_prompt = (self.root / "prompts" / "system.md").read_text(encoding="utf-8")
        return self.module.process_notes(client, system_prompt, notes, date.today().isoformat())


class GitVault(_VaultBase):
    """Isolated vault that is also a git repo wired to a bare local remote."""

    def __init__(self, module, root, index_path, repo, remote_path):
        super().__init__(module, root, index_path)
        self.repo = repo
        self.remote_path = remote_path

    def _remote(self) -> git.Repo:
        # Re-open each time so we observe the pushed refs, not a cached view.
        return git.Repo(self.remote_path)

    def remote_head_sha(self) -> str:
        return self._remote().head.commit.hexsha

    def remote_message(self) -> str:
        return self._remote().head.commit.message

    def remote_files(self) -> list[str]:
        tree = self._remote().head.commit.tree
        return [blob.path for blob in tree.traverse() if blob.type == "blob"]

    def run_main(self) -> int:
        """Run the full pipeline including the real git commit + push (Step 3)."""
        return self.module.main(commit=True)


# --- fixtures ----------------------------------------------------------------

@pytest.fixture
def vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    index_path = _build_vault_tree(root)
    module = _load_process_module()
    _redirect_module_paths(monkeypatch, module, root, index_path)
    return Vault(module, root, index_path)


@pytest.fixture
def git_vault(tmp_path, monkeypatch):
    root = tmp_path / "vault"
    index_path = _build_vault_tree(root, gitkeep=True)
    module = _load_process_module()
    _redirect_module_paths(monkeypatch, module, root, index_path)

    # Bare repo acts as `origin` — a real push target with no network.
    remote_path = tmp_path / "remote.git"
    git.Repo.init(remote_path, bare=True, initial_branch="main")

    repo = git.Repo.init(root, initial_branch="main")
    repo.git.config("user.name", "llm-vault-bot")
    repo.git.config("user.email", "llm-vault-bot@users.noreply.github.com")
    repo.create_remote("origin", str(remote_path))
    repo.git.add(A=True)
    repo.git.commit("-m", "chore: seed test vault")
    repo.git.push("--set-upstream", "origin", "main")

    return GitVault(module, root, index_path, repo, remote_path)
