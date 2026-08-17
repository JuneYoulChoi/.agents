# Rust configuration adapter

Prefer the project's existing serialization and configuration stack. A common
shape is typed deserialization into application-owned structs, but no crate is
mandatory.

- Define typed structs for the normalized configuration and use dedicated types
  for addresses, ports, URLs, paths, durations, sizes, and enums.
- Merge sources deterministically before deserialization or through an existing
  layered loader; preserve one documented winner for every key.
- Validate semantic relationships after parsing and return contextual errors
  without formatting secret values.
- Load once and pass shared immutable configuration through explicit application
  state. Use a validated snapshot mechanism only when reload is required.
- Distinguish Cargo features and compile-time environment values from deploy-
  time application settings; production endpoints should not require rebuilds.
- Test unknown/duplicate fields according to the compatibility policy, invalid
  Unicode or paths where relevant, source precedence, redaction, and legacy key
  migration.

Adding a configuration or serialization crate is a dependency change and must
follow the Brownfield/Greenfield dependency, license, and security decision.
