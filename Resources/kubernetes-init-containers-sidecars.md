---
domain: kubernetes
tags:
  - kubernetes
  - cka
  - pods
  - init-containers
  - sidecar
created: 2026-06-16
para: Resources
date: 2026-06-16
project: null
---
# Init Containers & Sidecars

> [!abstract] Core idea
> A container's lifetime = its **PID 1's lifetime**. The only thing that distinguishes init, sidecar, and app containers is **when** they start and **whether the pod waits** for them.

## Init containers

Setup containers in the initContainers list that run before the app containers. They run one at a time, in list order, and each must exit successfully before the next begins. The app containers only start once all of them have succeeded, so they act as a gate on pod startup.
They share the pod's volumes and network namespace with the app containers. That means an init container can prepare an emptyDir the app later reads, or reach a dependency on localhost, which is what the common setup patterns rely on.

## Sidecars

An init container that **stays alive** alongside the app instead of exiting. Starts before the app, runs for the pod's lifetime, shuts down after the app.

## What makes an init container a sidecar

A single field: `restartPolicy: Always` on the `initContainers` entry. That's the *only* mechanism — there is no `sidecar:` keyword in the API.

> [!note] One flag, three consequences
> With `restartPolicy: Always` the container:
>
> - doesn't block the init sequence (proceeds once **started**, not finished)
> - keeps running alongside the app
> - gains probes (`liveness`/`readiness`/`startup`) and `lifecycle` hooks, which standard init containers can't have

## Order of execution

1. Init containers run **one at a time**, in the order listed.
1. A **standard** init container blocks until it exits 0; the next then starts.
1. A **sidecar** only needs to *start* before the sequence continues, then stays running.
1. Once all are done/started, the app containers start.

## If an init container dies

- **Standard init container fails** → kubelet retries it per the pod's `restartPolicy`. Pod stays blocked in `Init:x/y`. (With pod `restartPolicy: Never`, a failure fails the whole pod.)
- **Must be idempotent** — every pod restart re-runs all init containers from the top.
- **Sidecar dies** → restarted in place (it's `Always`); the app keeps running.

> [!warning] Match the flag to the process
>
> - Long-running process **without** `restartPolicy: Always` → pod **hangs in init forever** (waiting for an exit that never comes).
> - Short-lived process **with** the flag → restart loop.

## Examples

```yaml
spec:
  initContainers:
    - name: wait-for-db          # standard: runs, exits, gates startup
      image: busybox:1.36
      command: ['sh', '-c', 'until nc -z db 5432; do sleep 2; done']
    - name: proxy                # sidecar: starts, stays
      image: envoyproxy/envoy
      restartPolicy: Always
  containers:
    - name: app
      image: myapp:1.0
```

## Use cases

- **Standard:** wait for a dependency, clone a repo / pull config into a shared `emptyDir`, run migrations, fix volume permissions.
- **Sidecar:** service-mesh proxy, log shipper, secret/cert refresher.

## Links

- [[cka-prep-workflow-killercoda|Dumb It Guy Questions Setup]]
- [[kubernetes-persistent-volumes-pvc-storageclass|Pv, Pvc, Storageclass]]
