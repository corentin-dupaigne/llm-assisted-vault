---
difficulty: easy
neetcode_section: "Stack"
struggled: false
project: neetcode-150
date_solved: 2026-06-19
tags: [leetcode, neetcode-150, stack]
---
## Initial Intuition

Mon intuition est qu'il faut utiliser le stack comme un cache. Des qu'on croise une parenthese ouvrante, on pop les elements du array dans un stack jusqu'a ce qu'on trouve une parenthese fermante ou qu'on ait parcouru tout le tableau. Une fois qu'on a trouve la parenthese fermante, on repop. Si le tableau est vide sans qu'on ait trouve la parenthese fermante on return false. Puis on pop tout les elements du stack servant de cache sur le stack original. A la fin, si le stack est vide -> on retourne true. 
- J'ai l'impression que cette solution serait O(n2) en temps car pour chaque element je dois reparcourir le tableau.

## My Solution

```go
func pop(b []byte) ([]byte, byte) {

	if len(b) == 0 {
		return []byte{}, 0
	}

	poped := b[len(b) - 1]

	return b[:len(b) - 1], poped
}

func isOpen(b byte) bool {
	return b == '('	|| b == '[' || b == '{'
}

func matchingPar(b byte) byte {
	if b == ')' {
		return '('
	} else if b == '}' {
		return '{'
	} else {
		return '['
	}
}


func isValid(s string) bool {

	var stack []byte

	for i, _ := range s {
		if isOpen(s[i]) {
			stack = append(stack, s[i])
		} else {
			var poped byte
			stack, poped = pop(stack)
			// fmt.Println(s, poped)
			if poped != matchingPar(s[i]) {
				return false
			}
		}
	}

	return len(stack) == 0
    
}


// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
func pop(b []byte) ([]byte, byte) {

	if len(b) == 0 {
		return []byte{}, 0
	}

	poped := b[len(b) - 1]

	return b[:len(b) - 1], poped
}

func isOpen(b byte) bool {
	return b == '('	|| b == '[' || b == '{'
}

func matchingPar(b byte) byte {
	if b == ')' {
		return '('
	} else if b == '}' {
		return '{'
	} else {
		return '['
	}
}


func isValid(s string) bool {

	var stack []byte

	for i, _ := range s {
		if isOpen(s[i]) {
			stack = append(stack, s[i])
		} else {
			var poped byte
			stack, poped = pop(stack)
			// fmt.Println(s, poped)
			if poped != matchingPar(s[i]) {
				return false
			}
		}
	}

	return len(stack) == 0
    
}


// Time: O(n)
// Space: O(n)
```

## Delta

Ma solution etait optimale.

## Review Log

- 2026-06-19 — first solve
