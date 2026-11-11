## Fiche cours : Opérateurs de bits

Reprise de ta fiche théorie (section 2 de tes fiches) avec le rappel des points clés.

### Les opérateurs, sur x = 1100 et y = 1010

| Opérateur | Nom                 | Résultat       | Règle                          |
| --------- | ------------------- | -------------- | ------------------------------ |
| `x & y`   | ET                  | `1000`         | 1 si les deux sont à 1         |
| `x \| y`  | OU                  | `1110`         | 1 si au moins un est à 1       |
| `x ^ y`   | XOR                 | `0110`         | 1 si différents                |
| `x &^ y`  | AND NOT (bit clear) | `0100`         | garde x, efface là où y vaut 1 |
| `^x`      | NOT (unaire)        | `...0011`      | inverse tout (en C : `~x`)     |
| `x << k`  | shift gauche        | `110000` (k=2) | multiplie par 2^k              |
| `x >> k`  | shift droit         | `0011` (k=2)   | divise par 2^k (non signé)     |

### Les trois motifs à connaître par cœur

```go
mask := uint32(1) << k

isSet := x&mask != 0        // tester le bit k
x |= mask                   // set le bit k
x &^= mask                  // clear le bit k (en C : x &= ~mask)
x ^= mask                   // toggle le bit k
```

Piège : `x & k` teste les bits **de la valeur k**, pas le bit numéro k. Il faut `1 << k`.

### Les deux astuces sur le bit de poids faible

- `x & (x - 1)` **efface** le lowest set bit.
- `x & -x` **isole** le lowest set bit. (`-x = ^x + 1` en complément à 2.)

```
x       = 0110 1000
x - 1   = 0110 0111
x&(x-1) = 0110 0000   ← bit effacé
x & -x  = 0000 1000   ← bit isolé
```

Applications :
```go
// Popcount : autant de tours que de bits à 1
func popcount(x uint32) int {
    n := 0
    for x != 0 { x &= x - 1; n++ }
    return n
}

// Puissance de 2 : un seul bit à 1
func isPow2(x uint64) bool { return x != 0 && x&(x-1) == 0 }
```

### Champs de registre (quotidien Arista)

Pour un champ de `width` bits à partir du bit `lo` :

```go
mask := uint32(1)<<width - 1         // width bits à 1

field := x >> lo & mask              // lire

x = x &^ (mask << lo) | (v & mask) << lo   // écrire
```

### Octets et endianness

- **Big endian** (réseau) : octet de poids fort en premier.
- **Little endian** (x86) : poids faible en premier.
- **Convertir avant de décaler** : `uint32(b[0])<<24`, jamais `uint32(b[0]<<24)`.

```go
v := uint32(b[0])<<24 | uint32(b[1])<<16 | uint32(b[2])<<8 | uint32(b[3])
```

### Priorité Go vs C

En Go, `<<`, `>>`, `&`, `&^` ont la priorité de `*`. Donc `x&mask != 0` se lit `(x&mask) != 0`. En C, c'est l'inverse. Parenthèses dès que tu doutes.

### Signés et débordement

- Non signés bouclent : `uint8(200) + uint8(100) == 44`.
- `>>` sur un signé négatif recopie le bit de signe (arithmetic shift).
- Sign extend : `int32(x << shift) >> shift` propage le bit de signe.

---
