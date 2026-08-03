# Incoming skills inventory

Downloaded on 2026-08-03. These are **source candidates**, not active skills.
They must be reviewed for licence, third-party tools, data access, and fit with
the universal intake/router before promotion to `skills/`.

| Source | Licence to verify at promotion | Installed skill count | Staging paths |
| --- | --- | ---: | --- |
| `obra/superpowers` | MIT | 10 | `incoming/superpowers/` |
| `anthropics/skills` | repository-specific / source-available components | 6 | `incoming/documentation/` |
| `mattpocock/skills` | MIT | 8 | `incoming/lifecycle/` |
| `wshobson/agents` | upstream licence | 4 | `incoming/design/` |
| `0xbigboss/claude-code` | upstream licence | 5 | `incoming/languages/` |
| `rmyndharis/antigravity-skills` | upstream licence | 10 | `incoming/quality/` |
| `novotnyllc/dotnet-artisan` | upstream licence | 4 | `incoming/languages/` |
| `github/awesome-copilot` | upstream licence | 1 | `incoming/lifecycle/prd/` |
| `pbakaus/impeccable` | upstream licence | 1 | `incoming/design/impeccable/` |
| `mindrally/skills` | upstream licence | 1 | `incoming/languages/rust/` |

## Promotion rule

1. Pin the upstream commit and confirm the licence.
2. Read the complete `SKILL.md` and all required referenced resources.
3. Declare runtime/tool/network/data dependencies and scope restrictions.
4. Adapt the entry and transition contract for the shared router.
5. Place the reviewed result in `skills/`; leave the original here unchanged.

`mcp-builder` is temporarily grouped under `incoming/documentation/` only by
download destination; classify it as an integration skill during promotion.
