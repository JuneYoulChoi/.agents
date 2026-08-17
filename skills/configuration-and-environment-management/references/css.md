# CSS configuration boundary

Treat CSS variation as presentation policy. Do not use stylesheets to carry
credentials, private endpoints, operational settings, or domain data.

- Use native custom properties for runtime theme values when browser support
  and inheritance semantics satisfy the requirement. Define stable token names,
  scope, fallback, ownership, and override order.
- Keep Sass variables and other preprocess-time tokens in the `build_time`
  category. A build is required to change them, so do not present them as
  deploy-time or runtime application configuration.
- Use classes, attributes, media queries, and controlled custom-property
  updates for themes. Define server-rendering and first-paint behavior to avoid
  flashes or hydration disagreement.
- Preserve an existing PostCSS or Sass pipeline when safe. Do not introduce a
  transformer merely to externalize a few constants. Use Stylelint only as an
  approved development check, not as application configuration.
- Keep design tokens synchronized with the UI/UX source of truth and record
  contrast, reduced-motion, high-contrast, localization, and responsive
  constraints where applicable.

Test missing tokens and fallbacks, cascade and layer precedence, theme changes,
browser targets, server/client first paint, contrast, reduced motion, and the
generated CSS artifact. Read [tool-selection.md](tool-selection.md) before
recommending PostCSS, Sass, or Stylelint.
