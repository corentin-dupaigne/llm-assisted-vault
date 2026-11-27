---
tags: [algo, trees, roadmap/week-1]
domain: leetcode
date: 2026-11-27
para: Resources
project: null
---
# Trees - Lowest Common Ancestor

## Theory

The **lowest common ancestor** (LCA) of two nodes `p` and `q` is the deepest node that has both `p` and `q` in its subtree. A node can be its own ancestor: if `p` is above `q`, the answer is `p`.

There are two versions, and they are solved differently.

### On a BST: O(h), no recursion

The BST order tells you which way to go:

- `p` and `q` are both smaller than the node → the LCA is on the left
- both larger → on the right
- otherwise they split here (or one of them is the node) → this is the LCA

### On any binary tree: O(n), postorder DFS

No order to guide you. Each call answers "did you find `p` or `q` in your subtree?":

- if the node is `nil`, `p` or `q`, return it
- otherwise, ask both children
- if **both** return something, `p` and `q` are on either side: the current node is the LCA
- otherwise, pass up whichever one is not `nil`

## Go template

```go
// BST
func lowestCommonAncestorBST(root, p, q *TreeNode) *TreeNode {
    cur := root
    for cur != nil {
        if p.Val < cur.Val && q.Val < cur.Val {
            cur = cur.Left
        } else if p.Val > cur.Val && q.Val > cur.Val {
            cur = cur.Right
        } else {
            return cur
        }
    }
    return nil
}

// Any binary tree
func lowestCommonAncestor(root, p, q *TreeNode) *TreeNode {
    if root == nil || root == p || root == q {
        return root
    }
    l := lowestCommonAncestor(root.Left, p, q)
    r := lowestCommonAncestor(root.Right, p, q)
    if l != nil && r != nil {
        return root
    }
    if l != nil {
        return l
    }
    return r
}
```

## Recognizing the pattern

- "common ancestor", "where two nodes meet"
- "BST" in the problem → the iterative O(h) version

> [!question]- In the general version, why can we return `root` as soon as `root == p`, without checking whether `q` is below?
> If `q` is under `p`, then `p` is the LCA, so returning `p` is correct. If `q` is elsewhere, another branch of some ancestor will find it, and that ancestor will see two non-nil results.

> [!question]- Why doesn't the BST version need recursion?
> Because at each node you know which direction to take. There is only one path to follow, so a simple loop is enough, with O(1) space.

## Problems

1. [Lowest Common Ancestor of a Binary Search Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/) (medium)
1. [Lowest Common Ancestor of a Binary Tree](https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/) (medium, not in NeetCode 150 but a classic)

## My notes

**The hint that should have pointed me to the solution:**

**My mistakes:**

**What I'm keeping:**

## Links

- [[Binary Trees - The Theory You Need]]
- [[Trees - BST and validation]]
- [[Trees - Build a tree from its traversals]]
- [[Trees - Level-order BFS]]
