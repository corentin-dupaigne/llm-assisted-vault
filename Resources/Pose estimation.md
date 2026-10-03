---
domain: computer-vision
tags: [3d-reconstruction, robotics]
date: 2026-10-03
para: Resources
project: null
---
# Pose Estimation: Theoretical Comparison

Theoretical comparison of pose estimation options for 3D Gaussian Splatting: how each approach works, its strengths and weaknesses, and its effect on training.

Pose estimation takes a set of images and produces three things: the position and orientation of the camera for each image (poses), the camera intrinsics (focal length, lens distortion), and a sparse 3D point cloud used to initialize the Gaussians. Most trainers expect these in COLMAP format.

______________________________________________________________________

## 1. Key concepts

The options below differ along two axes, so it helps to define them first.

### Features: handcrafted vs. learned

To relate images to each other, the software detects distinctive points (features) in each image and matches them across images.

- **Handcrafted features (SIFT):** detected by fixed mathematical rules looking for corners and gradients. Reliable and well understood, but they need visible texture. On plain surfaces, few or no features are found.
- **Learned features (SuperPoint, LightGlue):** detected and matched by neural networks trained on large datasets. They find more usable points on weak texture and match more reliably under changes of viewpoint and lighting, at the cost of requiring a GPU.

### Reconstruction strategy: incremental vs. global vs. feed-forward

- **Incremental:** start from two images, then add images one by one, refining everything as it grows. Accurate and robust, but slow on large sets, and early errors can propagate.
- **Global:** estimate all camera poses at once from all matches, then refine. Much faster on large sets, and less prone to drift.
- **Feed-forward (learned):** a neural network directly predicts poses and 3D structure from the images in one pass, without explicit feature matching. Very fast and robust on hard images, but less precise and limited in the number of images it can process at once.

All strategies can end with **bundle adjustment**, an optimization that jointly refines poses and 3D points to minimize the reprojection error (the distance between where a 3D point projects in an image and where it was actually detected).

______________________________________________________________________

## 2. Options

### COLMAP

**How it works:** incremental Structure-from-Motion with SIFT features by default. The reference tool, used by most Gaussian Splatting research and trainers.

| Strengths | Weaknesses |
|---|---|
| The standard: every trainer supports its output directly | Slow on large image sets (hours for thousands of images) |
| Accurate when images have enough texture | SIFT features fail on plain surfaces, so images of bare walls may not be registered |
| Mature, well documented, open source | Incremental strategy can drift or split into several disconnected models |
| Many settings to tune matching and reconstruction | Tuning requires expertise |

**Effect on reconstruction:** when it works, poses are precise and training quality is high. When it fails on textureless areas, images are dropped or badly placed, which directly produces holes, blur and floaters.

### GLOMAP

**How it works:** global Structure-from-Motion. It reuses COLMAP's feature extraction and matching, then replaces the incremental reconstruction with a global one.

| Strengths | Weaknesses |
|---|---|
| Much faster than COLMAP on large sets, often by an order of magnitude | Same SIFT features as COLMAP, so the same weakness on plain surfaces |
| Accuracy comparable to COLMAP in published benchmarks | Newer and less battle-tested |
| Output in COLMAP format, drop-in replacement | Global methods can be more sensitive to wrong matches |
| Open source | |

**Effect on reconstruction:** similar quality to COLMAP with much shorter processing time. It does not solve the texture problem, since matching is unchanged.

### COLMAP with learned features (hloc)

**How it works:** the hloc toolbox replaces SIFT with learned features and matchers (such as SuperPoint and LightGlue), then runs COLMAP's reconstruction on the resulting matches.

| Strengths | Weaknesses |
|---|---|
| More matches on weak texture and under viewpoint or lighting changes | Requires a GPU for feature extraction and matching |
| Keeps COLMAP's accurate reconstruction and output format | More complex setup than plain COLMAP |
| Open source | Some learned models have non-commercial licenses, so each component's license must be checked |

**Effect on reconstruction:** a direct way to register more images on difficult surfaces while keeping a standard pipeline.

### MASt3R-SfM

