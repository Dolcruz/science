# Paired endpoint errors

`paired_epe.csv` contains one row per directed registration pair. Each method predicts a three-dimensional displacement for the same scored source points. EPE is the arithmetic mean of the Euclidean distance between the predicted and reference displacement, in metres. Lower values indicate smaller errors.

Run `python verify.py` in this directory, or pass the script's path from any directory. It checks the CSV checksum, uniqueness of directed pairs, counts of tree instances, pairs and scored points, and the 97 published pairwise comparisons for the direct correction. It prints both equal-pair and equal-tree means. Verification uses the released pair scores and requires only the Python standard library. Recomputing a displacement estimate or its point-level error requires the underlying point clouds, predictions and references.

| Dataset | Instances | Directed pairs | Scored source points | Measurement |
|---|---:|---:|---:|---|
| `published_s5` | 20 | 97 | 22,145,252 | Published synthetic S5 test scans, using the common corrected 5 cm reference rows. |
| `additional` | 20 | 200 | 852,097 | Additional directed contexts on the released seed-7 simulations. The 632 patches cover 116 unordered scan pairs. A repeated source representative counts once per directed context. |
| `initial_11` | 11 | 55 | 3,153,708 | Five directed pairs per newly simulated tree. Nine trees use familiar presets and two use previously unseen presets. The two groups partition these 11 trees. |

`instance` identifies the simulated tree. `source_epoch` and `target_epoch` are the scan or frame identifiers used by that evaluation. `pair_id` combines the instance and the two ordered epoch IDs. `metric_points` counts the common scored rows for that pair. Counts summed across pairs may include a source point used in more than one registration.

| CSV column | Method |
|---|---|
| `mv_epe_m` | Original MV-Tree-LNDP |
| `direct_epe_m` | Local-affine correction applied directly to the original MV-Tree-LNDP field |
| `windreg96_epe_m` | WindReg96 before local-affine correction |
| `full_epe_m` | WindReg96 with local-affine correction |

On published S5, the full pipeline preserves the published stationary-point convention. The direct correction operates on the original predictions as supplied. Each column uses the archived native metric arithmetic.

The equal-pair mean gives every directed pair equal weight. The equal-tree mean first averages pairs within each tree and then gives every tree equal weight. The reported relative improvement is one minus the ratio of the two aggregate mean errors. The script also prints the two preset subgroups of `initial_11`. With only two trees, the unseen-preset result is descriptive.

For the initial 11 trees, the [nine-method comparison](methods-initial-11.csv) gives mean EPE, strict and relaxed hit fractions, and relative EPE reductions against original MV with paired 95% intervals. PlantMove was omitted because the original implementation requires MATLAB. The [pine scorer and reference vectors](pine/README.md) reproduce both methods' scores from their individual predicted displacements on one published S5 scan pair.

The source records for the three frozen evaluations are identified below. The direct S5 and full-pipeline S5 records agree on every original MV-Tree-LNDP pair metric.

| Archived pair records | SHA-256 |
|---|---|
| Published S5 full pipeline | `4ac3e938dc4cfd5974e85de4d814d4011ffef155b874b624ecb13ad3764bcdfd` |
| Published S5 direct correction | `7d06549aabbb8b3bba8e9e9c46199294aa9b82b2317927b28558f702a7192e34` |
| Additional contexts and initial 11 trees | `16e256e2142f00d40f1a2ce1aeadc2736e328f6b5515ca071fde9ee506ff8eef` |
