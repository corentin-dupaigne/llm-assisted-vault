---
domain: mathematics
tags: [leetcode, study-plan, flashcards]
date: 2026-11-23
para: Resources
project: null
---
# Complexité de la recherche exhaustive (force brute)

> [!info] Pourquoi c'est important
> Cette question tombe dans **chaque annale** (2023, 2024, 2025, 2026). Elle sert à montrer que la méthode naïve est inutilisable, ce qui justifie la programmation dynamique.

**Recherche exhaustive** : essayer **toutes** les solutions possibles, une par une, puis garder la meilleure. Elle est toujours juste, mais très lente.

______________________________________________________________________

## Méthode 1 : compter les solutions candidates

*Mots-clés de l'énoncé : « recherche exhaustive », « tester toutes les combinaisons », « combien de façons de… ».*

1. **Identifier les décisions** qui définissent une solution. Exemple : pour chaque objet, le prendre ou non.
1. **Compter les choix** de chaque décision. Exemple : 2 (oui ou non).
1. **Faire le produit** : nombre de candidats = choix₁ × choix₂ × … × choixₖ.
   - k décisions binaires → **2ᵏ**
   - k décisions à d choix → **dᵏ**
1. **Multiplier par le coût de vérification** d'un candidat (souvent O(n)).

> [!example] Pourquoi 2ⁿ et pas n²
> Ajouter un élément **double** le nombre de sélections : chaque ancienne sélection existe « avec » et « sans » le nouvel élément.
> 1 objet → 2 ; 2 objets → 4 ; 3 objets → 8 ; on multiplie, on n'ajoute pas.

### Annales

| Problème | Décisions | Candidats |
|---|---|---|
| Sac à dos (2024) | n objets : pris ou non | 2ⁿ |
| Justification de paragraphe (2026) | n − 1 espaces : couper ou non | 2ⁿ⁻¹ |
| Partition en palindromes (2023) | n − 1 positions : couper ou non | 2ⁿ⁻¹ |
| Word Break (2025) | jusqu'à n mots, chacun parmi d | dⁿ (× n pour comparer avec s) |

______________________________________________________________________

## Méthode 2 : compter le coût de la récursion naïve

*Mots-clés de l'énoncé : « implémentation récursive (naïve) », « nombre de comparaisons effectuées ».*

1. Partir de la **récurrence donnée** par l'énoncé.
1. Écrire une récurrence sur le **coût** : coût(n) = Σ coût(sous-appels) + travail local.
1. **La calculer en Python** quand l'énoncé le permet (Python autorisé à l'examen).
1. Conclure sur la croissance : si chaque appel en relance plusieurs sur des tailles proches de n, elle est **exponentielle**.

```python
# Modèle : compter les opérations d'une récursion naïve
def cout(n):
    A = [0] * (n + 1)          # A[i] = coût pour une entrée de taille i
    for i in range(2, n + 1):
        A[i] = sum(A[k] + A[i - k] for k in range(1, i)) + i // 2  # sous-appels + travail local
    return A[n]
```

*Ce modèle reprend l'exemple de l'annale 2023 (#Cut, n = 10 → 7381 comparaisons). Adapte la ligne de récurrence au sujet.*

______________________________________________________________________

## Pièges

> [!warning] À ne pas confondre
>
> - **n × W** est la taille de la **table de programmation dynamique**, pas le nombre de candidats de la force brute.
> - La sélection **vide** compte toujours. On compte **avant** de vérifier la capacité.
> - Dans un QCM, choisis la borne **la plus restrictive** parmi celles qui sont correctes. En 2024, la réponse attendue était O(2ⁿ), parmi O(2ⁿ), O(n!) et O(n²).
> - Le facteur de vérification (× n) peut compter : en 2025, la réponse attendue était dⁿ × n, pas dⁿ.

## Méthode 1 ou 2 ?

| L'énoncé dit… | Méthode |
| ---------------------------------------------------------------------------- | -------------------------- |
| « recherche exhaustive », « toutes les combinaisons », « combien de façons » | 1 : compter les candidats |
| « implémentation récursive », « nombre de comparaisons » | 2 : récurrence sur le coût |

## Links

- [[Coding Interview Method]]
- [[Planning de revisions - Rattrapages Proba Stats]]
