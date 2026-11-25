---
tags: [roadmap, interviews]
created: 2026-11-25
---

# Interview Prep Roadmap

> [!info] Every week
> - **New**: ~4 problems in NeetCode order
> - **Deep dive**: ~3 problems on a high-frequency topic, following the linked notes
> - **Exam** on Saturday, **day off** on Sunday
> - Method to apply everywhere: [[Coding Interview Method]]

> [!abstract] Order within a week
> Follow the day tags. Algo goes in the morning or my free slots at Enedis (hardest focus), SRE/CKA in the evening (mostly reading). The deep dive comes first because it's on Saturday's exam; the new topic comes second. Notes list more problems than needed: do the first 1 or 2 of each note, keep the rest for reviews.

> [!check] Exams (soft gate)
> Each week ends with an exam on that week's deep dive and SRE topic. Rules: [[Section exam protocol]]
> - **Pass** → move on.
> - **Fail** → move on anyway, but the failed topic takes next week's deep dive slot and is retested the following Saturday.

> [!tip] Spaced repetition (10–15 min a day, in the metro)
> - **Problems** → NeetTrack (FSRS). Needed a hint = rate it as a fail.
> - **Theory** → Anki, from the cards generated for each note.
> - **Patterns** → Anki, one card I write myself after each problem, from my "hint that should have pointed me" line.

> [!tip] What to cut to stay on track
> Hards (except 2 or 3 classics), and only the best-known problems in 2-D DP, Math & Geometry and Bit Manipulation.

## December

### Week 1 · Dec 2 → 8

**Deep dive: Trees**
- **Mon** · [[Trees - Recursive DFS]]
- **Tue** · [[Trees - Level-order BFS]]
- **Wed** · [[Trees - BST and validation]]
- **Wed** · [[Trees - Lowest Common Ancestor]]
- **Fri** · [[Trees - Build a tree from its traversals]]

**New: Tries**, after Trees: a trie is a tree, and its search is a DFS
- **Thu** · [[Tries - Structure and insertion]]
- **Thu** · [[Tries - Prefix search]]

