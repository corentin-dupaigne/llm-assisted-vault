---
domain: kubernetes
tags: [devops, golang, networking, bug]
date: 2026-09-20
para: Projects
project: cni
status: open
severity: high
---
Bug found while validating the tiny-cni DaemonSet on a live single-node minikube
cluster (`cnitest`, k8s v1.35.1, docker driver) at image `1.0.0`.

## Summary

A pod cannot reach **itself** through a ClusterIP Service. When kube-proxy DNATs a
Service connection back to the pod that originated it, the packet must leave the bridge
through the same port it entered on. A Linux bridge refuses this unless the port has
**hairpin mode** enabled, and tiny-cni never enables it. The packet is silently dropped
and the connection hangs until timeout.

Every other network path works. That is what makes this expensive to diagnose.

## Symptom

Single-replica Deployment behind a ClusterIP Service, calling its own Service name:

| Path (from pod `10.244.0.3`) | Result |
| --- | --- |
| `http://selfcall/hostname` — own ClusterIP Service | **10/10 TIMEOUT** |
| `http://selfcall-headless:8080/hostname` — headless, same pod | 10/10 OK |
| `http://10.244.0.3:8080/hostname` — own pod IP, direct | 5/5 OK |
| `http://selfcall/hostname` from a **different** pod | 5/5 OK |

With one replica the failure is **total and deterministic**, not flaky: kube-proxy has
exactly one backend to select, and it is always the caller.

The signature a user will observe is *"my app can reach itself by IP but not by Service
name"*, which reads as a DNS fault and sends the investigation in the wrong direction.
DNS is fine — resolution succeeds, the connection is what dies.

## Root cause

`tcni-bridge` is a virtual Ethernet switch in the node's netns. Each pod's veth pair has
one end in the pod (`eth0`) and one end enslaved to the bridge as a port.

Every Ethernet switch, hardware or virtual, obeys 802.1D: **never forward a frame out the
port it arrived on.** That is loop prevention, and Linux enforces it per-port,
unconditionally. For ordinary traffic it is invisible — pod A to pod B enters on port A
and leaves on port B.

A ClusterIP is not a real address on any interface; it is a fiction maintained by
kube-proxy's iptables rules. `br_netfilter` pushes bridged traffic through iptables
`PREROUTING`, which is how ClusterIP Services work for bridged pods at all. So:

```
pod (10.244.0.6) ── veth ──▶ [ bridge port tcni-def3fd8c ]
        dst = 10.96.0.x                    │
                                           ▼
                            iptables DNAT (kube-proxy)
                            picks backend 1-of-N...
                                           │
                            dst = 10.244.0.6  ← the sender itself
                                           ▼
                            bridge must egress via
                            tcni-def3fd8c — the ingress port
                                           │
                                           ✗ DROPPED
```

The U-turn is the "hairpin" — traffic doubling back like a hairpin bend. The kernel
exposes a per-port override at `/sys/class/net/<veth>/brport/hairpin_mode`; the CNI plugin
is responsible for setting it.

Getting DNAT for bridged traffic and needing hairpin mode are a package deal: the same
`br_netfilter` path that makes ClusterIP work at all is what creates the U-turn.

## Evidence

Every bridge port on the node reads `0`:

```
$ for v in $(ls /sys/class/net/tcni-bridge/brif/); do cat /sys/class/net/$v/brport/hairpin_mode; done | sort | uniq -c
      6 0
```

The source never touches it — `grep -rniE "hairpin|promisc" --include="*.go" .` returns
nothing.

Causality proven by flipping the flag on one veth by hand and repeating the identical
30-request loop from the same pod to the same 3-backend Service:

| | served by itself | served by others | timeouts |
| --- | --- | --- | --- |
| `hairpin_mode=0` (shipped) | 0 | 26 | **4** |
| `hairpin_mode=1` (manual) | 14 | 16 | **0** |

```sh
ip link set tcni-def3fd8c type bridge_slave hairpin on
```

The `served by itself` column is the whole story: with hairpin off, reaching yourself
through a Service is not slow, it is **structurally impossible**. Reverted after the test.

Reproduced again on a clean install after a full node stop/start, so it is not state
drift.

> The raw timeout count (4 in one run, 6 in another) is below the ~10 a uniform 1-in-3
> backend split predicts. Not chased down; conntrack behaviour across rapid sequential
> connections is the likely cause. The 0-vs-14 contrast is the unambiguous signal, not the
> ratio.

## Kubernetes does its half and waits on the CNI

Two artefacts on the node show the platform expects the plugin to handle this.

**kube-proxy writes the hairpin SNAT rule** — it anticipates self-directed traffic and
masquerades it so the reply has a sane return path:

