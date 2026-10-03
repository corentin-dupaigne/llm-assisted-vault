#!/usr/bin/env python3
"""Report near-duplicate domains/tags in the vault index (read-only).

The pipeline keeps *new* notes inside the existing vocabulary, but never edits a
filed note, so drift that is already in the vault stays until you fix it. This
lists it so you can: rename the stragglers in the notes' frontmatter by hand,
or add a line to `.vault/aliases.json` so future notes use the canonical form.

    .venv/bin/python .vault/scripts/lint_labels.py
"""

from __future__ import annotations

import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import process_inbox as pi  # noqa: E402


def main() -> int:
    index = pi.load_index()
    notes = index.get("notes", [])
    domain_use = Counter(n["domain"] for n in notes if n.get("domain"))
    tag_use = Counter(t for n in notes for t in n.get("tags") or [])

    groups: dict[str, set[str]] = defaultdict(set)
    for label in [*domain_use, *tag_use]:
        groups[pi.label_key(label)].add(label)
    duplicates = [sorted(g) for g in groups.values() if len(g) > 1]

    def uses(label: str) -> str:
        return f"{label} (domain×{domain_use[label]}, tag×{tag_use[label]})"

    print("Near-duplicate labels:" if duplicates else "No near-duplicate labels.")
    for group in sorted(duplicates):
        print("  " + "  ~  ".join(uses(label) for label in group))

    as_tag = [(n["path"], n["domain"]) for n in notes
              if n.get("domain") and n["domain"] in (n.get("tags") or [])]
    print(f"\nNotes whose domain is also one of their tags: {len(as_tag)}")
    for path, domain in as_tag:
        print(f"  {path}  ({domain})")

    both = sorted(set(domain_use) & set(tag_use))
    print(f"\nLabels used both as a domain and as a tag: {', '.join(both) or 'none'}")
    return 1 if duplicates or as_tag else 0


if __name__ == "__main__":
    sys.exit(main())
