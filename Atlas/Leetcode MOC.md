---
type: moc
theme: leetcode
created: 2026-06-17
---
## Exercices I struggled with

```dataview
LIST
FROM "Projects" OR "Areas" OR "Resources" OR "Archive"
WHERE domain = this.theme
AND struggled = True
SORT date DESC
```

## Exercices I did not struggle with
```dataview
LIST
FROM "Projects" OR "Areas" OR "Resources" OR "Archive"
WHERE domain = this.theme
AND struggled = False
SORT date DESC
```

---

