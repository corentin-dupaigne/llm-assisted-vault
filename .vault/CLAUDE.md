# CLAUDE.md

Guidance for working in this repository.

## Project purpose

This repo is an **LLM-assisted personal knowledge management vault**. The user
captures Markdown notes into `Inbox/` with zero filing decisions. On every push
to `main`, a GitHub Actions workflow runs `.vault/scripts/process_inbox.py`,
which uses the Claude API to classify each note according to the **PARA method**,
enrich it with metadata and wikilinks, move it to its destination, and record the
result in `.vault/vault.index.json`. The whole run is committed back to the repo.

## Core principles

- **Frictionless capture** — the user drops raw notes in `Inbox/` and makes no
  filing decision at capture time.
- **Immutability of filed notes** — once a note leaves the Inbox it is never
  automatically moved or modified again.
- **Full traceability** — every automated action is a distinct, identifiable
  commit (prefix `chore(llm):`) and is therefore reversible.
- **Portability** — notes are plain Markdown with universal YAML frontmatter,
  readable outside any specific tool.
- **Controlled cost** — if the Inbox holds no notes, no API call is made and no
  processing occurs.

## Repository structure

The vault **root** holds only the user's PARA folders; all machinery lives in a
hidden `.vault/` directory so the vault stays clean and tool-portable.

| Path                          | Role                                                      |
|-------------------------------|-----------------------------------------------------------|
| `Inbox/`                      | Drop zone — the single entry point for new notes.         |
| `Projects/`                   | Active work; one subfolder per active project at runtime. |
| `Areas/`                      | Ongoing responsibilities without a deadline (flat).       |
| `Resources/`                  | Reference material and general knowledge (flat).          |
| `Archive/`                    | Inactive or completed items (flat).                       |
| `Atlas/`                      | Maps of Content (MOCs); maintained manually by the user.  |
| `Templates/`                  | Note templates; never touched by automation.              |
| `Attachments/`                | Binary files and media; never touched by automation.      |
| `.vault/`                     | All non-vault machinery (hidden from the vault view).     |
| `.vault/prompts/system.md`    | System prompt sent to Claude for classification.          |
| `.vault/scripts/process_inbox.py` | The filing pipeline.                                  |
| `.vault/tests/`               | End-to-end test suite (see Tests below).                  |
| `.vault/vault.index.json`     | The vault's source of truth (see schema below).           |
| `.vault/requirements-dev.txt` | Runtime + test dependencies.                              |
| `.vault/.env`                 | Local `ANTHROPIC_API_KEY` (gitignored).                   |
| `.github/workflows/process_inbox.yml` | Triggers the pipeline on push to `main`.          |

`.github/` and `.gitignore` stay at the repo root by necessity: GitHub only
reads workflows from `.github/workflows/` at the root, and `.gitignore` must
govern the whole tree. The script derives both roots from its own location —
`VAULT_DIR` (`.vault/`) for the machinery and index, `REPO_ROOT` (its parent)
for the PARA folders and `.git` — so the two never get confused.

`Projects/`, `Areas/`, `Resources/`, and `Archive/` have no subfolders, except
`Projects/`, which gets one subfolder per active project. Empty folders are kept
in git with a `.gitkeep` file.

## Absolute rules

The automation must **never**:

- Move or modify any file outside of `Inbox/`.
- Touch `Atlas/`, `Templates/`, or `Attachments/`.
- Delete any file.
- Create links from existing notes toward the new note (links only ever flow
  **from** the new note **to** existing ones).
- Overwrite an already-filed note (immutability — a suffix is added on collision).
- Make an API call when the Inbox is empty.

If classification confidence is insufficient, the note is returned as
`unfileable` and **left untouched in `Inbox/`** rather than placed approximately.

## PARA filing hierarchy

Applied strictly in order; stop at the first match:

1. Tied to an **active project** listed in the index → `Projects/<project-name>/`
2. **Ongoing responsibility** without a deadline → `Areas/`
3. **Reference** material or general knowledge → `Resources/`
4. **Inactive or completed** → `Archive/`

Active projects are **auto-detected** at the start of each run by listing the
immediate subfolders of `Projects/`; the result replaces the `projects` array in
the index (the folder listing is authoritative). The user creates a project
simply by making a folder under `Projects/`. The LLM only files into a project
that already exists in the index.

### Capture-time placement override (deterministic escape hatch)

