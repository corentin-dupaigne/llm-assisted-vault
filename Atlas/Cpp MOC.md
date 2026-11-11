---
type: moc
theme: cpp
created: 2026-11-11
---
# Cpp — Map of Content

> [!info] Navigation map for the **Cpp** theme.
> The lists below populate automatically from each note's metadata.
> There is nothing to maintain by hand. Requires the **Dataview** plugin.

## Primary notes
Notes whose `domain` **is** this theme — the reference material *about* it.

```dataview
LIST
FROM "Projects" OR "Areas" OR "Resources" OR "Archive"
WHERE domain = this.theme
SORT date DESC
```

## Related notes
Notes that merely *touch* this theme through their `tags`.

```dataview
LIST
FROM "Projects" OR "Areas" OR "Resources" OR "Archive"
WHERE contains(tags, this.theme) AND domain != this.theme
SORT date DESC
```

---

