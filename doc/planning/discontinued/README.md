# Discontinued — archival only

The ROS 1 package in this directory (`mock`) is **discontinued** and kept only for
historical reference. It is **not built** and **not distributed** in any released
container image (the agent image is built only from `code/`).

This package is project-internal code (a mock-node test harness used during earlier
ROS 1 iterations of the course). It was created with `catkin_create_pkg`, which is why
it previously carried the default `<license>TODO</license>`. Its `<license>` has been
set to **MIT** to match the repository license, which is correct because the code is
project-internal (not vendored third-party code).

If this code is ever revived or shipped, it must be re-reviewed for provenance and
updated to the current ROS 2 / `code/` architecture.
