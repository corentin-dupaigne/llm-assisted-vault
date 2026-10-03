# Model benchmarks

Each folder is one run of `.vault/scripts/eval.py`. A run replays the vault's
past filings: every `organize` line of a `chore(llm):` commit, 65 cases on
2026-10-03. Each case gets the note and the index exactly as the pipeline saw
them at the time, and the result is scored against where the note lives today.
The vault itself was filed by **Sonnet 4.6**. All 65 historical runs came after
the switch from Haiku on 2026-06-04, and no other model has been used.

| File | Content |
|---|---|
| `summary.json` | Scores of the raw run |
| `cases.jsonl` | Every raw decision, the reference, and what the pipeline would file |
| `*.rescored.*` | The same decisions re-scored by later code (`--rescore`, no API call) |

The Sonnet 4.6 and Haiku 4.5 runs keep only their summaries; their per-case
decisions were lost to a rescore bug that has since been fixed (`5f7488e`).

## 2026-10-03: which model should file notes?

Same prompt and compact index for every run. Sonnet 4.6 and Haiku 4.5 use a
forced tool call. Sonnet 5.5 and Opus 5.5 reject a forced call, so they use
`tool_choice: auto` + `strict` at `effort: low`.

| | **Sonnet 4.6** (current) | Sonnet 5.5 | Opus 5.5 | Haiku 4.5 |
|---|---|---|---|---|
| Filed (not unfileable/rejected) | **98%** | 97% | 95% | 94% |
| Placement = vault | 97% | **98%** | 94% | 97% |
| Domain = vault (model-decided) | 89% | 89% | 91% | **92%** |
| Tag overlap (Jaccard)¹ | **0.72** | 0.54 | 0.54 | 0.55 |
| Link recall (vault links found) | **72%** | 46% | 51% | 31% |
| Link precision | 88% | 92% | 88% | **93%** |
| Links per note (vault: 2.7) | **2.2** | 1.4 | 1.6 | 0.9 |
| Input tokens / note | 3.7k | 4.6k | 4.6k | 3.7k |
| Cost for 65 notes | $0.95 | $0.81 | $1.68 | **$0.31** |
| Median latency | 4.1 s | 3.2 s | 4.4 s | **2.3 s** |

¹ Sonnet 4.6 and Haiku are scored before label hygiene (`47e2c83`); Sonnet 5.5
and Opus after it. Hygiene only rewrites tags. It lowers agreement with the
vault's own old spellings (e.g. 0.585 → 0.535 for Sonnet 5.5) while raising it
against a cleaned reference (0.585 → 0.603).

**Decision: keep Sonnet 4.6.** It finds by far the most of the links the vault
kept, and reuses existing tags best. It also files as well as any other model.
At this vault's volume (~65 notes in 4 months) it costs about $0.25/month.

Notes per model:

- **Opus 5.5** (effort `low`) makes the most placement mistakes. It pulls
  reference notes into related projects (*IPAM*, *Go Project Structure* →
  `Projects/cni`; *Bucket sort*, *Floyd's Tortoise and Hare* →
  `Projects/neetcode-150`), the "vacuuming" the capture-time `para:` override
  exists for. Its three unfileables are well argued, though: a study plan it
  sees as a project with no matching project, and a bare keyword list. Opus
  defaults to `medium` effort; `low` may undersell it. That has not been
  measured (another run is ~$2).
- **Sonnet 5.5** places notes best, but it finds fewer links and invents new
  domains (`clothing`, `algorithms`, `probability-statistics`). Its tokenizer
  uses ~24% more input tokens, so it is only 15% cheaper than Sonnet 4.6.
- **Haiku 4.5** is the cheapest and fastest, but links little. Its first run
  surfaced three pipeline bugs, now fixed: string tags split into characters,
  an invented project folder, and malformed labels.

Caveats: 65 cases, one run each (models are not deterministic). Agreement with
the vault is not correctness. Only one historical placement was ever corrected
by hand (*Floyd's Tortoise and Hare* → `Resources`), and no link was reviewed.
