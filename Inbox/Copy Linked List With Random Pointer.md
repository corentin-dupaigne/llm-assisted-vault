---
difficulty: medium
neetcode_section: "Linked List"
struggled: false
project: neetcode-150
date_solved: 2026-07-09
tags: [leetcode, neetcode-150, linked-list]
---
## Initial Intuition

My intuition is that I need two iteration to create the deep copy. One iteration to create the deepcopy list, set the .Val and .Next for each node and set .Random to the idx of the node it points to (one-indexed). On the same iteration we build an hashmap where the key is the idx (one-indexed) of the current node and its value, a pointer to it. 
On the second iteration, we replace the .Random value with m[curr.Random]

## My Solution

```go
// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
// Time: O(n)
// Space: O(n)

```

## Delta

Mon intuition de la hashmap etait bonne mais pas ma logique et le contenu de la hashmap n'etait pas bon non plus, ma methode aurait pu etre fonctionelle avec deux maps mais avec une seule ce n'etait pas possible. La meilleure solution est d'iterer sur toutes les node de la liste originale, pour chaque node on cree m

## Review Log

- 2026-07-09 — first solve
