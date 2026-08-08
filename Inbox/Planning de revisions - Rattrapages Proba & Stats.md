---
para: Projects
---
## Hypothèses

- **Deux examens** : Proba discrète (rattrapage **S7**) + Probabilités/Stats continues (rattrapage **S8**, **coefficient 2**).
- **Priorité** : on **boucle la proba discrète d'abord** (aucune intégration), puis on bascule sur la stat.
- **Objectif** : ~15/20 sur chacun. **Cadence** : 7 h/semaine sur 6 semaines (~42 h).
- **Principe** : comprendre le *pourquoi*, pas mémoriser des recettes.

**Légende** : « Vidéo » = conseillée uniquement si particulièrement utile · « Flashcards » = uniquement briques atomiques (formules, seuils, définitions).

**À confirmer** : la ou les dates exactes des rattrapages.
**Chaîne** : quasi toutes les vidéos ci-dessous viennent de la playlist *Statistics* de Professor Leonard → https://www.youtube.com/playlist?list=PL5102DFDC6790F3D0

---

# PHASE A — Proba discrète (sans calcul intégral, à boucler en premier)

### Bloc 1 — Proba conditionnelle & Bayes · ~5 h
- **Vidéo** : Leonard 4.4 « Multiplication Rule for And » → https://www.youtube.com/watch?v=05JCQswK3hE (si tu pars vraiment de zéro sur la notion de probabilité, 4.2 d'abord → https://www.youtube.com/watch?v=_EpXHuPnaK0). *Leonard couvre la conditionnelle, mais pas le Bayes « à l'envers » à la française → pour ça, l'arbre du corrigé.*
- **Flashcards — OUI** : P(A∩B) = P(A)·P(B|A) ; formule des probabilités totales.
- **Exos** : TD1 ex. 1 et 2 → Ex. 1 du partiel discret.

### Bloc 2 — Loi binomiale, E/V discrète & transformation aX+b · ~5 h
- **Vidéo** : Leonard 5.2 (distributions, moyenne, écart-type) → https://www.youtube.com/watch?v=WNgcmn5cXjI · 5.3 (binomiale) → https://www.youtube.com/watch?v=iGKSxMGX0Do · 5.4 (moyenne/écart-type binomiale) → https://www.youtube.com/watch?v=4Ew60JEPGUk. *La transformation aX+b n'est pas dans Leonard : c'est une règle courte, pas besoin de vidéo.*
- **Flashcards — OUI** : E = np, V = npq ; E(aX+b) = aE(X)+b ; V(aX+b) = a²V(X).
- **Exos** : TD1 ex. 7 ; TD2 ex. 11 → Ex. 2 du partiel discret.

### Bloc 3 — Couples de variables discrètes · ~5 h
- **Vidéo — aucune** : hors programme des stats US, Leonard ne le traite pas. → corrigé + TD, c'est la meilleure route.
- **Flashcards — léger** : indépendance ⟺ P(X=x, Y=y) = P(X=x)·P(Y=y) ; Cov = E(XY) − E(X)E(Y) *(cette carte covariance ressert au Bloc 8)*.
- **Exos** : TD2 ex. 13 et 14 → Ex. 3 du partiel discret.

### Bloc 4 — Blanc chronométré proba discrète · ~2 h
→ **Fin de Phase A : proba discrète bouclée.**

---

# PHASE B — Stats continues (nécessite l'intégration)

