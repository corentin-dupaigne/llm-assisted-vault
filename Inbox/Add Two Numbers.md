---
difficulty: medium
neetcode_section: "Linked List"
struggled: true
project: neetcode-150
date_solved: 2026-07-14
tags: [leetcode, neetcode-150, linked-list]
---
## Initial Intuition

<!-- Before coding: pattern recognized? Approach envisioned? Edge cases? -->


## My Solution

```go
func addTwoNumbers(l1 *ListNode, l2 *ListNode) *ListNode {

	res1 := 0
	curr1 := l1
	offset := 1
	for curr1 != nil {
		res1 += curr1.Val * offset
		offset *= 10
		curr1 = curr1.Next
	}

	res2 := 0
	curr2 := l2
	offset = 1
	for curr2 != nil {
		res2 += curr2.Val * offset
		offset *= 10
		curr2 = curr2.Next
	}

	sum := res1 + res2

	temp := strconv.Itoa(sum)

	dummy := &ListNode{}
	curr := dummy
	for i := len(temp) - 1; i >= 0; i-- {
		curr.Next = &ListNode{Val: int(temp[i] - '0')}
		curr = curr.Next
	}

	return dummy.Next
}

// Time: O(?)
// Space: O(?)

```

### Optimal Solution

```go
// Time: O(?)
// Space: O(?)

```

## Delta

My solution would work on smaller linked list but on large one the computation produces an overflow.

## Review Log

- 2026-07-14 — first solve
