---
difficulty: medium
neetcode_section: Arrays & Hashing
struggled: true
project: neetcode-150
date_solved: 2026-06-14
review_after: 2026-06-17
reviews: 0
---
## Initial Intuition

- Mon intuition naive est qu'il est possible de former l'array de resultat avec une double boucle mais cela ferait une complexite O(n2) et ce n'est donc pas optimal.


## My Solution

```go
func productExceptSelf(nums []int) []int {

	prefix := make([]int, len(nums))
	prefix[0] = 1

	suffix := make([]int, len(nums))
	suffix[len(nums) - 1] = 1


	for i := 1; i < len(nums); i++ {
		prefix[i] = prefix[i - 1] * nums[i - 1]
	}

	for i := len(nums) - 2; i >= 0; i-- {
		suffix[i] = suffix[i + 1] * nums[i + 1]
	}

	res := make([]int, len(nums))
	for i := 0; i < len(nums); i++ {
		res[i] = prefix[i] * suffix[i]
	}

	return res

}

// Time: O(1)
// Space: O(1)

```

### Optimal Solution

```go
func productExceptSelf(nums []int) []int {
	n := len(nums)
	res := make([]int, n)

	// Passe 1 : res[i] = produit de tout ce qui est à GAUCHE de i
	res[0] = 1
	for i := 1; i < n; i++ {
		res[i] = res[i-1] * nums[i-1]
	}

	// Passe 2 : on fait rouler le produit suffixe, on le combine dans res
	suffix := 1
	for i := n - 1; i >= 0; i-- {
		res[i] *= suffix      // gauche (déjà dans res) × droite (suffix)
		suffix *= nums[i]     // on met à jour le produit de droite
	}

	return res
}
// Time:  O(n)
// Space: O(1) extra (hors tableau de sortie)

```

## Delta

## Delta
- Ma première solution était fonctionnelle mais non optimale en espace : O(n) à cause des deux arrays `prefix` et `suffix` séparés, au lieu de O(1).
- **Erreur d'initialisation (0 vs 1)** : pour le premier élément du prefix et le dernier du suffix, j'avais mis 0, en partant du principe que le premier num n'a pas de prefix et le dernier pas de suffix. Mais comme on calcule un **produit**, l'élément neutre est 1, pas 0 (`x * 1 = x`, alors que `x * 0 = 0` détruirait tout le résultat). Règle générale : la valeur initiale d'un prefix/suffix = l'élément neutre de l'opération (0 pour une somme, 1 pour un produit).
- **Erreur d'opérateur** : dans ma version initiale j'avais additionné (`+`) au lieu de multiplier (`*`) — réflexe du prefix sum classique appliqué à tort à un produit.
- **Optimisation espace (O(n) → O(1))** : pas besoin de deux arrays. On écrit directement les prefix dans `res` (passe gauche→droite), puis on combine les suffix avec un **simple scalaire qui roule** (passe droite→gauche), car en lisant de droite à gauche je n'ai jamais besoin de relire une ancienne valeur de suffix. Une seule variable suffit → O(1) extra space.

## Pattern

Quand il est question de process un ensemble de nombre sauf l'element actuel, il faut directement penser a l'algorithme prefix - sufix consistant a :
- Build l'array de prefix
- Build l'array de suffix
- Build l'array de resultat en traitant prefix avec suffix


## Review Log

<!-- Date — could you reproduce it cold? what tripped you up? -->
- 2026-06-14 — first solve
