# Codex edit guard

On a Codex surface that loads project hooks, merge [the example](hooks.example.json)
into the trusted project's `.codex/hooks.json`. Replace `<harness-source>`
and `<project-root>` with the local source and project paths. Trust the
registered hook through Codex's native controls. With no task binding the
hook allows edits.

For an approved temporary guard, set `enforce` in
`.codex/harness-guard.json` to an object with `task_id`, `approval_id`, and
the project-relative `target_root` (`.` for the same project). Confirm
enforcement in the current session by attempting a disposable `apply_patch`
edit under the target. Record the JSON from `HARNESS_GUARD_OBSERVED` in the
tool denial as intake's `hook_guard`, select `enforcement_mode: hook`, and
start the Runner. A G0 hold needs a new denial in the current task revision
and the recorded recovery decision before `resume`.

The hook checks the paths in `apply_patch`, including both paths of a
move. The optional `exempt_paths` are project-relative files or folders.
Edits resume when the bound task is active. A completed or cancelled task
returns the hook to its dormant state. Shell writes remain governed by host
permissions. If the active Codex surface cannot demonstrate the native
denial, follow the [common enforcement levels](../../../plan/06-platform-adapters.md#enforcement-levels).
