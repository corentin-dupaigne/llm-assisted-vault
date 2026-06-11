---
difficulty: medium
neetcode_section: Array & Hashing
struggled: false
project: neetcode-150
domain: leetcode
tags: [array-hashing, hashmap, golang]
date: 2026-06-11
para: Projects
---
## Initial Intuition

Mon idée naïve de la solution au problème est que je peux utiliser une hashmap de la forme key:int, value:[]int la clef serait un mot de la liste sorted et la value serait un tableau contenant tous les anagrammes de ce mot qui sont dans la liste de mots passés en input.

Pour se faire je vais donc simplement iterer sur chaque mot et pour chaque mot je vais, dans la hashmap, ajouter le mot dans le array à la clef correspondante à sa version sorted.

- pour la complexité étant donné que cela demande de trier n mots et faire un parcours de tableau (plusieurs string) ça donne O(n log n) + O(n) -> O(n log n).
- Et en terme de complexite de memoire, O(n).

## My Solution

```go
import "slices"

func groupAnagrams(strs []string) [][]string {
	
	m := make(map[string][]string)
	
	for _, w := range strs {
		key := []rune(w)
		slices.Sort(key)
		key_str := string(key)
		m[key_str] = append(m[key_str], w)
	}
	
	res := make([][]string, 0)
	for _, val := range m {
		res = append(res, val)
	}

	return res

}

// Time: O(n * k log k)
// Space: O(n)

```

### Optimal Solution

```go
func groupAnagrams(strs []string) [][]string {

	m := make(map[[26]int][]string)

	for _, w := range strs {
		bytes := []byte(w)
		key := [26]int{}

		for _, b := range bytes {
			key[b - 'a']++
		}
		m[key] = append(m[key], w)
	}

	res := make([][]string, 0)
	for _, val := range m {
		res = append(res, val)
	}

	return res
}

// Time: O(n * m) // n: nombre de mots, m: longueur moyenne d'un mot
// Space: O(n)

```

## Delta

- Ma methode etait fonctionnelle mais pas optimale en complexite, je faisais un trie a chaque iteration pour ainsi utiliser la version triee du string comme clef dans la hashmap. Une meilleur methode permettant d'eviter le trie consiste a utiliser un array de taille 26 (les 26 lettres de l'alphabet) permettant de compter le nombre d'iteration de chaque lettre dans le mot. Pour se faire on itere sur chaque lettre du mot et on incremente le compteur a l'index [letter - 'a'] dans l'array. A noter que cela fonctionne uniquement si seuls les 26 lettres minuscules de l'alphabet peuvent etre passees en input car sinon l'index donne par [letter - 'a'] pourrait etre negatif. cela rajoute donc O(k) pour construire l'array au lieu de O(k log k) si on construisait la clef en triant.
- Je me suis egalement trompe dans le calcul de complexite pour ma solution, j'ai sous estime la complexite de temps du sorting. La complexite correcte est n * k log k, k log k pour chaque mot, et donc n * k log k car il y a n mots.

## Pattern

- ll faut garder en tete qu'il est possible d'utiliser des array comme clef de hashmap en go. Egalement prendre profit du fait que le nombre de lettre dans l'alphabet est deterministe.
- Quand je dois regrouper des ensembles de string selon un critere commun tel que des anagrames je peux prendre profit du fait qu'il y a 26 lettres dans l'alphabet pour ainsi utiliser un array d'iteration comme clef pour une hashmap contenant les groupes.

## Links

- [[valid-anagram|Valid Anagram]]
- [[contains-duplicate|Contains Duplicate]]
- [[two-sum|Two Sum]]
- [[golang-maps|Golang Maps Cheatsheet]]
