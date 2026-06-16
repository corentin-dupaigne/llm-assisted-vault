---
difficulty: medium
neetcode_section: "Arrays & Hashing"
struggled: false
project: neetcode-150
date_solved: 2026-06-15
review_after: 2026-06-22
reviews: 0
tags: [leetcode, neetcode-150, arrays-hashing]
---
## Initial Intuition

Mon intuition initiale est de d'abord build une hashmap ou chaque num de l'array nums est une clef de la hashmap, et les values sont vides. Cela va permettre de check en O(1) si un num exite dans le array. Maintenant pour chercher la longest sequence on va iterer sur chaque num, si num -1 n'existe pas dans la hashmap on sait que c'est le debut d'une sequence. Une fois qu'on est usr un num du debut d'une sequence on va check si num + 1 existe dans la hashmap, puis num + 1 + 1, etc. Jusqu'a que curr_num + 1 n'exite pas. A chaque fois qu'on trouve un num dans la hashmap on incremente le compteur. A la fin de l'iteration on check si compteur > max_compteur, si c'est le cas max_compteur = compteur. A la fin on retourne max_compteur.

- Au niveau de l'estimation de la complexite, on fait deux boucles non imbriquees c'est donc du O(n) + O(n) = O(n). Et pour le space c'est du O(n) aussi car on store les elements dans une hashmap.


## My Solution

```go
func longestConsecutive(nums []int) int {

	m := make(map[int]struct{})

	for _, num := range nums {
		m[num] = struct{}{}
	}

	max_count := 0
	for _, num := range nums {
		if _, ok := m[num - 1]; !ok {
			count := 1
			curr := num + 1
			for {
				_, ok1 := m[curr]
				if !ok1 {
					break
				}
				count++
				curr++	
			}
			if count > max_count {
				max_count = count
			}
		}
	}

	return max_count

}

// Time: O(n2) || deux boucles
// Space: O(n)

```

### Optimal Solution

```go
func longestConsecutive(nums []int) int {

	m := make(map[int]struct{})

	for _, num := range nums {
		m[num] = struct{}{}
	}

	max_count := 0
	for num, _ := range m {

		if _, ok := m[num - 1]; ok {
			continue
		}

		count := 1
		for {
			_, ok := m[num + 1]
			if !ok {
				break
			}
			count++
			num++
		}

		if count > max_count {
			max_count = count
		}
	}
	
	return max_count
}


// Time: O(n)
// Space: O(n)
```

## Delta

La cause du pire cas O(n²) : j'itère sur `nums` au lieu d'itérer sur
la map. Avec des doublons, chaque copie d'une même valeur passe le test
`m[num-1]` et relance un scan complet de la suite.

Exemple : nums = [1, 1, 1, 1, 2, 3, 4, 5]. Les quatre copies de 1 sont
chacune vues comme un début de suite (m[0] absent), donc je scanne la suite
1→5 quatre fois au lieu d'une. Avec d copies de 1 suivies d'une suite de
longueur L, le coût est d·L ; en posant d ≈ L ≈ n/2, on obtient ~n²/4 = O(n²).

Le fix `range nums` → `range m` corrige ça : les clés de la map étant
uniques, chaque valeur n'est visitée qu'une fois quel que soit le nombre
de doublons → O(n) garanti dans tous les cas.


## Review Log

- 2026-06-15 — Reussi rapidement mais solution pas optimale dans le pire cas avec beaucoup de doublons O(n2) vs O(n) mais refait de maniere optimale
