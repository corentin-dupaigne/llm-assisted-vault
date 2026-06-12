---
difficulty: medium
neetcode_section: Array & Hashing
struggled: true
project: neetcode-150
---
## Initial Intuition

- Mon intuition naive est qu'il est possible de faire une double boucle ou pour chaque nombre nombre de l'array de nombre je cherche son nombre d'iteration puis ajoute dans une hashmap frequency ou key: frequency, value: array de nombre. Par exemple si 3 et 2 apparaissent 2x alors: m[1] = [3, 2]. Le souci est que cela creerait une complexite de O(n2) ce qui n'est pas optimal.
- Il faudrait pouvoir obtenir une map ou array de frequency en un seul passage.
## My Solution

```go
// Je n'ai pas trouve la solution par moi meme, j'ai rechercher a propos de bucket sort et l'implementation suivante est basee sur bucket sort

// etapes de l'algorithme
// 1. Creer la hashmap de frequency
// 2. definir l'arret buckets, la taille du bucket est len(nums)
// 3. remplir les buckets
// 4. en iterant depuis la droite vers la gauche retourner les k buckets rempli
func topKFrequent(nums []int, k int) []int {
	freq := make(map[int]int)
	for _, num := range nums {
		freq[num]++
	}

	buckets := make([][]int, len(nums) + 1)
	for num, freq := range freq {
		buckets[freq] = append(buckets[freq], num)
	}

	res := []int{}
	counter := 0
	for i := len(nums); i > 0; i-- {
		for _, num := range buckets[i] {
			res = append(res, num)
			counter++
			if counter == k {
				return res
			}
		}
	}

	return []int{}
}

// Time: O(n)
// Space: O(n)

```

### Optimal Solution

```go
// Time: O(?)
// Space: O(?)

```
## Delta

Ma methode est optimale en temps mais la methode de trie par frequence avec heap permet d'etre optimale en space.

## Pattern

Quand la clé de tri est un entier dans un intervalle borné et connu → indexer par la clé (bucket/counting sort) au lieu de comparer. O(n) au lieu de n·log n.

> [!info] Indexation par clé
> **Indexer par clé** = utiliser la valeur elle-même comme **position (index)** dans un tableau, au lieu de la stocker et de la retrouver par comparaison.
