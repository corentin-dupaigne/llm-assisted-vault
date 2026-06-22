# Design Document — Projet DevOps + AWS (Option A)

> Application support : **Pomodoro** (3-tiers). Le code applicatif n'est pas noté ;
> ce document décrit tout l'enrobage **AWS + DevOps** et **justifie chaque choix**
> au regard des critères de notation : *résilience, scalabilité, logique
> d'architecture, et moindre privilège sur les flux*.

---

## 1. Contexte & contraintes

| Élément           | Valeur                                                                                                      |
| ----------------- | ----------------------------------------------------------------------------------------------------------- |
| Application       | Pomodoro 3-tiers : `frontend` (Nginx + statique), `backend` (Flask/Gunicorn, **stateless**), `db` (MySQL 8) |
| Environnement AWS | **AWS Academy Learner Lab**                                                                                 |
| Région            | `us-east-1` (verrouillée par le lab)                                                                        |
| Équipe            | Solo (groupes de 1 autorisés), `terraform apply` depuis le laptop                                           |
| Dépôt             | GitLab.com (prof invité : `mbounaceur`)                                                                     |
| Rendu             | Dépôt + rapport mail (schémas, flux, justifications)                                                        |

### Contraintes Learner Lab (structurantes)
- **Création de rôles IAM interdite** (`iam:CreateRole` refusé) → on **réutilise**
  `LabRole` / `LabInstanceProfile` (data sources Terraform), jamais de création.
- **Credentials temporaires (~4 h)** → pas d'automatisation AWS fiable depuis la CI :
  le déploiement se fait **manuellement** avec les creds frais du lab.
- **Budget / quotas limités** → RDS Single-AZ, pas de NAT Gateway.

---

## 2. Application (rappel)

- **frontend** : HTML/CSS/JS vanilla servi par Nginx ; Nginx **reverse-proxy `/api/*`**
  vers le backend → une seule origine côté navigateur.
- **backend** : Flask + Gunicorn, **sans état**, expose `/api/health`, `/api/sessions`, `/api/stats`.
- **db** : MySQL 8, table unique `sessions`, schéma chargé via `init.sql`.

Le backend stateless se prête à l'autoscaling ; le modèle Nginx-proxy permet une
**chaîne de flux linéaire** (front → back → db) idéale pour le moindre privilège.

---

## 3. Architecture AWS cible

```
                         Internet
                            │  HTTP :80
                   ┌────────▼─────────┐
                   │       ALB        │   public subnets (AZ-a, AZ-b)
                   │  SG-ALB: 80 ◄ 0.0.0.0/0
                   └────────┬─────────┘
                            │  :80  (SG-front ◄ SG-ALB uniquement)
                   ┌────────▼─────────┐
                   │ EC2 frontend     │   mini-ASG (min=max=desired=1)
                   │ (Nginx + statique)│  public subnet
                   └────────┬─────────┘
                            │  :5000 (SG-back ◄ SG-front uniquement)
                   ┌────────▼─────────┐
                   │ EC2 backend      │   mini-ASG (min=max=desired=1)
                   │ (Flask/Gunicorn) │   public subnet
                   └────────┬─────────┘
                            │  :3306 (SG-db ◄ SG-back uniquement)
                   ┌────────▼─────────┐
                   │ RDS MySQL 8      │   PRIVATE subnets (AZ-a, AZ-b)
                   │ Single-AZ        │   non joignable depuis Internet
                   └──────────────────┘

  Administration : AWS SSM Session Manager (aucun port 22 ouvert)
  Egress EC2     : Internet Gateway (pas de NAT)
  Secrets        : SSM Parameter Store (SecureString)
  Images         : Amazon ECR
  Observabilité  : Amazon CloudWatch (métriques, logs, alarmes → SNS)
```

### 3.1 Réseau (VPC)
- 1 VPC, **2 zones de disponibilité** (AZ-a, AZ-b) → couvre le minimum imposé.
- **Subnets publics** (2 AZ) : ALB + EC2 frontend/backend.
- **Subnets privés** (2 AZ) : RDS uniquement.
- **Internet Gateway** pour l'egress des EC2 (pull ECR, paquets, SSM, CloudWatch).
- **Pas de NAT Gateway** : choix budget (Learner Lab). Compensé par des SG verrouillés.

