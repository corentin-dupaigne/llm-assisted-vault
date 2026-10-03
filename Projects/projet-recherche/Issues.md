## Labels

| Label             | Usage                                                       |
| ----------------- | ----------------------------------------------------------- |
| `research`        | Veille, état de l'art, comparaison d'outils                 |
| `experiment`      | Expérience avec hypothèse, protocole, métriques, conclusion |
| `infra`           | Machine, environnement, conteneurs                          |
| `dev`             | Développement du pipeline et de l'application               |
| `docs`            | Documentation, rapports, livrables écrits                   |
| `blocked:cadrage` | Dépend des réponses du client (étape 1)                     |

## Milestones

| Milestone          | Objectif                                                                            |
| ------------------ | ----------------------------------------------------------------------------------- |
| M2 – État de l'art | Comparer les solutions existantes et retenir 2–3 outils                             |
| M3 – Simulation    | Mesurer la qualité atteignable sur une pièce proxy, valider les pistes de captation |
| M4 – Application   | Construire le pipeline applicatif utilisable par le chercheur                       |
| M5 – Livraison     | Documenter, transmettre, soutenir                                                   |

---

# M2 – État de l'art

## #1 Définir la grille de critères de comparaison

**Labels :** `research` · **Milestone :** M2 – État de l'art

