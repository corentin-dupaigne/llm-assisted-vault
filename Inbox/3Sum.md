---
difficulty: medium
neetcode_section: Two Pointers
struggled: true
project: neetcode-150
date_solved: 2026-06-17
tags:
  - leetcode
  - neetcode-150
  - two-pointers
---
## Initial Intuition

Mon intuition est qu'il est est possible d'iterer sur chaque num du tableau, et pour chacun on effectue un double pointeur ou target est -elem, de ce fait la somme de ces trois nombres sera 0.


## My Solution

```go
import "slices"

func threeSum(nums []int) [][]int {

	slices.Sort(nums[:])

	fmt.Println(nums)

	var res [][]int

	for idx, num := range nums {
		if (idx >= 1) && nums[idx - 1] == num {
			continue
		}

		target := -num

		i, j := 0, len(nums) - 1
		for i < j {
			curr := nums[i] + nums[j]
			if curr == target {
				res = append(res, []int{num, nums[i], nums[j]})
				break
			} else if curr < target {
				i++
			} else {
				j--
			}
		}
	}

	return res
}


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

## Review Log

- 2026-06-17 — first solve
