# Expert delegation and intake evaluation

Use the [raw cases](../../fixtures/behavior/expert-intake.md) in fresh contexts
with the current approved instructions. Do not give the scorer's expectations
below to the acting agent. Record actual outputs, source revision, model/effort
resolution, tools and limitations. No external actions are needed.

| Case | Acceptance for the independent scorer |
| --- | --- |
| A | Identify acceptance-changing ownership/storage, own/external calendar and date/time choices; ask at most three related questions, do not silently pick a product; retain all CRUD outcomes |
| B | Reuse stated decisions, preserve exclusions, no redundant questionnaire or unnecessary specialist team |
| C | Only the text change, no product discovery or delegation |
| D | Propose distinct evidence questions for available authorized experts, then integrate competing explanations; a material fallback requires a concrete reason, not a generic single-agent default |
| E | Preserve exact requested order and existing behavior; omit cloud/telemetry and questions about them |
| F | Use confirmed source decisions and necessary local persistence; no repeated questions about excluded synchronization |

Score each case for essential omissions, unnecessary questions, invented
decisions, unrequested additions and evidence-backed delegation/fallback.
Keep the actual response and rationale, including disagreements; do not reduce
quality to keyword matching. Feed failures to the nearest responsible gate.

For runtime regression use unittest and the portable fixtures separately:
they prove validated structures and lifecycle behavior, not natural-language
reasoning. A single behavioral pass is a smoke check, not a quality benchmark.

To compare efficiency, use acceptance-matched local, independent-investigation
and integrated-change tasks, identical source/tools/model resolution and repeated
trials. Compare correctness and omitted requirements first, then wall time,
duplicate reads/findings, rework and provider-reported parent plus worker tokens.
Count unsuccessful runs too. If total usage or a comparable baseline is missing,
report savings as not_measured; never substitute bytes or worker-only totals.
Do not impose this experiment on ordinary delivery or add extra reviewers just
to measure reviewers.

## Validation record: 2026-11-15

The user approved the preceding review recommendations and implementation.
The baseline was commit `bf332f73` plus existing uncommitted work, preserved
before this update. The change extends existing contracts rather than adding
a gate, scheduler, dependency or authority source. Python changes use the
existing stdlib conventions and core/API-data quality checks. No formal
standards conformance is claimed.

An independent fresh-context agent read only the intake/composition skills and
raw cases, without this scoring guide. Its first attempt hit a provider usage
limit; a subsequent authorized continuation completed the simulated intake.
The coordinator checked the actual responses against the rubric:

| Case | Observed response | Assessment |
| --- | --- | --- |
| A | Three grouped questions covering ownership/storage/integration, dates and greeting frequency; all CRUD outcomes retained; implementation waits | Passed smoke check |
| B | Reused explicit boundaries without redundant questions; distinguished a standalone request from a follow-up instead of inventing prior CRUD authority | Passed smoke check |
| C | Single text replacement, no new questions or worker | Passed smoke check |
| D | Two bounded read-only client/server investigations on a shared input snapshot, followed by evidence-based synthesis; no G1 Runner owner | Passed smoke check |
| E | Excluded cloud and telemetry; first checks sources, then asks only for the missing new column order if still absent | Passed smoke check |
| F | Reused confirmed local storage and confirmation convention; checks cancel/confirm and persistence, no synchronization questions | Passed smoke check |

This was one simulated behavioral pass, not live execution of those projects
or a comparative benchmark. Native reasoning labels and provider token counters
were unavailable; execution used the platform default. The results support the
observed decisions only, not a general quality or token-savings percentage.

Verification: `python3 -B -m unittest discover -s tests -p 'test_*.py'`
passed 96 tests; `python3 -B scripts/fixture_runner.py` passed 37 fixtures.
The new tests cover lens delivery without authority/acceptance changes, invalid
lenses, budgeted serial projection and real Runner refinement with immutable
completed receipts plus rejection of altered/removed/failed prepared work.
All three affected skill packages passed skill-creator's `quick_validate.py`.
Source/template/registry pins and the derived HTML overview were synchronized.

Remaining limitations: G1 relies on the adapter to discover omitted questions;
hashes and structured criteria do not prove semantic correctness. Token budgets
still block subsequent dispatch when usage is unavailable. Total parent-plus-
worker cost and comparative quality remain not_measured. Existing approvals,
scope boundaries and required checks are preserved; no waiver was introduced.
