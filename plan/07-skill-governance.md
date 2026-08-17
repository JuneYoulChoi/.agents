# Skill governance and promotion

Skills are executable instruction packages, not trusted documentation. A skill
may contain scripts, resources, network instructions, or hidden assumptions.
The governance process keeps downloaded candidates inert until review.

## Trust states

```text
incoming -> reviewed -> approved -> deprecated
              \-> rejected
```

- `incoming`: downloaded source; never discoverable by the Router.
- `reviewed`: a human or approved reviewer read the complete package and
  recorded provenance, license, dependencies, and risks.
- `approved`: adapted to the transition contract and available to routing.
- `deprecated`: retained for reproducibility but never selected for new tasks.
- `rejected`: retained only as a review record; never executable.

## Promotion checklist

The reviewer MUST record:

```text
[ ] repository URL, ref, commit, download date, and checksum
[ ] license and redistribution constraints
[ ] complete SKILL.md and required referenced resources read
[ ] scripts and executable files identified and reviewed
[ ] network, MCP, credential, filesystem, and data access declared
[ ] prompt injection and untrusted repository-content boundaries checked
[ ] platform compatibility and adapter mapping checked
[ ] inputs, outputs, transition, and failure behavior adapted
[ ] test fixture or manual verification completed
[ ] owner, version, update trigger, and rollback path recorded
```

Promotion copies or adapts the source into `skills/`; it does not mutate the
original quarantine copy. An update repeats the review and changes the version.
If a promoted skill fails integrity or validation, routing rolls back to the
previous approved version or the core fallback.

The current core entries are bundled with this harness and are an explicit
integrity exception: they are eligible only when the pinned harness-source
tree manifest covers their approved `skills/<id>/SKILL.md` paths and the active
registry is separately pinned and validated. The tree manifest excludes both
registry manifests themselves to avoid recursive hashes. A missing or
placeholder pin is a pre-promotion gap, not a trust grant; bootstrap routing
must fall back to the documented core procedure or stop until the manifests
are pinned. A project registry label alone can never upgrade an `incoming`,
deprecated, unverified, or failed-integrity entry.

The two internal maintenance skills follow the same contract. An upgrade
proposal must first use `harness-upgrade-analysis` to read the complete
`plan/` baseline and produce a per-file change classification. A user-approved
plan is required before changing an active skill, registry entry, gate, or
adapter. After implementation, `harness-overview-html` may publish a derived
overview, and verification must pin the source revision and retain unresolved
items. The HTML page is never an authority source for promotion.

## Bootstrap and adapter governance

Platform bootstraps are governed artifacts, not free-form prompt files. Keep
one canonical template per adapter under `adapters/`; rendered target
`AGENTS.md`/`CLAUDE.md` files are thin, managed copies. A promotion or update
record MUST include the template ID/version, source revision and checksum,
rendered-file hashes, protocol/schema version, byte-size result, supported
platform, and rollback transaction. Validate LF-normalized UTF-8 content and
reject unresolved placeholders or files over 32 KiB.

`registry/adapter-manifest.json` is the shared provenance record for template
IDs, platform mapping, source revision/tree hash, rendered names, limits, and
install policy. Its `PENDING_PIN_BEFORE_BOOTSTRAP` values are an explicit
pre-activation gap; a target config cannot claim automatic bootstrap until the
manifest and the active registry are pinned.

The root `AGENTS.md` and `CLAUDE.md` in this repository are an explicit
self-hosted source-repository entrypoint exception. They are not target
wrappers and must retain equivalent gates, source provenance, and a clear
self-hosted role marker; target wrappers are rendered only from the canonical
adapter templates.

The target `harness.json` pins source, template, registry, state, and
enforcement metadata but cannot change skill trust, bypass quarantine, or
weaken a core MUST. Copy is the default; symlinks require explicit approval,
containment, and hash pinning. Installation is an authorized atomic mutation:
unknown or edited managed files cause a conflict and explicit upgrade rather
than silent overwrite, and rollback preserves user edits. Root resolution must
use an explicit target or an unambiguous canonical root; it must reject escape
paths and accidental selection of the shared harness repository.

