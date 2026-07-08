
## Definition

IPAM is the networking function responsible for managing a **pool of IP addresses**: allocating addresses, tracking which are in use, and releasing them when no longer needed. It manages *addresses*, not the entities that borrow them.

## The three core jobs

- **Allocation** — pick an available address from the pool for a new request.
- **Release** — return an address to the pool when it's done (host leaves, lease expires, resource deleted).
- **Tracking** — persist the record of which addresses are allocated vs. free. This is the "state" of the pool.

## Why it's a real problem (not "just pick a number")

- **No duplicates** — two consumers must never receive the same IP. Concurrent requests make collision-avoidance genuine coordination work (race conditions on the shared pool).
- **State must persist** — allocation records must survive across requests and restarts. They can't live only in the memory of a short-lived process; they need durable storage (disk, database, or a shared authoritative store).
- **Release or leak** — failing to release an address on teardown leaks it, slowly exhausting the pool until no addresses remain.

## Scope boundary

IPAM's concern is **IP addresses only**. It does not track the lifecycle, health, or behavior of the things consuming addresses — only whether a given address is "handed out" or "free."

This narrow scope is a strength: it keeps IPAM a clean, self-contained unit of logic, independent of the systems that request addresses from it.

## Common building blocks

- **Address pool / CIDR** — a range of addresses IPAM draws from, expressed as a CIDR (e.g. `10.0.0.0/16`).
- **Subnet carving** — dividing a large range into smaller subnets (e.g. a `/16` into many `/24`s), often one per region, segment, or node.
- **Allocation record** — the persisted mapping of "address → who holds it," and the set of free addresses.
- **Lease** — in some systems (notably DHCP), an allocation is time-bound and must be renewed, otherwise it expires and is reclaimed automatically.
- **Gateway / routes** — IPAM often also assigns the default gateway and associated routes alongside the address.

## Where IPAM appears

The same core problem exists anywhere there's a finite address pool and multiple consumers:

- **DHCP** — the most widespread form. A DHCP server leases addresses to devices joining a network, tracks the leases, and reclaims them on expiry. Home routers, offices, and campuses all run this.
- **Enterprise / ISP networks** — dedicated IPAM software (e.g. Infoblox, NetBox, phpIPAM) tracks tens of thousands of addresses across subnets, VLANs, and sites. This operational discipline is the origin of the term.
- **Cloud providers** — allocation of private addresses from virtual-network CIDR ranges; some providers expose managed IPAM services for planning and tracking address space at scale.
- **Virtualization and containers** — VM platforms and container runtimes assign addresses to VMs/containers from a pool, tracked and reclaimed as they come and go.

## Static vs. dynamic allocation

- **Static** — addresses assigned manually or deterministically and rarely changed. Simple, predictable, but doesn't scale to churn.
- **Dynamic** — addresses handed out on demand from a pool and reclaimed automatically. Scales to many short-lived consumers but requires the tracking, persistence, and collision-avoidance machinery above.

## Key takeaway

IPAM is a fundamental, decades-old networking primitive. Its concepts — CIDR carving, allocation tracking, lease/release, collision avoidance, durable state — recur across DHCP, cloud networking, virtualization, and network design generally. Understanding it in one context transfers directly to the others.