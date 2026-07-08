---
domain: golang
tags: [devops]
date: 2026-07-08
para: Resources
project: null
---
Go's project layout is governed by two distinct categories: rules the compiler enforces (code will not build if violated) and conventions the community and tooling expect (nothing prevents violating them, but doing so signals unfamiliarity with the ecosystem). The two are worth keeping separate, because the enforced rules constrain how you *can* structure a project, while the conventions describe how you *should*.

## Compiler-enforced rules

**One package per directory.** Every `.go` file in a directory must declare the same `package` name; mixing package names in a single directory does not compile. A directory maps one-to-one to a package, which means splitting code into packages requires splitting it into directories. This is the rule that most shapes physical layout.

**No import cycles.** Package imports must form a directed acyclic graph. If A imports B and B imports C, then C importing A is rejected at compile time. There is no escape hatch. In practice this is the strongest force pushing toward sound design, because a cycle usually reveals that two packages are really one, or that a shared third package is needed to hold common types.

**Unused imports and unused local variables are errors.** Not warnings — the build fails. Package-level variables may be unused, but any unused local variable or import halts compilation.

**`package main` with `func main()` produces an executable.** Any other package name compiles to a library that can be imported but not run directly.

**`_test.go` files compile only under `go test`.** They are never included in the production binary, which is how tests can live alongside the code they exercise without affecting builds.

**Package name and directory name are technically independent.** The import path is the directory path; the identifier used in code is whatever the file's `package` clause declares. Convention keeps them identical (`internal/ipam` declaring `package ipam`), and the notable exception is `package main`, which does not match its directory.

## The `internal/` boundary

A package located under an `internal/` directory can be imported only by code rooted at the parent of that `internal/` directory, including every subdirectory beneath it, at any depth. Code outside that subtree — most importantly, a different module — receives a compile error when it attempts the import. This is enforced by the toolchain, not by a linter or a naming agreement.

```
tiny-cni/                    # parent of internal/
├── internal/
│   ├── ipam/                # the internal package
│   └── config/
├── cmd/tiny-cni/            # different package; may import internal/ipam
└── pkg/helper/              # different package; may import internal/ipam

github.com/other/project/    # different module; may NOT import it
```

The mechanism is best understood as project-private (more precisely, subtree-private) visibility, distinct from the per-package privacy provided by lowercase identifiers. The two compose: within `internal/ipam`, lowercase helpers remain visible only to `ipam` itself, while exported identifiers are callable by other packages in the project — yet `internal/` still prevents those exports from leaking outside it. The effect is code that is exported for the project's own use without becoming part of a public API surface that carries a compatibility obligation.

`internal/` may appear at any level of the tree, not only at the repository root. The rule always refers to the parent of the `internal/` directory, wherever that directory sits.

## Directories with special meaning

| Directory | Status | Purpose |
|-----------|--------|---------|
| `internal/` | Enforced | Subtree-private packages. |
| `cmd/` | Convention | Holds `main` packages, one subdirectory per binary. Most useful when a project builds multiple executables. |
| `pkg/` | Convention (debated) | Signals libraries intended for external import. Many projects omit it and place importable packages at the root. |
| `vendor/` | Special | When present, builds may use dependencies copied here rather than the module cache. Largely legacy since Go modules. |
| `testdata/` | Special | Ignored by the `go` tool during builds. The conventional home for test fixtures such as sample configuration or golden files. |

## Conventions

**File naming.** Lowercase with underscores for readability (`ip_allocator.go`). Two suffixes carry semantic weight: `_test.go` marks test files, and `_GOOS.go` / `_GOARCH.go` apply build constraints — `netlink_linux.go` compiles only on Linux. The build-constraint suffixes are a clean way to both document and enforce platform-specific code.

**Organize by responsibility, not by kind.** Grouping files by their type — a `models` package, a `services` package, a `utils` file — is an anti-pattern in Go and typically indicates habits carried from another language. Cohesion should follow domain: an `ipam` package holds its own types, logic, and errors together.

**Avoid catch-all packages.** A `utils` or `common` package tends to accumulate unrelated code and is a frequent source of import cycles. Genuinely shared code should be named for what it is (`iputil` rather than `utils`).

**Keep `package main` thin.** The entry point should parse input, wire dependencies together, delegate to internal packages, and handle the top-level error and exit. Business logic belongs in importable packages where it can be tested; `main` is the untestable shell and, typically, the single place that calls `os.Exit`.

**Defer structure until it is warranted.** A small project does not benefit from a deep directory tree. Begin with a few packages and split further only when a package grows unwieldy or a real dependency boundary emerges. Premature splitting introduces import-cycle problems and ceremony without corresponding benefit.

**`doc.go`.** An optional file containing only a package-level documentation comment, used when that documentation is substantial enough to warrant its own file. Common in larger codebases.

## Review considerations

The characteristics that indicate a sound Go layout are package boundaries that correspond to genuine responsibilities, an absence of import cycles, a thin `main`, deliberate use of `internal/` as a privacy boundary, and `testdata/` for fixtures. The recurring indicators of an inexperienced layout are a `utils` or `common` grab-bag, business logic accumulated in `main`, and a type-based folder structure (`models`, `services`, `controllers`) imported from another ecosystem. Idiomatic Go tends to be simpler than newcomers expect; correct boundaries matter more than an abundance of them.

## Links

- [[golang-interfaces]]
- [[golang-structs]]
- [[Roadmap]]
