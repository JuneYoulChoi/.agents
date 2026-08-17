---
name: colcon-workspace-engineering
description: Design, implement, review, debug, optimize, migrate, or verify colcon multi-package workspaces and workflows. Use for ROS 1/ROS 2 or other colcon workspaces, package discovery and dependency ordering, underlays and overlays, build/install/log layouts, isolated or merged installs, symlink installs, mixins, defaults and metadata, package selection, CMake or Python package builds, tests and test results, CI caching, environment sourcing, or reproducible multi-package builds.
---

# colcon Workspace Engineering

Treat colcon as a multi-package build/test orchestrator with explicit underlay,
overlay, environment, and artifact ownership. It is selected only when the
project owns such a workspace.

## Entry gate

Require intake, build/repository architecture, a colcon `TECH-*` record, and
the relevant ecosystem skill. Brownfield work requires colcon/extensions,
workspace roots, underlays/overlays, package metadata/graph, build/install/log
layout, defaults/mixins/meta, generated code, tests, CI, and baseline commands.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Define source/package graph, dependency declarations, underlay/overlay order,
   build/install/log isolation, environment sourcing, and generated artifacts.
3. Select build/test scope from changed packages and dependency/dependent graph;
   invoke `$language-engineering` for affected C/C++/Python/etc. packages.
4. Route defaults, mixins, build flags, paths, parallelism, and CI profiles
   through configuration without hiding required package metadata.
5. Verify clean and incremental builds, selected dependency/dependent scopes,
   install/use environment, test results, generated interfaces, overlay
   behavior, CI cache correctness, and developer docs.

## Result and exit

Return versions/extensions, workspace/package graph, underlays/overlays,
artifact/environment policy, build/test profiles, language bindings,
configuration, verification, docs, and open points. Block when workspace root,
overlay order, dependency declarations, or install/test result ownership is
ambiguous.
