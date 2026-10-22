
Almost every linked-list exercise relies on **about ten techniques**. The goal is to recognise which one applies, then avoid the pointer-manipulation traps.

---

## 1. The basics

```go
type ListNode struct {
    Val  int
    Next *ListNode
}
```

- A list is a **chain of nodes**. You can only access the first one (`head`), and the last one points to `nil`.
- **No direct access** to the i-th element: everything is O(n) because you have to walk the list.
- **The strength**: inserting or deleting a node whose **predecessor** you know costs O(1), without shifting any elements.

**Basic traversal**:
```go
for curr := head; curr != nil; curr = curr.Next {
    // process curr
}
```

> **Golden rule**: before changing `curr.Next`, save what comes after it (`next := curr.Next`). Otherwise you lose the rest of the list for good.

---

## 2. The dummy (sentinel) node

**The problem**: many operations treat the head differently, for example deleting the first node or building a new list that starts out empty. You end up writing lots of `if head == nil` checks.

**The fix**: create a fake node placed **before** the head.

```go
dummy := &ListNode{Next: head}
// ... work starting from dummy ...
return dummy.Next
```

**Why it works**: every real node now has a predecessor, including the head, so a single piece of logic covers every case.

> **Trigger**: whenever the head can change (deletion, insertion at the front, building a new list), use a dummy and return `dummy.Next`.

---

## 3. Reversing a list in place

This is **the** core technique. Many harder exercises reuse it.

**Iterative, with three pointers**:
```go
var prev *ListNode
curr := head
for curr != nil {
    next := curr.Next // 1. save the rest
    curr.Next = prev  // 2. flip the arrow
    prev = curr       // 3. move prev forward
    curr = next       // 4. move curr forward
}
return prev // new head
```

**The invariant**: on every iteration, `prev` is the head of the part **already reversed**, and `curr` is the head of the part **not yet processed**. When `curr == nil`, everything is reversed.

**Recursive**: reverse the rest of the list, then make the next node point back to the current one (`head.Next.Next = head; head.Next = nil`). It's elegant, but it costs O(n) stack memory.

**Variant: reversing a section, or groups of k nodes**
1. Find the node **just before** the section (`groupPrev`) and the node **just after** it.
2. Reverse the section with the same loop, but initialise `prev` to the node **just after**. The last reversed node then reconnects to the rest of the list automatically.
3. Reconnect `groupPrev.Next` to the section's new head.
4. The section's old head is now its tail, and becomes the `groupPrev` of the next group.
5. For groups of k: first check that at least k nodes remain; otherwise, leave the end untouched.

> Always draw it. In partial reversals, almost every bug comes from reconnecting one of the two ends wrongly.

---

## 4. Two pointers at different speeds (slow and fast)

`slow` moves one step at a time, `fast` moves two.

### 4.1 Finding the middle
```go
slow, fast := head, head
for fast != nil && fast.Next != nil {
    slow = slow.Next
    fast = fast.Next.Next
}
// slow is at the middle
```
- For an **odd length**, `slow` lands exactly on the middle.
- For an **even length**, `slow` lands on the **second** middle. To get the **first** middle (useful for splitting the list in two), start with `fast := head.Next`.

**Why**: by the time fast has covered the whole list, slow has covered half of it.

### 4.2 Detecting a cycle
If the list contains a cycle, `fast` eventually catches up with `slow`: once both are inside the cycle, the gap between them shrinks by 1 on every iteration. If there's no cycle, `fast` reaches `nil`.

### 4.3 Finding where the cycle starts
After they meet, move one pointer back to the head, then advance **both one step at a time**. They meet at the start of the cycle.

**Why**: let a be the distance from the head to the cycle's entry, b the distance from the entry to the meeting point, and c the cycle's length. Slow has travelled a + b, fast twice that: 2(a + b) = a + b + k·c. So **a = k·c − b**: starting from the meeting point, a steps bring you exactly back to the entry.

### 4.4 Cycle length
From the meeting point, advance one pointer until it returns to the same node, counting the steps.

---

## 5. Two pointers with a fixed gap

**The problem**: reach the k-th node **from the end** in a single pass, without knowing the length.

**The technique**:
1. Advance `fast` by k steps.
2. Then advance `fast` and `slow` together until `fast` reaches the end.
3. The gap of k is preserved, so `slow` ends up k nodes from the end.

**To delete that node**, you need to stop on its **predecessor**. Start both pointers from a **dummy** and stop when `fast.Next == nil`, then delete with `slow.Next = slow.Next.Next`. The dummy handles the case where the node to delete is the head.

> The two-pass alternative (compute the length, then advance length − k) is also O(n) and usually accepted. A single pass is a bonus.

---

## 6. Merging sorted lists

### 6.1 Two lists
```go
dummy := &ListNode{}
tail := dummy
for l1 != nil && l2 != nil {
    if l1.Val <= l2.Val {
        tail.Next, l1 = l1, l1.Next
    } else {
        tail.Next, l2 = l2, l2.Next
    }
    tail = tail.Next
}
if l1 != nil { tail.Next = l1 } else { tail.Next = l2 }
return dummy.Next
```
**The invariant**: `dummy.Next … tail` holds the smallest elements merged so far, in order. At the end, attach whatever is left of the non-empty list directly, without copying.

### 6.2 k lists
| Method | Complexity (N nodes in total) |
|---|---|
| Merge the lists one after another | O(N·k), too slow |
| **Min-heap** holding the head of each list | **O(N log k)** |
| **Divide and conquer**: merge lists in pairs, round by round | **O(N log k)**, with no extra data structure |

**Why divide and conquer is faster**: each round halves the number of lists, and each node is moved only once per round. There are log k rounds.

