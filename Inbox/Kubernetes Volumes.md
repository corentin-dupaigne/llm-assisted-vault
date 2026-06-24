> [!abstract] TL;DR
> A volume grafts a filesystem onto a container's directory tree at a `mountPath`. The container writes to a normal-looking path; the kernel transparently redirects those writes to the volume's real backing store. **What** the storage is = `volumes` (Pod level). **Where** it's plugged in = `volumeMounts` (container level). The shared `name` is the cable connecting the two.

## The two-field model

Every volume is declared once and mounted wherever needed.

| Field          | Level          | Answers                    | Example                                          |
| -------------- | -------------- | -------------------------- | ------------------------------------------------ |
| `volumes`      | Pod            | *"What is the storage?"*   | `emptyDir`, `persistentVolumeClaim`, `configMap` |
| `volumeMounts` | each container | *"Where do I plug it in?"* | `mountPath: /var/log`                            |

The `name` in `volumeMounts` must match the `name` in `volumes` **exactly**. A typo here is the classic silent failure: the Pod starts but the sharing doesn't work.


> [!warning] Common misconception
> A **symlink** is a file containing a *path* to another file — indirection at the path level, visible to the program (`ls -l` shows `-> target`).
> A **mount** is the kernel superimposing an *entire filesystem* over a directory — indirection at the mount-point level, **invisible** to the program. The container writes to `/var/log/x.log` believing it's local disk; it has no way to know it's redirected.

## emptyDir

The name is literal: **a directory that starts empty**. The name describes its *initial state*, not its location or technology. Kubernetes creates it blank at Pod start; containers fill it.

- Backed by the **node's** disk (under `/var/lib/kubelet/pods/<uid>/volumes/...`), or RAM with `medium: Memory`.
- Lifecycle tied to the **Pod**, not the container:
  - Container crashes/restarts → volume **survives**, files still there.
  - Pod deleted or rescheduled to another node → volume **erased**.
- Containers in a Pod share it because a Pod never spans nodes.

> [!tip] CKA triage reflex
> The implicit question in every volume task: *does the data need to survive the Pod or be shared across Pods?*
> - **Yes** → [[PersistentVolumes\|PVC]]
> - **No** (scratch, or sharing between containers of one Pod) → `emptyDir`

## Volume types at a glance

The name of each type tells you what's inside at the start / where the data comes from:

- `emptyDir` — starts empty, containers fill it.
- `configMap` / `secret` — pre-filled from the API object, read-only.
- `hostPath` — points at an **existing** path on the node (lives beyond the Pod, but pinned to that node).
- `persistentVolumeClaim` — durable storage **external to the node** (cloud disk, NFS, Ceph). Survives Pod death *and* reschedule.

## Pattern: sidecar logging

The canonical multi-container use case. One container produces, the other consumes, via a shared `emptyDir`.

```
┌─────────────────── Pod ───────────────────┐
│  wordpress (main)           sidecar        │
│  echo >> wordpress.log      tail -f / read │
│       │ writes                   ▲ reads   │
│       ▼                          │         │
│   /var/log ──────────────────► /var/log    │
│         (same emptyDir volume)             │
└────────────────────────────────────────────┘
```

```yaml
spec:
  containers:
  - name: wordpress
    image: wordpress:php8.2-apache
    command: ["/bin/sh", "-c", "while true; do echo 'WordPress is running...' >> /var/log/wordpress.log; sleep 5; done"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log          # writes here
  - name: sidecar
    image: busybox
    command: ["/bin/sh", "-c", "tail -f /var/log/wordpress.log"]
    volumeMounts:
    - name: shared-logs
      mountPath: /var/log          # reads here — same volume, same path
  volumes:
  - name: shared-logs
    emptyDir: {}
```

> [!note] Read vs write
> A `volumeMount` is read-write by default. You *can* add `readOnly: true` to the consumer to reflect its role — but **only if the task asks for it**. At the CKA, adding unrequested fields earns no points and risks failing an exact-spec check. Do exactly what's written.

> [!info] Modern sidecars (1.28+)
> There's now a real "sidecar" API: an `initContainer` with `restartPolicy: Always`, fixing startup/shutdown ordering. For the CKA and this exercise, "sidecar" just means "a second ordinary container in `spec.containers`."