```
-A KUBE-SEP-2N6QA66M66QWLLYO -s 10.244.0.3/32 --comment "default/selfcall" -j KUBE-MARK-MASQ
```

It prepares for the hairpin. It cannot make a bridge reflect a frame.

**kubelet is configured `hairpinMode: hairpin-veth`** — "veths should have hairpin set" —
yet every port still reads `0`. kubelet only enforces that under the legacy kubenet path;
with a CNI plugin it does nothing. Nobody else will do this for us. That is why the
upstream `bridge` plugin exposes `hairpinMode` as a config key.

## Blast radius

The failure requires one condition: **the calling pod is itself a backend of the ClusterIP
Service it dials.** Nothing else is affected, which is why a broad smoke test misses it —
a 34-pod scale test passed clean because none of those pods called their own Service.

- **Single-replica Service calling itself → 100% failure.** Deterministic and total. The
  common case for a small app that talks to itself by Service name.
- **N replicas → ~1 in N requests fail**, per backend pod. ~33% at 3 replicas, ~5% at 20.
  This is the nastier presentation: intermittent timeouts behind a load balancer, blamed
  on a slow dependency or flaky network for weeks. Adding replicas *lowers* the error
  rate, so it mimics a capacity problem and rewards exactly the wrong fix.
- **Multi-node does not help.** Only self-selection hairpins, so the rate stays 1/N however
  the replicas are spread.

Real-world patterns that hit it:

- An app configured with its own base URL (`APP_URL=http://myapp`) fetching its own OIDC
  discovery document or JWKS during token validation. Auth flows do this constantly.
- Webhook or callback URLs pointing at the app's own Service.
- An in-cluster reverse proxy or gateway whose upstream list includes itself.
- Any codebase that uses the Service name uniformly for internal calls instead of
  special-casing localhost.

**Immune** (all verified): headless Services, direct pod IPs, localhost, pods that do not
back the Service, and kubelet liveness/readiness probes (node → pod IP, no DNAT).

## Fix

`internal/network/network.go:244` enslaves the host veth to the bridge:

```go
err = netlink.LinkSetMaster(veth, bridge)
```

Immediately after, the port needs:

```go
err = netlink.LinkSetHairpin(hostVeth, true)
```

Constraints:

- Must be called on the **host-side** link, not the pod-side peer.
- Must be called **after** enslaving — a link that is not a bridge slave has no `brport`
  directory to write to.
- If `promiscMode` is ever added as an option (upstream `bridge` has one), note that
  hairpin mode and bridge promiscuous mode are **mutually exclusive** there. Do not wire
  both on.

Consider exposing it as a config key (`hairpinMode`, defaulting to on) for parity with the
upstream plugin, though a bridge CNI for Kubernetes has no real reason to run with it off.

## Verification plan

Regression test that fails on today's code and passes after the fix:

1. Single-replica Deployment + ClusterIP Service (`targetPort` ≠ `port`, to catch the
   headless port-remap trap below).
1. From the pod, 10 requests to its own Service name → expect **10/10 success**, currently
   0/10.
1. Assert `/sys/class/net/<host veth>/brport/hairpin_mode` reads `1` for every port on
   `tcni-bridge`.
1. Multi-replica variant: 30 requests from one backend to the Service, assert **0
   timeouts** and that the caller appears among the responders.

Worth adding to the e2e suite — see
[[CNI Conformance Test Suite — Requirements & Coverage]]. Note this is *not* a CNI-spec
conformance requirement (the spec says nothing about Services or hairpin); it belongs in a
Kubernetes-integration test tier, not the neutral spec suite.

## Gotcha encountered while testing

The first headless-Service check appeared to fail 10/10 and looked like a second bug. It
was a test error: a headless Service performs **no port remapping**, so `http://svc/`
targets port 80 rather than the Deployment's `targetPort` of 8080. Against the real port
it is 10/10 OK. Worth remembering when writing the regression test.

## Related

- [[CNI Conformance Test Suite — Requirements & Coverage]]
- [[Adrs to write]]
- Upstream `bridge` plugin `hairpinMode`: https://www.cni.dev/plugins/current/main/bridge/
- Also noted during the same session: the README roadmap claims pods cannot reach the
  internet, but egress works — `internal/network/network.go:184` installs the
  `MASQUERADE` rule and pods ping `8.8.8.8` fine. That roadmap line is stale.

## Links

- [[CNI Conformance Test Suite — Requirements & Coverage]]
- [[Adrs to write]]
- [[Roadmap]]
- [[CNI Conformance Test Suite]]
- [[IPAM (IP Address Management)]]
- [[Understanding TCP-IP addressing and subnetting basics]]
