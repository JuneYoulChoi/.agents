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

The two internal maintenance skills follow the same contract. An upgrade
proposal must first use `harness-upgrade-analysis` to read the complete
`plan/` baseline and produce a per-file change classification. A user-approved
plan is required before changing an active skill, registry entry, gate, or
adapter. After implementation, `harness-overview-html` may publish a derived
overview, and verification must pin the source revision and retain unresolved
items. The HTML page is never an authority source for promotion.

## Authoring rules for an adapted skill

Every active `SKILL.md` MUST declare a precise name and description, when it
should be used, when it must not be used, required inputs, expected artifacts,
validation, failure behavior, and its transition result. It SHOULD keep the
body concise and put large references/scripts in named resources. It MUST NOT
assume a project-specific path, cloud account, secret, or framework unless the
manifest declares that requirement.
