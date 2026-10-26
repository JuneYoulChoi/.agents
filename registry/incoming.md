# Incoming source inventory

Current layout: `incoming/<category>/<source-bundle>/<package>/`. Packages remain inert candidates. Original licenses are under `incoming/_provenance/`.

538 packages contain 554 SKILL.md entrypoints. See [candidate dispositions](skill-candidate-review.json) and [adoption review](../docs/harness/skill-adoption.md). The candidate inventory is not consulted for executable skill resolution.

| Category | Packages | Bundles |
| --- | ---: | --- |
| workflow | 160 | addyosmani-agent-skills, awesome-copilot, caveman, everything-claude-code, gstack, mattpocock-skills, superpowers, wshobson-agents |
| architecture | 13 | addyosmani-agent-skills, everything-claude-code, mattpocock-skills |
| context | 22 | addyosmani-agent-skills, agent-skills-for-context-engineering, caveman, context-mode, everything-claude-code, gstack, mattpocock-skills |
| documentation | 44 | addyosmani-agent-skills, anthropic-skills, antigravity-skills, archify, everything-claude-code, gstack, mattpocock-skills, mcollina-skills, visual-explainer, wshobson-agents |
| frontend | 48 | 0xbigboss-claude-code, addyosmani-agent-skills, anthropic-skills, everything-claude-code, gstack, impeccable, vercel-agent-skills |
| backend | 33 | dotnet-artisan, everything-claude-code, supabase-agent-skills, wshobson-agents |
| languages | 39 | 0xbigboss-claude-code, antigravity-skills, dotnet-artisan, everything-claude-code, mattpocock-skills, mindrally-skills, sota-skills, wshobson-agents |
| quality | 65 | 0xbigboss-claude-code, addyosmani-agent-skills, antigravity-skills, caveman, dotnet-artisan, everything-claude-code, gstack, mattpocock-skills, superpowers |
| security | 25 | addyosmani-agent-skills, everything-claude-code, rea, trailofbits-skills, wshobson-agents |
| devops | 26 | addyosmani-agent-skills, antigravity-skills, everything-claude-code, gstack, mattpocock-skills |
| integrations | 15 | anthropic-skills, everything-claude-code, gstack |
| ai | 25 | agent-gpu-skills, everything-claude-code, huggingface-skills |
| physical-ai | 3 | nvidia-skills |
| simulation | 9 | blender-claude-plugin, mujoco, nvidia-skills |
| 3d | 5 | blender-claude-plugin, everything-claude-code |
| robotics | 6 | dbwls99706, nvidia-skills |

## Promotion boundary

Download popularity does not grant execution. A full promotion requires provenance and license review, required resources and scripts reviewed, tool/network/data scope, compatibility, typed transitions, verification and rollback. Selected procedural adaptations do not promote their source packages. Original sources are preserved.

## Role-matched popularity review — 2026-10-25

Eight existing Superpowers/Matt Pocock packages were refreshed from pinned
official commits, preserving all 26 original files. Their bytes were already
current. Commit, license, raw-file hashes and rounded skills.sh install displays
are now recorded per package. Twenty packages have selected adaptations; all
source packages remain inactive. See the
[selection and connection report](../docs/harness/popular-skills-2026-10-25.md).

## Requested source bundles — 2026-10-26

435 packages downloaded/refreshed (427 new, 8 existing), 1,787 original files verified against pinned Git blobs. All new packages remain deferred and inactive. Canonical skills only; no runtime installation. See [comparison, packaging limits and proposed destinations](../docs/harness/skill-bundles-review-2026-10-26.md).
