---
domain: leetcode
tags: [leetcode, neetcode-150, linked-list, two-pointers, golang]
date: 2026-07-02
para: Projects
project: neetcode-150
---
> [!abstract] One-liner
> Two pointers through the same list — `slow` moves 1, `fast` moves 2. If the list has a cycle they collide; if it doesn't, `fast` reaches `nil`. O(n) time, **O(1) space**.

## The problem it solves

Detect a cycle in a singly linked list (LC 141). A cycle exists when some node's `next` points back to an earlier node instead of `nil`. You only get `head` — not the cycle's start index, not the length.

## Why a singly linked list has only two shapes

One `next` per node → the structure **can't branch**. So every list is either:

- **No cycle** — a straight line ending in `nil`
- **Cycle** — a "ρ" (rho) shape: a straight tail leading into **exactly one** loop

There can never be two separate loops (a node would need two `next` pointers). This "only one loop" fact is load-bearing for the coverage argument below.

## The code (Go)

```go
func hasCycle(head *ListNode) bool {
	slow, fast := head, head

	for fast != nil && fast.Next != nil {
		slow = slow.Next        // 1 step
		fast = fast.Next.Next   // 2 steps
		if slow == fast {       // same NODE (address), not same value
			return true
		}
	}

	return false
}
```

### Line-by-line

- `slow == fast` compares **pointers = memory addresses**, not `.Val`. True only when both sit on the *same physical node*. This is why duplicate values (allowed: up to 1000 nodes, vals only −1000..1000) can't fool it.
- Guard `fast != nil && fast.Next != nil`: Go `&&` short-circuits left→right. First check protects the second from a nil dereference before reading `fast.Next.Next`. In a no-cycle list, this is how the loop exits → `return false`.
- Check happens **after** both move: move slow, move fast, then compare.

## Why it's guaranteed to work

Two separate guarantees. Keep them distinct — I kept conflating them.

### 1. Coverage — both pointers necessarily end up in the same loop

Not "the collision" — this is the prior question of *why they're even in the same place to collide*.

- **Only one loop exists** (see shape argument). So "same loop" is free — there's only one to be in.
- **`slow` can't skip the entrance.** It moves 1 node at a time from `head`, so it *must* step onto the loop's entrance node wherever it is. Can't leap over it.
- **A loop has no exit.** Every node inside points to another node inside. Once `fast` gets in (arrives first, being faster), it's trapped circling. Same for `slow` once it arrives.
- ⇒ For **any** cycle — any length, starting anywhere — both pointers get trapped in the one loop. This is the "all possibilities" coverage, and it comes from geometry, not from inspecting each node.

### 2. Collision — once both are looping, they must meet

Being trapped together isn't enough on its own (two runners could stay exactly opposite forever). The **speed difference** forces it:

- Define **gap** = how many steps `fast` is behind `slow`, going forward around the loop.
- Each turn: slow +1, fast +2 ⇒ gap closes by exactly `2 − 1 = 1`.
- Gap counts down `... → 3 → 2 → 1 → 0`. **0 = same node = collision.**

> [!warning] The "fast leaps over slow" fear — killed
> Gap = 1: fast at `p`, slow at `p+1`. Fast hops 2 (`p → p+2`), slow hops 1 (`p+1 → p+2`). Both land on `p+2`. Fast physically jumps *over* `p+1`, but slow *left* `p+1` that same turn. They meet at the destination, never in passing. Gap was 1 → subtract 1 → 0.

## The math underneath

"A gap decreasing by 1 must hit 0" is a real theorem:

- A strictly decreasing sequence of **non-negative integers** is finite → must reach its minimum (well-ordering principle). Step of exactly 1 ⇒ bottoms out *at* 0.
- **The step size of 1 is essential.** If the gap decreased by 2: `5 → 3 → 1 → −1` — skips 0, no guarantee. This is *why* speeds 1 and 2 are canonical: relative speed `2 − 1 = 1`.
- Rigorous form: gap lives in integers **mod L** (loop length L). Subtracting 1 each step cycles through every residue `0..L−1`, so 0 is unavoidable within ≤ L steps.

> [!quote] Interview soundbite
> "Speeds 1 and 2 give a relative speed of 1, so the gap decrements by 1 and can't skip the meeting point — collision guaranteed within L steps."

## Complexity

| Approach | Time | Space | Notes |
| ------------------------ | ---- | -------- | -------------------------------------------------------------------------- |
| Hashset of visited nodes | O(n) | O(n) | Correct, obvious first answer. Key on node **pointer**, not value. |
| **Floyd's (this)** | O(n) | **O(1)** | Time-optimal AND space-optimal. The answer when asked "can you do better?" |

Both are time-optimal (must look at each node once). The "can you do better?" always points at **space** → two pointers.

## Links

- [[Merge two linked lists]]
- [[valid-palindrome]]
- [[two-sum-ii-input-array-is-sorted]]
- [[three-sum]]
- [[container-with-most-water]]
