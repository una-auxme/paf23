# Discontinued — archival only

The ROS 1 packages in this directory (`sim`, `potential_field`, `teb_planner`) are
**discontinued** and kept only for historical reference. They are **not built** and
**not distributed** in any released container image (the agent image is built only
from `code/`).

These packages are project-internal code, originally authored by PAF contributors
(e.g. `VinzenzMalke`) during earlier ROS 1 iterations of the course (they publish on
`/paf/hero/*` and `/carla/hero/*` topics). They were created with `catkin_create_pkg`,
which is why they previously carried the default `<license>TODO</license>` and a
`winni@todo.todo` maintainer placeholder. Their `<license>` has been set to **MIT** to
match the repository license, which is correct because the code is project-internal
(not vendored third-party code).

If this code is ever revived or shipped, it must be re-reviewed for provenance and
updated to the current ROS 2 / `code/` architecture.