The hierarchy is an LLM judgment call, so it is *non-deterministic* — the same
note could classify differently on different runs, and the model's notion of
"tied to an active project" is broad enough to pull durable reference material
into a project just because a related project is active (e.g. Kubernetes
PV/PVC concept notes vacuumed into a `cka` exam-prep project).

To take back control without re-prompting, the user may **declare placement in
the captured note's own frontmatter**. It is opt-in (only reach for it when you
disagree with the classifier) so frictionless capture is preserved:

```yaml
---
para: Resources        # I decide: durable reference, not project work
---
```

`reconcile_placement` then lets the note's own `para`/`project` win over the
model's choice for the **physical destination, the written frontmatter, and the
index entry** — all three stay consistent. Rules:

- An explicit, valid `para` in the note overrides the model's.
- Rerouting to a *different* root than the model picked **drops** the model's
  project association — a flat root (Areas/Resources/Archive) never carries a
  project. An explicit `project` in the note also wins.
- `para: Projects` with no resolvable project is incoherent → the note is
  **rejected and left in the Inbox** rather than filed approximately.

The LLM is still called for enrichment (domain, tags, wikilinks); only the
placement decision is taken over. The model keeps the destination only when the
note declares no override. This also closes a latent inconsistency: previously a
note could declare `para: Resources` in its frontmatter (which `merge_frontmatter`
keeps verbatim) yet be filed into `Projects/<x>/` by the model, leaving the
file's location at odds with its own metadata.

## `vault.index.json` schema

The index is the LLM's **only** source of truth about the vault's contents.

```json
{
  "projects": [],
  "domains": [],
  "tags": [],
  "notes": []
}
```

- `projects` — active projects, **auto-detected** from the subfolders of
  `Projects/` at the start of every run (the folder listing is authoritative).
- `domains` — canonical list of all domains in use.
- `tags` — canonical list of all tags in use.
- `notes` — one entry per filed note:

```json
{
  "title": "Note Title",
  "path": "Resources/Note Title.md",
  "domain": "kubernetes",
  "tags": ["k3s", "devops"],
  "para": "Resources",
  "project": null,
  "date": "2026-06-04"
}
```

After each run, the new note is appended to `notes`, and any genuinely new
domains/tags are added to their lists (reusing existing equivalents otherwise).

### Verifying the index against the vault (reconciliation)

The filing pipeline only ever writes the index entry for the note it just filed,
so a note edited *after* it was filed — its frontmatter, its title — would leave
the index permanently stale. To keep `vault.index.json` the true source of truth,
`reconcile_index` runs at the start of **every** push (right after `sync_projects`
and **before** any filing), regardless of whether the Inbox holds notes — and it
makes no API call, so it stays within the cost guard.

It rebuilds the index from the notes actually on disk across the four PARA roots:

- Every indexed note is **refreshed** from its file. `domain`, `tags` and `date`
  are re-read from the note's frontmatter and `title` is the filename, while
  `para`/`project` are derived from the file's **location** (so a hand-moved note
  self-corrects). A note's existing `date` is kept if the file has none, so a
  hand-written note without a date does not churn the index.
- An indexed note whose file is **gone** is dropped.
- A note found on disk but **never indexed** (created or moved in by hand) is
  added, in a stable sorted order.
- `domains` and `tags` are recomputed as the values **in use** by the surviving
  notes: existing entries keep their order (diff-friendly), newly seen values are
  appended, and values no note uses any more are pruned.

The pass is order-stable and a no-op when the index already matches disk, so a
fully in-sync vault pushes nothing. When the Inbox is empty but a reconciliation
did change the index, the run commits it as `chore(llm): reconcile vault index`.

## Frontmatter schema

Injected at the very top of every filed note, before existing content:

```yaml
---
domain: <single primary subject>
tags: [secondary-tag-1, secondary-tag-2]
date: <YYYY-MM-DD>
para: <Projects | Areas | Resources | Archive>
project: <project name or null>
---
```

### Merging with existing frontmatter

A captured note may already carry its own frontmatter (e.g. an Obsidian/Dataview
template with fields like `difficulty` or `struggled`). These five mandatory
fields are therefore **merged**, not prepended, by `merge_frontmatter`:

- An existing field — **mandatory or not** — is kept **verbatim** and never
  overridden. If the note already defines `tags: []`, that value stays, even
  though the model proposed tags.
- Every **missing** mandatory field is added.
- The result is always a **single** `---` block (the old behaviour stacked a
  second block on top of the existing one).

