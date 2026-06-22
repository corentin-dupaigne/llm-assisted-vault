---
difficulty: medium
neetcode_section: "Stack"
struggled: false
project: neetcode-150
date_solved: 2026-06-22
tags: [leetcode, neetcode-150, stack]
---
## Initial Intuition

Mon intuition est qu'on peut utiliser un stack sous forme de cache, on itere sur les nombres :
- tant que le nombre actuel est plus grand que le top du stack, on pop, puis on push l'element actuel.

Pour correctement completer l'array de resultat on peut utiliser utilise une struct composee de deux elements, val et index et le stack sera composee d'elements de cette struct.

Donc quand on pop un element pour res[i] = val, i -> poped.idx, val = le nombre d'elements poped avant cet element.

Mon intuition au niveau de la complexite est O(n) pour time and space.


## My Solution

```go
type Temp struct {
	Idx int
	Value int
}

func dailyTemperatures(temperatures []int) []int {
	var s []Temp
	res := make([]int, len(temperatures))
	
	for i, val := range temperatures {
		for len(s) > 0 && val > s[len(s) - 1].Value {
			poped := s[len(s) - 1]
			s = s[:len(s) - 1]
			res[poped.Idx] = i - poped.Idx
		}
		
		s = append(s, Temp{i, val})
	}

	return res
}


// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
func dailyTemperatures(temperatures []int) []int {
	var s []int
	res := make([]int, len(temperatures))
	
	for i, val := range temperatures {
		for len(s) > 0 && val > temperatures[s[len(s) - 1]]  {
			poped := s[len(s) - 1]
			s = s[:len(s) - 1]
			res[poped] = i - poped
		}
		
		s = append(s, i)
	}

	return res
}

// Time: O(n)
// Space: O(n)

```

## Delta

Ma solution est optimale en terme de complexite mais la struct n'etait pas necessaire.

## Review Log

- 2026-06-22 — first solve
