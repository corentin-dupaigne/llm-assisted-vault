<%*
const name = await tp.system.prompt("Problem name (e.g. Valid Sudoku)");
const slug = name.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");
const patterns = [
  "Arrays & Hashing", "Two Pointers", "Sliding Window", "Stack",
  "Binary Search", "Linked List", "Trees", "Tries", "Heap / Priority Queue",
  "Backtracking", "Graphs", "Advanced Graphs", "1-D DP", "2-D DP",
  "Greedy", "Intervals", "Math & Geometry", "Bit Manipulation"
];
const pattern = await tp.system.suggester(patterns, patterns, false, "Pattern");
const difficulty = await tp.system.suggester(["Easy", "Medium", "Hard"], ["easy", "medium", "hard"], false, "Difficulty");
await tp.file.rename(name);
-%>
---
tags: [leetcode]
link: https://leetcode.com/problems/<% slug %>/
pattern: "<% pattern %>"
difficulty: <% difficulty %>
created: <% tp.date.now("YYYY-MM-DD") %>
---

# <% name %>

## Trigger
> What in the problem statement should point me to the pattern?

- <% tp.file.cursor() %>

## Insight
> The key idea in one sentence.

- 

## Invariant
> What my pointers / data structure guarantee at every step. (optional)

- 

## Where I got stuck
- [ ] Finding the idea
- [ ] Implementation (indices, edge cases, Go details)
- [ ] Understanding the solution

