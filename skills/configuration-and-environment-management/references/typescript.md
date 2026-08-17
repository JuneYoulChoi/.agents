# TypeScript configuration adapter

Detect the runtime first: Node.js, browser, server-side rendering, build tool,
CLI, edge runtime, or a mixture. Preserve the framework's established public
and server-only environment-variable rules.

- Normalize configuration into one application-owned typed object at the
  composition boundary. Do not read `process.env`, import-meta environment
  values, or files throughout business modules.
- For Node.js, distinguish an absent variable from an empty string, parse
  booleans and numbers explicitly, and validate URLs, ports, durations, paths,
  enums, and cross-field constraints before side effects.
- Use `.env` loading only for an approved local-development workflow. Do not
  make dotenv files a production secret store or auto-load them from reusable
  library modules.
- Expose only explicitly public values to browser bundles. Treat every shipped
  JavaScript value, source map, HTML attribute, and fetched client config as
  public; prefixes such as `PUBLIC_` are naming controls, not secrecy controls.
- Use JSON or the project's existing parser for configuration files. Add a
  discovery layer such as cosmiconfig only when a CLI or developer tool truly
  needs multiple conventional locations; define search roots, precedence, and
  stop conditions so the current working directory cannot select an unintended
  file.
- Use the existing schema validator when present. Zod is a popular candidate
  for new typed validation, but it remains an ordinary dependency decision.
  Use Commander only when the approved CLI contract needs its command/flag
  model; prefer the existing CLI mechanism otherwise.

Test server/client separation, absent and empty values, invalid numeric input,
URL and port bounds, source precedence, config-file discovery roots, build-time
replacement, and secret absence from emitted bundles. Read
[tool-selection.md](tool-selection.md) before recommending a new dependency on
popularity grounds.
