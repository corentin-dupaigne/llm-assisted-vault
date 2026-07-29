---
para: Resources
---

> [!abstract] One-liner
> Manufacture a fake predecessor for the head so that every node in the list can be treated identically. It is a **syntactic** trick, not a memory-management one.

## The problem it solves

Almost every linked-list mutation has the shape "reach a node through its predecessor":

```go
prev.Next = cur.Next
```

The real head has no predecessor, so that line cannot be written for it. Without a dummy you are forced into two code paths:

```go
if cur == head {
    head = head.Next      // special path
} else {
    prev.Next = cur.Next  // normal path
}
```

Two paths doing one conceptual thing. That branch is where nil-pointer and wrong-return-value bugs live.

## Trigger question

> **Might the node I return be different from the node I was given?**

- **Yes** → dummy
- **No** → no dummy

That single question decides it. Nothing else is needed.

## The two modes

The constructor tells you which mode you are in.

### Mode 1 — Mutating an existing list

```go
dummy := &ListNode{Next: head}
prev := dummy
for cur := head; cur != nil; cur = cur.Next {
    // ... prev.Next = cur.Next  to unlink
    prev = cur
}
return dummy.Next   // NOT head
```

`Next: head` wraps the existing list. Use when the head might be removed or displaced.

### Mode 2 — Building a new list

```go
dummy := &ListNode{}
tail := dummy
for /* more input */ {
    tail.Next = &ListNode{Val: v}
    tail = tail.Next
}
return dummy.Next
```

`&ListNode{}` with a nil `Next` seeds a tail pointer. Solves the "first append is special because there is nothing to attach to" problem, which is the same problem wearing a different hat.

## Classification

| Problem                     | Dummy? | Mode | Why                                          |
| --------------------------- | :----: | ---- | -------------------------------------------- |
| Remove Nth Node From End    |   ✅    | 1    | The head itself may be the target            |
| Remove Linked List Elements |   ✅    | 1    | The head may match the value                 |
| Merge Two Sorted Lists      |   ✅    | 2    | Unknown which list's head wins               |
| Add Two Numbers             |   ✅    | 2    | Output built from nothing                    |
| Partition List              |   ✅    | 2    | Two lists built, then spliced                |
| Reverse Linked List         |   ❌    | —    | `prev` starts `nil` and *is* the accumulator |
| Linked List Cycle           |   ❌    | —    | Returns a bool, mutates nothing              |
| Middle of the Linked List   |   ❌    | —    | Read-only traversal                          |

Note that **Merge Two Sorted Lists deletes nothing** and still uses a dummy. This is the diagnostic case for whether your mental model is correct.

## Anti-model: it is not about memory leaks

> [!warning] Common wrong model
> "Dummy prevents losing the head, which would leak the list."

This is false and will mislead you:

1. **Go is garbage collected.** Dropping the last reference to a removed node is the *desired* outcome, not a leak.
2. **`head = head.Next` leaks nothing.** It is correct, GC-safe code. The reason to avoid it is that it is a *second branch*, not that it is unsafe.
3. **Merge Two Sorted Lists** removes zero nodes and still needs a dummy — impossible under the leak model.

The bug the dummy prevents is a **nil-pointer / wrong-return-value** bug, from branch proliferation.

### Where memory *does* enter (unrelated)

If you detach a node and then *retain* a reference to it, its `Next` pointer keeps the entire remainder of the list reachable. Defensive `cur.Next = nil` after unlinking addresses this. Orthogonal to the dummy pattern.

## Failure modes

- **Returning `head` instead of `dummy.Next`.** If the original head was removed, `head` now points into the middle of the list, or at a detached node.
  → **Habit:** the moment you write `dummy := &ListNode{Next: head}`, immediately write `return dummy.Next` at the bottom, *then* fill in the middle.
- **Forgetting `prev := dummy`.** Starting `prev` at `head` reintroduces the special case you just paid a node to eliminate.
- **Using `Next: head` in Mode 2.** You would prepend the input list to your output.

## Alternative: pointer-to-pointer

C solutions often use `ListNode **pp = &head` to get the same uniformity with zero allocation. Go supports this:

```go
pp := &head
for *pp != nil {
    if shouldRemove(*pp) {
        *pp = (*pp).Next
    } else {
        pp = &(*pp).Next
    }
}
return head
```

Correct, allocation-free, and harder to read under interview pressure. Know it exists. Reach for the dummy — one heap allocation is not the bottleneck, and clarity is scored.

## Cost / benefit

- **Cost:** one node.
- **Benefit:** `prev.Next = cur.Next` is unconditionally valid. An entire category of edge-case bug stops existing.

---

## Review Log

| Date | Recall | Notes |
|---|---|---|
| 2026-07-10 | — | Created |