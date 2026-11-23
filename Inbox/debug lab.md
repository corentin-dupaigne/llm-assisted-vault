# Labo debug — 1h, le minimum vital

Chaque dossier contient un programme bugué. Pour chacun :
1. lis le **symptôme** et l'**outil** imposé,
2. trouve **la ligne fautive** et **la cause** avec l'outil (pas en relisant le code au hasard),
3. corrige, recompile, vérifie.

Note pour chaque exercice : *outil utilisé → ce qu'il t'a dit → ta correction*. Envoie-moi tes notes à la fin.

---

## Antisèche des outils

```bash
# Compilation normale (comme l'exam)
g++ -Wall -Wextra -Werror -pedantic -std=c++20 -Wold-style-cast *.cc

# Sanitizers : à utiliser dès qu'un programme plante ou affiche des valeurs bizarres
g++ -std=c++20 -g -O0 -fsanitize=address,undefined *.cc && ./a.out
#   → lire le TYPE d'erreur (heap-use-after-free, heap-buffer-overflow, runtime error…)
#   → puis la première ligne "#N ... dans TON fichier.cc:LIGNE"

# gdb : compiler avec -g -O0, SANS sanitizers
g++ -std=c++20 -g -O0 *.cc && gdb ./a.out
```

| gdb | Effet |
|---|---|
| `r` | lancer |
| `bt` | où ça a planté (pile d'appels) |
| `f N` | se placer dans le niveau N de la pile |
| `p var` | afficher une variable (`p curr`, `p i`, `p *this`) |
| `info locals` | toutes les variables locales |
| `b fichier.cc:LIGNE` / `b Classe::methode` | point d'arrêt |
| `n` / `s` / `c` | ligne suivante / entrer dans la fonction / continuer |
| `catch throw` | s'arrêter quand une exception est lancée |
| `q` | quitter |

---

## Les exercices (~7 min chacun)

### ex1_compile — ne compile pas
- **Outil :** le compilateur seul.
- **Règle :** corrige **uniquement la première erreur**, recompile, recommence.
- **À noter :** combien de compilations il t'a fallu, et quelle était chaque cause.

### ex2_vector — « Best score » affiche n'importe quoi au lieu de 42
- **Outil :** sanitizers.
- **Question :** quel est le type d'erreur ? À quelle ligne la mémoire a-t-elle été libérée, et pourquoi ? (Indice : que fait un `vector` quand il grandit ?)

### ex3_bounds — affiche `10 | 20 | 30 | 40` alors que la capacité est 3
- **Outil :** sanitizers.
- **Question :** le programme ne plante pas sans sanitizer. Pourquoi est-ce quand même grave ? Quelle condition est fausse ?

### ex4_segfault — « Segmentation fault », et rien ne s'affiche
- **Outil :** gdb (`r`, `bt`, `p`).
- **Questions :** à quelle ligne ? Que valent `curr` et `i` au moment du crash ? Quel est le bug dans la boucle ?
- **Bonus :** pourquoi même la première ligne (« sum of first 2 ») ne s'affiche pas avant le crash ? Et que devrait-elle afficher (5 + 10 = 15) ?

### ex5_reverse — « Segmentation fault »
- **Outil :** sanitizers (lis bien le `runtime error` qui arrive *avant* le crash).
- **Question :** quel objet déclenche le crash ? Réécris le constructeur pour qu'il soit correct, y compris avec une liste vide.

### ex6_logic — « Average: 10 » au lieu de 13.25
- **Outil :** au choix : `std::cerr` temporaires, ou gdb avec `b average`, `n`, `p sum`.
- **Question :** il y a **deux** bugs. Lesquels ?

### ex7_exception — `terminate called … what(): map::at`
- **Outil :** gdb, `catch throw` puis `r` puis `bt`.
- **Question :** le message ne dit pas quel appel pose problème. Lequel est-ce (fonction, ligne, argument) ? Comment rendre `remove` robuste, avec un message clair ?

### ex8_leak — tout s'affiche correctement
- **Outil :** sanitizers (LeakSanitizer s'active automatiquement en fin de programme).
- **Question :** qu'est-ce qui fuit, et pourquoi ? Corrige-le de **deux façons** : avec un destructeur, puis (mieux) avec `std::unique_ptr` comme dans ta Queue.

---

## À retenir

| Symptôme | Premier réflexe |
|---|---|
| Ne compile pas | **Première** erreur seulement |
| Plante / valeur absurde | **Sanitizers** |
| Plante et les sanitizers ne suffisent pas | **gdb** : `r`, `bt`, `f N`, `p` |
| Exception non attrapée | **gdb** : `catch throw`, `r`, `bt` |
| Résultat faux sans plantage | `std::cerr` ou gdb `b` + `n` + `p` |
