---
difficulty: easy
neetcode_section: Two Pointers
struggled: false
project: neetcode-150
date_solved: 2026-06-16
review_after: 2026-06-23
reviews: 0
domain: leetcode
tags: [two-pointers, golang, neetcode-150]
date: 2026-06-16
para: Projects
---
## Initial Intuition

Mon intuition est qu'il est possible de simplement placer un pointeur au debut du string (i) et un a la fin (j), comparer str[i] et str[j], les deux elements doivent etre les memes sinon on retourne false. Puis on incremente i et decremente j, tant que i < j.
Apres la boucle, on retourne true.

- time : O(n)
- space O(1)

## My Solution

```go
func isAlphanumeric(b byte) bool {
	return (b >= '0' && b <= '9') || (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z')
}

func isLowercase(b byte) bool {
	return b >= 'a' && b <= 'z'
}


func isPalindrome(s string) bool {
	for i, j := 0, len(s) - 1; i < j; i, j = i + 1, j - 1 {

		for !isAlphanumeric(s[i]) {
			i++
		}

		for !isAlphanumeric(s[j]) {
			j--
		}

		if i > j {
			return false
		}

		a := s[i]
		b := s[j]

		if !isLowercase(b) {
			b += 32
		}

		if !isLowercase(a) {
			a += 32
		}

		if a != b {
			return false
		}
	}

	return true
}

// Time: O(n)
// Space: O(1)

```

### Optimal Solution

```go
func isAlphanumeric(b byte) bool {
	return (b >= '0' && b <= '9') || (b >= 'a' && b <= 'z') || (b >= 'A' && b <= 'Z')
}

func isLowercase(b byte) bool {
	return b >= 'a' && b <= 'z'
}


func isPalindrome(s string) bool {
	for i, j := 0, len(s) - 1; i < j; i, j = i + 1, j - 1 {

		for i < j && !isAlphanumeric(s[i]) {
			i++
		}

		for i < j && !isAlphanumeric(s[j]) {
			j--
		}

		a := s[i]
		b := s[j]

		if !isLowercase(b) {
			b += 32
		}

		if !isLowercase(a) {
			a += 32
		}

		if a != b {
			return false
		}
	}

	return true
}


// Time: O(n)
// Space: O(1)

```

## Delta

Ma solution n'etait pas fonctionnelle a cause des potentiels overflow du a mon incrementation/decrementation de i/j. Je ne checkais pas si i < j dans la condition du for, ce qui fait que l'index pouvait overflow. A part ca ma solution etait correcte en complexite

## Review Log

- 2026-06-16 — Un peu fastidieux, et erreur de fonctionnalite.

## Links

- [[golang-strings|String Manipulation Golang]]
