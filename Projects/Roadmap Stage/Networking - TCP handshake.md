---
tags: [sre, networking, tcp, roadmap/week-1]
domain: networking
date: 2026-11-27
para: Projects
project: Roadmap Stage
---
# Networking - TCP handshake

## Theory

TCP provides a **reliable, ordered** byte stream on top of IP, which guarantees nothing. Before exchanging data, both machines must agree on their starting **sequence numbers**: that's what the handshake is for.

### Opening: 3 messages

1. **SYN** (client → server): "I want to connect, my sequence number starts at x."
1. **SYN-ACK** (server → client): "OK, I got x, and mine starts at y."
1. **ACK** (client → server): "I got y."

The connection is established: each side knows how to number and acknowledge the other's bytes. Cost: **1 round trip (RTT)** before any data can be sent.

A connection is identified by 4 values: **source IP, source port, destination IP, destination port**. The client's source port is picked at random (ephemeral port).

### Closing: 4 messages

Each direction closes separately: **FIN**, then **ACK**, in each direction. An **RST** cuts the connection abruptly, without a clean close (closed port, killed process, firewall).

### TIME_WAIT

The side that closes first stays in **TIME_WAIT** for 2 × MSL (often 60 seconds on Linux). Why:

- to make sure the last ACK arrived, and resend it if not
- to prevent late packets from the old connection from being mistaken for packets of a new connection with the same 4 values

Real production issue: a server or proxy that opens and closes lots of short connections piles up thousands of sockets in TIME_WAIT and can run out of ephemeral ports. Fix: reuse connections (keep-alive, connection pools).

### What makes TCP reliable

- **Acknowledgements and retransmission**: a byte not acknowledged in time is resent.
- **Flow control**: the receive window says how much the other side can still take.
- **Congestion control**: TCP slows down when it detects losses, so it doesn't flood the network.

### TCP or UDP

| | TCP | UDP |
|---|---|---|
| Connection | handshake | none |
| Reliability | ordering and delivery guaranteed | no guarantee |
| Cost | more latency | lighter |
| Uses | HTTP/1.1 and HTTP/2, SSH, databases | DNS, live video, games, QUIC (HTTP/3) |

## Commands

```bash
ss -tan                           # TCP connections and their state (ESTAB, TIME-WAIT…)
ss -tan state time-wait | wc -l   # how many sockets in TIME_WAIT
nc -vz example.com 443            # check whether a TCP port answers
sudo tcpdump -i any 'tcp port 443' -n   # watch SYN, SYN-ACK, ACK go by
```

> [!question]- Why 3 messages and not 2?
> Each side must announce its sequence number **and** get confirmation that the other received it. The SYN-ACK combines the server's reply and its own announcement, but the server still needs the final ACK.

> [!question]- A client sends a SYN and never gets a reply. What can that mean? And if it gets an RST?
> No reply: a firewall dropping packets, an unreachable host or a broken route. RST: the host is reachable, but nothing is listening on that port (or a firewall is actively rejecting).

> [!question]- A server has 30,000 sockets in TIME_WAIT. Is that a problem?
> Not necessarily, it's normal behavior. It becomes a problem if the client or proxy runs out of ephemeral ports. Then you should reuse connections instead of opening one per request.

## Resources (in this order)

1. *High Performance Browser Networking* (Ilya Grigorik, free online), chapter 2 [Building Blocks of TCP](https://hpbn.co/building-blocks-of-tcp/): section **Three-Way Handshake** only (~5 min)
1. Vincent Bernat, [Coping with the TCP TIME-WAIT state on busy Linux servers](https://vincent.bernat.ch/en/blog/2014-tcp-time-wait-state-linux): section **About the TIME-WAIT state**, subsections **Purpose** and **Problems** only. Skip "Other solutions" (~10 min)

## My notes

**My explanation in 3 sentences:**

**What I was mixing up:**

## Links

- [[Networking - DNS resolution]]
- [[Networking - HTTP request end to end]]
- [[Understanding TCP-IP addressing and subnetting basics]]