**How it works:** uses MASt3R, a neural network that predicts dense 3D correspondences between pairs of images, then assembles them into a full reconstruction with global optimization.

| Strengths | Weaknesses |
|---|---|
| Very robust on textureless surfaces and low overlap, since it reasons about 3D structure rather than only local texture | Heavy GPU memory and compute requirements |
| Dense matches rather than sparse points | Research code: less mature, fewer options, less documentation |
| Works even with few images | Non-commercial license for the model weights |
| | Output may need conversion before use by trainers |

**Effect on reconstruction:** can succeed where feature-based methods fail entirely, at the cost of compute, maturity and licensing constraints.

### VGGT

**How it works:** a large feed-forward network that takes a set of images and directly predicts camera poses, depth maps and 3D points in a single pass.

| Strengths | Weaknesses |
|---|---|
| Extremely fast: seconds instead of minutes or hours | Number of images per pass is limited by GPU memory |
| Robust on hard images since no explicit feature matching is needed | Poses less precise than optimization-based methods unless refined with bundle adjustment afterwards |
| Also predicts dense depth, which can help initialize training | Research code, and licensing must be checked for the intended use |

**Effect on reconstruction:** a fast and robust way to get approximate poses, best used followed by a bundle adjustment refinement for training-quality precision.

### RealityScan (Epic Games)

**How it works:** a proprietary photogrammetry application (formerly RealityCapture) with its own feature matching and alignment, able to export poses in formats usable by Gaussian Splatting trainers.

| Strengths | Weaknesses |
|---|---|
| Fast, polished graphical interface | Proprietary, closed algorithms |
| Can combine images with LiDAR scans in the same alignment | Windows-focused |
| Free for most users | Licensing conditions depend on use and revenue |
| Handles large datasets well | Less control over, and understanding of, what happens internally |

**Effect on reconstruction:** a strong practical option, particularly when mixing camera and LiDAR data, but not usable where open-source tooling is required.

### Sensor-based poses (SLAM from phones or scanners)

**How it works:** poses come from the capture device itself, which tracks its movement with motion sensors, cameras and sometimes LiDAR (for example ARKit on iPhone, or professional scanners).

| Strengths | Weaknesses |
|---|---|
| No separate pose estimation step | Precision is often lower than image-based bundle adjustment, and may need refinement |
| Robust on textureless surfaces, especially with LiDAR | Tied to specific devices and often to proprietary software |
| Real-world scale | Export to trainer-compatible formats is not always available |

**Effect on reconstruction:** a way to bypass the texture problem entirely, depending on the capture hardware chosen.

______________________________________________________________________

## 3. Summary

| Option | Strategy | Features | Speed | Robustness on plain surfaces | Precision | Open source | Maturity |
|---|---|---|---|---|---|---|---|
| COLMAP | Incremental | SIFT | Slow | Low | High | Yes | High |
| GLOMAP | Global | SIFT | Fast | Low | High | Yes | Medium |
| COLMAP + hloc | Incremental | Learned | Medium | Medium to high | High | Yes (check model licenses) | Medium |
| MASt3R-SfM | Global | Dense learned | Slow | High | Medium to high | Code yes, weights non-commercial | Low |
| VGGT | Feed-forward | None (end-to-end) | Very fast | High | Medium (high with refinement) | Check license | Low |
| RealityScan | Proprietary | Proprietary | Fast | Medium | High | No | High |
| Sensor-based (SLAM) | Device tracking | Device-dependent | Real-time | High with LiDAR | Medium | Device-dependent | Device-dependent |

## 4. Hypotheses

Hypotheses suggested by this comparison, to be tested experimentally:

1. On images of plain surfaces, feature-based methods with SIFT (COLMAP, GLOMAP) register significantly fewer images than learned approaches.
1. GLOMAP matches COLMAP's precision with much shorter processing time.
1. Learned features (hloc) are the best compromise between robustness, precision and a standard, open-source pipeline.
1. Feed-forward methods (VGGT) give usable poses quickly but need bundle adjustment refinement to match the training quality of optimization-based methods.

## Links

- [[Gaussian Splatting pipeline]]
