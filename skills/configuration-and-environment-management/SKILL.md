---
name: configuration-and-environment-management
description: Design, review, migrate, implement, or verify portable application configuration and environment handling. Use when software contains or introduces IPs, hosts, ports, URLs, paths, timeouts, retries, pool sizes, feature flags, credentials, environment variables, profiles, YAML/JSON/TOML/properties files, deploy-time or runtime settings, public client bootstrap or theme values, shell configuration, or environment-specific hardcoded values in C++, Rust, Java, Python, TypeScript, Go, HTML, CSS, Shell, or another language.
---

# Configuration and Environment Management

Treat configuration as a cross-cutting contract, not as a language or file-
format choice. Preserve project conventions and load only the relevant language
reference.

## Entry gate

Require an intake record and an architecture baseline attempt. For Greenfield
work, require an accepted planning/design slice. For Brownfield or Hybrid work,
require an impact record covering existing configuration behavior before
material edits. If product defaults, operator authority, compatibility, or the
acceptable secret source is unclear, return to clarification.

When configuration belongs to a selected runtime, framework, protocol,
platform, simulator, middleware, or build ecosystem, require its `TECH-*`
record and use the selected ecosystem skill to define semantic keys and
lifecycle. This skill owns externalization, source/precedence, validation,
secret separation, and migration; it does not replace ecosystem rules.

Do not use this skill to externalize every constant. Do not place secrets in
repository files, examples, logs, task state, or architecture documents.

This is a conditional `G4` concern branch. Activate it only when request,
architecture, impact, or runtime evidence contains a justified configuration
candidate. A verification failure may reopen this branch through bounded
backward feedback while preserving unrelated workflow and technology results.

## 1. Classify each candidate

Classify every candidate value as exactly one primary kind:

```text
code_constant | build_time | deploy_time | runtime | secret
```

- Keep protocol invariants and implementation constants in code unless a
  requirement says they vary.
- Keep compiler, target, and feature-build choices in the build system.
- Externalize environment-dependent deployment and runtime values.
- Treat credentials, tokens, private keys, and equivalent sensitive values as
  secret references, never ordinary configuration values.

Record evidence for the classification. Avoid speculative configurability: a
new setting needs an owner, supported variation, validation rule, and test.

## 2. Discover the existing configuration model

Inspect current config files, command-line flags, environment variables, secret
providers, deployment manifests, defaults, startup code, tests, and operator
documentation. Establish the actual precedence and failure behavior before
changing them. In Brownfield work, preserve existing keys and semantics unless
an approved migration and compatibility window exist.

Read [references/common.md](references/common.md) for the common contract and
[references/config-formats.md](references/config-formats.md) when selecting or
changing a format. Read [references/secrets.md](references/secrets.md) whenever
sensitive values or production configuration are in scope. Read
[references/tool-selection.md](references/tool-selection.md) before proposing a
new configuration dependency or using popularity as selection evidence.

## 3. Define the configuration contract

For every externalized setting, record:

```yaml
key: ''
kind: build_time | deploy_time | runtime | secret
purpose: ''
type: ''
required: true
safe_default: null
sources: []
precedence: []
validation: []
secret: false
owner: ''
reload: startup | dynamic | not_applicable
compatibility: ''
deprecation: null
redaction: ''
tests: []
documentation: []
```

Use typed parsing and fail fast before serving traffic or performing side
effects. Error messages identify the invalid key and expected constraint while
redacting sensitive values. Do not silently coerce invalid or missing critical
settings.

## 4. Apply the language adapter

Detect the implementation language and framework from project evidence, then
read only the matching reference:

- C++: [references/cpp.md](references/cpp.md)
- Rust: [references/rust.md](references/rust.md)
- Java: [references/java.md](references/java.md)
- Python: [references/python.md](references/python.md)
- TypeScript/JavaScript: [references/typescript.md](references/typescript.md)
- Go: [references/go.md](references/go.md)
- Shell: [references/shell.md](references/shell.md)
- HTML public bootstrap boundary: [references/html.md](references/html.md)
- CSS theme/token boundary: [references/css.md](references/css.md)

Read exactly one primary implementation-language reference for each
configuration producer. Also read the HTML or CSS boundary reference only when
that configuration is rendered into those public artifacts. A frontend may
therefore use the TypeScript reference plus the directly affected HTML/CSS
boundary without loading unrelated language guidance.

For an unlisted language, apply the common contract and the project's existing
typed configuration mechanism. Do not introduce a dependency solely because a
reference names an ecosystem pattern; dependency changes require impact,
license, security, and approval review.

If `$language-engineering` is selected for the implementation slice, its
language profile owns general code idioms while this skill's corresponding
reference owns configuration-specific mechanisms. Record both without loading
unrelated language profiles.

## 5. Test, document, and transition

Test safe defaults, each supported source, precedence, invalid and missing
values, boundary values, compatibility aliases, and secret redaction. Include
restart/reload and rollback behavior when operationally relevant.

Keep the architecture-level model under `docs/architecture/` when it affects
external interfaces, deployment, security, modules, or runtime behavior. Put
the operator/developer key reference in the project's established documentation
location. Document schemas and examples without real secrets or machine-
specific production values.

Return:

```yaml
configuration:
  status: confirmed | draft | migrated | conflicted
  primary_language: ''
  boundary_contexts: []
  references_loaded: []
  candidates: []
  retained_constants: []
  externalized: []
  sources: []
  precedence: []
  secret_strategy: ''
  compatibility: []
  tool_selection_evidence: []
  artifacts: []
  validation: []
  documentation: []
  open_points: []
transition:
  next_stage: clarification | design | execution | verification
  next_skill: ''
  entry_conditions: []
```

## Exit gate

Do not proceed to material execution when a required setting lacks a source,
type, validation, owner, or secret strategy; when precedence is ambiguous; or
when a Brownfield key migration lacks compatibility and rollback. Route
completed implementation to `$verify-and-handoff`.
