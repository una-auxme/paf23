# Third-Party Licenses

This project (`paf`) is distributed under the **MIT License** (see
[`LICENSE`](./LICENSE)). This file lists the third-party software, model weights, and
code that this repository uses, embeds, derives from, **or installs into its published
container image**, together with their licenses and provenance, so that the attribution
the licenses require is preserved.

- How to contribute / licensing of contributions: [`CONTRIBUTING.md`](./CONTRIBUTING.md)
- Per-model provenance, checksums and licenses: [`code/perception/MODELS.yaml`](./code/perception/MODELS.yaml)

> **License-compliance note (history).** Earlier revisions used the
> [`ultralytics`](https://github.com/ultralytics/ultralytics) package (YOLOv8 / YOLO11)
> inside the perception node and **shipped it in the published Docker image**.
> `ultralytics` is **AGPL-3.0**, which is incompatible with this MIT-licensed project
> for the combined work. It has been removed (see `code/perception/perception/vision_node.py`
> and `code/requirements.txt`) and replaced with permissively-licensed **torchvision**
> detectors (BSD-3-Clause). CI guard: `.github/workflows/license-check.yml` fails the
> build if `ultralytics` or other copyleft/NC dependencies reappear.

---

## Embedded / derived code (in the Git repository)

| Component | License | Where | Attribution kept |
| --- | --- | --- | --- |
| CARLA Leaderboard evaluator | MIT | `code/test/run_test.py` | `Copyright (c) 2018-2019 Intel Corporation.` (authors: German Ros, Felipe Codevilla) + MIT pointer at top of file |
| CARLA ScenarioRunner (`route_manipulation.py`) | MIT | `code/planning/planning/local_planner/utils.py` — `location_to_gps()` | `Copyright (c) 2019 CVC at UAB.` in the function docstring |
| Prior PAF iterations — `ll7/psaf2`, `ll7/paf21-1` | MIT (same project lineage) | acting / planning behavior tree, global-planner helpers | source URLs cited in the affected files |

## Cloned / installed into the published image (from the Dockerfile)

`build/docker/agent-ros2/Dockerfile` clones the following repositories during the
image build. They are **pinned to immutable commit SHAs** (the build fails if the
referenced branch/tag moves), so the exact code in every published image is fixed.

| Repository | Ref | Pinned commit | License |
| --- | --- | --- | --- |
| `carla-simulator/ros-bridge` | `leaderboard-2.1` | `6b7db446eadb457df53a2b72cc75d4829f82cab4` | MIT |
| `carla-simulator/scenario_runner` | `leaderboard-2.1` | `d7bcaf0dee05fdfd720bda45740b8c9f11ee478a` | MIT |
| `Zelberor/leaderboard` (fork of CARLA leaderboard) | `leaderboard-2.1` | `44f0b4b2257f1879a39950c8da06fe4982d3d16b` | MIT — `Copyright (c) 2019 CARLA` |
| `Box-Robotics/ros2_numpy` | `jazzy` | `d5ebf723e1d2457d36fa89bf021b212e340c3c11` | Apache-2.0 |
| `splintered-reality/py_trees_ros` | `2.3.0` | `0101e9d0959c23932cf5044f89a4670e05f6526b` | BSD-3-Clause |
| `splintered-reality/py_trees_ros_interfaces` | `2.1.1` | `14216c2ee6646ebf6cfc6385061723d5820e2720` | BSD-3-Clause |
| `splintered-reality/py_trees_ros_viewer` | `0.2.5` | `9260e59479415150492f052ac2308c1f3d022a8f` | BSD-3-Clause |
| `ros2/geometry2` (single header file, `tf2_eigen.h`) | pinned commit | `1621942bc2ad1270ee0bfc1f6b7a44a5849a7b5e` | BSD-3-Clause |
| `ghcr.io/una-auxme/carla-leaderboard-api:2.1` (CARLA PythonAPI) | tag `:2.1` | *(not digest-pinned yet — see "Remaining work")* | MIT (CARLA) |

> Licenses of the Ubuntu base image, ROS 2 packages, NVIDIA/CUDA toolkit, and all
> transitive pip/apt dependencies are inventoried by the **SPDX SBOM** the build
> workflow attaches to each published image (see below). That SBOM, not this file,
> is the authoritative per-image license inventory.

## Runtime Python dependencies

Only packages that impose attribution or copyleft obligations are listed. Full
version pins are in `code/requirements*.txt`. All are permissive.

`torch` / `torchvision` (BSD-3-Clause), `numpy` (BSD-3-Clause),
`opencv-python` (Apache-2.0), `scikit-learn` (BSD-3-Clause, DBSCAN in `vision_node.py`),
`shapely` (BSD-3-Clause), `py_trees` (BSD-3-Clause), `transforms3d` (BSD-2-Clause),
`pymap3d` (BSD-2-Clause), `cython` (Apache-2.0), `debugpy` (MIT), `ruamel.yaml` (MIT),
`dvclive` (Apache-2.0), `tqdm` (MPL-2.0/MIT), `simple-pid` (MIT),
`yacs` (MIT) + `prefetch_generator` (MIT) for YOLOP.

## Models and weights

See [`code/perception/MODELS.yaml`](./code/perception/MODELS.yaml) for the full record
(name, version, sha256, source, license, training data, redistribution basis).

| Model | License | How obtained |
| --- | --- | --- |
| Traffic-light classifier (committed `.pt`) | MIT (project-owned) | Trained in-repo (DVC). From-scratch CNN, **no** pretrained backbone. sha256 in manifest. |
| torchvision COCO detectors (`fasterrcnn_resnet50_fpn_v2`, …) | BSD-3-Clause (code) + COCO terms | Auto-downloaded from `download.pytorch.org` by `vision_node.py` on first launch. |
| YOLOP | MIT | Auto-downloaded via `torch.hub.load("hustvl/yolop", ...)` by `Lanedetection_node.py`. |

## Documentation / experiments (NOT part of the shipped agent)

Under `doc/perception/experiments/`, kept for reference only.

| Component | License | Notes |
| --- | --- | --- |
| [CLRerNet](https://github.com/hirotomusiker/CLRerNet) | MIT | Cloned in the experiment Dockerfile (not the agent image). |
| [mmdetection](https://github.com/open-mmlab/mmdetection) | Apache-2.0 | Same experiment Dockerfile. |
| [super-gradients](https://github.com/Deci-AI/super-gradients) (YOLO-NAS) | Apache-2.0 code / **NC weights** | YOLO-NAS **weights** are non-commercial / research-only. One-off eval only; must not be redistributed or shipped. |
| [ultralytics](https://github.com/ultralytics/ultralytics) (YOLOv8) | **AGPL-3.0** | Used **only** by the standalone eval script `object-detection-model_evaluation/yolo.py`. Not a dependency of the shipped agent. Kept because historical benchmark results reference YOLOv8. |

---

## Published image: how license & provenance are conveyed

The deliverable users receive is the container image (`ghcr.io/una-auxme/paf`), not
only the Git repo. For each push to `main`, `.github/workflows/build.yml` publishes:

- an **immutable per-commit tag** `sha-<short>` **and** the floating `latest`;
- **OCI labels** on the image declaring, among others,
  `org.opencontainers.image.licenses = MIT`, `.source`, `.revision`, `.version`
  (set in the `agent-deploy` Dockerfile stage from CI build-args);
- a **SLSA in-toto provenance attestation** (buildx `provenance: true`) recording the
  source → image mapping;
- the **image digest** (printed to the run summary);
- an **SPDX SBOM** (`anchore/sbom-action`) uploaded as a workflow artifact, inventorying
  the installed Python/ROS/apt packages.

This is what answers *"under what license and from what source is this image conveyed?"*
in a machine-readable way.

---

## Remaining work (not auto-resolvable here)

These require a human or organisational decision and are tracked for follow-up:

1. **Image SBOM enforcement.** The SBOM step currently runs with `continue-on-error`
   until verified green on the self-hosted runner; flip to required afterwards.
2. **Pin the remaining mutable references.** `ghcr.io/una-auxme/carla-leaderboard-api:2.1`
   and the GitHub Actions in the non-build workflows (`ruff.yml`, `markdownlint.yml`,
   `drive.yml`, `add-to-project.yml`) still use moving tags. Pin them to commit SHAs
   like `build.yml` already is.
3. **Contributor-rights review by counsel.** A DCO is now in place
   ([`CONTRIBUTING.md`](./CONTRIBUTING.md)) and the PR template asks for sign-off, but
   the combined-work / contributor-rights position should be confirmed by qualified
   counsel, especially if a copyleft component is ever reintroduced.
4. **REUSE / per-file SPDX.** File-level SPDX headers (`SPDX-License-Identifier: MIT`)
   via the [REUSE](https://reuse.software/) convention would make independent file
   reuse auditable and would allow re-enabling the ROS `ament_copyright` linters.
   Not required by MIT, but recommended.
5. **Image signing.** Add `cosign` keyless signing + SBOM attestation once a signing
   identity / OIDC permissions are configured.
