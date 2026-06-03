# LLM-Assisted Vault

A personal knowledge management vault that **classifies, enriches, and links your
notes for you**. You drop a raw Markdown note into `Inbox/` and push. A GitHub
Actions workflow then calls the Claude API to file the note with the
[PARA method](https://fortelabs.com/blog/para/), add metadata and wikilinks, move
it to the right place, and commit the result back — no manual filing required.

The vault is plain Markdown with universal YAML frontmatter, so it stays readable
and portable in Obsidian, Logseq, a plain editor, or anything else.

---

## How it works

```
  You: write a note            GitHub Actions (on push to main)
  ┌───────────────┐            ┌────────────────────────────────────────┐
  │ Inbox/idea.md │ ──push──▶  │ .vault/scripts/process_inbox.py        │
  └───────────────┘            │   1. read note + vault index           │
                               │   2. ask Claude to classify (PARA)     │
                               │   3. inject frontmatter + wikilinks    │
                               │   4. move note to its destination      │
                               │   5. update .vault/vault.index.json    │
                               │   6. commit & push (chore(llm): …)     │
                               └────────────────────────────────────────┘
                                              │
              ┌───────────────────────────────┴───────────────┐
              ▼                                                ▼
   Resources/tcp-handshake.md                  (or left in Inbox if unfileable)
```

If the Inbox is empty, **no API call is made** — empty pushes cost nothing.

### The PARA decision

Each note is filed by a strict hierarchy (first match wins):

1. Tied to an **active project** in the index → `Projects/<project-name>/`
2. **Ongoing responsibility** without a deadline → `Areas/`
3. **Reference** material or general knowledge → `Resources/`
4. **Inactive or completed** → `Archive/`

If confidence is insufficient, the note is **left untouched in `Inbox/`** rather
than filed approximately.

---

## Repository structure

The vault **root** holds only your PARA folders; all machinery lives in a hidden
`.vault/` directory.

| Path | Role |
|------|------|
| `Inbox/` | Drop zone — the single entry point for new notes. |
| `Projects/` | Active work; one subfolder per active project. |
| `Areas/` | Ongoing responsibilities without a deadline. |
| `Resources/` | Reference material and general knowledge. |
| `Archive/` | Inactive or completed items. |
| `Atlas/` | Maps of Content (MOCs), maintained by you. |
| `Templates/` | Note templates (incl. an Obsidian MOC template). |
| `Attachments/` | Binary files and media. |
| `.vault/` | All automation: pipeline, prompt, index, tests, docs. |
| `.github/workflows/process_inbox.yml` | Triggers the pipeline on push to `main`. |

`.github/` and `.gitignore` stay at the root because GitHub and git require them
there. Everything else the automation needs is under `.vault/` — see
[`.vault/CLAUDE.md`](.vault/CLAUDE.md) for the full reference.

---

## Setup

### 1. Add your Anthropic API key as a repo secret

The workflow reads `ANTHROPIC_API_KEY` from GitHub Actions secrets:

```bash
gh secret set ANTHROPIC_API_KEY        # paste your key when prompted
```

That is all that is required for the automation to run on every push.

### 2. (Optional) Local development

To run the pipeline or tests locally, create a virtualenv and provide the key via
`.vault/.env`:

```bash
python -m venv .venv
.venv/bin/pip install -r .vault/requirements-dev.txt
echo 'ANTHROPIC_API_KEY=sk-ant-...' > .vault/.env   # gitignored, never committed
```

---

## Usage

### Capture a note

Create any Markdown file in `Inbox/` and push to `main`:

```bash
echo "# k3s networking\n\nNotes on CNI setup..." > Inbox/k3s.md
git add Inbox/k3s.md && git commit -m "capture: k3s networking" && git push
```

The workflow runs automatically. When it finishes, the note has been filed (e.g.
to `Resources/k3s-networking.md`) with frontmatter like:

```yaml
---
domain: kubernetes
tags: [k3s, networking]
date: 2026-06-04
para: Resources
project: null
---
```

…and, if relevant existing notes were found, a `## Links` section of wikilinks at
the end. Notes can be written in **English or French**; metadata is always
emitted in English.

### Register an active project

Projects are the only thing you maintain by hand. Add them to the `projects` list
in `.vault/vault.index.json` so the LLM can file work into `Projects/<name>/`:

```json
{
  "projects": [
    { "name": "website-redesign", "description": "Rebuild the marketing site." }
  ],
  "domains": [],
  "tags": [],
  "notes": []
}
```

`domains`, `tags`, and `notes` are maintained automatically by the pipeline.

---

## Principles & guarantees

- **Frictionless capture** — no filing decisions at write time.
- **Immutability** — once a note leaves the Inbox it is never auto-moved or
  modified again.
- **Full traceability** — every automated run is a distinct `chore(llm):` commit,
  so it is auditable and reversible.
- **Portability** — plain Markdown + YAML, no proprietary lock-in.
- **Controlled cost** — no Inbox notes means no API call.

The automation **never** touches anything outside `Inbox/`, never modifies
`Atlas/` / `Templates/` / `Attachments/`, never deletes a file, and never links
from existing notes back toward a new one.

---

## Tests

An end-to-end suite lives in `.vault/tests/`. API tests hit the real Claude API
(skipped automatically when no key is set); git-step tests run against a throwaway
local repo and always run.

```bash
.venv/bin/python -m pytest .vault/tests/ -v
```

See the [Tests section of `.vault/CLAUDE.md`](.vault/CLAUDE.md#tests) for inspecting
the notes the model produces.

---

## Implementation notes

- **Model:** `claude-sonnet-4-6`.
- **Structured output** is guaranteed via **forced tool use** (a `file_note` tool
  with a strict schema), so responses are always valid structured data — no JSON
  parsing failures, no markdown fences.
- Full design reference: [`.vault/documentation/vault-architecture.md`](.vault/documentation/vault-architecture.md).