### Contexte
Toutes les fiches outils (#2 à #6) doivent être remplies avec les mêmes critères pour pouvoir être comparées.

### Tâches
- [ ] Lister les critères : qualité visuelle, robustesse aux murs blancs, robustesse aux reflets, matériel requis (GPU, VRAM), temps de traitement, formats d'export, facilité d'usage pour un non-spécialiste, licence, coût, maturité / maintenance du projet
- [ ] Définir une échelle de notation pour chaque critère
- [ ] Créer le template de fiche outil dans `docs/sota/_template.md`

### Definition of done
- Grille et template validés par tout le groupe

### Dépendances
Aucune — à faire en premier.

---

## #2 Recenser les solutions open source d'entraînement 3DGS

**Labels :** `research` · **Milestone :** M2 – État de l'art

### Contexte
Identifier les implémentations open source utilisables pour entraîner un splat à partir d'images.

### Tâches
- [ ] Étudier au minimum : nerfstudio (splatfacto), gsplat, dépôt original Inria
- [ ] Chercher d'autres implémentations récentes et maintenues
- [ ] Remplir une fiche par outil selon la grille #1

### Definition of done
- Une fiche par outil dans `docs/sota/`

### Dépendances
#1

---

## #3 Recenser les logiciels et services clé en main

**Labels :** `research` · **Milestone :** M2 – État de l'art

### Contexte
Des solutions commerciales ou gratuites existent et pourraient suffire au besoin du client.

### Tâches
- [ ] Étudier au minimum : Postshot, Polycam, Luma
- [ ] Chercher d'autres services (apps mobiles, services cloud)
- [ ] Vérifier pour chacun : où sont traitées les données (local / cloud), coût, limites de la version gratuite
- [ ] Remplir une fiche par outil selon la grille #1

### Definition of done
- Une fiche par outil dans `docs/sota/`

### Dépendances
#1

---

## #4 Recenser les méthodes d'estimation de poses robustes

**Labels :** `research` · **Milestone :** M2 – État de l'art

### Contexte
COLMAP échoue souvent sur des murs blancs sans texture. Des alternatives existent pour estimer les poses des caméras.

### Tâches
- [ ] Étudier au minimum : hloc (SuperPoint + LightGlue), GLOMAP, méthodes basées sur MASt3R
- [ ] Vérifier la compatibilité de leurs sorties avec les outils d'entraînement de #2
- [ ] Remplir une fiche par méthode selon la grille #1

### Definition of done
- Une fiche par méthode, avec un avis sur la facilité d'intégration

### Dépendances
#1

---

## #5 Recenser les approches pour reflets et surfaces sans texture

**Labels :** `research` · **Milestone :** M2 – État de l'art

### Contexte
Une salle d'opération contient beaucoup d'inox, de scialytiques et de murs lisses : des points faibles connus du 3DGS de base.

### Tâches
- [ ] Rechercher les variantes de 3DGS qui gèrent la spécularité et les reflets
- [ ] Rechercher les approches utilisant des priors de profondeur ou de normales
- [ ] Pour chaque méthode : code disponible ? maintenu ? matériel requis ?

### Definition of done
- Liste des méthodes avec disponibilité du code et niveau de maturité

### Dépendances
#1

---

## #6 Recenser les options d'affichage et d'export

**Labels :** `research`, `blocked:cadrage` · **Milestone :** M2 – État de l'art

### Contexte
Le choix du viewer dépend du support cible du client (casque VR, navigateur, écran).

### Tâches
- [ ] Recenser les viewers et plugins : Unity, Unreal, viewers web
- [ ] Recenser les formats de splat (`.ply`, `.splat`, `.ksplat`, `.spz`…) et leur compatibilité
- [ ] Évaluer les contraintes de performance selon le support cible

### Definition of done
- Tableau de compatibilité format × viewer × support

### Dépendances
#1, réponses du cadrage client

---

## #7 Vérifier les licences des outils présélectionnés

**Labels :** `research` · **Milestone :** M2 – État de l'art

### Contexte
L'outil sera réellement utilisé par un client. Certaines implémentations sont sous licence non commerciale.

### Tâches
- [ ] Relever la licence de chaque outil et de ses dépendances principales
- [ ] Préciser l'usage prévu par le client (recherche, usage interne, commercial)
- [ ] Signaler toute incompatibilité

### Definition of done
- Tableau outil / licence / usage autorisé dans `docs/sota/licences.md`

### Dépendances
#2, #3, #4

---

## #8 Synthèse de l'état de l'art et shortlist

**Labels :** `research` · **Milestone :** M2 – État de l'art

### Contexte
Point de décision : choisir les 2–3 outils à tester en simulation.

### Tâches
- [ ] Construire le tableau comparatif global à partir des fiches
- [ ] Retenir 2–3 outils avec justification
- [ ] Rédiger la décision sous forme d'ADR (`docs/adr/001-shortlist-outils.md`)
- [ ] Présenter la shortlist au client

### Definition of done
- ADR mergée et shortlist validée par le client

### Dépendances
#2 à #7

---

# M3 – Simulation

## #9 Installer le PC prêté

**Labels :** `infra` · **Milestone :** M3 – Simulation

### Contexte
Le laboratoire prête un PC avec GPU. Il doit être opérationnel avant toute expérience.

### Tâches
- [ ] Relever les caractéristiques (GPU, VRAM, OS, stockage)
- [ ] Installer les drivers NVIDIA, CUDA, Docker (+ NVIDIA Container Toolkit)
- [ ] Mettre en place un accès distant pour le groupe
- [ ] Lancer un entraînement de test sur un dataset public

### Definition of done
- Un entraînement de test aboutit et la procédure est documentée dans `docs/infra.md`

### Dépendances
Aucune — peut démarrer en parallèle de M2.

---

## #10 Choisir et préparer une pièce proxy

**Labels :** `experiment` · **Milestone :** M3 – Simulation

### Contexte
En attendant l'accès à une vraie salle, il faut une pièce qui reproduit ses difficultés.

### Tâches
- [ ] Identifier une pièce avec murs clairs et surfaces brillantes (salle de bain, labo, cuisine inox…)
- [ ] Organiser l'accès (créneaux, autorisations)
- [ ] Photographier la pièce pour documenter ses caractéristiques

### Definition of done
- Pièce identifiée et accès planifié

### Dépendances
Aucune

---

## #11 Rédiger le protocole de captation v1

**Labels :** `docs` · **Milestone :** M3 – Simulation

### Contexte
La qualité de la capture conditionne tout le reste du pipeline. Captation inside-out (depuis l'intérieur de la pièce).

### Tâches
- [ ] Définir : trajectoire, hauteurs de prise de vue, vitesse, recouvrement
- [ ] Définir les réglages : exposition et balance des blancs verrouillées, résolution, fréquence
- [ ] Rédiger une checklist utilisable sur le terrain

### Definition of done
- Protocole dans `docs/capture-protocol.md`, suivi pour la première capture

### Dépendances
#10

---

## #12 Script d'extraction des frames avec filtre anti-flou

**Labels :** `dev` · **Milestone :** M3 – Simulation

### Tâches
- [ ] Extraire les frames avec ffmpeg à une fréquence paramétrable
- [ ] Écarter les images floues (score de netteté, seuil paramétrable)
- [ ] Documenter les paramètres par défaut

### Definition of done
- Une commande unique, testée sur une vidéo réelle

### Dépendances
#9

---

## #13 Mettre en place l'évaluation quantitative

**Labels :** `dev` · **Milestone :** M3 – Simulation

### Contexte
Sans métriques, la comparaison des outils ne repose que sur des impressions.

### Tâches
- [ ] Mettre de côté des vues de test (ex. 1 image sur 8), jamais utilisées à l'entraînement
- [ ] Calculer PSNR, SSIM, LPIPS sur ces vues
- [ ] Relever aussi temps d'entraînement, VRAM max, taille du fichier
- [ ] Générer un rapport (CSV + images côte à côte rendu / réalité)

### Definition of done
- Script qui produit le rapport pour n'importe quel outil de la shortlist

### Dépendances
#9

---

## #14 Benchmark des outils de la shortlist

**Labels :** `experiment` · **Milestone :** M3 – Simulation

### Hypothèse
À compléter selon la shortlist (#8).

### Protocole
- [ ] Même capture, mêmes images, mêmes vues de test pour tous les outils
- [ ] Faire tourner chaque outil avec ses paramètres par défaut, puis avec un réglage optimisé
- [ ] Évaluer avec le script #13

### Definition of done
- Tableau de résultats + captures visuelles + conclusion écrite

### Dépendances
#8, #11, #12, #13

---

## #15 Expérience marqueurs : avec vs sans posters/stickers

**Labels :** `experiment` · **Milestone :** M3 – Simulation

### Hypothèse
Ajouter de la texture sur les murs améliore l'estimation des poses et la qualité du rendu.

### Protocole
- [ ] Capturer la pièce sans marqueurs, puis avec marqueurs, avec le même protocole
- [ ] Tester plusieurs variantes : posters, stickers, marqueurs discrets (sol, plafond, coins)
- [ ] Mesurer : nombre d'images recalées par COLMAP, métriques #13
- [ ] Évaluer la visibilité des marqueurs dans le rendu final

### Definition of done
- Résultats chiffrés + recommandation, en tenant compte de l'impact visuel pour la formation

### Dépendances
#11, #13, #14

---

## #16 Expérience captation : rotation au centre vs grille de stations

**Labels :** `experiment` · **Milestone :** M3 – Simulation

### Hypothèse
Une rotation depuis un point fixe ne fournit pas assez de parallaxe ; plusieurs positions et hauteurs sont nécessaires.

### Protocole
- [ ] Capture A : trépied au centre, rotation complète
- [ ] Capture B : plusieurs stations réparties dans la pièce
- [ ] Capture C : plusieurs stations × plusieurs hauteurs
- [ ] Mesurer : réussite de COLMAP, métriques #13, zones non couvertes

### Definition of done
- Conclusion sur la faisabilité du robot trépied et le schéma de captation minimal

### Dépendances
#11, #13

---

## #17 Rapport de simulation et présentation au client

**Labels :** `docs` · **Milestone :** M3 – Simulation

### Contexte
Point de décision : valider avec le client l'outil retenu et le protocole de captation avant de construire l'application.

### Tâches
- [ ] Synthétiser #14, #15, #16
- [ ] Comparer la qualité atteinte au résultat attendu par le client
- [ ] Préparer une démo visuelle
- [ ] Présenter au client et consigner sa décision

### Definition of done
- Décision go/no-go et choix d'outil validés par le client, consignés dans une ADR

### Dépendances
#14, #15, #16

---

# M4 – Application

## #18 Architecture du pipeline

**Labels :** `dev` · **Milestone :** M4 – Application

### Tâches
- [ ] Définir les étapes, leurs entrées/sorties et formats
- [ ] Définir où tourne chaque étape (PC du chercheur, PC prêté…)
- [ ] Définir la structure des dossiers de travail
- [ ] Rédiger l'ADR `docs/adr/00X-architecture-pipeline.md`

### Definition of done
- ADR validée par le groupe

### Dépendances
#17

---

## #19 Conteneuriser l'outil retenu

**Labels :** `infra` · **Milestone :** M4 – Application

### Tâches
- [ ] Écrire le Dockerfile avec versions épinglées (CUDA, PyTorch, outil)
- [ ] Vérifier le fonctionnement sur le PC prêté
- [ ] Documenter la construction et l'exécution

### Definition of done
- Image reproductible : un membre du groupe la reconstruit et l'exécute sans aide

### Dépendances
#18

---

## #20 CLI d'orchestration vidéo → splat → export

**Labels :** `dev` · **Milestone :** M4 – Application

### Tâches
- [ ] Enchaîner : extraction (#12), poses, entraînement, évaluation (#13), post-traitement (#21), export
- [ ] Gérer les paramètres via un fichier de config
- [ ] Permettre de relancer à partir d'une étape
- [ ] Journaliser chaque exécution

### Definition of done
- Une commande unique produit un splat exporté à partir d'une vidéo

### Dépendances
#18, #19

---

## #21 Post-traitement : nettoyage et compression

**Labels :** `dev` · **Milestone :** M4 – Application

### Tâches
- [ ] Supprimer les floaters et les gaussiennes hors de la pièce
- [ ] Compresser (élagage, degré de SH réduit, format compressé)
- [ ] Mesurer taille et qualité avant/après

### Definition of done
- Gain de taille mesuré avec perte de qualité documentée

### Dépendances
#18

---

## #22 Détection des échecs et messages d'erreur clairs

**Labels :** `dev` · **Milestone :** M4 – Application

### Contexte
Le chercheur n'est pas spécialiste : un échec doit être compréhensible et actionnable.

### Tâches
- [ ] Détecter les cas d'échec courants (peu d'images recalées, vidéo trop floue, VRAM insuffisante)
- [ ] Afficher un message clair avec l'action à faire (ex. « refaire la capture en suivant le protocole »)

### Definition of done
- Chaque cas d'échec identifié produit un message explicite

### Dépendances
#20

---

## #23 Intégration du viewer cible

**Labels :** `dev`, `blocked:cadrage` · **Milestone :** M4 – Application

### Tâches
- [ ] Intégrer le splat dans le viewer retenu (#6)
- [ ] Atteindre le framerate cible sur le support du client
- [ ] Ajouter un mesh de collision si une interaction est requise

### Definition of done
- Splat affiché de façon fluide sur le support du client

### Dépendances
#6, #21, réponses du cadrage client

---

## #24 Interface ou procédure pour le chercheur

**Labels :** `dev`, `blocked:cadrage` · **Milestone :** M4 – Application

### Tâches
- [ ] Définir avec le client le mode d'utilisation (CLI simple, script, interface graphique)
- [ ] Implémenter la solution retenue
- [ ] Tester avec une personne extérieure au groupe

### Definition of done
- Le chercheur lance le pipeline sans aide

### Dépendances
#20, réponses du cadrage client

---

## #25 Spécification du schéma de captation du robot

**Labels :** `docs`, `blocked:cadrage` · **Milestone :** M4 – Application

### Tâches
- [ ] À partir des résultats de #16, définir positions, hauteurs, vitesse et nombre d'images
- [ ] Préciser les contraintes matérielles du robot
- [ ] Valider avec le client

### Definition of done
- Spécification validée dans `docs/robot-capture-spec.md`

### Dépendances
#16, réponses du cadrage client

---

## #26 Test de bout en bout sur une capture neuve

**Labels :** `experiment` · **Milestone :** M4 – Application

### Protocole
- [ ] Réaliser une nouvelle capture en suivant uniquement la documentation
- [ ] Faire tourner le pipeline complet sans intervention manuelle
- [ ] Comparer le résultat aux attentes du client

### Definition of done
- Résultat conforme, ou liste des écarts transformés en issues

### Dépendances
#20 à #24

---

# M5 – Livraison

## #27 Documentation utilisateur

**Labels :** `docs` · **Milestone :** M5 – Livraison

### Tâches
- [ ] Protocole de captation final
- [ ] Guide d'utilisation du pipeline
- [ ] FAQ des erreurs courantes

### Definition of done
- Relue et testée par quelqu'un qui n'a pas codé le pipeline

### Dépendances
#26

---

## #28 Documentation technique / README

**Labels :** `docs` · **Milestone :** M5 – Livraison

### Tâches
- [ ] Installation from scratch
- [ ] Architecture et choix techniques (lien vers les ADR)
- [ ] Limites connues et pistes d'amélioration

### Definition of done
- Un autre membre du groupe installe le projet from scratch en suivant uniquement le README

### Dépendances
#26

---

## #29 Session de passation avec le chercheur

**Labels :** `docs` · **Milestone :** M5 – Livraison

### Tâches
- [ ] Planifier la session
- [ ] Faire réaliser au chercheur une capture et un traitement complets
- [ ] Recueillir ses retours et les consigner

### Definition of done
- Le chercheur produit un splat seul

### Dépendances
#27, #28

---

## #30 Rapport final

**Labels :** `docs` · **Milestone :** M5 – Livraison

### Tâches
- [ ] Rédiger le plan
- [ ] Intégrer l'état de l'art (#8), les expériences (#14, #15, #16) et l'architecture (#18)
- [ ] Relecture croisée

### Definition of done
- Rapport rendu

### Dépendances
#29

---

## #31 Soutenance et vidéo de démo de secours

**Labels :** `docs` · **Milestone :** M5 – Livraison

### Tâches
- [ ] Préparer les slides
- [ ] Préparer la démo live
- [ ] Enregistrer une vidéo de démo de secours
- [ ] Faire une répétition complète

### Definition of done
- Soutenance réalisée

### Dépendances
#30