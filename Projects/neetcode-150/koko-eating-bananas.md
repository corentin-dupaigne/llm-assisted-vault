---
difficulty: medium
neetcode_section: Binary Search
struggled: true
project: neetcode-150
date_solved: 2026-06-24
tags:
  - leetcode
  - neetcode-150
  - binary-search
domain: leetcode
date: 2026-06-24
para: Projects
---
## Initial Intuition

Mon intuition pour cet exercice est qu'on peut obtenir le nombre d'heures necessaires pour manger toutes les bananes par rapport a k grace au calcul sum(piles) / k.
Au niveau de l'application du pattern binary search, je pense qu'il faut l'utiliser pour trouver k. Peut etre pouvons nous commencer avec k = 1, verifier si sum(piles)/k \<= hours, si c'est le cas on retourne k, sinon on multiplie k par 2. si sum(piles)/k > hours, on divise par 2. Je pense qu'il y a une faille dans cette solution car si apres une division ou multiplication par * 2 sum(piles)/k \<= hours est true cela ne garanti pas que c'est le plus petit k possible.

## My Solution

```go
// Time: O(?)
// Space: O(?)

```

### Optimal Solution

```go
import "slices"

func minEatingSpeed(piles []int, h int) int {

	l, r := 1, slices.Max(piles)

	res := r
	for l <= r {
		k := (l + r) / 2

		totalHours := 0
		for _, pile := range piles {
			totalHours += int(math.Ceil(float64(pile) / float64(k)))
		}

		if totalHours <= h {
			res = k
			r = k - 1
		} else {
			l = k + 1
		}
	}

	return res
	
}

// Time: O(n * log max(piles))
// Space: O(1)

```

## Delta

Mon intuition etait mauvaise, j'ai reflechi au probleme comme si Koko pouvait manger plusieurs fois par heures ce qui n'est pas le cas. Pour la solution optimale il fallait d'abord trouver min bound et max bound. Min bound etant 1 (s'il y a une banane par pile), et le max est max(piles) (si chaque pile a max(piles banane)). on set res au max possible (max(piles))
On calcul mid (mid == k), on increment un compteur totalHours ou l'on process le nombre d'heures necessaires pour manger toutes les bananes avec le current k. si c'est plus petit ou egale que le nombre d'heures disponibles on update res et on reduit la fenetre vers la gauche. Sinon on reduit la fenetre vers la droite. On retourne res.

## Review Log

- 2026-06-24 — first solve

## Links

- [[find-minimum-in-rotated-sorted-array|Find Minimum In Rotated Sorted Array]]
- [[golang-sorting|Golang Sorting]]
