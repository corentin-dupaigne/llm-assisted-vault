---
type: moc
theme: 
created: {{date}}
---
# {{title}} — Map of Content

> [!info] Navigation map for the **{{title}}** theme.
> Set `theme` in the frontmatter above to the canonical domain/tag string this MOC
> covers (lowercase, hyphen-separated — e.g. `kubernetes`). The lists below populate
> automatically from each note's metadata; there is nothing to maintain by hand.
>
> Move this MOC into `Atlas/` once instantiated. Requires the **Dataview** plugin.

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

<!--
Manual fallback (no Dataview / portability outside Obsidian):
delete the query blocks above and list wikilinks by hand instead.

## Primary notes
- [[Note A]]

## Related notes
- [[Note B]]
-->
