# C implementation profile

- Detect the language standard, compiler, target ABI, build system, warning
  policy, sanitizer availability, and embedded/real-time constraints.
- Make ownership and lifetime explicit for every pointer and buffer. Document
  who allocates, mutates, transfers, and frees resources.
- Use fixed-width types only where representation is part of a protocol or
  storage contract. Validate size, alignment, endian, bounds, and integer
  conversion at external boundaries.
- Prefer small modules with private state, narrow headers, include guards, and
  no hidden cross-module mutable globals.
- Define error results and cleanup paths. Avoid unchecked allocation, I/O,
  indexing, format strings, and partial initialization.
- Treat signal handlers, interrupts, callbacks, and threads as distinct
  concurrency contexts; state which operations are safe in each.
- Preserve the project's formatter, static analyzer, compiler warnings, unit
  test framework, and coverage/sanitizer configuration.
- Verify representative target builds, warnings-as-errors where established,
  boundary/error paths, resource cleanup, sanitizers/static analysis when
  available, and protocol/ABI compatibility.

Primary references: ISO C implementation requirements, compiler documentation,
project coding standard, and CERT C when the project adopts it.
