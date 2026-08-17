# colcon workspace engineering practices

## Workspace and package graph

- Record the workspace root, source roots, package names/types, ignored paths,
  manifests, build/run/test dependencies, generated interfaces, and external
  underlay. Package manifests/build files remain authoritative; do not encode
  missing dependencies only in build order or shell setup.
- Treat an underlay as immutable input and an overlay as a deliberate override.
  Record sourcing order and every overridden package/API/ABI compatibility
  expectation. Use a clean shell for reproducibility checks.
- Keep `build`, `install`, and `log` as generated artifacts outside source
  ownership. Decide isolated vs merged install from isolation, path length,
  packaging, and platform needs; merged install can mask undeclared dependencies.

## Build, test, and configuration

- Pin colcon and required extension compatibility. Keep `defaults.yaml`, mixins,
  `.meta`, and `colcon.pkg` scoped, reviewed, and documented; do not hide a
  project requirement in a developer-global config.
- Select packages with their required dependencies for clean builds and include
  dependents for regression when a public package contract changes. Distinguish
  quick incremental evidence from clean acceptance evidence.
- Use symlink install only where development semantics support it; verify the
  packaged/copied install path separately when release behavior differs.
- Bound parallel workers and resources from CI/developer evidence. Cache only
  artifacts whose key covers OS/toolchain, underlay, package manifests, build
  options, and relevant sources; a stale cache is not a passing build.

## Verification and anti-patterns

- Verify package discovery/graph, clean build, targeted incremental build,
  install/local setup in a clean shell, unit/integration/launch tests,
  `colcon test-result`, generated output, overlay override behavior, and CI.
- Reject committed build/install/log artifacts, undeclared dependencies masked
  by merged installs, ambient global mixins, sourcing multiple unknown overlays,
  ignoring failed test results, and validating only the package that changed
  when downstream contracts are affected.

Primary sources: version-matched colcon core/extension documentation, package
build-system documentation, and the selected ROS/ecosystem build guidance.
