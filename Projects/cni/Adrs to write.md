---
domain: kubernetes
tags: [devops, golang, pods]
date: 2026-09-28
para: Projects
project: cni
---
This ADR should document the decision to **hardcode the pod subnet in the CNI config (aligned with the cluster CIDR) rather than fetching the node's `spec.podCIDR` from the Kubernetes API**, because single-node has one constant subnet and fetching would pull in disproportionate machinery (ServiceAccount, RBAC, API client), with the explicit note that this flips to API-fetching when multi-node makes per-node subnets a real requirement.

## Links

- [[Roadmap]]
- [[IPAM (IP Address Management)]]
- [[CNI Conformance Test Suite — Requirements & Coverage]]
- [[Understanding TCP-IP addressing and subnetting basics]]
