---
name: language-engineering
description: Apply implementation-language-specific engineering rules after architecture and ecosystem selection. Use when creating, changing, reviewing, debugging, refactoring, optimizing, or testing code in C, C++, C#, Rust, Go, Java, Python, JavaScript, TypeScript, HTML, CSS, Shell, or a mixed-language module, especially when an ecosystem skill needs a concrete language binding and idiomatic implementation profile.
---

# Language Engineering

Translate an approved module and ecosystem contract into idiomatic, safe,
testable code. Let ecosystem skills decide domain architecture; let this skill
decide language-level structure, types, ownership, errors, concurrency, build,
and verification.

## Entry gate

Require intake, architecture, and the applicable Greenfield design or
Brownfield impact record. Require a selected/detected ecosystem technology when
the language is used through a framework binding. Do not select a language
solely because the agent prefers it.

This is a `G5` specialist branch. Activate one instance per changed authored
language boundary and keep unrelated or generator-owned language profiles
suppressed. A language/build failure may reopen `G5`; a pure implementation
defect returns to `G6` without reclassifying unaffected technology branches.
`language_scope` must be `authored_in_scope`; a language that is merely
detected, generated, or mentioned in documentation does not activate this
skill.

## 1. Detect the implementation context

Inspect manifests, build files, source extensions, lockfiles, generated-code
markers, compiler/runtime configuration, tests, formatting/lint configuration,
and CI. Record language version, toolchain, module owner, framework binding,
generated vs authored files, and project conventions.

Brownfield conventions win when maintained, safe, and compatible. A toolchain,
edition, module-system, formatter, or dependency change requires impact and
approval review.

## 2. Load only the matching profile

- C: [references/c.md](references/c.md)
- C++: [references/cpp.md](references/cpp.md)
- C#: [references/csharp.md](references/csharp.md)
- Rust: [references/rust.md](references/rust.md)
- Go: [references/go.md](references/go.md)
- Java: [references/java.md](references/java.md)
- Python: [references/python.md](references/python.md)
- JavaScript: [references/javascript.md](references/javascript.md)
- TypeScript: [references/typescript.md](references/typescript.md)
- HTML: [references/html.md](references/html.md)
- CSS: [references/css.md](references/css.md)
- Shell: [references/shell.md](references/shell.md)

Load one profile per changed implementation boundary. Load multiple profiles
only for genuinely mixed authored code or a public HTML/CSS boundary. Generated
gRPC/ROS/schema output is not hand-edited; load the producer language and
generator contract instead.

## 3. Reconcile ecosystem and language rules

Use this precedence:

```text
user-approved requirement and architecture contract
> accepted architecture/design pattern constraints
> official ecosystem binding contract
> project build/test/style convention
> language safety and idiom profile
> general recommendation
```

Record conflicts. Do not force a generic language pattern that violates an
ecosystem lifecycle, serialization, ownership, real-time, or generated-code
contract.

## 4. Produce an implementation profile

```yaml
implementation_profile:
  module: ''
  ecosystem_skills: []
  language: ''
  language_version: ''
  binding: ''
  profile_loaded: ''
  authored_paths: []
  generated_paths: []
  build_toolchain: []
  conventions: []
  error_model: ''
  ownership_and_lifecycle: ''
  concurrency_model: ''
  configuration_contracts: []
  verification: []
  documentation_effects: []
  open_points: []
transition:
  next_stage: clarification | design | execution | verification
  next_skill: ''
  entry_conditions: []
```

## Exit gate

Block material execution when the language/binding version is unknown and
material to correctness, generated files would be hand-edited, ownership or
error behavior is undefined at a public boundary, or required build/test
evidence is unavailable. Route configuration candidates to
`$configuration-and-environment-management` and completed work to
`$verify-and-handoff`.
