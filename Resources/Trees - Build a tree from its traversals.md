---
tags: [algo, trees, roadmap/week-1]
domain: leetcode
date: 2026-11-27
para: Resources
project: null
---
# Trees - Build a tree from its traversals

## Theory

Given the **preorder** and **inorder** traversals of a tree (all values distinct), you can rebuild the tree uniquely. You just need to see what each traversal gives you:

- **Preorder** (node, left, right): the **first** element is always the root of the current subtree.
- **Inorder** (left, node, right): once the root is known, everything **to its left** in the inorder belongs to the left subtree, and everything **to its right** to the right subtree.

The algorithm:

1. Take the next value from the preorder: it's the root.
1. Find it in the inorder, at index `m`.
1. Recursively build the left subtree from the inorder range `[l, m-1]`, then the right one from `[m+1, r]`.

Two optimizations take it from O(n²) to **O(n)**:

- a **map** from value to inorder index, to find `m` in O(1)
- a **shared pointer** into the preorder instead of slicing. It works because the preorder lists the whole left subtree before the right one, exactly the order in which we build them.

## Go template

```go
func buildTree(preorder []int, inorder []int) *TreeNode {
    idx := make(map[int]int, len(inorder))
    for i, v := range inorder {
        idx[v] = i
    }
    pre := 0
    var build func(l, r int) *TreeNode
    build = func(l, r int) *TreeNode {
        if l > r {
            return nil
        }
        v := preorder[pre]
        pre++
        n := &TreeNode{Val: v}
        m := idx[v]
        n.Left = build(l, m-1) // left first: same order as the preorder
        n.Right = build(m+1, r)
        return n
    }
    return build(0, len(inorder)-1)
}
```

## Recognizing the pattern

- "construct a tree from two traversals"
- more generally, **serialization**: turning a tree into a string and back. A preorder with `nil` markers (`"1,2,N,N,3,N,N"`) is enough on its own.

> [!question]- Why must the left subtree be built before the right one?
> Because the `pre` pointer moves through the preorder, which lists the whole left subtree before the right one. Swapping the calls would read the wrong values.

> [!question]- Why isn't the preorder alone enough, unless it has `nil` markers?
> Without markers, you can't tell where the left subtree ends. The inorder gives you that boundary. `nil` markers give it too, directly in the string.

> [!question]- What happens if the values aren't distinct?
> The value → index map becomes ambiguous, and the tree can no longer be rebuilt uniquely.

## Problems

1. [Construct Binary Tree from Preorder and Inorder Traversal](https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/) (medium)
1. [Serialize and Deserialize Binary Tree](https://leetcode.com/problems/serialize-and-deserialize-binary-tree/) (hard, but a classic)

## My notes

**The hint that should have pointed me to the solution:**

**My mistakes:**

**What I'm keeping:**

## Links

- [[Binary Trees - The Theory You Need]]
- [[Trees - BST and validation]]
