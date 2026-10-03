This document defines how to compare capture methods (step 1 of the Gaussian Splatting pipeline) for reconstructing empty operating rooms. The goal is to find out which capture choices matter most for quality, especially on white, textureless walls, before settling on a final setup.

## 1. What we compare

| Factor        | Options                                                      | Question it answers                                             |
| ------------- | ------------------------------------------------------------ | --------------------------------------------------------------- |
| Camera        | Phone vs. dedicated camera (mirrorless or 360°)              | Is a phone good enough for the client to reuse the setup?       |
| Movement      | Handheld vs. gimbal vs. tripod robot on a predefined pattern | How much does a controlled path improve coverage and sharpness? |
| Wall texture  | Bare walls vs. posters or stickers                           | Does added texture fix pose estimation on white walls?          |
| Depth sensing | Camera only vs. LiDAR (phone LiDAR, professional scanner)    | Is LiDAR worth its cost for this use case?                      |

## 2. Test room

Use a room that resembles an operating room: large white or plain walls, some reflective metal surfaces, a central object (table, bed), and a door. Ideally use the same room for every run.

Record for the report: room dimensions, lighting (natural or artificial, and whether it changes during the day), and photos of the room.

## 3. What stays constant

Only one factor changes per run. Everything else is fixed:

| Element                   | Fixed value                                                                   |
| ------------------------- | ----------------------------------------------------------------------------- |
| Room and furniture layout | Identical for every run                                                       |
| Lighting                  | Artificial light only, same switches, blinds closed                           |
| Frame extraction          | Same frame rate from video (for example 2 to 3 fps), or a similar image count |
| Image resolution          | Same for every run (for example 1600 px wide)                                 |
| Pose estimation           | Same tool and settings (for example GLOMAP)                                   |
| Trainer                   | Same tool, version and settings (for example Splatfacto, 30,000 iterations)   |
| Hardware                  | Same GPU for every training run                                               |
| Camera settings           | Exposure, white balance and focus locked, as far as the device allows         |

## 4. Runs

The baseline is the simplest, cheapest setup. Each other run changes one factor from the baseline.

| Run | Camera               | Movement     | Walls              | Depth              | Changed factor                                    |
| --- | -------------------- | ------------ | ------------------ | ------------------ | ------------------------------------------------- |
| B   | Phone                | Handheld     | Bare               | Camera only        | None (baseline)                                   |
| C1  | Dedicated camera     | Handheld     | Bare               | Camera only        | Camera                                            |
| M1  | Phone                | Gimbal       | Bare               | Camera only        | Movement                                          |
| M2  | Phone                | Tripod robot | Bare               | Camera only        | Movement                                          |
| T1  | Phone                | Handheld     | Posters / stickers | Camera only        | Wall texture                                      |
| D1  | Phone with LiDAR     | Handheld     | Bare               | Phone LiDAR        | Depth sensing                                     |
| D2  | Professional scanner | Scanner path | Bare               | Professional LiDAR | Depth sensing (reference, if one can be borrowed) |

Once the single-factor results are in, combine the factors that helped into one final run (for example dedicated camera + robot + posters) to check that the gains add up.

**Note on LiDAR runs:** LiDAR devices produce their own camera poses through SLAM, so D1 and D2 cannot go through the same pose estimation tool as the other runs. Record which part of the pipeline changed, and compare them mainly on the final result.

## 5. Capture guidelines (all runs)

- Walk a loop around the room at two or three heights (roughly waist, chest and above head), camera facing inward, then a loop facing the walls.
- Move slowly to avoid motion blur, and keep strong overlap between consecutive frames.
- Cover the floor and ceiling corners, and the areas behind furniture.
- Avoid people, moving objects, and your own reflection in metal surfaces where possible.
- Keep capture duration similar between runs, and note it.

## 6. Metrics

**Pose estimation (step 2)**

| Metric | Meaning |
|---|---|
| Registered images (%) | Share of images for which a pose was found. Low values mean the capture failed. |
| Mean reprojection error (px) | How consistent the poses and points are. Lower is better. |
| Sparse point count | Number of 3D points found. Very low counts on walls reveal the texture problem. |

**Reconstruction quality (step 3)**

Hold out every 8th image as a test set, never used for training.

| Metric | Meaning |
|---|---|
| PSNR (dB) | Pixel-level fidelity. Higher is better. |
| SSIM | Structural similarity. Higher is better (max 1). |
| LPIPS | Perceptual difference. Lower is better. |
| Number of Gaussians | Drives file size and rendering speed. |

**Qualitative review**

Render the same five viewpoints for every run, including at least one looking at a bare wall and one at a metal surface. Rate each on a 1-to-5 scale:

- Wall quality (flat and sharp, or blurry and holey)
- Floaters
- Reflections on metal surfaces
- Overall realism for a person standing in the room

**Cost and effort**

- Capture time
- Equipment cost
- Processing time (pose estimation + training)
- Ease of reproduction by the client

## 7. Results

### Pose estimation

| Run | Images | Registered (%) | Reprojection error (px) | Sparse points |
|---|---|---|---|---|
| B | | | | |
| C1 | | | | |
| M1 | | | | |
| M2 | | | | |
| T1 | | | | |
| D1 | | | | |
| D2 | | | | |

### Reconstruction quality

| Run | PSNR | SSIM | LPIPS | Gaussians | Training time |
|---|---|---|---|---|---|
| B | | | | | |
| C1 | | | | | |
| M1 | | | | | |
| M2 | | | | | |
| T1 | | | | | |
| D1 | | | | | |
| D2 | | | | | |

### Qualitative review

| Run | Walls | Floaters | Reflections | Realism | Notes |
|---|---|---|---|---|---|
| B | | | | | |
| C1 | | | | | |
| M1 | | | | | |
| M2 | | | | | |
| T1 | | | | | |
| D1 | | | | | |
| D2 | | | | | |

### Cost and effort

| Run | Capture time | Equipment cost | Processing time | Reproducible by the client? |
|---|---|---|---|---|
| B | | | | |
| C1 | | | | |
| M1 | | | | |
| M2 | | | | |
| T1 | | | | |
| D1 | | | | |
| D2 | | | | |

## 8. Conclusion

To fill in after the runs:

- Which factor had the largest effect on quality?
- Which factor had the largest effect on pose estimation success?
- Final recommended capture setup, with its cost and the expected quality.
- Limitations of the tests (single room, lighting, equipment available).