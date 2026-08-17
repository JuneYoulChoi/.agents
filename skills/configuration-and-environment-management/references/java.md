# Java configuration adapter

Detect whether the project uses Spring Boot or another configuration framework
before choosing an implementation.

## Spring Boot

- Bind related settings to typed configuration properties rather than scattering
  string lookups or `@Value` expressions.
- Apply bean validation or equivalent startup validation for required values,
  ranges, formats, and cross-field rules.
- Use `application.yml` or `application.properties` consistently with existing
  conventions. Treat profiles as named environment behavior, not a place for
  committed secrets.
- Document the effective precedence across command-line arguments, system
  properties, environment variables, profile files, and packaged defaults.
- Test binding, profile selection, overrides, invalid values, deprecations, and
  sanitized diagnostics.

## Non-Spring Java

Normalize properties, environment variables, command-line arguments, or the
existing framework into one application-owned typed configuration object.
Validate before starting services and inject the result explicitly. Do not add
Spring or another large framework solely for configuration loading.

Keep build-tool properties for build variation and runtime sources for deploy-
time settings. Dependency additions require compatibility, license, and
security review.
