# C++ implementation profile

- Detect the C++ standard, compiler/stdlib, CMake or other build system,
  exception/RTTI policy, ABI boundary, and target constraints.
- Prefer value semantics and RAII. Use explicit ownership; default to automatic
  storage and standard smart pointers rather than raw owning pointers.
- Keep public interfaces narrow, const-correct, and free of unnecessary
  implementation types. Treat ABI, allocation, exceptions, and STL types
  carefully across shared-library or language boundaries.
- Express invariants with types and constructors. Avoid partially initialized
  objects, hidden lifetime coupling, unchecked casts, and manual lock/unlock.
- Define exception vs status/error policy from the project and ecosystem
  binding. Never throw across a C ABI or an incompatible callback boundary.
- Give every thread, callback, executor, and asynchronous operation an owner,
  cancellation/shutdown rule, and synchronization strategy.
- Preserve generated files and existing formatter/linter/static-analysis
  configuration. Do not introduce template or dependency complexity without a
  measured requirement.
- Verify build variants, unit/integration tests, warnings, sanitizer/static
  analysis where supported, concurrency shutdown, performance QAS, and ABI or
  wire compatibility.

Primary references: the detected ISO C++ version, C++ Core Guidelines where
adopted, compiler/build documentation, and the framework binding contract.
