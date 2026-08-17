---
name: react-engineering
description: Design, implement, review, debug, refactor, optimize, or verify React web or native user interfaces. Use for React components, hooks, state ownership, effects, rendering, routing/data boundaries, forms, accessibility, design systems, hydration or server/client boundaries, frontend testing, React performance, or migration of an existing React application.
---

# React Engineering

Design around user interactions, component ownership, and accessible platform
semantics. React is a UI library; detect the host framework/build/runtime before
applying project structure rules.

## Entry gate

Require intake, UI/architecture evidence, and the React `TECH-*` record.
Brownfield work requires detected React/host framework versions, rendering
mode, component/state/data conventions, design system, tests, and browser/native
targets.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Map UC and interaction states to component boundaries, data ownership,
   loading/error/empty/success states, and accessibility behavior.
3. Keep state minimal and closest to its owner; derive rather than synchronize
   redundant state. Use effects only to synchronize with external systems.
4. Invoke `$language-engineering` for TypeScript/JavaScript and directly
   affected HTML/CSS boundaries. Node.js is a separate production-runtime
   selection even when used for building.
5. Route public bootstrap/theme values through configuration with an explicit
   non-secret contract; never place credentials in a client artifact.
6. Verify component behavior, accessibility, interaction/E2E, responsive and
   error states, rendering/performance QAS, and architecture/design docs.

## Result and exit

Return host/rendering mode, component and state ownership, data/effect
boundaries, language profiles, accessibility contract, configuration,
verification, docs, and open points. Block implementation when user-facing
states, ownership, accessibility, or server/client/public-data boundaries are
materially ambiguous.
