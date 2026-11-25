---
tags: [algo, tries, roadmap/week-1]
---

# Tries - Structure and insertion

## Theory

A **trie** (prefix tree) stores words character by character. Each node represents a **prefix**: the path from the root down to it. Words that start the same way share the same nodes.

Example with `car`, `cat` and `do`:

```
(root)
 ├─ c ─ a ─ r*
 │       └─ t*
 └─ d ─ o*
```

The star marks a node where **a word ends**. That marker is essential: without it, you can't tell the word `ca` (absent) from the prefix `ca` (present, since it leads to `car` and `cat`).

Each node holds:
- its **children**, one per possible next character. With only `a` to `z`, a `[26]*Trie` array is faster than a map.
- an **`end`** boolean

### Complexity

For a word of length `L`:
- insert, search, prefix check: **O(L)**, regardless of how many words are stored
- space: **O(sum of the lengths)** in the worst case, less when prefixes are shared

That's the advantage over a map of strings: a map answers "does this word exist?" in O(L), but can't answer "does any word start with this prefix?" without scanning everything.

## Go template

```go
type Trie struct {
    children [26]*Trie
    end      bool
}

func Constructor() Trie {
    return Trie{}
}

func (t *Trie) Insert(word string) {
    node := t
    for i := 0; i < len(word); i++ {
        c := word[i] - 'a'
        if node.children[c] == nil {
            node.children[c] = &Trie{}
        }
        node = node.children[c]
    }
    node.end = true
}

// find returns the node for the prefix, or nil if it doesn't exist
func (t *Trie) find(s string) *Trie {
    node := t
    for i := 0; i < len(s); i++ {
        node = node.children[s[i]-'a']
        if node == nil {
            return nil
        }
    }
    return node
}

func (t *Trie) Search(word string) bool {
    n := t.find(word)
    return n != nil && n.end
}

func (t *Trie) StartsWith(prefix string) bool {
    return t.find(prefix) != nil
}
```

## Recognizing the pattern

- "prefix", "autocomplete", "starts with"
- many words to look up **at the same time** in one structure (a grid, a text)

> [!question]- What's the difference between `Search("ca")` and `StartsWith("ca")` if the trie only holds `car`?
> `StartsWith` returns `true`: the `ca` node exists. `Search` returns `false`: that node doesn't have `end = true`.

> [!question]- Why does `word[i] - 'a'` work as an index?
> `word[i]` is a byte (ASCII code). The letters `a` to `z` have consecutive codes, so the subtraction gives a number between 0 and 25.

## Resources

- Tech Interview Handbook, [Trie cheatsheet](https://www.techinterviewhandbook.org/algorithms/trie/): sections **Introduction** and **Time complexity** only (~3 min)

## Problems

1. [Implement Trie (Prefix Tree)](https://leetcode.com/problems/implement-trie-prefix-tree/) (medium)

## My notes

**The hint that should have pointed me to the solution:**

**My mistakes:**

**What I'm keeping:**
