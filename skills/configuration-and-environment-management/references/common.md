# Common configuration contract

## Design principles

- Separate application behavior from environment-specific values.
- Prefer one typed configuration object at the application boundary instead of
  reading environment variables or files throughout business code.
- Preserve the project's established mechanism unless evidence justifies a
  migration.
- Make source precedence explicit and deterministic.
- Validate once at startup or at the controlled reload boundary.
- Keep safe non-secret defaults reviewable; require explicit values when a
  default could connect to the wrong system, weaken security, or hide an error.
- Pass configuration into modules through constructors or explicit interfaces;
  avoid ambient global reads where practical.

## Default precedence

Use the project's existing order when documented and safe. Otherwise propose:

```text
explicit command-line argument
> environment variable or secret reference
> environment/profile configuration file
> shared non-secret configuration file
> safe code default
```

Do not let the same key have multiple undocumented names. If a legacy alias is
needed, define which name wins, emit a non-secret deprecation warning, and set a
removal condition.

## Validation and failure

Validate types plus semantic constraints such as port range, URL scheme,
address syntax, duration bounds, positive pool sizes, allowed enum values,
required path permissions, and mutually dependent settings. Aggregate safe
validation errors when useful, but fail before network listeners, migrations,
or external side effects begin.

For dynamic reload, define atomic snapshot replacement, reader consistency,
rejection of invalid updates, audit evidence, and rollback to the last valid
snapshot. Default to startup-only loading when dynamic reload is not required.

## Documentation split

Architecture documentation records configuration boundaries, source ownership,
precedence, security strategy, and deployment/runtime relationships. A key
reference records name, purpose, type, required/default behavior, supported
sources, example placeholder, reload behavior, and deprecation status. Never
publish real production endpoints or secret values merely to make an example
look complete.