**SRE: life of a request**, in this order (it's the real order of a request)
- **Mon** · [[Networking - DNS resolution]]
- **Tue** · [[Networking - TCP handshake]]
- **Wed** · [[Networking - TLS]]
- **Thu** · [[Networking - HTTP request end to end]]
- **Fri** · Practice: `dig +trace`, `curl -v`, `openssl s_client`

**Exam (Saturday)**: Trees · Networking

### Week 2 · Dec 9 → 15

**Deep dive: Sliding Window + Two Pointers**
- **Mon** · [[Two Pointers - Sorted array]]
- **Tue** · [[Two Pointers - Fast and slow]]
- **Wed** · [[Sliding Window - Fixed size]]
- **Thu** · [[Sliding Window - Variable size with a counter]]

**New: Heap / Priority Queue**
- **Wed** · [[Heap - How it works and container-heap in Go]]
- **Thu** · [[Heap - Top-k]]
- **Fri** · [[Heap - Two heaps for the median]]

**CKA: troubleshooting**
- **Mon** · [[CKA - Debugging a pod]]
- **Tue** · [[CKA - Pending vs CrashLoopBackOff]]
- **Wed** · [[CKA - Service without endpoints]]
- **Thu** · [[CKA - Cluster DNS]]

**Exam (Saturday)**: Sliding Window + Two Pointers · Kubernetes troubleshooting

### Week 3 · Dec 16 → 22

**Deep dive: Heap**
- **Mon** · [[Heap - Top-k]]
- **Tue** · [[Heap - Two heaps for the median]]
- **Wed** · [[Heap - Merge k sorted lists]]

**New: Backtracking**
- **Wed** · [[Backtracking - Choose, explore, unchoose template]]
- **Thu** · [[Backtracking - Subsets]]
- **Thu** · [[Backtracking - Permutations]]
- **Fri** · [[Backtracking - Combination sum]]

**CKA: speed**
- **Mon** · [[CKA - Imperative commands]]
- **Tue** · [[CKA - dry-run and YAML generation]]
- **Wed** · [[CKA - Aliases and kubectl explain]]

**Exam (Saturday)**: Heap

### Week 4 · Dec 23 → 29 (Christmas, lighter week)

**Algo: NeetTrack reviews only**

**CKA: rest of the curriculum**
- **Mon** · [[CKA - RBAC]]
- **Tue** · [[CKA - NetworkPolicy]]
- **Wed** · [[CKA - Storage PV and PVC]]
- **Thu** · [[CKA - etcd backup]]

**No exam this week**

## January

### Week 5 · Dec 30 → Jan 5

**Deep dive: Backtracking**
- **Mon** · [[Backtracking - Choose, explore, unchoose template]]
- **Mon** · [[Backtracking - Pruning]]
- **Tue** · [[Backtracking - Grid search]]

**New: Graphs**
- **Wed** · [[Graphs - Representation]]
- **Wed** · [[Graphs - BFS and DFS on a grid]]
- **Thu** · [[Graphs - Connected components]]
- **Fri** · [[Graphs - Cycle detection and topological sort]]

**CKA: killer.sh, session 1**
- **Wed (session) · Fri (review)** · [[CKA - killer.sh mistakes]]

**Exam (Saturday)**: Backtracking. killer.sh is the CKA check.

### Week 6 · Jan 6 → 12

**Deep dive: Graphs**
- **Mon** · [[Graphs - BFS and DFS on a grid]]
- **Tue** · [[Graphs - Cycle detection and topological sort]]
- **Wed** · [[Graphs - Union-Find]]

**New: Intervals + Greedy**
- **Thu** · [[Intervals - Merge and insert]]
- **Thu** · [[Intervals - Overlaps and meeting rooms]]
- **Fri** · [[Greedy - Recognizing a greedy problem]]

**CKA: killer.sh, session 2**
- **Wed (session) · Fri (review)** · [[CKA - killer.sh mistakes]]

**Exam (Saturday)**: Graphs

### Week 7 · Jan 13 → 19 (CKA exam)

**Deep dive: Intervals + Greedy**
- **Mon** · [[Intervals - Merge and insert]]
- **Tue** · [[Intervals - Overlaps and meeting rooms]]
- **Wed** · [[Greedy - Recognizing a greedy problem]]

**New: 1-D DP**
- **Thu** · [[DP - Recurrence and memoization]]
- **Thu** · [[DP - From top-down to bottom-up]]
- **Fri** · [[DP - Climbing stairs and house robber]]

**Exam (Saturday)**: Intervals + Greedy

### Week 8 · Jan 20 → 26

**Deep dive: 1-D DP**
- **Mon** · [[DP - Recurrence and memoization]]
- **Tue** · [[DP - Subsequences]]
- **Wed** · [[DP - Coin change]]

**New: Advanced Graphs**
- **Thu** · [[Graphs - Dijkstra]]
- **Fri** · [[Graphs - Minimum spanning tree]]

**SRE: Linux debugging**
- **Mon** · [[Linux - Debugging a slow server]]
- **Tue** · [[Linux - CPU and load average]]
- **Wed** · [[Linux - Memory and the OOM killer]]
- **Thu** · [[Linux - Disk and inodes]]
- **Fri** · [[Linux - Logs with dmesg and journalctl]]

**Exam (Saturday)**: 1-D DP · Linux debugging

### Week 9 · Jan 27 → Feb 2

**Deep dive: Graphs, second pass**
- **Mon** · [[Graphs - BFS and DFS on a grid]]
- **Tue** · [[Graphs - Cycle detection and topological sort]]

**New: 2-D DP (classics only)**
- **Wed** · [[DP - Grids]]
- **Thu** · [[DP - LCS and edit distance]]

**SRE: processes, memory, reliability**
- **Mon** · [[Linux - Processes, fork and exec]]
- **Tue** · [[Linux - Signals]]
- **Wed** · [[Linux - Page cache]]
- **Thu** · [[SRE - SLI, SLO and error budget]]
- **Fri** · [[SRE - Symptom-based alerting]]

**Exam (Saturday)**: Graphs · Processes, memory, reliability

## February

### Week 10 · Feb 3 → 9

**New: end of the list**
- Remaining Stack, Linked List and Sliding Window problems

**Deep dive: weak spots**
- The topics failed in earlier exams, then the weakest in NeetTrack

**SRE: system design**
- **Mon** · [[System Design - Interview approach]]
- **Tue** · [[System Design - Load balancer and cache]]
- **Wed** · [[System Design - Message queue]]
- **Thu** · [[System Design - Rate limiter]]
- **Fri** · [[System Design - Monitoring system]]

**Exam (Saturday)**: System design

### Weeks 11 to 13 · Feb 10 → end of Feb

**Algo: real interview conditions**
- Timed mediums, out loud in English, on patterns already seen

**Company prep**
- [[STAR stories]]
- One note per interview: format, stack, likely questions

**Exam (each Saturday)**: a full mock interview, with no topic announced
