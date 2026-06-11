---
difficulty: easy
neetcode_section: Array & Hashing
struggled: false
project: neetcode-150
domain: leetcode
date: 2026-06-10
tags: [array-hashing, hashmap, golang]
para: Projects
---
## Initial Intuition

Mon intuition naive est qu'on peut simplement faire une double boucle pour tester toutes les combinaisons avec par exemple deux variables i, y. Je check si nums[i] + nums[y] == target, si c'est le cas je retourne [min(i,y), max(i, y)].

- La complexite de cet algorithme serait O(n2) en time complexite et en space O(1) car je n'ai rien besoin de stocker.

Mon intuition pour la methode optimale est de fill une hashmap en iterant sur les nums, pour chaque num -> je store key: num, value: idx. Puis j'itere sur chacune des clefs de la hashmap, je regarde si la clef target - current_clef existe dans la hashmap. Si c'est le cas je recupere son index et je retourne un array contenant les deux clefs (en s'assurant que les elements soient dans l'ordre croissant grace a min, max).

- La complexite de cet algorithme serait O(n) en time et O(n) en memoire (la hashmap).

## My Solution

```go

func twoSum(nums []int, target int) []int {
	
	m := make(map[int]int)
	
	for i := 0; i < len(nums); i++ {
		m[nums[i]] = i
	}
	
	for key := range m {
		_, ok := m[target - key]
		if ok {
			return []int{ min(m[target - key], m[key]), max(m[target - key], m[key]) }
		}
	}

	return []int{}
}

// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
func twoSum(nums []int, target int) []int {
	
	m := make(map[int]int)
	
	for i := 0; i < len(nums); i++ {
		if _, ok := m[target - nums[i]]; ok {
			return []int{ m[target - nums[i]], i }
		}

		m[nums[i]] = i
	}

	return []int{}
}

// Time: O(n)
// Space: O(n)

```

## Delta

Ma solution est en O(n) time/memory et est donc proche de la solution optimale mais il y a deux differences importantes, une erreur faisant que le leetcode ne passe pas les tests, et un probleme d'optimisation.

- L'erreur etant que je cree d'abord la hashmap et pour chaque nombre je cree key: value, value: index. Le souci etant que si il y a plusieurs fois le meme nombre l'index est override. Exemple : num[0] = 3 -> map[3] = 0 -> num[1] = 3 -> map[3] = 1. Ce qui fait que si la target etait 6 je retournerais [1, 1] au lieu de [0, 1].
- Le souci d'optimisation est que je fais deux parcours, un pour former la map, et un parcours pour chercher la bonne combinaison. Ce n'est pas necessaire, je peux simplement former la map lors de l'iteration et etant donne qu'il faut deux nombres pour faire une combinaison permettant une solution quand je croise le deuxieme nombre le premier est forcement deja dans la map ce qui fait que un seul parcours suffit.

## Pattern

Quand j'ai besoin de trouver une paire d'éléments satisfaisant une condition, je stocke value → index dans une hashmap et je cherche le complément à la volée en un seul passage. Le deuxième élément de la paire arrive toujours après le premier dans le tableau, donc quand je le croise le premier est forcément déjà dans la map.

## Links

- [[contains-duplicate|Contains Duplicate]]
- [[golang-maps|Golang Maps Cheatsheet]]
- [[golang-loops|Golang Loops And Range]]
