---
domain: leetcode
tags: [golang, neetcode-150, study-plan]
date: 2026-11-11
para: Resources
project: null
---
Almost every tree exercise is a **traversal** (depth-first or breadth-first) plus **one decision**: what information travels **down** the tree, and what travels back **up**. Recognising that is 80% of the work.

______________________________________________________________________

## 1. The basics

```go
type TreeNode struct {
    Val         int
    Left, Right *TreeNode
}
```

**Vocabulary**

- **Root**: the top node. **Leaf**: a node with no children.
- **Depth** of a node: the number of edges from the root to that node (top-down).
- **Height** of a node: the number of edges on the longest path down to a leaf (bottom-up). Some problems count **nodes** instead of edges, so check the definition.
- **Balanced**: for every node, the heights of the left and right subtrees differ by at most 1.
- **Binary search tree (BST)**: for every node, **all** values on the left are smaller and **all** values on the right are larger (§9).

**Complexity reflex**: visiting every node is O(n) time. Memory is **O(h)** for recursion, with h the height: O(log n) if the tree is balanced, **O(n)** if it's degenerate (a "tree" shaped like a linked list).

______________________________________________________________________

## 2. The recursive mindset

Most tree solutions are recursive. Ask yourself three questions **before** coding:

1. **What does my function return for one node?** (Its height? Whether its subtree is valid? Its subtree's sum?)
1. **What is the base case?** Almost always `node == nil`, and what it should return (0? true? nothing?).
1. **How do I combine the children's results** into the current node's result?

> **Trust the recursion**: assume the call on `node.Left` already returns the correct answer for the left subtree. Your job is only to combine it with the right subtree's answer and the current node.

```go
func height(node *TreeNode) int {
    if node == nil {
        return 0
    }
    return 1 + max(height(node.Left), height(node.Right))
}
```

______________________________________________________________________

## 3. Depth-first traversals (DFS)

Three orders, depending on **when** you process the node relative to its children:

| Order | Sequence | Typical use |
|---|---|---|
| **Preorder** | node → left → right | Copying or serialising a tree, passing information **down** |
| **Inorder** | left → node → right | **BST: visits values in sorted order** |
| **Postorder** | left → right → node | Computing something from the children's results, information going **up** |

**Iterative version (explicit stack)**: useful if recursion depth is a concern, or if you need to stop early. Inorder is the one worth knowing:

```go
stack := []*TreeNode{}
curr := root
for curr != nil || len(stack) > 0 {
    for curr != nil {               // go as far left as possible
        stack = append(stack, curr)
        curr = curr.Left
    }
    curr = stack[len(stack)-1]      // pop
    stack = stack[:len(stack)-1]
    // process curr: values come out in sorted order in a BST
    curr = curr.Right
}
```

______________________________________________________________________

## 4. Breadth-first traversal (BFS, level by level)

Use a **queue**. The key trick: **snapshot the queue's size** at the start of each level, so you process exactly one level per iteration.

```go
queue := []*TreeNode{root}
for len(queue) > 0 {
    size := len(queue)              // number of nodes on this level
    for i := 0; i < size; i++ {
        node := queue[0]
        queue = queue[1:]
        // process node (i == size-1 is the last node of the level)
        if node.Left != nil { queue = append(queue, node.Left) }
        if node.Right != nil { queue = append(queue, node.Right) }
    }
    // end of a level
}
```

> Don't forget `if root == nil` before starting, otherwise you push a `nil` into the queue.

**When to use BFS rather than DFS**: when the problem talks about **levels** (values per level, the first or last node of each level, what you "see" from one side), or about the **minimum depth** (BFS stops at the first leaf it meets).

______________________________________________________________________

## 5. Information going up (postorder)

The node needs its **children's results** to compute its own. This covers heights, sizes, sums, and "is this subtree valid?" checks.

### 5.1 The "returned value ≠ global answer" pattern

Very common, and the source of many mistakes. The value a node **returns to its parent** isn't always the value that **answers the problem**.

**Example of reasoning**: for the longest path between any two nodes, a path can go **through** a node (left branch + node + right branch), but the parent can only extend **one** branch.

- **Returned** to the parent: the length of the **best single branch** (`1 + max(left, right)`).
- **Global answer**, updated at each node: the path **through** the node (`left + right`).

```go
best := 0
var dfs func(*TreeNode) int
dfs = func(node *TreeNode) int {
    if node == nil {
        return 0
    }
    l, r := dfs(node.Left), dfs(node.Right)
    best = max(best, l+r)   // path that bends at this node
    return 1 + max(l, r)    // single branch for the parent
}
dfs(root)
```

**Value-sum variant**: if values can be **negative**, a branch can make the path worse. Ignore it by clamping its contribution to 0: `l := max(dfs(node.Left), 0)`. Initialise the global answer to the **root's value** (or `math.MinInt`), not to 0, since the answer itself can be negative.

### 5.2 Early exit with a sentinel value

To check a property like balance while computing heights, return a **special value** (for example -1) meaning "already invalid", and propagate it immediately. This avoids recomputing heights, giving O(n) instead of O(n²).

______________________________________________________________________

## 6. Information going down (preorder)

The node needs information about its **ancestors**. Pass it as a **parameter**.

Examples of state to pass down:

- the **maximum (or minimum) seen so far** on the path from the root, to decide whether the current node "beats" all its ancestors;
- the current **depth**;
- the **min/max bounds** a value must respect (BST validation, §9.3);
- the **current path or running sum**.

```go
var dfs func(node *TreeNode, maxSoFar int) int
dfs = func(node *TreeNode, maxSoFar int) int {
    if node == nil {
        return 0
    }
    count := 0
    if node.Val >= maxSoFar {
        count = 1
    }
    maxSoFar = max(maxSoFar, node.Val)
    return count + dfs(node.Left, maxSoFar) + dfs(node.Right, maxSoFar)
}
```

> **To decide between §5 and §6**: if the answer for a node depends on what's **below** it, go postorder (up). If it depends on what's **above** it, pass a parameter (down). Some problems need both.

______________________________________________________________________

## 7. Walking two trees in parallel

To **compare** two trees, recurse on both **at the same time**:

```go
func same(a, b *TreeNode) bool {
    if a == nil || b == nil {
        return a == b           // true only if both are nil
    }
    return a.Val == b.Val && same(a.Left, b.Left) && same(a.Right, b.Right)
}
```

- **Mirror/symmetry**: same idea, but compare `a.Left` with `b.Right` and `a.Right` with `b.Left`.
- **Is tree B contained in tree A**: try the comparison from **every** node of A. That's O(n·m), which is generally accepted. A faster alternative is to serialise both trees with null markers and search for one string inside the other.

> The `nil` checks come **first**: one nil and the other not means false.

______________________________________________________________________

## 8. Modifying a tree

- **Mirroring** a tree: swap `Left` and `Right` at every node (pre- or postorder, both work).
- **Building** a node: `&TreeNode{Val: v}`, then attach its children.
- Return the subtree's (possibly new) root from the recursive function, and reassign it: `node.Left = f(node.Left)`. This pattern makes insertion and deletion simple (§9).

______________________________________________________________________

## 9. Binary search trees (BST)

### 9.1 The key property

**An inorder traversal of a BST yields the values in sorted order.** Many BST problems become simple sorted-list problems thanks to this.

### 9.2 Search and insertion, O(h)

At each node, go **left** if the value is smaller, **right** if larger: you discard a whole subtree at each step.

```go
func insert(node *TreeNode, v int) *TreeNode {
    if node == nil {
        return &TreeNode{Val: v}
    }
    if v < node.Val {
        node.Left = insert(node.Left, v)
    } else {
        node.Right = insert(node.Right, v)
    }
    return node
}
```

### 9.3 Validating a BST: the classic trap

Comparing each node only to its **parent** is **wrong**: a node deep in the left subtree must also be smaller than the root. Pass **bounds** down instead (§6):

- going left: the upper bound becomes the current value;
- going right: the lower bound becomes the current value.

Start with no bounds (use `math.MinInt`/`math.MaxInt`, or pointers that can be `nil`). **Alternative**: an inorder traversal must be **strictly increasing**; compare each value with the previous one.

### 9.4 The k-th smallest value

Inorder traversal with a **counter**, stopping as soon as you reach k. The iterative version (§3) makes it easy to stop early.

### 9.5 Deleting a node: three cases

1. **Leaf**: just remove it (return `nil`).
1. **One child**: replace the node with that child.
1. **Two children**: replace its value with that of its **inorder successor** (the smallest value in the right subtree: go right once, then all the way left), then delete that successor from the right subtree.

### 9.6 Lowest common ancestor

- **In a BST**: from the root, if both values are smaller, go left; if both are larger, go right; otherwise, the current node is the **split point**, and that's the answer. O(h).
- **In a general binary tree** (no ordering): postorder. A node returns itself if it's one of the targets; if it receives a non-nil result from **both** children, it's the answer. Otherwise, it passes up the non-nil result.

______________________________________________________________________

## 10. Rebuilding a tree from two traversals

With **preorder + inorder** (and distinct values):

- the **first preorder value** is the root;
- its **position in inorder** splits the values: everything to the left belongs to the left subtree, everything to the right to the right subtree;
- recurse on each side, consuming the preorder from left to right.

**For O(n)**: store each value's inorder index in a `map` (instead of searching each time), and keep a **shared index** into the preorder that moves forward on each node created. Build the left subtree **before** the right one, because that's the preorder sequence.

______________________________________________________________________

## 11. Serialising and deserialising

**The idea**: a preorder traversal **with a marker for null children** (for example `"N"`) describes a tree completely and unambiguously.

- **Serialisation**: preorder, write the value or `N`, separated by commas.
- **Deserialisation**: read the values in the **same order**, with a shared index. On `N`, return `nil`; otherwise, create the node, then build its left subtree, then its right subtree.

A level-by-level (BFS) version with markers also works.

> In Go: `strings.Builder` or a slice joined with `strings.Join` for writing, `strings.Split` and `strconv.Atoi` for reading.

______________________________________________________________________

## 12. Go specifics

- **Closures** for a shared "global" answer: declare `var dfs func(...)` first, then assign it, so it can call itself.
- **Queue**: a slice with `queue[0]` and `queue = queue[1:]`, which is fine in an interview.
- **Bounds**: `math.MinInt`, `math.MaxInt` (the `math` package).
- `max` and `min` are built in since Go 1.21. On an older version, write them yourself.

______________________________________________________________________

## 13. Traps to avoid

| Trap | How to avoid it |
|---|---|
| Forgetting the `nil` base case | Write it first in every recursive function |
| Calling BFS on a `nil` root | Return early before creating the queue |
| Mixing up the returned value and the global answer | Write both explicitly (§5.1) |
| Global answer initialised to 0 when values can be negative | Initialise with the root's value or `math.MinInt` |
| Validating a BST against the parent only | Pass bounds down (§9.3) |
| Duplicate values in a BST | Check what the problem says: strict or not |
| Recomputing heights at every node, O(n²) | Compute once in postorder, with a sentinel value (§5.2) |
| Confusing height and depth, edges and nodes | Reread the problem's definition |
| Recursion too deep on a degenerate tree | Mention it, or switch to the iterative version |

**Cases to always test**: empty tree, a single node, a degenerate tree (all on one side), negative values, duplicates.

______________________________________________________________________

## 14. Recognition table

| If the problem involves… | Think of… |
|---|---|
| Something computed from the children (height, size, sum, validity) | Postorder, value going up (§5) |
| A path between two arbitrary nodes | Returned value ≠ global answer (§5.1) |
| A condition depending on ancestors (max so far, depth, bounds) | Parameter going down (§6) |
| Levels, what you see from one side, minimum depth | BFS with a size snapshot (§4) |
| Comparing, mirror, inclusion of one tree in another | Two trees in parallel (§7) |
| Sorted order, k-th value in a BST | Inorder traversal (§9.1, 9.4) |
| Search, insertion, deletion in a BST | Go left/right, O(h) (§9.2, 9.5) |
| Validating a BST | Bounds passed down (§9.3) |
| Common ancestor | Split point (BST) or postorder (general tree) (§9.6) |
| Rebuilding a tree from traversals | Preorder root + inorder split + index map (§10) |
| Turning a tree into a string and back | Preorder with null markers (§11) |

______________________________________________________________________

## 15. Complexities to know

- Almost everything is **O(n) time** (each node visited once), and **O(h) memory** for recursion or a stack, or **O(width)** for BFS.
- BST operations (search, insertion, deletion, common ancestor): **O(h)**, so O(log n) if balanced and O(n) in the worst case.
- Checking inclusion of one tree in another by comparing from every node: **O(n·m)**.

> **Method for every exercise**: (1) decide what goes **down** and what comes back **up**, (2) answer the three questions in §2, (3) walk through a small tree of 5–7 nodes by hand, (4) code it, (5) test the cases in §13.

## Links

- [[golang-structs]]
- [[Floyd's Tortoise and Hare]]
- [[Linked Lists - The Theory You Need]]
- [[bucket-sort]]
