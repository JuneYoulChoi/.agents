# Codex native work dispatch

Use the shared [native work contract](../../skills/workflow-composition/references/native-work.md)
for task-scoped work. The Runner binds skills, roles and evidence. Codex starts
and observes its own workers.

1. Check the current task revision, role, allowed tools, owned paths and
   fresh worker capacity. Prepare only units bound to the current skill with
   `prepare-work` and `mode: native`. Optional units can run locally in
   `mode: serial` when an authorized native worker is unavailable.
2. Start one fresh Codex subagent per prepared unit. Use the host option to
   omit inherited conversation history, such as `fork_turns: none` when exposed.
   Send only the returned packet and any allocated evidence output path.
   Use the packet's role guidance. Honor the host's granted tools and path
   boundaries. Keep prerequisite evidence accessible to that worker.
3. Observe the returned worker ID and terminal result. On timeout, request
   cancellation and confirm termination before releasing owned paths. Verify
   the result and write the required host receipt using the actual worker ID.
   Join through `record-work` before submitting the skill.
4. For required jydlc development, run G6 implementation and G7 verification
   in distinct workers. G7 inspects the integrated G6 revision. One free
   slot supports the sequence. Report a blocker if required native execution
   cannot be provided.

Record the actual model and native reasoning in `execution_resolution`.
Report counters only when the host exposes them. This procedure applies only
to the native capability present in the current session.
