---
difficulty: medium
neetcode_section: Arrays & Hashing
struggled: true
project: neetcode-150
date_solved: 2026-06-16
reviews: 0
tags:
  - leetcode
  - neetcode-150
  - arrays-hashing
---
## Initial Intuition

Mon intuition est qu'il faut faire trois boucles pour checker toutes les conditions. 
1. Une boucle qui check que les conditions sont respectees pour les rows
2. Une boucle qui check que les conditions sont respectees pour les cols
3. Une boucle qui check que les conditions sont respectees pour les box 3x3


## My Solution

```go
type square struct {
	r int
	c int
}

func isValidSudoku(board [][]byte) bool {

	rows := make(map[int]map[byte]bool)
	cols := make(map[int]map[byte]bool)
	squares := make(map[square]map[byte]bool)

	for r := 0; r < 9; r++ {
		for c := 0; c < 9; c++ {
			if board[r][c] == '.' {
				continue
			}
			if cols[c] == nil {
				cols[c] = make(map[byte]bool)
			}

			if rows[r] == nil {
				rows[r] = make(map[byte]bool)
			}

			if squares[square{r / 3, c / 3}] == nil {
				squares[square{r / 3, c / 3}] = make(map[byte]bool)
			}

			if cols[c][board[r][c]] {
				return false
			}
			if rows[r][board[r][c]] {
				return false
			}
			if squares[square{r / 3, c / 3}][board[r][c]] {
				return false
			}

			cols[c][board[r][c]] = true
			rows[r][board[r][c]] = true
			squares[square{r / 3, c / 3}][board[r][c]] = true
		}
	}

	return true
}


// Time: O(n2)
// Space: O(n2)

```

### Optimal Solution

```go

// Time: O(?)
// Space: O(?)

```

## Delta

<!-- The key difference between your approach and the optimal one -->

## Review Log

- 2026-06-16 — first solve
