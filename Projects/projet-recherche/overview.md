---
domain: computer-vision
tags: [3d-reconstruction, robotics, mathematics]
date: 2026-10-03
para: Projects
project: projet-recherche
---
For this project—**reconstructing empty operating rooms from video using 3D Gaussian Splatting (3DGS)**—the main knowledge needs are **3D computer vision, graphics, numerical optimization, and experimental evaluation**. Immersive medical training adds a second layer of requirements.

|Knowledge area|What you need to understand|Why it matters|
|---|---|---|
|**Mathematical foundations**|Linear algebra, 3D coordinates, rotations, covariance matrices, derivatives, gradient descent|Understand camera geometry and how Gaussian parameters are optimized.|
|**Programming and tools**|Python, NumPy, basic PyTorch, image/video processing, Git, GPU environments|Prepare video frames, run reconstruction software, troubleshoot, and reproduce experiments.|
|**Camera geometry and reconstruction**|Camera calibration, lens distortion, feature matching, Structure from Motion (SfM), bundle adjustment|Estimate camera positions and an initial sparse 3D scene, commonly using COLMAP.|
|**3D Gaussian Splatting**|Gaussian position, scale, orientation, opacity and color; projection, alpha blending, differentiable rendering, densification and pruning|Understand how the representation learns the room’s appearance and renders new viewpoints.|
|**Video capture and preparation**|Viewpoint coverage, overlapping frames, camera movement, blur, exposure, frame selection|Collect footage that supports reliable reconstruction.|
|**Research and evaluation**|Literature review, baselines, controlled experiments, held-out views, visual quality, runtime and memory measurements|Demonstrate what works, where it fails, and what your project contributes.|
|**Immersive application development**|Real-time rendering, scene scale, navigation, VR integration, interaction and collision geometry|Turn the reconstruction into a usable training environment, if implementation is in scope.|
|**Medical training context**|Room layout, equipment identification, intended learning tasks, staff feedback and local recording requirements|Decide which details must be accurate and whether the environment supports the intended training.|

The standard technical pipeline is:

**Video → selected frames → camera poses and sparse points → optimize 3D Gaussians → render unseen viewpoints → evaluate → integrate into a viewer or VR application.**

COLMAP’s [official tutorial](https://colmap.github.io/tutorial) explains the camera-pose and sparse-reconstruction stages. The [original 3DGS paper and implementation](https://repo-sam.inria.fr/fungraph/3d-gaussian-splatting/) explain Gaussian optimization and rendering.

**The most important project-specific challenges** are likely to be plain walls, reflective equipment, occluded areas, and lighting changes. Capture planning deserves as much attention as the reconstruction algorithm: COLMAP explicitly highlights texture, consistent illumination, overlapping views, and camera translation as key factors. [Capture guidance](https://colmap.github.io/tutorial#structure-from-motion)

For an academic project, you should also establish:

- **What counts as success?** Photorealistic walkthroughs, accurate dimensions, equipment recognition, or demonstrated learning improvement require different evaluations.
- **What will you investigate?** A manageable question is how frame selection or camera paths affect reconstruction quality, processing time, and scene completeness.
- **What is the final deliverable?** A desktop viewer is a smaller scope than an interactive VR training system.

**A crucial distinction:** a photorealistic Gaussian scene does not automatically provide an accurate, editable surface model or working equipment interactions. Treat geometry, collisions, and training behavior as additional requirements.

To start, prioritize **Python, linear algebra, camera geometry, COLMAP, and the original 3DGS method**. Advanced CUDA programming and extensive medical knowledge can remain optional unless your contribution specifically requires them.

## Links

- [[Gaussian Splatting pipeline]]
- [[Pipeline]]
- [[Pose estimation]]
- [[capture comparaison]]
- [[Issues]]
- [[cours exploration]]
