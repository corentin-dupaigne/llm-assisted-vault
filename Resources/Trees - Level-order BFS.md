---
tags: [algo, trees, roadmap/week-1]
domain: leetcode
date: 2026-11-27
para: Resources
project: null
---
# Trees - Level-order BFS

## Theory

BFS (breadth-first search) visits the tree **level by level** using a **queue** (FIFO): take a node from the front, push its children to the back. Nodes come out in order of depth.

The trick that makes BFS "level by level": **at the start of each round, the queue holds exactly one full level**. Save its size, then process exactly that many nodes. The children added meanwhile belong to the next level.

It's the natural tool whenever a problem talks about **levels**, a **side view** or the **minimum distance from the root**. A DFS can sometimes do it by passing the depth as a parameter, but BFS expresses it directly.

### Complexity

- Time: **O(n)**
- Space: **O(w)**, where `w` is the maximum width. For a complete tree, the last level holds about n/2 nodes, so O(n).

## Go template

```go
func levelOrder(root *TreeNode) [][]int {
    var res [][]int
    if root == nil {
        return res
    }
    q := []*TreeNode{root}
    for len(q) > 0 {
        size := len(q) // freeze the level size BEFORE the inner loop
        level := make([]int, 0, size)
        for i := 0; i < size; i++ {
            n := q[0]
            q = q[1:]
            level = append(level, n.Val)
            if n.Left != nil {
                q = append(q, n.Left)
            }
            if n.Right != nil {
                q = append(q, n.Right)
            }
        }
        res = append(res, level)
    }
    return res
}
```

In Go, a slice works as a queue: `q[0]` to read the front, `q = q[1:]` to pop it, `append` to push to the back.

## Recognizing the pattern

- "level by level", "level order", "zigzag"
- "what you see from the right" → the **last** node of each level
- "minimum depth" → the first level where you find a leaf

> [!question]- Why store `size := len(q)` before the inner loop?
> Because `len(q)` grows during the loop as children are added. Without a frozen size, you would mix the current level with the next one.

> [!question]- How do you get the right side view with this template?
> For each level, keep only the node processed when `i == size-1`.

> [!question]- For minimum depth, why is BFS better than DFS?
> BFS stops at the first leaf it meets, which is necessarily the shallowest. DFS has to explore the whole tree to be sure.

## Resources

- Tech Interview Handbook, [Tree cheatsheet](https://www.techinterviewhandbook.org/algorithms/tree/): section **Techniques → Traversing by level** only (~3 min)

## Problems

1. [Binary Tree Level Order Traversal](https://leetcode.com/problems/binary-tree-level-order-traversal/) (medium)
1. [Binary Tree Right Side View](https://leetcode.com/problems/binary-tree-right-side-view/) (medium)
1. [Minimum Depth of Binary Tree](https://leetcode.com/problems/minimum-depth-of-binary-tree/) (easy)
1. [Binary Tree Zigzag Level Order Traversal](https://leetcode.com/problems/binary-tree-zigzag-level-order-traversal/) (medium)

## My notes

**The hint that should have pointed me to the solution:**

**My mistakes:**

**What I'm keeping:**

## Links

- [[Binary Trees - The Theory You Need]]
- [[Trees - BST and validation]]
- [[Trees - Build a tree from its traversals]]
- [[Coding Interview Method]]
