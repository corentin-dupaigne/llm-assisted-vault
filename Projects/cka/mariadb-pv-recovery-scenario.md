---
project: cka
para: Projects
domain: kubernetes
tags:
  - storage
  - devops
  - cka
date: 2026-06-12
---
> [!question] Scenario
> A user accidentally deleted the MariaDB Deployment in the `mariadb` namespace. The deployment was configured with persistent storage. Your responsibility is to re-establish the deployment while ensuring data is preserved by reusing the available PersistentVolume.

> [!todo] Task
> A PersistentVolume already exists and is **retained** for reuse. Only one PV exists.
>
> - Create a PVC named `mariadb` in the `mariadb` namespace: Access Mode `ReadWriteOnce`, Storage `250Mi`
> - Edit `~/mariadb-deploy.yaml` to use that PVC
> - Apply the updated Deployment
> - Ensure the Deployment is running and stable

______________________________________________________________________

## Solution

### 1. Inspect the existing PV first

You must read the PV's specs before writing the PVC — the PVC has to be *compatible* with them or it won't bind.

```bash
kubectl get pv
kubectl get pv mariadb-pv -o yaml
```

Key fields to read off:

| Field | Value (this task) | Why it matters |
|---|---|---|
| `storageClassName` | `standard` | PVC must match this **exactly** (case-sensitive) |
| `accessModes` | `ReadWriteOnce` | PVC's requested mode must be in this list |
| `capacity.storage` | `250Mi` | PV capacity must be **≥** PVC request |
| `volumeMode` | `Filesystem` | PVC must match exactly |
| `persistentVolumeReclaimPolicy` | `Retain` | data is preserved on PVC deletion |
| `status.phase` | `Available` | ready to bind — no stale `claimRef` to clear |

> [!info] If the PV were `Released` instead of `Available`
> A retained PV whose old PVC was deleted keeps a stale `claimRef` and shows `Released` — it will **not** bind to a new PVC until you clear it:
>
> ```bash
> kubectl patch pv mariadb-pv -p '{"spec":{"claimRef": null}}'
> ```
>
> Here the PV is already `Available`, so this step is **not needed**.

### 2. Create the PVC

Match every binding criterion to the PV — especially `storageClassName: standard` (the PV uses a **named class**, so do *not* omit the field or use `""`).

```yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: mariadb
  namespace: mariadb
spec:
  accessModes:
    - ReadWriteOnce
  volumeMode: Filesystem
  resources:
    requests:
      storage: 250Mi
  storageClassName: standard
```

```bash
kubectl apply -f mariadb-pvc.yaml
```

Confirm it bound to the right PV before continuing:

```bash
kubectl get pvc -n mariadb
# STATUS must be Bound, VOLUME must be mariadb-pv
```

> [!warning] If the PVC stays `Pending`
> The two usual culprits, in order:
>
> 1. `storageClassName` mismatch — `standard` vs `Standard` (case-sensitive), or accidentally omitted (k3s/default clusters inject the default class instead).
> 1. A `Released` PV with a stale `claimRef` (see callout above).

### 3. Wire the Deployment to the PVC

Edit `~/mariadb-deploy.yaml`. Add a `volumes` entry referencing the PVC and a matching `volumeMounts` in the container. MariaDB's data path is `/var/lib/mysql`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mariadb
  namespace: mariadb
spec:
  replicas: 1
  selector:
    matchLabels:
      app: mariadb
  template:
    metadata:
      labels:
        app: mariadb
    spec:
      containers:
        - name: mariadb
          image: mariadb:10.6
          env:
            - name: MYSQL_ROOT_PASSWORD
              value: rootpass
          volumeMounts:
            - name: mariadb-storage
              mountPath: /var/lib/mysql
      volumes:
        - name: mariadb-storage
          persistentVolumeClaim:
            claimName: mariadb
```

> [!note] Wiring checklist
>
> - `volumes[].name` (`mariadb-storage`) must equal `volumeMounts[].name`.
> - `claimName` must equal the PVC name (`mariadb`).
> - Deployment `metadata.namespace` must be `mariadb`.

### 4. Apply and verify

```bash
kubectl apply -f ~/mariadb-deploy.yaml
kubectl rollout status deployment/mariadb -n mariadb
kubectl get pods -n mariadb
```

**Success criteria:** pod is `Running`, `1/1 Ready`, and not restarting.

```bash
# Optional sanity checks
kubectl describe pod -n mariadb -l app=mariadb   # confirm volume mounted
kubectl logs -n mariadb -l app=mariadb           # confirm MariaDB started clean
```

______________________________________________________________________

## Key concepts

> [!abstract] Why this works
> This is **static binding** to a pre-existing PV, not dynamic provisioning. The PV and its underlying storage (`hostPath: /mnt/data/mariadb`) already exist; the StorageClass `standard` plays **no active role** — its name is only the label the PVC matches against. Reusing the retained PV is what preserves the old MariaDB data.

**PVC → PV binding criteria** (all must hold):

- **Access mode** — PV must *include* the mode the PVC requests (superset OK).
- **Capacity** — PV must be *≥* the PVC request (not exact; excess is wasted).
- **Storage class** — *exact* string match (`standard` = `standard`).
- **Volume mode** — *exact* match (`Filesystem` = `Filesystem`).

**Binding is one-to-one** — a PV binds to exactly one PVC; it is never shared or split between claims. Pod-level sharing (multiple pods on one PVC) is a separate axis governed by access modes (`RWX` / `RWO`).

**`storageClassName` traps:**

| PVC value | Behaviour |
|---|---|
| `standard` (named) | matches a PV labelled `standard`, or provisions via that class |
| *omitted* | default class injected (≠ no class) — **wrong here**, would miss the PV |
| `""` | no class, no default — binds only to a *classless* PV |

## Links

- [[kubernetes-persistent-volumes-pvc-storageclass|Pv, Pvc, Storageclass]]
- [[cka-prep-workflow-killercoda|Dumb It Guy Questions Setup]]
