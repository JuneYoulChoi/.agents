# Configuration format selection

Choose a format from project evidence and operator needs; do not impose one
format across repositories.

| Mechanism | Prefer when | Watch for |
| --- | --- | --- |
| Environment variables | Small deploy-time overrides, containers, secret references | Strings need typed parsing; naming and empty-value semantics must be explicit |
| Command-line flags | Process-local explicit overrides and diagnostics | Secret leakage through process listings and shell history |
| JSON | Strict machine interchange and existing JSON tooling | No standard comments; verbose for operator-edited files |
| YAML | Human-edited nested configuration and an established safe parser | Implicit types, duplicate keys, unsafe tags, indentation errors |
| TOML | Human-edited typed application configuration | Ecosystem/parser compatibility and merge semantics |
| Java properties | Existing JVM/Spring conventions and flat settings | Weak typing and escaping rules |

Prefer one primary non-secret file format plus environment or secret overrides.
Multiple formats require one normalized typed model and documented precedence.
Reject duplicate keys when the parser supports detection. Parse untrusted YAML
with safe data-only behavior and never construct arbitrary objects.

Do not use configuration files for high-frequency domain data, mutable business
records, or values requiring transactional coordination; use the appropriate
data store or control plane instead.