### Bloc 0 — Trousse intégration · ~8-10 h · à faire en premier dans cette phase
- **Vidéo — aucune** : une leçon de calcul intégral de 2 h serait un gâchis pour 6 schémas. → **moi**, pas-à-pas sur tes exos. (∫xⁿ, ∫1/x, ∫eˣ, bornes, une IPP ∫y·eʸ, l'intégrale double séparable.)
- **Flashcards — OUI** : les 6 primitives (recto = intégrale, verso = résultat).

### Bloc 5 — Loi normale + table · ~4 h · (sans calcul)
- **Vidéo** : Leonard 6.2 (intro normale + v.a. continues) → https://www.youtube.com/watch?v=shrTfDUB9Hk · 6.3 (normale centrée réduite, z-score) → https://www.youtube.com/watch?v=-Lj6SvaVGr4. **C'est le point fort de Leonard, fonce.**
- **Flashcards — OUI** : Φ(−z) = 1 − Φ(z) ; quantiles 90 % → 1,645 · 95 % → 1,96 · 99 % → 2,575.
- **Exos** : Ex. 2 du partiel stats.

### Bloc 6 — Variables à densité · ~6 h
- **Vidéo** : route principale = **cours écrit (résumé + excellence-maths) + moi**, car Leonard ne calcule pas E/V par intégrale. Vidéo optionnelle *plus rigoureuse* si le cours écrit ne suffit pas : MIT 6.041 Lecture 8, Continuous Random Variables (Tsitsiklis) → https://ocw.mit.edu/courses/6-041sc-probabilistic-systems-analysis-and-applied-probability-fall-2013/resources/lecture-8-video-1/ — excellent mais un cran au-dessus, à réserver.
- **Flashcards — OUI** : 3 conditions d'une densité ; E(X) = ∫ x·f(x) dx ; V = E(X²) − E(X)².
- **Exos** : refaire l'Ex. 1 du partiel stats sans le corrigé.

### Bloc 7 — Approximation binomiale → normale (Moivre-Laplace) · ~3 h
- **Vidéo** : Leonard 6.5 (TCL) → https://www.youtube.com/watch?v=JaVA-nXKVRI — **pour le pourquoi** (l'approximation, c'est le TCL appliqué à la binomiale). L'exo lui-même est court et mécanique.
- **Flashcards — OUI** : condition np ≥ 5 et n(1−p) ≥ 5 ; B(n,p) ≈ N(np, npq).
- **Exos** : Ex. 4 du partiel stats.

### Bloc 8 — Couples de variables continues · ~5 h
- **Vidéo — aucune** adaptée à ton niveau (contenu calculatoire hors stats US). → corrigé + moi.
- **Flashcards** : réutilise les cartes covariance/indépendance (version continue : indépendance ⟺ f(x,y) = f_X(x)·f_Y(y)).
- **Exos** : Ex. 3 du partiel stats.

### Bloc 9 — Convergences · ~6 h · le plus dur → vise le partiel, pas le sans-faute
- **Vidéo — aucune** vidéo d'intro à ton niveau. → article **Major Prépa** (écrit) + moi.
- **Flashcards — OUI** : Tchebychev P(|X−E(X)| ≥ ε) ≤ V(X)/ε² ; méthode conv. en loi = calculer F_n puis passer à la limite.
- **Exos** : Ex. 5 du partiel stats.

### Bloc 10 — Blanc chronométré stats · ~3 h
→ **Fin de Phase B : stats bouclée.**

---

## Semaine par semaine (~7 h/semaine)

| Semaine | Contenu                                     | Fin de semaine                             |
| ------- | ------------------------------------------- | ------------------------------------------ |
| **S1**  | Bloc 1 + Bloc 2                             | Gros des Ex. 1 et 2 du partiel discret     |
| **S2**  | Bloc 3 + Bloc 4 (**blanc proba**)           | Proba discrète bouclée                     |
| **S3**  | Bloc 0 (intégration) + Bloc 5 (normale)     | Tu sais intégrer + loi normale maîtrisée   |
| **S4**  | Bloc 6 (densités) + Bloc 7 (Moivre-Laplace) | Densités + capacity planning               |
| **S5**  | Bloc 8 (couples continus) + début Bloc 9    | Covariance continue, convergences entamées |
| **S6**  | Fin Bloc 9 + Bloc 10 (**blanc stats**)      | Stats bouclée                              |

---

## Récap flashcards (le deck complet)

Un petit deck, une carte = un concept, réponse d'une ligne. **Rien d'autre que ceci** — les méthodes et démonstrations ne vont PAS en cartes.

1. Les 6 primitives (Bloc 0)
2. P(A∩B) = P(A)·P(B|A) ; probabilités totales (Bloc 1)
3. E = np ; V = npq ; E(aX+b) = aE(X)+b ; V(aX+b) = a²V(X) (Bloc 2)
4. Cov = E(XY) − E(X)E(Y) ; indépendance (discret puis continu) (Blocs 3 & 8)
5. Φ(−z) = 1 − Φ(z) ; quantiles 1,645 / 1,96 / 2,575 (Bloc 5)
6. 3 conditions d'une densité ; E(X) = ∫x·f ; V = E(X²) − E(X)² (Bloc 6)
7. Condition np ≥ 5, n(1−p) ≥ 5 ; B(n,p) ≈ N(np, npq) (Bloc 7)
8. Tchebychev ; méthode convergence en loi (Bloc 9)

---

## Plan de repli (si une semaine saute)

**À ne JAMAIS couper** : Bloc 1, Bloc 2 (proba) ; Bloc 0, Bloc 5, Bloc 7 (stats).
**À sacrifier en dernier** : Bloc 9 (surtout la convergence en loi) et les sous-questions dures du Bloc 8.
