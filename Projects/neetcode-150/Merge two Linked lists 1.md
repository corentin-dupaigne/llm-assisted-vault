---
difficulty: easy
neetcode_section: "Linked List"
struggled: false
project: neetcode-150
date_solved: 2026-07-07
tags: [leetcode, neetcode-150, linked-list]
---
## Initial Intuition

<!-- Before coding: pattern recognized? Approach envisioned? Edge cases? -->


## My Solution

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */

func mergeTwoLists(list1 *ListNode, list2 *ListNode) *ListNode {
	dummy := &ListNode{}
	curr := dummy
	for list1 != nil && list2 != nil {
		if list1.Val < list2.Val {
			curr.Next = list1
			lis1 = list1.Next
		} else {
			curr.Next = list2
			list2 = list2.Next
		}
		curr = curr.Next
	}
	
	if list1 != nil {
		curr.Next = list1
	}
	
	if list2 != nil {
		curr.Next = list2
	}
	
	return dummy.Next
}


// Time: O(n)
// Space: O(1)

```

### Optimal Solution

```go
// Time: O(?)
// Space: O(?)

```

## Delta

<!-- The key difference between your approach and the optimal one -->

## Review Log

- 2026-07-07 — first solve
