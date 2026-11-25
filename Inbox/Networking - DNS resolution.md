---
tags: [sre, networking, dns, roadmap/week-1]
---

# Networking - DNS resolution

## Theory

DNS translates a name (`example.com`) into an IP address. It's **the very first step** of a request: without an IP, you can't send the first TCP packet.

### The players

| Player | Role |
|---|---|
| **Stub resolver** (on my machine) | checks `/etc/hosts` and the local cache, otherwise asks a recursive resolver |
| **Recursive resolver** (ISP, `8.8.8.8`, `1.1.1.1`, set in `/etc/resolv.conf`) | does all the lookup work for me and caches the answers |
| **Root servers** | know the servers for each TLD (`.com`, `.fr`…) |
| **TLD servers** (`.com`) | know the authoritative servers for each domain |
| **Authoritative server** (`example.com`) | holds the actual answer: the A or AAAA record |

### The path, with nothing cached

1. The browser and the OS check their caches. Nothing.
2. The stub resolver asks the **recursive resolver**.
3. The recursive resolver asks a **root server**: "where is `example.com`?" → "I don't know, but here are the `.com` servers".
4. It asks a **`.com` server** → "here are the authoritative servers for `example.com`" (NS records).
5. It asks the **authoritative server** → "`example.com` = 93.184.215.14" (A record).
6. The recursive resolver caches the answer for its **TTL** and returns it.

The lookup goes **from the top of the hierarchy down**: root, then TLD, then domain. The stub sends a **recursive** query ("give me the final answer"); the resolver sends **iterative** queries ("tell me who to ask next").

### Also worth knowing

- **Transport**: UDP port 53 by default, TCP for large responses or zone transfers.
- **Record types**: A (IPv4), AAAA (IPv6), CNAME (alias to another name), NS (authoritative servers), MX (mail), TXT (free text, verifications).
- **TTL**: how long a cached answer stays valid. A long TTL makes an IP change slow to propagate.
- **In Kubernetes**: pods query **CoreDNS**. With `ndots:5`, a short name like `api` is first tried with the search domains (`api.default.svc.cluster.local`…), which can multiply the queries.

## Commands

```bash
dig example.com          # answer and TTL
dig +trace example.com   # shows the whole path: root → .com → authoritative
dig @8.8.8.8 example.com # query a specific resolver
cat /etc/resolv.conf     # which resolver my machine uses
```

> [!question]- In what order do DNS and the TCP handshake happen? Why?
> DNS first. The SYN packet needs a destination IP address, and DNS is what provides it.

> [!question]- The recursive resolver has nothing cached. Who does it ask first?
> A root server, which points it to the `.com` servers, which point it to the authoritative server for `example.com`.

> [!question]- You change a server's IP, but some users keep hitting the old one for hours. Why?
> Resolvers keep the old answer cached until its TTL expires. Good practice: lower the TTL before a migration.

> [!question]- Why does DNS use UDP rather than TCP by default?
> A query and its answer usually fit in a single packet. UDP skips the handshake, so resolution is faster.

## Resources (in this order)

1. Cloudflare Learning, [What is DNS?](https://www.cloudflare.com/learning/dns/what-is-dns/): sections **What's the difference between an authoritative DNS server and a recursive DNS resolver?** and **What are the steps in a DNS lookup?** (the 8 numbered steps) (~10 min)
2. Same page, section **What is DNS caching? Where does DNS caching occur?** (~5 min)
3. Run `dig +trace example.com` and match each block of the output to a step of the lookup (~5 min)

## My notes

**My explanation in 3 sentences:**

**What I was mixing up:**
