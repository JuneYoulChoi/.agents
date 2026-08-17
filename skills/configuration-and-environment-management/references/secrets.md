# Secret configuration

Classify credentials, tokens, private keys, client secrets, sensitive DSNs, and
equivalent values as secrets. Store only secret identifiers or provider
references in ordinary configuration.

## Required controls

- Do not commit real secrets, local secret files, generated credentials, or
  decrypted output.
- Use placeholder-only examples and ensure local override files are ignored by
  version control when the project permits them.
- Prefer the deployment platform's approved secret provider; environment
  variables are a transport mechanism, not automatically a secure store.
- Scope access by environment and workload identity; avoid one credential
  shared across development, test, and production.
- Redact values from logs, exceptions, diagnostics, task state, test snapshots,
  command history, and generated documentation.
- Define rotation, revocation, missing-secret failure, and rollback behavior.
- Prevent secret values from being used as map keys, metric labels, cache keys,
  or equality-test output.

Tests use synthetic values and assert both successful lookup and non-disclosure.
Accessing a real secret or external secret manager remains an approval-bound
action under the harness authority rules.
