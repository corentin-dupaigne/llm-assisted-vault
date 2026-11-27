---
project: projet-recherche
domain: computer-vision
tags: [3d-reconstruction, robotics]
date: 2026-11-27
para: Projects
---
### 1. Objectif

Comparer des méthodes open source de Gaussian Splatting sur deux critères :

- **la qualité visuelle** : est-ce que le rendu ressemble aux vraies photos ?
- **la précision géométrique** : est-ce que la reconstruction est fidèle aux dimensions réelles, mesurée en centimètres par rapport à un scan laser ?

Le second critère est le plus important pour le projet, puisque le client a besoin d'une salle fidèle à la réalité.

### 2. Outils

- **NerfBaselines** lance les implémentations officielles de chaque méthode avec un protocole d'évaluation identique : mêmes images de test, même calcul des métriques. Il fournit PSNR, SSIM, LPIPS, le temps d'entraînement et la VRAM.
- **Sa limite** : il ne mesure que la qualité d'image, pas la géométrie. On a donc ajouté notre propre pipeline d'évaluation géométrique.

### 3. Données : ETH3D

- C'est un dataset public avec des photos reflex et un **scan laser de référence** (Faro, précision millimétrique), avec des poses de caméra déjà alignées sur le scan en mètres. Il n'y a donc aucun recalage à faire.
- 3 scènes intérieures : *office* (26 photos), *delivery_area* (44) et *terrains* (42). *terrains* contient des panneaux texturés sur des murs blancs, proche de l'idée des posters sur les murs.
- La version vidéo d'ETH3D a été écartée : elle est en niveaux de gris et en fisheye.

### 4. Protocole

- Images réduites d'un facteur 4 (environ 1550 px), à cause de la carte graphique (RTX 3070, 8 Go). La résolution est **identique pour toutes les méthodes**.
- Découpage fixe : 1 image sur 8 réservée au test, identique pour toutes les méthodes.
- **Géométrie** : on rend des cartes de profondeur depuis les caméras, on les fusionne en volume TSDF (voxels de 1 cm), puis on compare au scan laser avec l'outil officiel d'ETH3D. On obtient l'accuracy, la complétude et le F1 à 1, 2, 5, 10, 20 et 50 cm. La procédure est identique pour toutes les méthodes.

### 5. Validation du pipeline

On a vérifié que l'évaluation est fiable avant d'interpréter les chiffres :

- le scan laser seul, passé dans l'outil, donne **98,6 %** de F1 à 1 cm ;
- une profondeur parfaite, calculée à partir du scan et passée dans notre fusion, donne **97,2 %** ;
- l'échelle et le repère sont vérifiés : les points COLMAP sont à 1 cm du scan en médiane.

Un mauvais score mesure donc bien la méthode, pas un bug du pipeline.

### 6. Premiers résultats : 3DGS sur office

| PSNR test | SSIM | LPIPS | Temps | VRAM | F1 à 1 cm | F1 à 5 cm |
|---|---|---|---|---|---|---|
| 17,4 | 0,83 | 0,37 | 31 min | ≈ 3,8 Go | 2,8 % | 10,4 % |

**Interprétation**

- **Sur-apprentissage marqué** : le PSNR est d'environ 41,5 sur les images d'entraînement, mais seulement 17,4 sur les images de test. Avec 22 vues espacées et des murs sans texture, 3DGS reproduit les photos sans retrouver la vraie forme de la pièce.
- **Géométrie très mauvaise** : la profondeur rendue est presque toujours devant la vraie surface (environ 22 % trop courte), à cause d'artefacts semi-transparents flottants. Changer les paramètres de fusion ne modifie pas la conclusion.
- **Conséquence** : le 3DGS d'origine n'est pas adapté si la précision géométrique compte. Il faut des méthodes conçues pour la géométrie.

### 7. En cours

Le benchmark complet a été lancé pendant la nuit : **8 méthodes × 3 scènes**.

- Méthodes géométriques en priorité : **2DGS, PGSR, GOF** (d'après la littérature, PGSR est la plus précise, et elle compense aussi les variations d'exposition).
- Puis 3DGS-MCMC, Scaffold-GS, Mip-Splatting et gsplat.
- Résultats visuels à récupérer. La géométrie de ces méthodes sera calculée ensuite, à partir des modèles sauvegardés.

### 8. Points d'attention

- ETH3D a peu de vues par scène. Les métriques visuelles y mesurent surtout la robustesse avec peu d'images, ce qui n'est pas représentatif d'une capture vidéo. Elles seront plus parlantes sur notre propre capture.
- Seulement 4 à 6 images de test par scène : les petites différences de PSNR ne sont pas significatives.
- Avec 8 Go de VRAM, certaines méthodes (GOF, PGSR) risquent de ne pas tenir. Il faudrait alors une machine plus puissante, et pas une résolution réduite pour certaines méthodes seulement.

### 9. Prochaines étapes

1. Récupérer les résultats de la nuit et compléter l'évaluation géométrique pour chaque méthode.
1. Retenir les 2 ou 3 meilleures méthodes.
1. Les tester sur une **vraie capture vidéo de la salle**, avec des mesures au télémètre laser comme contrôle.

### 10. Questions pour les chercheurs

- Quelle **précision géométrique** est nécessaire pour la formation : 1 cm, 5 cm ?
- Leur **PC GPU** est-il disponible, et quelle carte a-t-il, pour les méthodes lourdes et la capture finale ?
- Est-il possible d'avoir un **accès à la salle** avec des mesures de référence (télémètre, voire un scan laser) ?

## Links

- [[Gaussian Splatting pipeline]]
- [[Pipeline]]
- [[overview]]
- [[Issues]]
- [[notes]]
- [[capture comparaison]]
