---
difficulty: medium
neetcode_section: "Two Pointers"
struggled: true
project: neetcode-150
date_solved: 2026-06-23
tags: [leetcode, neetcode-150, two-pointers]
domain: leetcode
date: 2026-06-24
para: Projects
---
## Initial Intuition

Mon intuition est qu'il faut trouver les deux plus hauts et plus eloignes. J'imagine qu'il faut compute la quantite a chaque iteration Et en fonction on bouge les pointeurs, la question est comment savoir quel pointeur bouger.
J'ai regarde 3 hint car je ne trouvais pas, il est dit qu'il faut bouger uniquement le pointeur avec la height la plus petite, je n'ai pas compris tout de suite mais je viens de comprendre que vu que la quantite maximale est definie par le petit (si on a une height de 4 et une height de 8 si 8 etait 4 a la place ca ferait la meme quantite). On bouge donc uniquement le pointeur sur la height la plus petite car c'est uniquement comme ca qu'on va pouvoir ameliorer la quantite sur cette range.

## My Solution

```go

func maxArea(heights []int) int {

	i := 0
	j := len(heights) - 1

	max := 0

	for i < j {
		quantity := (j - i) * min(heights[i], heights[j])
		if quantity > max {
			max = quantity
		}

		if heights[i] < heights[j] {
			i++
		} else if heights[i] > heights[j] {
			j--
		} else {
			i++
			j--
		}
	}

	return max

}

// Time: O(n)
// Space: O(1)

```

### Optimal Solution

```go

func maxArea(heights []int) int {

	i := 0
	j := len(heights) - 1

	max := 0

	for i < j {
		quantity := (j - i) * min(heights[i], heights[j])
		if quantity > max {
			max = quantity
		}

		if heights[i] < heights[j] {
			i++
		} else if heights[i] > heights[j] {
			j--
		} else {
			i++
			j--
		}
	}

	return max

}


// Time: O(n)
// Space: O(1)

```

## Delta

Ma solution est optimale.

## Review Log

- 2026-06-23 — first solve

## Links

- [[valid-palindrome|Valid Palindrone]]
- [[two-sum-ii-input-array-is-sorted|Two Integer Sum Ii]]
- [[three-sum|3Sum]]
