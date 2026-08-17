# Python implementation profile

- Detect supported Python versions, `pyproject.toml`/environment manager,
  package layout, type checker, formatter/linter, tests, and deployment entry.
- Keep import and package boundaries explicit. Avoid import-time side effects,
  ambient mutable globals, and path manipulation that hides packaging defects.
- Add useful type annotations at public and complex boundaries; validate
  external data at runtime rather than assuming annotations enforce it.
- Use context managers for resources. Define exception ownership, preserve
  causes, and avoid broad catches that turn failures into ambiguous defaults.
- Give threads, processes, tasks, event loops, cancellation, and blocking calls
  clear ownership; never block an async loop unknowingly.
- Preserve the existing environment/lock/dependency mechanism. Do not introduce
  a framework solely for convenient configuration or validation.
- Verify imports/package build, type/lint policy, unit/integration tests,
  async/error/shutdown paths, supported-version matrix, and performance or
  numerical reproducibility where required.

Primary references: Python language/library documentation, packaging guides,
and official documentation for the detected framework/binding.
