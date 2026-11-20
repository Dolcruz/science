# Running combined registration on the published S5 test data

Download the **S5 test patches** and the **merged MV-Tree-LNDP predictions** from the data deposit. Keep the `test/<tree>/<pair>_c<cluster>.npz` directory structure. The merged predictions are in `LNDP_S5_on_S5/predicted_motion`. The optional **s5_predicted_matches.zip** companion contains the matching network's predicted correspondences for these exact 97 pairs. Leave that ZIP compressed. [Weiser, Tabernig and Höfle, data and model weights](https://doi.org/10.11588/DATA/JQNDRP)

After installing the combined package requirements, run these commands from its directory. Substitute the paths to your downloaded data for the example paths. Use new output paths.

```sh
python prepare_paper_pair.py S5_patches/test LNDP_S5_on_S5/predicted_motion/small_pine_anim_42_0_2_out.npz small_pine_inputs --cache s5_predicted_matches.zip
python combined_registration.py small_pine_inputs/source.npy small_pine_inputs/anchors.npz LNDP_S5_on_S5/predicted_motion/small_pine_anim_42_0_2_out.npz small_pine_registered.npz --up 0 0 1
```

The first command uses NumPy and runs on the CPU. It checks the merged MV prediction and every expected regular patch against a frozen inventory. It constructs the source union in the original benchmark row order and verifies its SHA-256. Each row of `anchors.npz` is a predicted source/target correspondence with its confidence before thresholding. The second command produces `s_pc`, `t_pc` and `s2t_flow`, the estimated source-to-target displacement in metres at each source row. The S5 simulation uses positive Z as physical up.

The published `*_out.npz` alone contains the predicted displacement field. The original evaluation script does not export the matching network's correspondence confidence. Ground-truth correspondences and motion fields from labelled patch files are unsuitable as model inputs. The companion ZIP holds the correspondence predictions computed during the original-pair WindReg benchmark. It is specific to the published S5 scan instances.

## Recomputing S5 correspondences with the author's matcher

Use the author's working Tree-LNDP GPU environment with the prepared `DeformationPyramid` repository, S5 correspondence configs and both compiled KPConv wrappers (`correspondence/cpp_wrappers`). This path also needs the WindReg wheel installed, PyTorch, PyYAML, and EasyDict. The S5 weights directory must contain `plants_S5_stems_weights.pth` and `outlier_S5_stems_weights.pth`. The original config and checkpoint hashes are checked before inference.

The data deposit contains a bare Git repository at `02_code/04_Non-rigid_registration_methods/DeformationPyramid.git`. Clone it to obtain the source tree. The S5 development branch is `plants_modern` at commit `351cc74a5aa27783f88c49512210991902db32ea`. Follow the repository's KPConv build instructions for your GPU environment.

```sh
git clone --branch plants_modern 02_code/04_Non-rigid_registration_methods/DeformationPyramid.git DeformationPyramid
```

```sh
python prepare_paper_pair.py S5_patches/test LNDP_S5_on_S5/predicted_motion/small_pine_anim_42_0_2_out.npz fresh_pine_inputs --author-repo DeformationPyramid --weights 03_model_weights
```

The optional matcher adapter reads observed coordinates from each regular patch, applies the same centering and neighborhood calibration, and restores predicted match coordinates to the common scan frame. It uses the regular target crops supplied with the S5 data. Raw matching depends on the installed GPU runtime and native extensions. The cache provides the exact correspondence values used in the reported S5 experiment. The license for the optional GPL-3.0 matcher integration in `tree_match.py` is included as `GPL-3.0.txt`.
