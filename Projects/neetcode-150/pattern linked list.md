---
project: neetcode-150
domain: leetcode
tags: [linked-list, neetcode-150, golang]
date: 2026-07-02
para: Projects
---
# Dummy Head Node

## One-liner

A throwaway placeholder node placed *before* the list so the **first node stops being a special case**. One uniform loop handles every node, first included.

## When to reach for it

Any time the **first element needs different handling than the rest**. In linked lists that's constantly:

- Merging lists ([[Merge Two Sorted Lists]])
- Removing nodes (the head might be the one you delete)
- Partitioning / reordering a list
- Building a new list by re-linking nodes

> [!tip] Trigger phrase
> "The first node has nothing before it to attach to." → dummy head.

## Why it works

The first node is only special because nothing precedes it — you have no `Next` to write into. The dummy *is* that predecessor. Now the loop rule ("compare, link the smaller, advance") applies to the real first node with zero special handling.

- `dummy` — never moves. Remembers the front. Return `dummy.Next` at the end.
- `curr` (write head) — moves forward. Always points at the last node placed so far.

## The shape

```go
dummy := &ListNode{}   // placeholder, Val is garbage, never read, never returned
curr := dummy          // moving write-head

for /* work remaining */ {
    // pick a node, link it, advance — SAME code for the first node and all others
    curr.Next = chosenNode
    curr = curr.Next
}

return dummy.Next      // real list starts AFTER the placeholder
```

## Contrast (the thing it deletes)

```go
// WITHOUT dummy — first node handled by different code than the rest → two seams, two bug sites
if list1.Val < list2.Val { res = list1; list1 = list1.Next } else { res = list2; list2 = list2.Next }
curr := res
for ... { /* every OTHER node, duplicated logic */ }
```

## Key insight

Re-linking beats allocating. The nodes already exist in the input lists — merging/partitioning is just pointing `Next` fields in the right order. No `&ListNode{}` per element, no copying `Val`. The **only** allocation is the single dummy.

> [!warning] Return `dummy.Next`, not `dummy`
> The placeholder is not part of the answer. Returning `dummy` prepends a garbage node.

## Cost / benefit

- **Cost:** one throwaway node (a few bytes, immediately GC'd).
- **Benefit:** deletes an entire special case → fewer seams, fewer edge cases.

## Generalization

This is the linked-list instance of a broader move: **when the first item behaves differently, a sentinel absorbs the difference.** Same idea as sentinel values in arrays/loops. See [[Sentinel Values]].

## Review log

- <!-- YYYY-MM-DD — recall quality, notes -->

## Links

- [[Merge two linked lists]]
