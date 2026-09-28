---
domain: kubernetes
tags: [devops, golang, networking, bug]
date: 2026-09-28
para: Projects
project: cni
---
When I tested to plug my custom cni plugin (that I will now refer as tinycni) in an actual living cluster I did not notice any problem at first, everything seemed to work smoothly. Then I realized that one test would not pass. A pod could not reach itself through a ClusterIP Service. The root cause took me time to understand.

| Path (from pod `10.244.0.3`) | Result |
| ------------------------------------------------------------- | ----------------- |
| `http://selfcall/hostname` - own ClusterIP Service | **10/10 TIMEOUT** |
| `http://selfcall-headless:8080/hostname` - headless, same pod | 10/10 OK |
| `http://10.244.0.3:8080/hostname` - own pod IP, direct | 5/5 OK |
| `http://selfcall/hostname` from a **different** pod | 5/5 OK |
With one replica the failure is total and deterministic.

## Route cause

## Links

- [[Roadmap]]
- [[CNI Conformance Test Suite — Requirements & Coverage]]
- [[CNI Conformance Test Suite]]
- [[IPAM (IP Address Management)]]
- [[Understanding TCP-IP addressing and subnetting basics]]
