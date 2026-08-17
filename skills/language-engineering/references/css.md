# CSS implementation profile

- Detect the project's cascade strategy, layers, modules/scoping, design-token
  ownership, browser support, reset, build processing, and component boundary.
- Prefer a predictable cascade and low-specificity selectors. Do not solve
  ownership problems with escalating specificity or pervasive `!important`.
- Separate semantic design tokens from component implementation values; keep
  public runtime theming limited to intentionally exposed non-secret values.
- Design mobile/responsive layouts from content constraints. Support zoom,
  text reflow, forced colors where required, reduced motion, focus visibility,
  and logical directions.
- Avoid layout/paint work unsupported by a measurable UX requirement. Treat
  animation as interaction behavior with interruption and reduced-motion rules.
- Verify supported browsers/viewports, overflow and long/localized content,
  contrast/focus/reduced motion, visual regression where established, and CSS
  build/lint output.

Primary references: CSS specifications/MDN compatibility evidence, WCAG,
project design-system rules, and host framework/build documentation.