Adapters declare `hook`, `manual`, or `unsupported` enforcement. Capability
loss is a compatibility event requiring fixture coverage and a documented
fallback. Read-only diagnosis may remain available, but material mutation,
external/destructive actions, approval bypass, and state-integrity operations
are not permitted without deterministic enforcement or a recorded safe manual
guard. Update the cross-platform parity fixtures whenever either adapter
changes.

## Authoring rules for an adapted skill

Every active `SKILL.md` MUST declare a precise name and description, when it
should be used, when it must not be used, required inputs, expected artifacts,
validation, failure behavior, and its transition result. It SHOULD keep the
body concise and put large references/scripts in named resources. It MUST NOT
assume a project-specific path, cloud account, secret, or framework unless the
manifest declares that requirement.

A skill may declare role or minimum capability needs but MUST NOT pin a vendor
model name, price tier, or token budget as portable policy. Gate depth and risk
produce the shared `execution_profile`; the platform adapter owns actual model
and reasoning resolution and records any upgrade, degradation, default, or
unavailable control. Platform-specific effort labels remain adapter evidence,
not skill policy. Model capability cannot grant authority, weaken a MUST,
or replace an unresolved user decision.

`registry/routing-gates.json` assigns active skills to one primary `G0`–`G7`
gate. The manifest is deliberately small: it defines gate inputs/outputs,
approved skill placement, deterministic forward edges, and bounded feedback
targets. Do not add a general rule language, learned weights, environment-
specific constants, or a skill for every possible combination. The Router
loads a body only after activation and records suppression for materially
plausible adjacent skills. A gate or skill update that changes predecessor,
join, feedback, or invalidation behavior requires F-017 coverage.

Skills emit typed results; they do not directly retrain or rewrite routing
policy. New evidence may produce a backward feedback record, but only the
Router may reopen a gate and it must preserve immutable prior results and
unaffected branches. A recurring material failure is escalated after the
bounded retry budget rather than encoded as an implicit preference.

Cross-language skills keep one language-neutral contract in `SKILL.md` and
load only the detected ecosystem reference. A reference may describe an
established C++, Rust, Java, Python, TypeScript/JavaScript, Go, Shell, HTML,
CSS, or framework mechanism, but it cannot make that dependency mandatory,
bypass project conventions, or skip dependency, license, security,
compatibility, and approval review. HTML and CSS are public artifact boundaries,
not secret-bearing runtime configuration languages.

Technology ecosystem skills use one approved `SKILL.md` per ecosystem and keep
detailed, version-sensitive practice in directly linked references. They MUST
require intake, architecture, and Greenfield/Brownfield evidence; define
professional architecture/structure/rules/anti-patterns; declare language and
adjacent-skill relationships; separate authored from generated code; expose
configuration surfaces; require ecosystem-specific verification and documents;
and return a transition. They MUST NOT infer an adjacent product (for example
Docker to Kubernetes or ROS 2 to MoveIt), install a dependency, or treat a CLI
probe as adoption authority.

`technology-selection-and-integration` owns product-neutral classification,
capability mapping, selection status, compatibility, relationship graph, and
ADR/approval routing. `language-engineering` owns idiomatic implementation
profiles for changed authored boundaries. An ecosystem skill may override a
generic language recommendation only where an official binding/lifecycle/
serialization/real-time contract requires it; the conflict and evidence remain
recorded. Detailed references are reviewed against version-matched official
specifications/documentation first, then official examples and maintained
project conventions, then reviewed widely adopted community practice.

Popularity evidence is advisory and role-specific. Record the source URL,
metric type, measurement window, review date, count or rank, applicability,
owner, and revisit trigger. Compare only candidates serving the same function
inside the same ecosystem; npm downloads, Homebrew installs, Go importer counts,
GitHub stars, and catalog ranks are not interchangeable. A maintained, safe,
compatible project convention wins unless an approved decision documents why a
change is needed. A popularity result never grants dependency, network, or
execution authority.
