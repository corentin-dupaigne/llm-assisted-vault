---
domain: leetcode
neetcode_section: Array & Hashing
struggled: false
date: 2026-06-10
project: neetcode-150
tags: [array-hashing, hashmap, golang]
para: Projects
---
## Initial Intuition

Il faut chercher des doublons -> la methode naive serait de faire un brute force grace a un double boucle mais cela serait de complexite O(n2). Utiliser une hashmap permettra de reduire le lookup a O(1) ce qui me permet de verifier l'unicite en un seul passage.

J'initialise une hashmap -> j'itere sur tous les nombres -> si le nombre est une clef existante de la hashmap je retourne true.

Une fois que j'ai parcouru tous les nombres, cela signifie qu'il n'y a pas de duplicate, je peux donc retourner false.

## My Solution

```go

func hasDuplicate(nums []int) bool {
	m := make(map[int]bool)
	
	for _, num := range nums {
		_, ok := m[num]
		if ok {
			return true
		}
		m[num] = true
	}
	
	return false
		
}
// Time: O(n)
// Space: O(n)

```

- On parcours un tableau donc O(N) en complexite de temps
- On doit creer une hashmap qui sera au maximum de taille N donc O(N) en memoire

### Optimal Solution

```go
func hasDuplicate(nums []int) bool {
	m := make(map[int]struct{})
	
	for _, num := range nums {
		_, ok := m[num]
		if ok {
			return true
        }
		m[num] = struct{}{}
	}
	
	return false
		
}

// Time: O(n)
// Space: O(n)

```

## Delta

Ma solution etait optimale en terme de complexite, la seule difference relativement negligeable est que pour faire le set j'aurai pu utiliser m := make(map[int]struct{}) et pour
inserer n[num] = struct{}{} (instance anonyme d'une struct vide). Cela aurait permi d'economiser 1 byte par insertion dans le set. Possible dans ce cas car je n'utilise pas la value.

## Pattern

- Quand j'ai besoin de verifier une unicite de maniere optimale je peux utiliser une hashmap avec valeur vide (grace a struct{}), on peut aussi appeler ca du value-less, ce qui me permet de simuler un set. Le set me permet d'avoir un look-up en O(1) ce qui me permet de verifier l'unicite des valeurs d'un tableau en O(N).
