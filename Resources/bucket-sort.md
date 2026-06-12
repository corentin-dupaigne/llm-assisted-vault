---
domain: leetcode
tags: [array-hashing]
date: 2026-06-12
para: Resources
project: null
---
> [!abstract] In one sentence
> Sort by **distributing** elements into buckets based on their value, then **sorting each bucket** and **concatenating** them in order. Fast when data is uniformly distributed.

## Idea

Instead of comparing all elements against each other, exploit their **value** to place them directly into the right group. See Key Indexing.

## Algorithm

1. **Create** k buckets, each responsible for a sub-range of values.
1. **Scatter** — walk the input once, drop each element into its bucket (`index = f(value)`, no comparison).
1. **Sort** each bucket individually (insertion sort, or built-in sort).
1. **Gather** — concatenate buckets in order. No merging: bucket 0 < bucket 1 < ... so a simple `append`.

## Complexity

| Case | Time | Why |
| -------------------------------- | ------------ | --------------------------------------------------- |
| Average (uniformly distributed) | **O(n + k)** | small buckets → sorting each is negligible |
| Worst (everything in one bucket) | **O(n²)** | one bucket swallows everything → back to naive sort |

- **Space: O(n + k)** (the buckets).
- **Stable** if the inner sort is.

## When to use it

> [!warning] When to use — and when NOT
> Useful **only** if data is **uniformly distributed** over a **bounded, known** range (ideally guaranteed by construction: uniform floats in \[0,1), calibrated values).
> If the range is unknown/huge/unbounded → data clusters into one bucket → O(n²). Prefer a comparison sort or a heap instead.

## Cousins

- **Counting sort** — one bucket per exact value (small integer range).
- **Radix sort** — bucketing digit by digit; sidesteps the distribution problem (always 10 or 256 buckets). Widely used in practice for integers / fixed-length keys.

## In practice

Almost never a stdlib's default `sort()` (which can assume nothing about the data). Lives in specialized code: sorting uniform floats, radix sort (databases, GPUs), histograms, spatial partitioning.

## Classic application

[[Top K Frequent Elements]] — bucket indexed by frequency (range 1..n, bounded) → O(n) instead of n·log n.

## Links

- [[golang-sorting|Golang Sorting]]
