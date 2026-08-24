---
name: technology-selection-and-integration
description: Select, classify, compose, or review project technologies and their ecosystem engineering skills from requirements and evidence. Use when a request names or implies a runtime, library, framework, protocol, platform, simulator, middleware, build tool, container system, robotics stack, or a material technology adoption, replacement, integration, or compatibility decision, including ROS 2, Node.js, React, gRPC, Isaac Lab, Isaac Sim, MoveIt, Docker, Kubernetes, Modbus, and colcon.
---

# Technology Selection and Integration

Select technology from project purpose and constraints, then load the smallest
set of approved ecosystem and language skills. Do not treat popularity, a named
technology, or an installed executable as proof that the project should adopt
it.

## Entry gate

Require an intake record and an architecture baseline attempt. For Greenfield,
require goals, UC/requirements, and relevant QAS. For Brownfield or Hybrid,
require discovery of the existing stack, versions, contracts, build/deploy
paths, and regression constraints before recommending a replacement or new
dependency.

If the user mandates a technology, record `required_by_user`; still validate
compatibility and consequences. If the technology is only mentioned as an
idea, record `candidate`. Return to clarification when the distinction changes
architecture, cost, security, license, hardware, or operational scope.

## 1. Classify the technology without flattening it

Read [references/technology-taxonomy.md](references/technology-taxonomy.md).
Assign one `primary_kind` and zero or more `secondary_roles`. Also record domain,
lifecycle scope, selection status, and evidence. `framework` is one kind, not
the name for every technology.

## 2. Map capability before product

Derive required capabilities from UC, external interfaces, FA, and QAS. Map
each candidate to those capabilities and record missing or excess scope.
Compare alternatives serving the same function; do not compare download counts
across unrelated ecosystems.

Treat an accepted `PATTERN-*` result as an implementation constraint only
after its drivers and trade-offs are recorded. Technology evidence may refine
or invalidate a candidate pattern through G5 feedback, but product popularity
or a framework example does not select an architecture pattern.

Use this evidence order:

```text
user-approved requirement and project policy
> official specification and versioned documentation
> official reference architecture and maintained examples
> observed project convention and executable evidence
> reviewed, widely adopted community practice
> proposal or inference
```

## 3. Resolve the integration graph

Read [references/composition-and-selection.md](references/composition-and-selection.md)
for relationship and compatibility rules. Record every edge as `required`,
`recommended`, `optional`, `detected`, or `incompatible`, with a condition and
rationale. Never infer Docker implies Kubernetes, React implies a Node.js
production server, ROS 2 implies MoveIt/Isaac, or Isaac Lab implies a cluster.

Check version, OS, architecture, language binding, runtime, GPU/driver,
middleware/protocol, license, security, build, deploy, and operational
compatibility as applicable. A material adoption or replacement requires an
ADR and user/owner approval.

## 4. Assemble approved skills progressively

Select only the ecosystem skills that correspond to `selected`,
`required_by_user`, or relevant `detected_existing` technologies. Then invoke
`$language-engineering` for each implementation-producing module and
`$configuration-and-environment-management` for varying build/deploy/runtime
or secret-backed values.

Do not invoke `incoming/`. A missing specialist skill uses the core procedure
and records the gap; it never grants permission to download or activate one.

This skill is a `G4` concern gate and may emit several `G5` ecosystem/language
branches when a real integration spans them. Record every materially plausible
adjacent branch as activated, candidate, suppressed, or blocked with evidence.
Do not use learned weights or popularity thresholds. Compatibility or
verification feedback may reopen `G4`; preserve unrelated valid technology
branches and accepted user decisions.

## 5. Produce the technology artifact

```yaml
technology:
  id: TECH-001
  name: ''
  primary_kind: runtime | library | framework | protocol | platform | tool
  secondary_roles: []
  domains: []
  lifecycle_scope: []
  selection_status: required_by_user | detected_existing | candidate | selected | rejected | not_applicable | prohibited
  purpose: ''
  required_capabilities: []
  project_evidence: []
  version_policy: ''
  compatibility: {}
  relationships: []
  ecosystem_skills: []
  language_bindings: []
  configuration_surfaces: []
  alternatives: []
  decision_id: null
  verification_profiles: []
  documentation_effects: []
  open_points: []
gate_result:
  gate_id: G4
  activated_branches: []
  suppressed_branches: []
  output_artifacts: []
transition:
  next_stage: clarification | design | assembly | execution | verification
  next_skill: ''
  entry_conditions: []
```

## Exit gate

Do not enter material implementation when a selected technology lacks a
purpose, evidence, supported version/binding, required compatibility checks,
or an owner-approved material decision. Route Greenfield work back to design,
Brownfield changes back to impact, and an implementable module to the selected
ecosystem skill followed by `$language-engineering`.
