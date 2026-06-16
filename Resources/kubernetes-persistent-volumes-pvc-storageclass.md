---
para: Resources
domain: kubernetes
tags:
  - storage
  - devops
date: 2026-06-12
---
## Persistent Volume

A cluster resource representing an actual piece of storage that exists, pointing to where the data physically lives.

## Persistent Volume Claim

A namespaced request for storage that binds to a matching PV, letting a pod consume storage without knowing the underlying infrastructure.

## Storage Class

A named recipe that tells a provisioner how to create a PV on demand when no suitable one already exists (dynamic provisioning).

______________________________________________________________________

## Path of a volume request

![[Pasted image 20260612100339.png]]

______________________________________________________________________

## Three path possible based on the value of StorageClassName

![[Pasted image 20260612101645.png]]

______________________________________________________________________

## Common questions

**What happens when a pvc requires for a volume but there's no PV available and no storage class (storageClassName: "')?**

- The PVC stays stuck in `Pending` state indefinitely.

**Why class is on both PVC and PV?**

- because they play opposite roles — the PVC's field is a _request/selector_ ("I want this class") and the PV's field is a _label_ ("I am this class"), and binding works by matching the request against the label, so both sides need to name it.

**What are the PVC↔PV match criteria?**

- the PV must offer at least the requested access mode, have capacity ≥ the request, and exactly match the PVC's `storageClassName` and `volumeMode` (plus any selector/`claimRef` constraints).

## Links

- [[cka-prep-workflow-killercoda|Dumb It Guy Questions Setup]]