The index entry mirrors each note's *effective* metadata: for any mandatory
field the note already defined, the existing value wins over the model's.

If wikilinks were identified, a `## Links` section is appended at the very end
of the note:

```markdown
## Links

- [[Existing Note Title]]
```

## Filenames are the readable title

A filed note's filename **is** its human-readable title (`ArgoCD Helm Install No
CRDs.md`), not a slug. Obsidian is built around filename-as-title, so this keeps
every native surface — the file explorer, quick-switcher, graph node labels, and
the Dataview MOCs in `Atlas/` — readable with no extra metadata, and lets a
wikilink resolve as the bare `[[Note Title]]` (Obsidian resolves by basename, and
the basename is the title). The filename is derived in code by
`title_to_filename`, which is a *light* sanitisation — not slugging: it keeps
spaces and capitalisation and only strips/replaces the characters that are
illegal in a filename or that break wikilinks (`: ? * " < > | # ^ [ ]`, and `/`,
`\` → `-`). So `TCP/IP` is filed as `TCP-IP.md` while its index `title` keeps the
exact `TCP/IP`. The title itself is the note's **Inbox filename** — the readable
name you give the capture; the note body (including any heading) is never
inspected.

The model is instructed (system prompt + `file_note` schema) to build each link
as a bare `[[Note Title]]` using the title verbatim from the index.
`resolve_wikilinks` is a code-side safety net over that contract: it matches each
proposed link against the indexed notes by **title or basename**, re-emits it as
the canonical basename (so it always resolves), de-duplicates, and **drops** any
link matching no indexed note — so a hallucinated link can never be written
broken.

## Markdown formatting

Before a filed note is written, its Markdown **body** (the captured content plus
the generated `## Links` section) is normalized with `mdformat`. The `wikilink`
extension keeps `[[Obsidian links]]` intact — without it mdformat escapes the
brackets. The YAML frontmatter is built canonically and reattached verbatim, so
formatting never rewrites `project: null` or reorders keys. Unfileable notes are
left untouched in `Inbox/` and are not formatted.

## Naming conventions

- `domain` and `tags` are always **lowercase and hyphen-separated**
  (`machine-learning`, `personal-finance`). Before creating a new domain or tag,
  reuse a close existing equivalent from the index to avoid near-duplicates
  (`devops` / `dev-ops` / `DevOps`).
- A note has **exactly one** `domain` and **zero or more** `tags`. The `domain`
  is the single subject the note is centrally about; `tags` are secondary
  subjects it merely touches on.

## Commit convention

All automated commits use the prefix **`chore(llm):`**.

- Single filed note: `chore(llm): organize <filename> → <target_path>`
- Single unfileable note: `chore(llm): unfileable <filename> — <reason>`
- Multiple notes: one commit summarizing all outcomes.

## Languages

Notes may be written in **French or English**; the LLM handles both. Domains and
tags are always emitted in English.

## Forcing valid structured output

`classify_note` uses **forced tool use**: a `file_note` tool with a strict
`input_schema` is supplied and `tool_choice` requires it. The model returns a
`tool_use` block whose `input` is already a parsed dict conforming to the schema
— no prose, no ```json fence, and nothing to `json.loads` (so it cannot fail to
parse). This is model-agnostic; in particular it works on models that reject
assistant-message prefill (e.g. `claude-sonnet-4-6`). If no tool call comes back
at all, the note is treated as `unfileable`.

## Tests

`.vault/tests/` holds an end-to-end suite that exercises the real pipeline
against the live Claude API on an isolated temporary vault (no git, no touching
the real vault). API tests are skipped automatically when `ANTHROPIC_API_KEY` is
unset; the git-step tests run regardless. Run from the repo root:

```bash
python -m venv .venv
.venv/bin/pip install -r .vault/requirements-dev.txt
.venv/bin/python -m pytest .vault/tests/ -v     # reads the key from .vault/.env
.venv/bin/python -m pytest .vault/tests/ -v -s  # also stream the live decisions
```

To inspect the notes the model actually produced, pin the throwaway vaults to a
known (gitignored) directory instead of pytest's auto-cleaned temp dir:

```bash
.venv/bin/python -m pytest .vault/tests/ -s --basetemp=.e2e-output
find .e2e-output -path '*/vault/*' -name '*.md'   # browse the filed notes
```

The key is read from `.vault/.env` (gitignored, never committed). CI passes it
via the `ANTHROPIC_API_KEY` environment variable instead.
