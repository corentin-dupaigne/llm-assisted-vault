---
tags: [algo, trees, bst, roadmap/week-1]
domain: leetcode
date: 2026-11-27
para: Resources
project: null
---
# Trees - BST and validation

## Theory

A **binary search tree** (BST) follows a rule on **every** node, not just its direct children: the whole left subtree is strictly smaller than the node, and the whole right subtree is strictly larger.

Two consequences to know by heart:

1. **An inorder traversal gives the values sorted.** It's the tool for "k-th smallest", "validate a BST" or "two swapped nodes".
1. **You can discard half the tree at each node**, like a binary search. Search, insertion and LCA run in **O(h)** instead of O(n).

### The validation trap

Checking only `left.Val < n.Val < right.Val` is not enough:

```
    5
   / \
  4   6
     / \
    3   7
```

Each node is fine compared to its children, but 3 sits in the right subtree of 5 while being smaller than 5. You need to **propagate bounds**: each node must stay inside a range `(lo, hi)` inherited from its ancestors.

## Go template

```go
// Validation with bounds: the info comes from ancestors, so it goes in as a parameter
func isValidBST(root *TreeNode) bool {
    var valid func(n *TreeNode, lo, hi int) bool
    valid = func(n *TreeNode, lo, hi int) bool {
        if n == nil {
            return true
        }
        if n.Val <= lo || n.Val >= hi {
            return false
        }
        return valid(n.Left, lo, n.Val) && valid(n.Right, n.Val, hi)
    }
    return valid(root, math.MinInt64, math.MaxInt64)
}

// Iterative inorder: stop at the k-th element without visiting everything
func kthSmallest(root *TreeNode, k int) int {
    var stack []*TreeNode
    cur := root
    for cur != nil || len(stack) > 0 {
        for cur != nil { // go all the way left
            stack = append(stack, cur)
            cur = cur.Left
        }
        cur = stack[len(stack)-1]
        stack = stack[:len(stack)-1]
        k--
        if k == 0 {
            return cur.Val
        }
        cur = cur.Right
    }
    return -1
}
```

## Recognizing the pattern

- "BST" in the problem → think **sorted inorder** or **discard half**
- "k-th smallest / largest" → inorder
- "validate" → bounds passed down

> [!question]- Why use `math.MinInt64` and `math.MaxInt64` as bounds instead of the problem's min and max values?
> Because node values can be exactly the min or max of an `int32`. With bounds strictly outside that range, no valid value is rejected by mistake.

> [!question]- What other method can validate a BST?
> Do an inorder traversal and check that each value is strictly greater than the previous one.

> [!question]- What is the complexity of `kthSmallest`?
> O(h + k) time: one walk down the left side, then k nodes visited. O(h) space for the stack.

## Resources

- Tech Interview Handbook, [Tree cheatsheet](https://www.techinterviewhandbook.org/algorithms/tree/): sections **Binary search tree (BST)** and **Time complexity** only (~5 min)

## Problems

1. [Validate Binary Search Tree](https://leetcode.com/problems/validate-binary-search-tree/) (medium)
1. [Kth Smallest Element in a BST](https://leetcode.com/problems/kth-smallest-element-in-a-bst/) (medium)
1. [Search in a Binary Search Tree](https://leetcode.com/problems/search-in-a-binary-search-tree/) (easy, warm-up)

## My notes

**The hint that should have pointed me to the solution:**

**My mistakes:**

**What I'm keeping:**

## Links

- [[Binary Trees - The Theory You Need]]
- [[Coding Interview Method]]
