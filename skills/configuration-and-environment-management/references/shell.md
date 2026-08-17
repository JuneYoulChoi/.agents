# Shell configuration adapter

Detect the required shell and portability target before using Bash-specific
features. Preserve the repository's established script conventions.

- Normalize command-line flags, environment variables, approved config-file
  values, and defaults near the script entrypoint. Use the documented order
  `CLI > environment > file > safe default` unless the project contract says
  otherwise.
- Use `getopts` or the existing parser for flags. Quote expansions, distinguish
  unset from empty values, validate numeric ranges and paths, and avoid `eval`,
  untrusted `source`, or command construction from configuration strings.
- Use `jq` for JSON and `yq` for YAML only when the dependency is already
  available or approved. Do not implement a general YAML parser with `sed`,
  `awk`, or regular expressions.
- Keep secrets out of command-line arguments, `set -x` traces, process lists,
  logs, generated files, and error messages. Prefer an approved file descriptor,
  secret reference, or workload mechanism where available.
- Use ShellCheck for static analysis and shfmt for formatting when compatible
  with the target dialect. Use Bats when shell behavior needs repeatable tests;
  small scripts may use the existing test harness instead.
- Apply strict-mode options deliberately. `set -e`, `set -u`, and `pipefail`
  have dialect- and context-specific behavior and do not replace explicit error
  checks.

Test unset and empty input, whitespace/newlines/globs, malicious-looking values,
numeric boundaries, missing tools, precedence, secret redaction, exit codes,
and cleanup/rollback. Read [tool-selection.md](tool-selection.md) before adding
shell tooling.
