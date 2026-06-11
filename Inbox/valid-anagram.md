---
domain: leetcode
difficulty: easy
neetcode_section: Array & Hashing
struggled: false
project: neetcode-150
---

## Initial Intuition

- Il faut comparer deux string, et l'ordre ne compte pas. Mon intuition naive est qu'on pourrait tout simplement trier les deux string par ordre alphabetique et verifier si ils sont egaux. Si ils sont egaux ce sotn donc des anagrammes, mais avec cette solution on ne profite pas du fait que l'ordre ne compte pas.
	- J'estime la complexite de la methode naive a O(2 log n), 2 car il y a seulement deux string a comparer et log n car c'est la complexite pour un tri. Mais si le nombre de string etait variable ce serait O(k log n). Et en memoire O(1) car il faut simplement store deux string.

- Comme methode optimale pour profiter du fait que l'ordre ne compte pas je pourrais former une hashmap pour chaque string d'une forme key=lettre, value=num_iteration. A chaque fois que je croise une lettre j'incremente le compteur de la lettre si elle existe, sinon j'instancie la clef correspondant a la lettre et met son compteur a 0. A la fin je compare les deux hashmap, si elles sont egales, les deux mots sont des anagrammes. Je choisi une hashmap et pas un tableau car pour utiliser un tableau j'aurai eu besoin que la clef soit un int alors que dans ce cas j'ai besoin que la clef soit une lettre.
	- J'estime la complexite a O(n) car cela demande un seul parcours de tableau et quelques operations mais la complexite reste donc a O(n). Et en memoire O(n) car deux hashmap, O(2n) plus exactement mais on arrondi.
	Pour eviter des operations inutiles je peux egalement verifier que les mots sont egaux en longueurs, si il ne sont pas egaux en longueurs ils ne peuvent pas etre des anagrammes.


## My Solution

```go

import "maps"

func isAnagram(s string, t string) bool {

	if len(s) != len(t) {
		return false
	}

	map1 := make(map[byte]int)
	map2 := make(map[byte]int)
	
	for i := 0; i < len(s); i++ {

		_, ok := map1[s[i]]
		if ok {
			map1[s[i]]++
		} else {
			map1[s[i]] = 1
		}
		
		_, ok2 := map2[t[i]]
		if ok2 {
			map2[t[i]]++
		} else {
			map2[t[i]] = 1
		}
	}
	
	return maps.Equal(map1, map2)
}

// Time: O(n)
// Space: O(1)

```

### Optimal Solution

```go
func isAnagram(s string, t string) bool {

    if len(s) != len(t) {
        return false
    }

    m := make(map[byte]int)
    for i := 0; i < len(s); i++ {
        m[s[i]]++
        m[t[i]]--
    }

    for _, val := range m {
        if val != 0 {
            return false
        }
    }

    return true
}

// Time: O(n)
// Space: O(1)

```
## Delta

Ma solution etait correcte en complexite, la difference se situe dans la connaissance du langage go et mon code aurait pu etre plus lisible et elegant. Mon if qui verifie si la clef existe n'etait pas necessaire car si la clef n'existe pas go la cree automatiquement, pas de undefined behavior. 

Egalement incrementer et decrementer le compteur est plus elegant et propre que build et comparer deux maps.

A savoir que je m'etais egalement trompe sur la complexite je pensais que la complexite memoire est O(n), n etant la longueur du string. Sauf que vu que la taille max de la hashmap est deterministe (26 lettres dans l'alphabet), c'est donc du O(1).

## Pattern

<!-- "When I see X, I think Y." — phrased generically -->
