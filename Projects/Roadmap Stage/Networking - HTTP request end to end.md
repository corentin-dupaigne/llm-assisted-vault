---
tags: [sre, networking, http, roadmap/week-1]
domain: networking
date: 2026-11-27
para: Projects
project: Roadmap Stage
---
# Networking - HTTP request end to end

The classic interview question: "What happens when I type `https://example.com` and press Enter?" This note puts the other three together in the right order.

## The full path

1. **URL parsing**: `https` scheme, so port 443 by default, host `example.com`, path `/`.
1. **DNS**: name → IP address. See [[Networking - DNS resolution]].
1. **TCP**: SYN, SYN-ACK, ACK handshake to the IP on port 443. See [[Networking - TCP handshake]].
1. **TLS**: the server proves its identity, both sides set up keys. See [[Networking - TLS]].
1. **HTTP request**, sent encrypted:
   ```
   GET / HTTP/1.1
   Host: example.com
   User-Agent: ...
   Accept: text/html
   ```
   The `Host` header tells the server which site is requested.
1. **Server side**, typically:
   - a **load balancer** takes the connection and picks a healthy server
   - a **reverse proxy** (Nginx, Envoy) often terminates TLS and routes by name and path
   - the **application** handles the request, queries a cache or a database
1. **HTTP response**: a status code, headers and a body.
1. **The browser renders the page**: it parses the HTML, then fetches CSS, JS and images, reusing the same connection when possible.

## Kubernetes version (my homelab)

Load balancer or public IP → **Gateway API (Envoy)**, which terminates TLS and routes by name → **Service** → kube-proxy does a **DNAT** from the Service IP to a pod IP (see my ClusterIP article) → the **pod**, reached through the CNI.

## Status codes to know

| Code | Meaning | In production, it often means |
|---|---|---|
| 200 | OK | |
| 301 / 302 | redirect | HTTP to HTTPS, old URL |
| 400 | bad request | client-side bug |
| 401 / 403 | unauthenticated / forbidden | expired token, wrong permissions |
| 404 | not found | wrong path, wrong routing |
| 429 | too many requests | rate limiting |
| 500 | internal server error | bug or exception in the app |
| 502 | bad gateway | the proxy can't reach the app (pod down, wrong port) |
| 503 | service unavailable | no healthy backend, overload |
| 504 | gateway timeout | the app responds too slowly |

## HTTP versions

- **HTTP/1.1**: one request at a time per connection, but connections are reusable (keep-alive).
- **HTTP/2**: several requests in parallel over a single TCP connection (multiplexing).
- **HTTP/3**: runs on **QUIC**, over UDP. It merges the transport and TLS handshakes, and a lost packet no longer blocks every stream.

## Commands

```bash
curl -v https://example.com        # the whole path: connection, TLS, request, response
curl -w '%{time_namelookup} %{time_connect} %{time_appconnect} %{time_starttransfer}\n' -o /dev/null -s https://example.com
# DNS, TCP, TLS and first-byte times: to find which step is slow
```

> [!question]- Give the path in one sentence, in order.
> DNS to get the IP, TCP handshake, TLS handshake, HTTP request, server-side handling (load balancer, proxy, app), response, rendering.

> [!question]- A site returns 502s. Where do you look?
> Between the proxy and the app: the proxy can't reach its backend. Check the proxy logs, the pods' state, and whether the Service has endpoints and targets the right port.

> [!question]- A page takes 3 seconds to load. How do you find which step is slow?
> With `curl -w` and the `time_namelookup`, `time_connect`, `time_appconnect` and `time_starttransfer` timings. They separate DNS, TCP, TLS and server processing time.

## Resources (in this order)

1. MDN, [Overview of HTTP](https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Overview): sections **Components of HTTP-based systems** (including Proxies), **HTTP flow** and **HTTP Messages** (~10 min)
1. GitHub, [alex/what-happens-when](https://github.com/alex/what-happens-when): sections **DNS lookup**, **Opening of a socket**, **TLS handshake**, **HTTP protocol** and **HTTP Server Request Handle** only. Skip the keyboard and rendering sections (~15 min)
1. My own article, [How Does a ClusterIP Actually Work?](https://corentindupaigne.com/journal/how-does-a-clusterip-actually-work/): reread it as the Kubernetes end of the path (~5 min)

## My notes

**My full explanation in 2 minutes, out loud:**

**What I was mixing up:**

## Links

- [[Networking - DNS resolution]]
- [[iptables Netfilter and masquerade]]
- [[IPAM (IP Address Management)]]
- [[Understanding TCP-IP addressing and subnetting basics]]
