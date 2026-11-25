---
tags: [algo, tries, roadmap/week-1]
---

# Tries - Prefix search

Prerequisite: [[Tries - Structure and insertion]]

## Theory

Two uses go beyond simple word lookup.

### 1. Wildcard: DFS inside the trie

When a character can be **any letter** (the `.` in "Add and Search Words"), you can no longer follow a single path. At each `.`, try **every non-nil child**: it's a DFS inside the trie.
- Normal letter: only one branch possible.
- `.`: up to 26 branches, return `true` as soon as one succeeds.

### 2. Many words in a grid: trie + backtracking

In "Word Search II", searching for each word separately in the grid is very expensive. The idea is to **flip** the problem:
1. Put all the words in a trie.
2. Run **one** DFS from each grid cell, moving through the trie at the same time.
3. If the next letter isn't a child of the current node, **stop right away**: no word starts that way. This pruning is what makes the solution fast.
4. When you reach an `end` node, you've found a word.

Classic optimizations: store the full word in the final node instead of a boolean, and clear it once found to avoid duplicates.

## Go template

```go
// Wildcard '.': DFS inside the trie from index i
func (t *Trie) searchWild(word string, i int) bool {
    if i == len(word) {
        return t.end
    }
    if word[i] == '.' {
        for _, child := range t.children {
            if child != nil && child.searchWild(word, i+1) {
                return true
            }
        }
        return false
    }
    child := t.children[word[i]-'a']
    return child != nil && child.searchWild(word, i+1)
}
```

## Recognizing the pattern

- wildcard character → DFS inside the trie
- "find all the words from a list in a grid" → trie + backtracking (see [[Backtracking - Grid search]])

> [!question]- What is the complexity of `searchWild` on a word made only of `.`?
> In the worst case, you visit every trie node down to that depth: it's bounded by the size of the trie, not by 26^L, because you only follow children that exist.

> [!question]- Why is Word Search II so much faster with a trie than searching for each word separately?
> You walk the grid once for all the words at the same time, and the trie cuts a branch as soon as no word starts with the letters read so far.

## Resources

- Tech Interview Handbook, [Trie cheatsheet](https://www.techinterviewhandbook.org/algorithms/trie/): sections **Corner cases** and **Techniques** only (~3 min)

## Problems

1. [Design Add and Search Words Data Structure](https://leetcode.com/problems/design-add-and-search-words-data-structure/) (medium)
2. [Word Search II](https://leetcode.com/problems/word-search-ii/) (hard, optional: do it after backtracking)

## My notes

**The hint that should have pointed me to the solution:**

**My mistakes:**

**What I'm keeping:**
