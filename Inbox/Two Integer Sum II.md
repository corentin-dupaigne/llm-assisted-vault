---
difficulty: medium
neetcode_section: "Two Pointers"
struggled: false
project: neetcode-150
date_solved: 2026-06-16
review_after: 2026-06-23
reviews: 0
tags: [leetcode, neetcode-150, two-pointers]
---
## Initial Intuition

- Tout d'abord il faut prendre en compte que les indices sont 1 indexed. Il faut egalement prendre en consideration que les nombres sont sorted.
Vu que les elements sont sorted on peut mettre un pointeur a gauche de l'array et un a droite. On fait la somme de nums[i] + nums[j] si c'est egal a target on retourne [i + 1, j + 1]. Sinon si nums[i] + nums[j] est plus petit que target on incremente i, sinon on decremente j.


## My Solution

```go
func twoSum(numbers []int, target int) []int {

	i, j := 0, len(numbers) - 1
	for i < j {
		compute := numbers[i] + numbers[j]

		if compute == target {
			return []int{i + 1, j + 1}
		} 

		if compute < target {
			i++
		} else {
			j--
		}
	}

	return []int{}
}

// Time: O(n)
// Space: O(1)
```

### Optimal Solution

```go
func twoSum(numbers []int, target int) []int {

	i, j := 0, len(numbers) - 1
	for i < j {
		compute := numbers[i] + numbers[j]

		if compute == target {
			return []int{i + 1, j + 1}
		} 

		if compute < target {
			i++
		} else {
			j--
		}
	}

	return []int{}
}


// Time: O(n)
// Space: O(1)
```

## Delta

Mon code est parfait, j'aurai pu juste mieux nommer la variable compute et la nommer sum a la place.
## Review Log

- 2026-06-16 — very quickly solved (15min)
