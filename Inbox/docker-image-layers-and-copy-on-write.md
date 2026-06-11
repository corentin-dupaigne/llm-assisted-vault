---
domain: docker
tags: [containerization, devops, storage]
date: 2026-06-05
para: Resources
project: null
---
### Read-Only Image Layers

Each instruction in a `Dockerfile`, such as `RUN`, `COPY`, or `ADD`, adds a permanent storage layer to the image stack. These layers are strictly immutable, meaning they can never be modified once they are created. It is important to remember that if a specific layer is changed, Docker must rebuild every layer that follows it in the `Dockerfile` because the foundation above that change has been invalidated. Because of this immutability, it is not truly possible to delete content from a previous layer; a "deletion" only hides the file in the current view while the data remains in the underlying layers. The storage driver, usually `overlay2`, manages this complexity by stacking these layers and presenting them as a single, unified file system to the user.

---

### The Writable Container Layer

When a container is launched from an image, Docker adds a thin, Writable Layer on top of the existing read-only stack. This layer acts as the active workspace where all runtime changes, such as new logs or modified configuration files, are stored. Unlike the image layers beneath it, the writable layer is ephemeral and is permanently deleted when the container is removed. This ensures that the underlying image remains clean and unchanged, allowing it to be reused by many different containers simultaneously.

![[Pasted image 20260123230359.png]]

---

### Copy-on-Write (CoW)

The Copy-on-Write strategy is the mechanism that allows a container to appear as if it is modifying an image. When a process inside the container attempts to modify a file that exists in a read-only layer, the storage driver first searches the stack from the top down to locate the file. Once found, Docker copies the entire file up to the Writable Layer before any changes are applied. From that point forward, the version in the Writable Layer "shadows" the original, meaning that the container only sees the new version while the original remains untouched in the layer below. This process also handles deletions by creating "whiteout" markers in the top layer that signal the file system to ignore the file in the lower layers.

---

### Layer Caching and Reusability

The layered architecture is specifically designed to optimize build speed and minimize disk usage through caching and sharing. During the build process, Docker checks its local cache to see if a layer with the exact same instruction and parent already exists, allowing it to skip redundant tasks. Furthermore, because the base layers are read-only, they can be safely shared across different images on the same host machine. For example, if multiple applications are built on the same version of Alpine Linux, the physical files for that operating system are stored only once on the disk, significantly reducing storage overhead.

---

### Summary of File Operations

|**Operation**|**Technical Action**|**Impact on Storage**|
|---|---|---|
|**Reading**|The system searches the stack top-down and reads the first instance found.|There is no additional disk space consumed.|
|**Modifying**|The file is copied to the Writable Layer (CoW) and then edited.|Disk usage increases by the size of the file being modified.|
|**Deleting**|A whiteout marker is placed in the Writable Layer to hide the file.|The file is hidden from view, but no space is actually freed from the image.|
