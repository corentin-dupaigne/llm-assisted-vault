---
domain: golang
tags: []
date: 2026-09-28
para: Resources
project: null
---
## Core principle

A package name describes **what it provides**, not what it does. It is read together with the identifiers it exports — `pkg.Func` forms a two-word phrase at the call site, so name for that combined reading.

## Rules

- **Short, lowercase, single word.** No `under_scores`, no `camelCase`, no plurals unless the domain is inherently plural. → `bytes`, `http`, `json`, `time`, `io`
- **Noun for the package, verbs in the functions.** The subject is the package; the actions are its API. → `json` exposes `Marshal` / `Unmarshal`
- **Avoid stutter.** The package qualifier is already the first word of every call, so don't repeat it in function names.
  - `bytes.Buffer` — not `bytes.BytesBuffer`
  - `link.Create()` — not `link.CreateVeth()`
- **No grab-bag names.** `util`, `common`, `helpers`, `misc` describe nothing and collect junk. If the contents don't share a nameable concept, they probably shouldn't be one package.

## Why it holds

Verbs live in functions, nouns in package names. The noun names the subject; the exported functions supply the actions. Naming the domain and letting functions carry the verbs is what makes call sites read as clear phrases.

## References

- Effective Go — package names
- The Go Blog — "Package names"

## Links

- [[Go Project Structure — Rules & Conventions]]
- [[io.Reader]]
