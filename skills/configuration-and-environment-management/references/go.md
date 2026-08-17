# Go configuration adapter

Prefer the standard library and the project's existing packages. Parse all
external sources into one application-owned struct before starting listeners,
goroutines, migrations, or external clients.

- Use `os.LookupEnv` when absent and empty values differ, `flag` for a small
  CLI, `encoding/json` for JSON, and typed parsers such as `net/netip`,
  `net/url`, and `time.ParseDuration` for semantic values.
- Keep loading out of package `init` functions and reusable libraries. Return a
  validated configuration from the composition root and inject it explicitly.
- For environment-only struct binding, caarlos0/env is a focused candidate.
  For layered files, environment variables, flags, and defaults, Viper is a
  popular candidate, but define its precedence and key normalization explicitly,
  use an instance rather than ambient global state, and account for its
  case-insensitive keys and concurrent read/write limitation.
- Use Cobra only for an approved, non-trivial CLI command model. Use
  go-playground/validator only when its tag and validation model fits the
  project's existing conventions. Neither is required for configuration.
- Use godotenv only for an approved local-development workflow; do not treat a
  committed `.env` file as a production secret store.
- Reject unknown file fields when compatibility policy permits, and make legacy
  key aliases, deprecation warnings, and removal conditions explicit.

Use table-driven tests and `t.Setenv` where supported. Test absent versus empty
values, parse errors, integer and port bounds, duration units, URL/address
validation, source precedence, alias migration, redaction, and startup failure
before side effects. Read [tool-selection.md](tool-selection.md) before
recommending an ecosystem package.
