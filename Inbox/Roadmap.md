---
project: cni
---
## Sprint 0 — Spec contract, single node (M0)

**S0.1 — Plugin receives kubelet invocation**
- AC: binary reads config from stdin + `CNI_*` env, logs them, returns valid minimal JSON
- AC: kubelet execs it (pod visibly attempts networking)

**S0.2 — veth + netns wiring**
- AC: veth pair created, one end moved into pod netns, `lo` up

**S0.3 — IP + route inside pod**
- AC: pod gets an IP, default route set, correct JSON result returned
- AC: `ADD` and `DEL` both implemented

**Sprint goal:** two same-node pods ping each other.

---

## Sprint 1 — IPAM without conflicts (M1)

**S1.1 — Per-node subnet allocation**
- AC: cluster CIDR carved into `/24`s, node claims one via Node annotation on first boot

**S1.2 — In-node IP tracking**
- AC: allocated IPs tracked, no double-assignment

**S1.3 — Release on DEL**
- AC: IP returned to pool on `DEL`, no leak after repeated pod churn

**Sprint goal:** pods cycle repeatedly on a node — no dupes, no exhaustion.

---

## Sprint 2 — VXLAN datapath (M2, core)

**S2.1 — Daemon creates vxlan0**
- AC: DaemonSet brings up `vxlan0` on each node

**S2.2 — FDB + routes per remote node**
- AC: for each other node, FDB entry + route to its pod `/24` via tunnel installed

**S2.3 — MTU correctness**
- AC: pod MTU = underlay − 50
- AC: `curl https://` (large payload) succeeds cross-node

**Sprint goal:** pods on different nodes ping and move real traffic.

---

## Sprint 3 — Egress + host connectivity (M3)

**S3.1 — Internet egress**
- AC: masquerade rule `podCIDR → outside`, pod reaches public internet

**S3.2 — Host connectivity**
- AC: pod↔host both directions working

**S3.3 — Don't break the cluster**
- AC: pod resolves DNS (CoreDNS), reaches a ClusterIP Service (kube-proxy intact)

**Sprint goal:** a pod has full, normal network behavior.

---

## Sprint 4 — Survivability (M4)

**S4.1 — Idempotent reconciliation**
- AC: applying desired state twice changes nothing the second time
- AC: dirty state self-heals to correct state

**S4.2 — Restart resilience**
- AC: daemon restart → no drift, no duplicate FDB/routes

**S4.3 — Reboot recovery**
- AC: node reboot → datapath returns, pods networked, zero manual steps
- AC: no leaked veths / stale routes

**Sprint goal:** v0.1 — set `--flannel-backend=none` and daily-drive it.

---

## Backlog (post-v0.1, unplanned)

- **v0.2** — Dynamic membership: `client-go` informer on Nodes → auto FDB/route updates
- **v0.3** — hostPort (portmap), `CHECK` + `VERSION`, structured logging, metrics
- **v0.4** — NetworkPolicy (subset: ingress + namespace scope)
- **v1.0** — Failure-mode testing, docs, clean install, interview writeup
- **Thesis (defer):** observability-native datapath — per-pod accounting, `/metrics`, flow logs, tunnel health. Doesn't affect M0/M1.