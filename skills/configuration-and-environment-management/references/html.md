# HTML configuration boundary

Treat HTML as a public presentation and bootstrap boundary, not as a private
application configuration store.

- Put only small, non-secret bootstrap values in `data-*` attributes or `meta`
  elements. Escape them for their exact HTML attribute or text context.
- For substantial client runtime configuration, fetch a versioned public JSON
  document through the TypeScript/JavaScript bootstrap, validate it before
  rendering, and define missing, malformed, timeout, retry, cache, and rollback
  behavior.
- When deployment substitutes values into static HTML, use a context-aware
  renderer with an allowlist. Never use unrestricted text replacement for
  URLs, markup, scripts, or JSON, and never inject credentials or private
  endpoints.
- Define base-path, origin, CSP, localization, cache-control, and version
  compatibility behavior when they affect startup. A client-visible endpoint
  is public even when the HTML source is generated server-side.
- Prefer semantic native HTML. Prettier may format an established frontend
  project, and html-validate may enforce structural rules, but neither is a
  runtime configuration dependency.

Test HTML escaping, CSP compatibility, public-config schema validation,
unavailable or stale config, base-path deployment, cache invalidation, and the
absence of secrets in the response and generated artifacts. Use
[typescript.md](typescript.md) when a script loads or validates the public
configuration, and read [tool-selection.md](tool-selection.md) before adding a
formatter or validator.
