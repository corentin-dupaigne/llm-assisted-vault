---
tags: [algo, trees, roadmap/week-1]
---

# Trees - Recursive DFS

## Theory

Almost every tree problem comes down to one idea: **a function that solves the problem for a node, assuming it already works for both children**. You don't "follow" the recursion in your head: you trust the calls on `Left` and `Right`, and only ask how to combine their results.

Three questions, always in this order:
1. **Base case**: what does the function return for `nil`? (often `0`, `true` or `nil`)
2. **What I ask the children**: which value should each child send back up?
3. **How I combine**: with both answers and the node's value, what do I return to my parent?

### Two families of DFS

| Family | Idea | Examples |
|---|---|---|
| **The answer bubbles up** | the return value *is* the subtree's answer | max depth, balanced tree, same tree |
| **The answer is computed along the way** | the function returns info the parent needs (often a height) and updates a global variable at each node | diameter, max path sum |

The classic trap in the second family: **what I return to my parent is not the answer**. For the diameter, I return a height (one side only, because the parent can only extend one branch), but I update the answer with `left + right` (the path that goes through me).

### Traversal orders

- **Preorder** (node, left, right): handle the node before its children. Useful to copy or serialize a tree.
- **Inorder** (left, node, right): on a BST, gives the values **sorted**.
- **Postorder** (left, right, node): you need the children's results before handling the node. Most height problems work this way.

### Complexity

- Time: **O(n)**, each node is visited once.
- Space: **O(h)** for the call stack, where `h` is the height. Balanced tree: O(log n). Degenerate tree (one long branch): O(n).

## Go template

```go
// Family 1: the answer bubbles up
func maxDepth(root *TreeNode) int {
    if root == nil {
        return 0
    }
    return 1 + max(maxDepth(root.Left), maxDepth(root.Right))
}

// Family 2: return a height, keep the answer in a captured variable
func diameterOfBinaryTree(root *TreeNode) int {
    best := 0
    var height func(n *TreeNode) int
    height = func(n *TreeNode) int {
        if n == nil {
            return 0
        }
        l, r := height(n.Left), height(n.Right)
        best = max(best, l+r) // path going through n
        return 1 + max(l, r)  // what the parent can extend
    }
    height(root)
    return best
}
```

In Go, a recursive closure must be declared with `var height func(...)` **before** it is assigned, otherwise it can't call itself.

## Recognizing the pattern

- "depth", "height", "balanced", "same tree", "subtree" → family 1
- "longest path between two nodes", "max path sum" → family 2 (global variable)
- "count the nodes that…" based on their ancestors → pass info **down** as a parameter (for example the max seen since the root)

> [!question]- Why doesn't the diameter return `l + r` to the parent?
> Because the parent can only extend **one** branch. A path that goes down both left and right of `n` can't go any higher. So we return `1 + max(l, r)`, and `l + r` is only used to update the answer.

> [!question]- What is the space complexity on a degenerate tree?
> O(n): the call stack goes as deep as the height, and a tree shaped like a straight line has a height of n.

> [!question]- In "Count Good Nodes", why pass a value as a parameter instead of returning it?
> Because the useful info (the max since the root) comes from the **ancestors**, not the children. What comes from above goes in as a parameter; what comes from below comes back as the return value.

## Resources

- Tech Interview Handbook, [Tree cheatsheet](https://www.techinterviewhandbook.org/algorithms/tree/): sections **Corner cases** and **Techniques → Use recursion** only (~5 min)

## Problems

1. [Maximum Depth of Binary Tree](https://leetcode.com/problems/maximum-depth-of-binary-tree/) (easy)
2. [Invert Binary Tree](https://leetcode.com/problems/invert-binary-tree/) (easy)
3. [Same Tree](https://leetcode.com/problems/same-tree/) (easy)
4. [Balanced Binary Tree](https://leetcode.com/problems/balanced-binary-tree/) (easy)
5. [Diameter of Binary Tree](https://leetcode.com/problems/diameter-of-binary-tree/) (easy, family 2)
6. [Count Good Nodes in Binary Tree](https://leetcode.com/problems/count-good-nodes-in-binary-tree/) (medium, info passed down)
7. [Subtree of Another Tree](https://leetcode.com/problems/subtree-of-another-tree/) (easy)

## My notes

**The hint that should have pointed me to the solution:**

**My mistakes:**

**What I'm keeping:**
