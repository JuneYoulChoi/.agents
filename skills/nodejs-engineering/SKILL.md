---
name: nodejs-engineering
description: Design, implement, review, debug, migrate, optimize, or verify Node.js applications, services, CLIs, workers, libraries, and build tooling. Use for Node.js runtime/version decisions, package/module layout, ESM or CommonJS, event-loop and asynchronous behavior, streams, process lifecycle, package managers, server shutdown, Node security, diagnostics, testing, or Node-based TypeScript/JavaScript systems.
---

# Node.js Engineering

Treat Node.js as a runtime with event-loop, process, package, and operational
contracts. Do not infer a server architecture merely because Node is used for
frontend tooling.

## Entry gate

Require intake, architecture, and the applicable `TECH-*` record. Brownfield
work requires detected Node version/support policy, package manager/lockfile,
module system, entrypoints, process model, framework, tests, and deployment.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Classify Node as production runtime, build runtime, CLI, worker, library, or
   mixed role and bound its modules/processes.
3. Define request/task lifecycle, async error propagation, cancellation,
   resource ownership, graceful shutdown, health, and observability.
4. Invoke `$language-engineering` with TypeScript or JavaScript from project
   evidence. Do not migrate language/module/package-manager choices implicitly.
5. Route ports, hosts, URLs, timeouts, concurrency limits, flags, paths, and
   credentials through `$configuration-and-environment-management`.
6. Verify type/lint/build/test policy, failure/shutdown behavior, event-loop and
   stream backpressure, dependency/security evidence, and supported runtimes.

## Result and exit

Return runtime role/version, module/package/process boundaries, async/error and
shutdown model, language profile, configuration contracts, verification, docs,
and open points. Block material execution when runtime/module ownership,
unhandled failure policy, shutdown, or dependency compatibility is undefined.
