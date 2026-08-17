# Python configuration adapter

Prefer the project's existing settings mechanism. Pydantic Settings or another
typed library may be used when already approved, but it is not a core
dependency.

- Normalize file, environment, command-line, and secret-provider values into
  one typed settings object at the application boundary.
- Use explicit types and validators for URLs, addresses, ports, durations,
  paths, enums, and related-field constraints.
- Avoid module-import side effects that read configuration before tests or
  application initialization can control the environment.
- Inject settings into services instead of calling `os.environ` throughout
  business code.
- Define case sensitivity, prefixes, nested-key syntax, empty values, and source
  precedence explicitly.
- Test isolated environments, invalid values, default behavior, source
  precedence, secret representations, and compatibility aliases.

Do not add a settings package without the normal dependency, license, security,
and migration review.
