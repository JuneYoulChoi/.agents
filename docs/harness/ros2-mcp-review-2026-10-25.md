# ROS 2 skill and MCP integration review — 2026-10-25

The user approved downloading the recommended ROS 2 skill and MCP tool,
integrating the relevant parts, checking routing/gates/claims and committing.
Base: `32b2b7d`; the existing five-layer view and G0–G7 remain unchanged.
Scope is this shared harness, not a robot or a target software project.

## What and why

The active ROS 2 skill gains bounded runtime-provenance and evidence guidance
from an immutable external skill snapshot. The original package remains in
incoming. The external MCP server is an optional tool, stored separately with
its original runtime subset, license, lockfile and file hashes.

```text
incoming/robotics/dbwls99706/ros2-engineering-skills  (inert original)
                         │ selected procedural ideas rewritten
                         ▼
G4 technology selection → G5 core.ros2-engineering 0.2.0
                              │ only ROS 2 + ros_mcp_server selected
                              ▼
                    mcp-inspection reference
                              │ actual capability + project read scope
                              ▼
                  tools/ros-mcp-server/run.sh
                              │ stdio, nine graph/type queries
                              ▼
                    approved rosbridge endpoint
                              │ observation/error, not inferred safety
                              ▼
                       G7 evidence handoff
```

No new always-on agent, MCP dependency in the Core, global client registration,
robot connection or robot control is introduced. Normal ROS 2 development does
not require MCP. Other downloaded MCP-related skills remain candidates.

## Review decisions

| Boundary | Decision and evidence |
| --- | --- |
| ROS skill source | `dbwls99706/ros2-engineering-skills`, commit `f0de84dfedd67b067ccc6d2851e681529606930c`, Apache-2.0; 204 original files downloaded. SKILL.md and selected relevant claims inspected. Full reference/scripts audit not claimed. |
| MCP source | `robotmcp/ros-mcp-server`, commit `476591ac058f58cae810cc775e50b51f8d3d757c`, version 3.1.2, Apache-2.0; 42 original runtime files retained with raw SHA-256 hashes. |
| Active skill | Retain the existing authority/result contract. Version 0.2.0 adds optional references; no upstream hooks, validators or installer is activated. |
| Tool access | Explicit allowlist of nine graph/type queries, stdio only, fixed explicit endpoint. No prompts/resources, writes, subscriptions, network scans or endpoint switching. |
| Error handling | Upstream `_check_response` does not recognize every `{error: ...}` response; some tools can report missing/empty data. The adapter rejects transport failures, malformed fields and correlation/service mismatches before they reach tool formatters. |
| ROS version/namespace | Do not use upstream absence-based ROS-version inference. This bounded profile expects ROS 2 types and `/rosapi`; mismatches are reported as compatibility gaps. |
| Model/reasoning | Current Codex platform default; explicit model/effort control and native effort label not exposed. No claim of an exact portable-profile match. |
| Standards/patterns | Guidance only, no formal conformance or new architecture-pattern selection. Extend the current conditional-reference and adapter boundaries. |

## Verification scope

- The pre-change baseline passed 36 runtime/documentation tests.
- `tests/test_ros2_mcp.py` checks selected-pair activation, missing/candidate/
  unrelated technology suppression, blocked/unknown/maintenance cases,
  existing gate preservation, Runner reference delivery/persistence, runtime
  hash isolation and original upstream file integrity.
- `tools/ros-mcp-server/test_inspect_server.py` checks real stdio initialization
  and tool discovery, no startup network connection, denied control tools,
  invalid endpoint settings, successful mocked observations and transport,
  malformed-response, mismatch and failed-service errors.
- Existing runtime, fixture and documentation suites cover active registry
  placement, candidate snapshot hashes, links, quarantine and existing gates.

Manual response review cases: tool absent → disclose unavailable capability;
connection failure → graph unknown; successful empty list → only this endpoint's
observed graph is empty; source YAML → not proof of runtime parameters; topic
metadata → not proof of QoS/delivery/freshness; initialization → not robot
connection; stop/control request → unavailable in inspection profile, never
claim physical stopping. These are scoped instruction/implementation reviews,
not a statistically validated model-answer benchmark.

## Limitations and handoff

Final results: **44 runtime/documentation tests, 37 integration fixtures, and
8 offline MCP protocol/response tests passed**. Authored Python lint, shell
syntax, skill frontmatter, source links and original-file checks passed. The
counts describe the executed checks above, not hardware or model-answer proof.

The local isolated runtime was installed and its MCP protocol tested. A project
endpoint and actual client registration are still needed for live use. ROS 2,
rosbridge, simulation, hardware, camera data, QoS/latency and physical safety
were not tested. The profile requires a trusted private/tunnelled `ws://`
endpoint; TLS/authentication and comprehensive transitive dependency security
audit are not claimed. Upstream's frozen dependency set was preserved.

Use [setup and usage](../../tools/ros-mcp-server/README.md). Runtime/cache/build
output is not committed or included in harness source pins. Upstream source,
lockfile, adapter and routing are pinned. Refresh pins after authored edits.
Updates require reviewing changed upstream tools/response formats and rerunning
the same checks. Rollback is a scoped commit revert; remove the optional local
runtime and any project registration separately. Original user files and
untracked OS/cache files are preserved.
