## Le pattern de base

Binary search divise l'espace de recherche en deux a chaque etape. O(log n) temps, O(1) espace.

```go
func BinarySearch(nums []int, target int) int {
    lo, hi := 0, len(nums)-1
    for lo <= hi {
        mid := lo + (hi-lo)/2  // evite overflow vs (lo+hi)/2
        if nums[mid] == target {
            return mid
        } else if nums[mid] < target {
            lo = mid + 1
        } else {
            hi = mid - 1
        }
    }
    return -1  // pas trouve
}
```

### Les 3 pieges classiques

1. **Overflow** : `mid = (lo + hi) / 2` overflow si lo+hi > MaxInt. Toujours ecrire `mid = lo + (hi-lo)/2`.
2. **Boucle infinie** : si tu oublies `+1` ou `-1` dans `lo = mid + 1` / `hi = mid - 1`, la boucle ne termine pas.
3. **Off-by-one** : `lo <= hi` (pas `<`) quand tu cherches un element exact. Avec `<`, tu rates le cas ou lo == hi == index de la cible.

### Variante : Lower Bound (premiere occurrence)

Quand il y a des doublons, ou qu'on cherche la premiere position >= target :

```go
func LowerBound(nums []int, target int) int {
    lo, hi := 0, len(nums)  // hi = len, pas len-1
    for lo < hi {            // pas <=
        mid := lo + (hi-lo)/2
        if nums[mid] < target {
            lo = mid + 1
        } else {
            hi = mid  // pas mid-1
        }
    }
    return lo  // premiere position ou nums[lo] >= target
}
```

**Difference cle** : `hi = len(nums)` (pas `len-1`), `lo < hi` (pas `<=`), et `hi = mid` (pas `mid-1`). C'est le template `sort.Search` de Go.

### Variante : Upper Bound (premiere position > target)

```go
func UpperBound(nums []int, target int) int {
    lo, hi := 0, len(nums)
    for lo < hi {
        mid := lo + (hi-lo)/2
        if nums[mid] <= target {  // <= au lieu de <
            lo = mid + 1
        } else {
            hi = mid
        }
    }
    return lo
}
```

### Go standard library

`sort.Search(n, func(i int) bool)` est le lower bound generique : il retourne le plus petit `i` dans `[0, n)` tel que `f(i)` est vrai.

```go
i := sort.Search(len(nums), func(i int) bool { return nums[i] >= target })
```

### Search on the answer (recherche sur la reponse)

Quand le probleme demande "le minimum/maximum X tel que condition", binary search sur X :

```go
lo, hi := minPossible, maxPossible
for lo < hi {
    mid := lo + (hi-lo)/2
    if condition(mid) {
        hi = mid      // cherche plus petit
    } else {
        lo = mid + 1
    }
}
// lo = reponse
```

### Tableau tourne (rotated sorted array)

Un tableau trie puis decale : `[4,5,6,7,0,1,2]`. La moitie gauche ou droite est toujours triee.

```
Si nums[lo] <= nums[mid] → la moitie gauche est triee
    Si target est dans [nums[lo], nums[mid]] → hi = mid - 1
    Sinon → lo = mid + 1
Sinon → la moitie droite est triee
    Si target est dans [nums[mid], nums[hi]] → lo = mid + 1
    Sinon → hi = mid - 1
```

### Complexites

| Algo | Temps | Espace |
|------|-------|--------|
| Binary search classique | O(log n) | O(1) |
| Lower/Upper bound | O(log n) | O(1) |
| Rotated array search | O(log n) | O(1) |
| Search on answer | O(log(range) * check) | O(1) |

---

## Exercices — ordre de priorite

### Priorite haute (entretien Arista)

| # | Nom | Description | Cible |
|---|-----|-------------|-------|
| 1 | BinarySearch | Recherche classique dans un tableau trie | 3 min |
| 2 | SearchInsertPosition | Trouver l'index d'insertion (= lower bound) | 4 min |
| 3 | SearchRotatedArray | Chercher dans un tableau trie puis tourne | 8 min |
| 4 | Sqrt | Racine carree entiere sans math.Sqrt | 5 min |
| 5 | MissingNumber | Trouver le nombre manquant dans [0..n] | 5 min |

### Priorite moyenne

| # | Nom | Description | Cible |
|---|-----|-------------|-------|
| 6 | FirstLastPosition | Premier et dernier index d'un element | 6 min |
| 7 | PeakElement | Trouver un pic dans un tableau non trie | 6 min |
| 8 | MinRotatedArray | Minimum dans un tableau tourne | 5 min |

---

## Prototypes

```go
// Exo 1 : Chercher target dans nums trie. Retourne l'index ou -1.
func BinarySearch(nums []int, target int) int {
    // a toi
}

// Exo 2 : Index ou target serait insere dans nums trie. (LeetCode 35)
func SearchInsertPosition(nums []int, target int) int {
    // a toi
}

// Exo 3 : Chercher target dans un tableau trie puis tourne. Retourne l'index ou -1.
// Ex: nums = [4,5,6,7,0,1,2], target = 0 → 4
func SearchRotatedArray(nums []int, target int) int {
    // a toi
}

// Exo 4 : Racine carree entiere de x (arrondie vers le bas). Sans math.Sqrt.
func Sqrt(x int) int {
    // a toi
}

// Exo 5 : Tableau de n entiers distincts dans [0, n]. Trouver celui qui manque.
// Ex: [3,0,1] → 2
func MissingNumber(nums []int) int {
    // a toi
}

// Exo 6 : Premier et dernier index de target dans nums trie. [-1,-1] si absent.
func FirstLastPosition(nums []int, target int) [2]int {
    // a toi
}

// Exo 7 : Trouver un index i tel que nums[i] > nums[i-1] et nums[i] > nums[i+1].
func PeakElement(nums []int) int {
    // a toi
}

// Exo 8 : Minimum dans un tableau trie tourne sans doublons.
func MinRotatedArray(nums []int) int {
    // a toi
}
```
