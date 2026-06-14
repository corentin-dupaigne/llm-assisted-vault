<%*
// --- Interactive prompts on file creation ---
const difficulty = await tp.system.suggester(
  ["🟢 easy", "🟡 medium", "🔴 hard"],
  ["easy", "medium", "hard"],
  false, "Difficulty?"
);
const sections = ["Arrays & Hashing","Two Pointers","Sliding Window","Stack",
  "Binary Search","Linked List","Trees","Tries","Heap / Priority Queue",
  "Backtracking","Graphs","Advanced Graphs","1-D DP","2-D DP","Greedy",
  "Intervals","Math & Geometry","Bit Manipulation"];
const section = await tp.system.suggester(sections, sections, false, "NeetCode section?");
const struggled = await tp.system.suggester(
  ["No — got it cleanly","Yes — needed help / hint"],
  [false, true], false, "Did you struggle?"
);
// Next review: 3 days if struggled, 7 if clean (simple SR seed)
const reviewOffset = struggled ? 3 : 7;
-%>
---
difficulty: <% difficulty %>
neetcode_section: "<% section %>"
struggled: <% struggled %>
project: neetcode-150
date_solved: <% tp.date.now("YYYY-MM-DD") %>
review_after: <% tp.date.now("YYYY-MM-DD", reviewOffset) %>
reviews: 0
tags: [leetcode, neetcode-150, <% section.toLowerCase().replace(/[^a-z0-9]+/g, "-") %>]
---
## Initial Intuition

<!-- Before coding: pattern recognized? Approach envisioned? Edge cases? -->


## My Solution

```go
// Time: O(?)
// Space: O(?)

```

### Optimal Solution

```go
// Time: O(?)
// Space: O(?)

```

## Delta

<!-- The key difference between your approach and the optimal one -->


## Pattern

<!-- "When I see X, I think Y." — phrased generically -->


## Review Log

<!-- Date — could you reproduce it cold? what tripped you up? -->
- <% tp.date.now("YYYY-MM-DD") %> — first solve
