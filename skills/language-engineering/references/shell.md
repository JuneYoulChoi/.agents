# Shell implementation profile

- Detect the declared shell and supported platforms before choosing syntax.
  Do not present Bash-specific behavior as portable POSIX shell.
- Quote expansions, delimit options, validate paths and inputs, avoid `eval`,
  and keep globbing/word-splitting behavior intentional.
- Use strict/error modes only with semantics understood for the selected shell;
  add explicit error handling around expected non-zero commands, pipelines, and
  cleanup.
- Make temporary files/directories private and trap cleanup. Avoid destructive
  targets derived from empty variables, broad roots, unresolved substitutions,
  or unvalidated globs.
- Separate configuration from commands, redact secrets, and avoid leaking them
  through tracing, process arguments, logs, or generated files.
- Prefer small orchestration scripts over reimplementing application logic.
  Keep commands non-interactive and reproducible where automation requires it.
- Verify syntax/lint where available, paths containing spaces/newlines as
  relevant, failure and interrupt cleanup, missing tools, supported shells/OS,
  idempotence, and safe dry-run behavior for mutations.

Primary references: selected shell specification/manual, ShellCheck rules where
adopted, and project automation conventions.