### 3.2 Compute
- **EC2 dans des mini-ASG** (`min=max=desired=1`) pour frontend et backend.
  - Bénéfice : **auto-recovery** si l'instance meurt + narrative *scalable*
    (monter `max` suffit).
- **mini-ASG derrière l'ALB** via un Target Group + health checks.

### 3.3 Données
- **RDS MySQL 8 Single-AZ** en subnets privés.
- **Multi-AZ documenté en future-work** (bascule d'une ligne Terraform).

---

## 4. Flux & moindre privilège (critère noté ★)

### 4.1 Security Groups en cascade
Chaque tier n'accepte **que le SG du tier au-dessus** — **aucun CIDR ouvert** entre tiers.

| SG         | Inbound autorisé | Source      | Justification                                        |
| ---------- | ---------------- | ----------- | ---------------------------------------------------- |
| `SG-ALB`   | TCP 80           | `0.0.0.0/0` | Seul point d'entrée public                           |
| `SG-front` | TCP 80           | `SG-ALB`    | Front joignable uniquement par l'ALB                 |
| `SG-back`  | TCP 5000         | `SG-front`  | Back joignable uniquement par le front (Nginx-proxy) |
| `SG-db`    | TCP 3306         | `SG-back`   | DB joignable uniquement par le backend               |

- **Aucun inbound SSH (22)** sur aucun SG.
- **Egress** : restreint au nécessaire (HTTPS sortant pour ECR/SSM/updates).

### 4.2 Administration sans SSH
- Accès shell via **SSM Session Manager** (l'agent SSM + l'instance profile suffisent).
- Conséquence : **0 port 22 exposé**, pas de bastion, pas de clé SSH à gérer.

### 4.3 RDS privée
- RDS en subnets **privés**, **pas d'IP publique**, `publicly_accessible = false`.
- → la base est **structurellement injoignable depuis Internet** (argument le plus fort).

### 4.4 IAM
- **Contrainte lab** : on réutilise `LabRole` / `LabInstanceProfile` (création interdite).
- L'instance profile fournit aux EC2 : SSM, pull ECR, push logs/métriques CloudWatch,
  lecture des paramètres SSM.
- Le moindre privilège côté projet repose donc **principalement sur les Security Groups**
  (l'IAM fin n'est pas modifiable dans le lab — assumé et expliqué).

---

## 5. Secrets
- Credentials RDS stockés dans **SSM Parameter Store** en `SecureString`.
- Injectés dans les conteneurs au déploiement (Ansible lit SSM via l'instance profile).
- **Plus aucun mot de passe en clair** (contrairement au `docker-compose` de dev).

---

## 6. Observabilité — CloudWatch (décision : pas de Prometheus/Grafana)

> Prometheus/Grafana écarté : sans dashboards custom, il fait doublon avec CloudWatch
> et ajoute une EC2 + des exporters à maintenir, pour un gain quasi nul vu la deadline.

| Besoin                | Mise en œuvre CloudWatch                                            |
| --------------------- | ------------------------------------------------------------------- |
| Métriques système EC2 | CloudWatch agent (CPU, mém, disque)                                 |
| Métriques conteneurs  | **Container Insights**                                              |
| Logs des 3 conteneurs | CloudWatch Logs (+ **Logs Insights** pour les requêtes)             |
| Métriques managées    | ALB (5xx, latence, hôtes unhealthy), RDS (CPU, connexions, storage) |
| Dashboard             | 1 dashboard unique ALB / EC2 / RDS                                  |
| Alertes               | **Alarmes → SNS** (ALB 5xx, RDS storage/CPU, host unhealthy)        |
| Résilience            | **EC2 auto-recovery alarm**                                         |

---

## 7. Chaîne DevOps

### 7.1 Infrastructure as Code — Terraform
- **State local** (solo, apply depuis le laptop).
- Modules : `network` (VPC/subnets/IGW/routes/SG), `data` (RDS + SSM params),
  `compute` (ASG + Launch Template + ALB + Target Group), `ecr`, `observability`
  (CloudWatch dashboard/alarms/SNS).
- IAM **référencé** (data sources `LabRole` / `LabInstanceProfile`), jamais créé.
- Provider figé sur `us-east-1`.

### 7.2 Gestion de configuration — Ansible
- Inventaire **dynamique** `aws_ec2`.
- Connexion **via SSM** (plugin de connexion AWS SSM) → cohérent avec le « 0 SSH ».
- Rôles : hardening de base, install Docker, `docker login` ECR, pull image,
  run conteneur, injection des secrets depuis SSM.

### 7.3 CI/CD — GitLab CI
Répartition imposée par les creds temporaires du Learner Lab :

| Phase              | Où                                           | Étapes                                               |
| ------------------ | -------------------------------------------- | ---------------------------------------------------- |
| Qualité & sécurité | **CI GitLab (sans AWS)**                     | `lint → test → security → build image → scan image`  |
| Déploiement (CD)   | **Laptop (creds lab frais)** ou job `manual` | `docker push ECR → terraform apply → ansible deploy` |

Pipeline CI (stages) :
1. **lint** — `hadolint` (Dockerfiles), formatage Python, `tfsec`/`checkov` (Terraform)
2. **test** — tests applicatifs (le cas échéant)
3. **security (DevSecOps)** — `gitleaks` (secrets), `semgrep` (SAST),
   `pip-audit`/`safety` (dépendances)
4. **build** — `docker build` des images front/back
5. **scan** — `trivy` (image + filesystem)
6. *(deploy : job `manual` ou hors-CI depuis le laptop)*

### 7.4 DevSecOps (bonus fortement encouragés)
- Secrets : **gitleaks**
- SAST : **semgrep**
- Dépendances : **pip-audit** / **safety**
- Images Docker : **trivy**
- IaC : **tfsec** / **checkov**
- Dockerfiles : **hadolint**
- **Rapports** publiés en **artefacts GitLab**.

---

## 8. Compromis assumés (à justifier dans le rapport)

| Compromis                     | Raison                                    | Compensation / future-work                              |
| ----------------------------- | ----------------------------------------- | ------------------------------------------------------- |
| EC2 en subnets **publics**    | Pas de NAT (budget Learner Lab)           | SG en cascade + SSM-only + 0 port 22 ; RDS reste privée |
| RDS **Single-AZ**             | Budget / quotas lab                       | Multi-AZ = 1 ligne Terraform à flipper                  |
| **HTTP** sur l'ALB            | Pas de domaine ; déploiement non imposé   | ACM + Route53 en future-work                            |
| IAM via **LabRole**           | Création de rôles interdite               | Moindre privilège porté par les SG ; expliqué           |
| **State Terraform local**     | Solo, apply laptop                        | S3 + DynamoDB si travail en équipe                      |
| **Pas de Prometheus/Grafana** | Doublon CloudWatch sans dashboards custom | CloudWatch couvre métriques/logs/alarmes                |

---

## 9. Cartographie sur les critères de notation

| Critère                    | Réponse dans le design                                                  |
| -------------------------- | ----------------------------------------------------------------------- |
| **Résilience**             | Multi-AZ réseau, mini-ASG auto-recovery, RDS managée + backups, alarmes |
| **Scalabilité**            | ASG (monter `max`), backend stateless, ALB                              |
| **Logique d'architecture** | 3-tiers mappé 1:1 sur l'infra, flux linéaire front→back→db              |
| **Moindre privilège**      | SG en cascade, 0 SSH, RDS privée, secrets SSM, aucun CIDR inter-tiers   |

---

## 10. Plan de construction

1. **Terraform `network`** — VPC, subnets 2 AZ (public/privé), IGW, routes, **SG chaînés**.
2. **Terraform `data`** — RDS Single-AZ + paramètres SSM (secrets).
3. **Terraform `compute`** — Launch Template + mini-ASG (front/back), ALB + Target Group,
   ECR, références `LabRole`/`LabInstanceProfile`.
4. **Terraform `observability`** — dashboard CloudWatch, alarmes, SNS.
5. **Ansible** — rôles install Docker / deploy conteneurs / secrets SSM (connexion SSM).
6. **GitLab CI** — pipeline qualité/sécurité + scans DevSecOps + build/scan image.
7. **Rapport** — schémas, captures, flux (moindre privilège), justifications.

---

*Document de conception — sera la base du rapport final.*
