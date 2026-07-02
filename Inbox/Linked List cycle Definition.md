---
difficulty: easy
neetcode_section: "Linked List"
struggled: false
project: neetcode-150
date_solved: 2026-07-02
tags: [leetcode, neetcode-150, linked-list]
---
## Initial Intuition

My initial intuition is that I can use an hashset where the key is a pointer to a LinkedList,  the hashset is used as a visited datastructure. I traverse the linkedlist and add each node to the hashset, then when I am on the last node I then check if next exists in the hashset. If it does, the linkedlist contain a cycle. But how to know if I am on the last node? I thought I could simply know I'm on the last node when curr.Next is nil but that won't work since if it a cycle there is a next. I guess I can simply check if the node exists in the hashset at everystep.


## My Solution

```go
/**
 * Definition for singly-linked list.
 * type ListNode struct {
 *     Val int
 *     Next *ListNode
 * }
 */

func hasCycle(head *ListNode) bool {
	visited := make(map[*ListNode]bool)

	if head == nil {
		return false
	}

	curr := head
	for curr.Next != nil {
		if visited[curr] {
			return true
		} else {
			visited[curr] = true
		}

		curr = curr.Next
	}

	return false
}


// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
// Time: O(?)
// Space: O(?)

```

## Delta

My solution is optimal in time complexity but not in space complexity. The optimal space complexity is with Floyd's Tortoise and Hare.

Example:

linked list: 
![[Pasted image 20260702170503.png]]

ptr1, ptr2 := head, head
step 1: ptr1 -> 2, ptr2 -> 3
step 2: ptr1 -> 3, ptr2 -> 2
step 3: ptr1 -> 4, ptr2 -> 4

## Review Log

- 2026-07-02 — first solve