> In Go, a heap requires `container/heap` and implementing an interface. Divide and conquer is often simpler to write in an interview.

---

## 7. Split, transform, recombine

Many "hard" exercises are just a **combination** of the techniques above:
1. **Find the middle** (§4.1) and **cut** the list in two (`middle.Next = nil`).
2. **Reverse** the second half (§3).
3. **Walk both halves in parallel** to **compare** them (symmetry) or **interleave** them (alternating one node from each).

> **Watch out for the cut**: if you forget `middle.Next = nil`, the first half still points into the second, and you create a cycle or an infinite loop.

---

## 8. Arithmetic on numbers stored digit by digit

When a list represents a number (one digit per node):
- **Digits in reverse order** (units first): add as you walk, just like on paper, with a **carry**.
- **Digits in normal order**: reverse the lists first, or use a stack.

```go
for l1 != nil || l2 != nil || carry != 0 {
    sum := carry
    if l1 != nil { sum += l1.Val; l1 = l1.Next }
    if l2 != nil { sum += l2.Val; l2 = l2.Next }
    carry = sum / 10
    tail.Next = &ListNode{Val: sum % 10}
    tail = tail.Next
}
```
> **The classic trap**: forgetting the **final carry**. That's why the loop condition includes `carry != 0`.

---

## 9. Deep-copying a list with extra pointers

**The problem**: on top of `Next`, each node has a pointer to **any other node** (or `nil`). The copy must point to the **new** nodes, not the old ones.

**Method 1, the simplest (O(n) memory)**: a mapping table.
1. First pass: create every copy and record `old → new` in a `map`.
2. Second pass: wire the copies' pointers using the table (`new.X = table[old.X]`).

> Set `table[nil] = nil` up front, or handle `nil` explicitly, to avoid a special case.

**Method 2, O(1) memory**: interleave the copies.
1. Insert each copy right after its original: A → A' → B → B' → …
2. Wire the extra pointers: the copy of "whatever A points to" sits right after it, so `A'.X = A.X.Next`.
3. Separate the two lists and restore the original one.

---

## 10. Doubly linked list + hash map

**The need**: a structure where you can, in **O(1)**, look up an element by key, move it to the front, and remove the oldest one. This is the typical shape of a **cache** with eviction.

**The combination**:
- a **`map[key]*Node`** to find a node in O(1);
- a **doubly linked list** (`Prev` and `Next`) to keep the usage order. With the predecessor directly available, you can unlink a node from anywhere in O(1).

```go
type Node struct {
    Key, Val   int
    Prev, Next *Node
}
```

**The details that matter**:
- **Two sentinels**, `head` and `tail`, linked to each other at the start. You then never hit a `nil` case when inserting or removing.
- **Two primitive operations**, written once:
  - `remove(node)`: link `node.Prev` and `node.Next` to each other;
  - `insertFront(node)`: insert right after `head`.
- "Using" an element = `remove` then `insertFront`.
- **Evicting** = removing `tail.Prev`, the oldest one.
- **Store the key in the node**: when evicting, you also need to delete the `map` entry, and only the node knows its key.

---

## 11. "Implicit" lists

A linked list doesn't need actual nodes. Any rule of the form **"from x, the next element is f(x)"** forms one:
- an array where a cell's **value** is the **index** of the next cell (`i → nums[i]`);
- a sequence of numbers where each term is computed from the previous one.

All the cycle techniques (§4.2 to 4.4) apply directly, with "advance" meaning `x = f(x)`.

> **Trigger**: bounded values that can serve as indices, an O(1) memory constraint, or a sequence where the question is whether it "eventually loops". Think "value = pointer" and cycle detection.

---

## 12. Traps to avoid

| Trap | How to avoid it |
|---|---|
| Losing the rest of the list | Save `next := curr.Next` before changing `curr.Next` |
| Dereferencing `nil` (a panic in Go) | Check `fast != nil && fast.Next != nil`, **in that order** |
| Creating a cycle by accident | Cut with `x.Next = nil` after splitting a list |
| Special case for the head | Use a dummy |
| Wrong middle for an even length | Choose deliberately between `fast := head` and `fast := head.Next` |
| Forgetting the final carry or leftover nodes | Put those cases in the loop condition, or attach the remainder at the end |
| Wrong reconnection in partial reversals | Draw the pointers **before** coding |

**Cases to always test**: empty list, one node, two nodes, even and odd lengths, operations that touch the head or the tail.

---

## 13. Recognition table

| If the problem involves… | Think of… |
|---|---|
| The head can change, building a new list | Dummy (§2) |
| Reversing the order, fully or partly | Three-pointer reversal (§3) |
| Middle, halves, symmetry | Slow and fast (§4.1), then reversal (§3) and parallel walk (§7) |
| A possible loop, finding where it starts | Floyd (§4.2 to 4.3) |
| The k-th from the end, in one pass | Fixed gap (§5) |
| Combining sorted lists | Merge (§6), with a heap or divide and conquer for k lists |
| Numbers stored digit by digit | Addition with carry (§8) |
| Copying a structure with arbitrary pointers | Old → new table, or interleaved copies (§9) |
| Lookup by key + usage order, all in O(1) | `map` + doubly linked list with sentinels (§10) |
| An array of index-like values, O(1) memory, a sequence that loops | Implicit list + Floyd (§11) |

---

## 14. Complexities to know

- Most techniques run in **O(n) time and O(1) memory**, which is the level expected in an interview.
- Exceptions: **O(n) memory** for the mapping table (§9, method 1) and for recursion (call stack); **O(N log k)** for merging k lists.

> **Method for every exercise**: (1) find the trigger in the table in §13, (2) draw 3 or 4 nodes on paper and walk through the technique by hand, (3) code it, (4) test the edge cases from §12.