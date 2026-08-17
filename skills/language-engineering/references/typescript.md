# TypeScript implementation profile

- Apply the JavaScript profile, then detect TypeScript version, `strict`
  options, project references, module resolution, emit owner, and generated
  declaration/code paths.
- Prefer precise domain types, discriminated unions, narrowing, and `unknown`
  at untrusted boundaries. Avoid `any`, non-null assertions, and casts that
  merely silence an unproven contract.
- Remember that types disappear at runtime. Validate external/config/API data
  and keep runtime schema and generated-client ownership explicit.
- Separate transport/generated models from stable domain models when their
  compatibility or release cadence differs.
- Preserve established path/module/build conventions. Do not duplicate types
  that can be generated from an authoritative schema.
- Verify type-check without relying only on transpilation, lint/format, tests,
  declaration/API compatibility when published, runtime validation, browser or
  Node target matrix, and generated-code freshness.

Primary references: TypeScript Handbook/configuration reference, ECMAScript
runtime documentation, and selected framework/binding guidance.
