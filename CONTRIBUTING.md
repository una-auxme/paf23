# Contributing to PAF

Thank you for contributing to **PAF (Praktikum Autonomes Fahren)**! This document
records the project's contribution and licensing rules so that everyone's rights are
clear and the project stays legally distributable under its MIT license.

## 1. Inbound = Outbound (MIT)

This project is licensed under the **MIT License** (see [`LICENSE`](./LICENSE)).

> Unless you state otherwise, **every contribution you make is intentionally
> submitted to be licensed under the MIT License**, and you represent that you have
> the right to submit it under those terms.

If your contribution cannot be licensed under MIT (e.g. it is AGPL/GPL/LGPL, or it
carries a "non-commercial"/"research-only" restriction), **do not submit it** without
first discussing it with the maintainers.

The top-level `Copyright (c) 2023 UNA-AuxMe` notice is the project-level notice; it is
**not** a claim that AUXME is the sole author of every line. Individual files and
commits retain the copyright of their respective authors. Where a file has a notable
individual or third-party author, that attribution is kept in the file header or in
[`THIRD_PARTY_LICENSES.md`](./THIRD_PARTY_LICENSES.md).

## 2. Developer Certificate of Origin (DCO)

To make the licensing of contributions auditable, this project uses a light-weight
**DCO**. By submitting a pull request, you certify the statements of the
[Developer Certificate of Origin](https://developercertificate.org/). Concretely,
**every commit must be signed off**:

```bash
git commit -s -m "your message"
```

This adds a `Signed-off-by: Your Name <you@example.com>` trailer. Use your **real name
and a deliverable email** (the same identity you intend to be credited under). If you
forget `-s`, amend with `git commit --amend -s`.

When opening a PR, confirm the DCO checkbox in the pull-request template.

## 3. Third-party and copied code

If you copy, port, or substantially adapt code from another project (even a few
lines), you **must**:

1. Keep the original copyright notice and license pointer in the file (a bare URL is
   **not** sufficient for MIT/BSD — include the copyright line and a link to the
   license).
2. Verify the upstream license is **compatible with MIT** (MIT, BSD, Apache-2.0 are
   fine). **AGPL-3.0, GPL, LGPL, SSPL, CC-BY-NC-\* and any "non-commercial" license
   are not acceptable** for code that ships in the agent.
3. Add a row to [`THIRD_PARTY_LICENSES.md`](./THIRD_PARTY_LICENSES.md).

> Do not introduce `ultralytics` (AGPL-3.0) or any AGPL/GPL dependency into the
> shipped agent. This project already removed Ultralytics once for exactly this
> reason; CI (`.github/workflows/license-check.yml`) will fail the build if it
> reappears.

## 4. Models and datasets

If you add or retrain a model, update [`code/perception/MODELS.yaml`](./code/perception/MODELS.yaml)
with its name, version, sha256, source, license, initial checkpoint, training data
and redistribution basis. Never commit model weights whose license is unclear.

## 5. Distribution note

The primary thing users receive is the **container image**, not just the Git
repository. Anything installed by the Dockerfile (`build/docker/agent-ros2/Dockerfile`)
becomes part of the distributed deliverable, so new system/Python/git dependencies
added there are subject to the same license rules as code.
