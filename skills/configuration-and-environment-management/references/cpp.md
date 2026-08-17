# C++ configuration adapter

Use the repository's existing parser and dependency policy. Do not add a YAML,
JSON, or TOML library merely because C++ has no standard runtime config parser.

- Parse external sources at the executable boundary into a typed configuration
  structure with value types for addresses, ports, durations, sizes, paths, and
  enums.
- Validate before starting threads, opening listeners, connecting externally,
  or mutating data.
- Pass immutable configuration by value, reference, or constructor injection;
  avoid scattered `getenv` calls and mutable process-wide globals.
- Keep compile definitions and CMake options for true build-time variation.
  Do not require recompilation for environment-specific endpoints or ports.
- Make ownership and lifetime explicit. For reloadable config, publish a
  validated immutable snapshot atomically and retain the last valid snapshot.
- Test parser errors, numeric overflow, duration units, path encodings, source
  precedence, and backward-compatible key aliases.

If a new parser dependency is unavoidable, review its license, maintenance,
security posture, exception behavior, binary-size impact, and integration with
the existing build and package system before approval.
