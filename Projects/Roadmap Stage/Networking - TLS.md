---
tags: [sre, networking, tls, roadmap/week-1]
domain: networking
date: 2026-11-27
para: Projects
project: Roadmap Stage
---
# Networking - TLS

## Theory

TLS does three things on top of TCP:

1. **Authentication**: the server proves it really is `example.com`, using a certificate.
1. **Confidentiality**: the data is encrypted.
1. **Integrity**: any change in transit is detected.

It is **not** a check that the client "can handle HTTPS". The server proves its identity, then both sides agree on encryption keys.

### The TLS 1.3 handshake (1 round trip)

1. **ClientHello**: the client sends the algorithms it supports, its share of the key exchange, and the name of the site it wants (**SNI**). SNI lets one server host several sites on a single IP.
1. **ServerHello**: the server picks the algorithms and sends its share of the key exchange. From there, both sides compute the same secret key (**ECDHE**) without ever sending it over the network.
1. The server sends, already encrypted: its **certificate**, a **signature** proving it owns that certificate's private key, and a **Finished** message.
1. The client checks the certificate, sends its own **Finished**, and HTTP data can flow.

TLS 1.2 needed 2 round trips. On a fresh HTTPS connection, count: DNS + 1 RTT for TCP + 1 RTT for TLS 1.3, before the first byte of HTTP.

### Certificate validation

The client checks:

- the **chain of trust**: the site's certificate is signed by an intermediate authority, itself signed by a **root authority** in the system's or browser's trust store
- that the requested **name** is in the certificate (SAN field)
- that the certificate **hasn't expired**

### Why ephemeral key exchange (ECDHE)

Session keys are recomputed for each connection and thrown away afterwards. Even if the server's private key is stolen later, old recorded conversations stay unreadable: that's **forward secrecy**.

### Link with my homelab

cert-manager requests certificates from Let's Encrypt, which checks that I control the domain (HTTP-01 or DNS-01 challenge), then signs the certificate. Envoy then presents that certificate during the handshake.

## Commands

```bash
openssl s_client -connect example.com:443 -servername example.com   # see the handshake and the chain
curl -v https://example.com          # see TLS, then the HTTP request
openssl x509 -in cert.pem -noout -dates -subject -ext subjectAltName
```

> [!question]- What exactly does the server prove during the handshake?
> That it owns the private key matching a valid certificate, signed by a trusted authority, for the requested name.

> [!question]- A user sees "certificate has expired". What happened, and how do you prevent it?
> The certificate is past its validity end date. Automate renewal (cert-manager, certbot) and monitor the expiry date with an alert.

> [!question]- What is SNI for?
> To send the site's name in the ClientHello, so a server hosting several domains on one IP can present the right certificate.

> [!question]- Why is the session key never sent over the network?
> Thanks to Diffie-Hellman (ECDHE): each side sends a public value, and both compute the same secret key on their own.

## Resources (in this order)

1. Cloudflare Learning, [What happens in a TLS handshake?](https://www.cloudflare.com/learning/ssl/what-happens-in-a-tls-handshake/): sections **What are the steps of a TLS handshake?** and **What is different about a handshake in TLS 1.3?** (~10 min)
1. *High Performance Browser Networking*, chapter 4 [Transport Layer Security (TLS)](https://hpbn.co/transport-layer-security-tls/): three sections only, **RSA, Diffie-Hellman and Forward Secrecy**, **Server Name Indication (SNI)** and **Chain of Trust and Certificate Authorities** (~15 min). Skip its "TLS Handshake" section: it describes TLS 1.2 (2 round trips), not 1.3.

## My notes

**My explanation in 3 sentences:**

**What I was mixing up:**

## Links

- [[Networking - DNS resolution]]
- [[Networking - HTTP request end to end]]
- [[Networking - TCP handshake]]
