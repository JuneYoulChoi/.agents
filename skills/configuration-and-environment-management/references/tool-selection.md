# Configuration tool selection

Use popularity as discovery evidence, not as an automatic dependency grant.
Preserve a safe, maintained project convention before introducing a new tool.

## Selection rule

1. Define one functional role: environment parsing, schema validation,
   configuration discovery, CLI parsing, formatting, linting, or testing.
2. Compare tools only within the same ecosystem, role, and measurement window.
3. Prefer a language or browser standard-library mechanism when it satisfies the
   contract without fragile custom parsing.
4. Review maintenance, release recency, license, security, transitive
   dependencies, runtime size, supported platforms, and migration cost.
5. Record the source, metric type, measurement window, review date, rationale,
   owner, and revisit trigger. Download or importer counts never override an
   incompatible architecture or an established safe project mechanism.

## Reviewed popularity evidence

The following evidence was reviewed on 2026-08-17. Counts are volatile and
must be refreshed before using them for a material dependency decision.
The evidence owner is the shared-harness maintainer; revisit it on a dependency
decision, a material upstream change, or after 90 days. npm counts came from
the official package-specific [Downloads API](https://github.com/npm/registry/blob/main/docs/download-counts.md),
Homebrew counts from its [30-day install analytics](https://formulae.brew.sh/api/analytics/install/30d.json),
and Go importer counts from the linked pkg.go.dev pages. This review establishes
candidate popularity only; it does not complete license, security, maintenance,
compatibility, or migration approval.

| Ecosystem and role | Candidate evidence | Measurement |
| --- | --- | --- |
| TypeScript environment files | [dotenv](https://www.npmjs.com/package/dotenv) | 145,783,235 npm downloads, 2026-08-09 through 2026-08-15 |
| TypeScript schema validation | [Zod](https://www.npmjs.com/package/zod) | 224,127,336 npm downloads, same week |
| TypeScript configuration discovery | [cosmiconfig](https://www.npmjs.com/package/cosmiconfig) | 85,691,037 npm downloads, same week |
| TypeScript CLI | [Commander](https://www.npmjs.com/package/commander) | 414,820,145 npm downloads, same week |
| HTML formatting | [Prettier](https://www.npmjs.com/package/prettier) | 111,128,037 npm downloads, same week |
| HTML validation | [html-validate](https://www.npmjs.com/package/html-validate) | 420,937 npm downloads versus HTMLHint 176,346, same week |
| CSS transformation | [PostCSS](https://www.npmjs.com/package/postcss) | 233,884,569 npm downloads, same week |
| CSS linting | [Stylelint](https://www.npmjs.com/package/stylelint) | 9,117,991 npm downloads, same week |
| CSS preprocessing | [Sass](https://www.npmjs.com/package/sass) | 20,567,534 npm downloads, same week |
| Shell JSON/YAML | [jq](https://jqlang.org/) / [yq](https://github.com/mikefarah/yq) | 77,520 / 47,914 Homebrew installs, 2026-07-18 through 2026-08-17 |
| Shell static analysis/format/test | [ShellCheck](https://www.shellcheck.net/), [shfmt](https://github.com/mvdan/sh), [Bats](https://bats-core.readthedocs.io/) | 29,956 / 8,519 / 11,409 Homebrew installs, same 30-day window |
| Go multi-source configuration | [Viper](https://pkg.go.dev/github.com/spf13/viper) | imported by 103,320 packages at review time |
| Go CLI | [Cobra](https://pkg.go.dev/github.com/spf13/cobra) | imported by 195,884 packages at review time |
| Go validation | [validator](https://pkg.go.dev/github.com/go-playground/validator/v10) | imported by 24,133 packages at review time |
| Go environment parsing | [caarlos0/env](https://pkg.go.dev/github.com/caarlos0/env/v11) | imported by 1,037 packages at review time; zero-dependency parser |

npm downloads, Homebrew installs, and Go `Imported by` counts are different
signals and must never be ranked against one another. Tool documentation is a
design input; the skill has no network or package-manager runtime dependency.
