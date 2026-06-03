# LLM-Assisted Vault — Architecture & Features

## Vision

A personal knowledge management vault where the friction of capture and organization is reduced to a minimum. The user writes and drops — the system organizes, connects, and enriches automatically.

The vault is designed to be **portable and independent of any specific tool**. Files remain standard Markdown enriched with universal metadata, readable and usable outside of any particular environment.

---

## Core Principles

- **Frictionless capture** — the user makes no filing decision at the time of writing
- **Immutability of filed notes** — a placed note will never be automatically moved or modified
- **Full traceability** — every automated action is recorded and reversible
- **Portability** — no data locked into a proprietary format
- **Controlled cost** — no automatic processing if no note needs to be treated

---

## Vault Structure

```
/Inbox/          ← drop zone, single entry point
/Projects/       ← active work with one subfolder per project
/Areas/          ← ongoing responsibilities without deadlines
/Resources/      ← thematic references and knowledge
/Archive/        ← inactive or completed items
/Atlas/          ← thematic navigation maps (MOCs)
/Templates/      ← note templates
/Attachments/    ← binary files and media
```

### PARA Filing Logic

Each note is filed according to a simple decision hierarchy:

1. Is it related to an identified active project? → `Projects/<project-name>/`
2. Is it an ongoing responsibility without a deadline? → `Areas/`
3. Is it a reference or general knowledge? → `Resources/`
4. Is it completed or inactive? → `Archive/`

Subfolders only exist within `Projects/`, one per active project. All other categories are flat — fine-grained thematic navigation is handled by MOCs.

---

## Note Metadata

Each processed note automatically receives a structured metadata header:

```yaml
---
domain: <primary subject of the note>
tags: [secondary-tag-1, secondary-tag-2]
date: <processing date>
para: <Projects | Areas | Resources | Archive>
project: <project name or null>
---
```

### Domain vs Tags

- **`domain`** — the single primary subject of the note. A note has exactly one domain.
- **`tags`** — secondary subjects the note touches without being centrally about them.

This distinction enables two-level navigation: finding notes *about* a subject, and finding notes that *mention* a subject.

---

## Vault Index

A central index file is automatically maintained. It contains:

- The list of active projects with their descriptions
- The canonical list of all domains in use
- The canonical list of all tags in use
- An inventory of all notes with their metadata

This index acts as the vault's memory. It allows the automated system to:
- Reuse existing domains and tags rather than creating new near-duplicates
- Identify candidate notes to link to from a new note
- Know active projects without traversing the file tree

The index is updated after every automated processing run.

---

## Automated Processing

### Trigger

Processing is triggered only when files are present in `/Inbox/` at the time of a sync. If Inbox is empty, no processing occurs and no cost is incurred.

### For Each Note in Inbox

The automated system performs the following steps in order:

1. **Reading** the note and the vault index
2. **Filing decision** — PARA category and project if applicable
3. **Metadata generation** — domain, tags, date, para, project
4. **Link identification** — existing notes relevant enough to link to from the new note
5. **Wikilink injection** into the body of the note
6. **Moving** the note to its final destination
7. **Index update**

### Strict Rules

- A filed note is **never moved** again afterwards
- Links are created **only from the new note toward existing ones**, never the reverse
- If filing confidence is insufficient, the note **stays in Inbox** — it is not placed approximately
- Each processing run produces a distinct, identifiable record

### Metadata Consistency

Before creating a new domain or tag, the system consults the index to check for an equivalent existing term. This prevents the proliferation of near-duplicate variants (`devops`, `dev-ops`, `DevOps`) that would fragment navigation.

---

## Navigation — Maps of Content (MOCs)

MOCs are thematic navigation notes stored in `/Atlas/`. They contain no substantive content but aggregate links to relevant notes on a given theme.

### Two Levels of Relevance

Each MOC distinguishes:

- **Primary notes** — notes whose `domain` matches the MOC's theme
- **Related notes** — notes whose `tags` include the MOC's theme without it being their central subject

This separation makes it easy to identify reference resources for a theme versus notes that touch on it in passing.

### MOC Characteristics

- MOCs update automatically thanks to metadata — no manual maintenance required
- A note can appear in multiple MOCs simultaneously without being duplicated
- MOCs are created manually by the user when a theme reaches critical mass — they are not generated automatically

---

## Traceability and Control

### History

Each automated processing run produces a distinct versioned record, separate from human contributions. This makes it possible to:
- Precisely identify what the automated system did
- Revert a specific processing run without affecting the rest of the vault
- Audit filing decisions over time

### Error Handling

If a note remains in Inbox after processing, it is an explicit signal that the system could not file it with sufficient confidence. The user can then move it manually or rephrase the note to assist filing.

---

## What the System Does Not Do

- Never modifies an already-filed note
- Never creates links from existing notes toward new ones
- Never generates MOCs automatically
- Never merges similar notes
- Never deletes anything
