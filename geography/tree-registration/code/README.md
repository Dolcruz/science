# Run the tree registration methods

The included example contains a complete simulated spruce patch, an upstream motion estimate and 67 predicted matches. It lets you run the same CPU implementations used in the comparison. The full published S5 benchmark uses much larger scan pairs.

## Try the included scan pair

From a clone of this repository, start in `geography/tree-registration/code`. The commands below use a fresh, activated Python 3.10 environment. For example, create it with `python -m venv .venv` and activate it with `.venv\Scripts\Activate.ps1` in PowerShell or `. .venv/bin/activate` in a POSIX shell.

```sh
python -m pip install -r requirements.txt
python refine_motion.py --paper ../example/prediction.npz refined_flow.npy
python combined_registration.py ../example/source.npy ../example/matches.npz ../example/prediction.npz registered.npz --up 0 0 1
```

The first command after installation smooths the upstream predictions. Its output has shape `(1164, 3)`, in the input prediction's row order. The second runs the full method. Its output contains `s_pc` (source), `t_pc` (target) and `s2t_flow` (displacement in metres). The registered cloud is `s_pc + s2t_flow`. Positive Z is vertical in this example. For other scans, supply the physical up direction in their coordinate system. Use a fresh output filename on each run.

| Application | Inputs |
|---|---|
| Local correction · [refine_motion.py](refine_motion.py) and [branch_motion.py](branch_motion.py) | An MV prediction archive, or source points and their predicted displacements as two aligned NPY arrays. For the separate arrays use `--source source.npy --flow predicted_flow.npy output.npy`. |
| Full method · [combined_registration.py](combined_registration.py) | Observed source union, predicted correspondences and confidences, original MV source/target/flow, physical up direction. The trained WindReg96 CPU model and its Python source are in the [bundled wheel](windreg-0.1.0-py3-none-any.whl). |
| Elastic solver · [solve.py](solve.py) and [elastic_field.py](elastic_field.py) | An observed NPZ with `source` and `target`, plus a correspondence NPZ with `source`, `target` and `confidence`. Run `python solve.py observed.npz matches.npz output.npz`. |

For an original S5 test pair, the [S5 preparation guide](PAPER_INPUTS.md) gives the data directories and the two commands from published inputs to a full prediction. The [companion cache](https://github.com/Dolcruz/science/releases/download/tree-registration-v1/s5_predicted_matches.zip) contains the 8,038,647 predicted matches for those 97 pairs. For a new acquisition, the upstream matcher must produce its own correspondences. Use predicted motion as the input field. Some labelled dataset files use the same key, `s2t_flow`, for reference motion.

## Example and verification

The example uses validation patch `spruce_deadbranches_anim_7_3_0_c18` from the authors' simulated data. `prediction.npz` contains the observed 1,164 source and 4,074 target rows and the upstream displacement prediction. `matches.npz` contains predicted coordinates and confidences. `source.npy` contains the observed source union in the full method's output order. This patch served as a software check and was outside the 97 published test pairs. [Source data and code](https://doi.org/10.11588/DATA/JQNDRP)

In the checked Python 3.10 environment the SHA-256 of the full method's `s2t_flow.tobytes()` for this example was `d452c2043f0c246e438f8004415b8b08dc650a2b2c9eb4d21ae41240b220d89f`. A separate whole-pine reproduction used public S5 inputs and all 174,614 output rows. [Score the pine output](../evidence/pine/README.md) · [Full-field verification](../evidence/pine-verification.json)

## Attribution

The WindReg implementation and local correction carry the [WindReg contributors' MIT license](LICENSE). The wheel retains Yang Li's MIT notice for the vendored deformation-pyramid modules. The optional [matcher integration](tree_match.py) adapts geometry preparation from the authors' code and carries the [GNU GPL version 3](GPL-3.0.txt). Its neural networks and weights are supplied by the original deposit. The release distributes the fitted WindReg96 model for inference.

Hannah Weiser, Ronald Tabernig and Bernhard Höfle (2026), *Reducing wind effects in multi-scan terrestrial laser scanning point clouds of trees combining LiDAR simulation and deep learning*, Forestry 99(4), cpag068. The example, S5 match cache and pine figure derive from their simulated scans. The example adds model predictions, the cache contains inferred correspondences and the figure maps endpoint errors. The underlying research data are licensed under [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). [Paper](https://doi.org/10.1093/forestry/cpag068) · [heiDATA deposit](https://doi.org/10.11588/DATA/JQNDRP)
