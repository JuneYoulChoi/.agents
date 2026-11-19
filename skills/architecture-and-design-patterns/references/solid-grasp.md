# SOLID and GRASP responsibility checks

Use when a module, class, component or service boundary is being created or
changed: at G2 for LLD responsibility assignment, at G5 for a pattern decision,
and at G6 through the object-oriented quality profile. These are diagnostic
checks with evidence, not shapes to impose. Check only the boundaries in scope
and record each applicable item as `satisfied`, `violated`, or `not_applicable`
with the observed evidence. A violation needs a concrete cost (coupled edits,
test obstacle, defect, blocked change); otherwise record it as an observation.

## SOLID

| Principle | Check | Violation signal | Do not over-apply |
| --- | --- | --- | --- |
| Single responsibility | Does the unit change for one actor or reason? | Unrelated requirements edit the same unit; mixed policy, I/O and formatting | Splitting cohesive behavior into forwarding fragments |
| Open/closed | Can the known variation be added without editing stable callers? | Each new variant edits the same conditional in several places | Extension points for variations no requirement names |
| Liskov substitution | Can every implementation honor the caller's contract, including errors and ordering? | Type checks on subtypes, narrowed inputs, unsupported operations that throw | Inheritance used only to share code |
| Interface segregation | Do clients depend only on operations they use? | Implementers stub unused methods; a change forces unrelated clients to rebuild or retest | One interface per method without a distinct client |
| Dependency inversion | Does policy depend on a boundary it owns rather than on a volatile detail? | Domain code imports a framework, driver or transport; tests need the real external system | An interface for a single stable implementation with no test or variation need |

## GRASP

| Pattern | Assignment question | Violation signal |
| --- | --- | --- |
| Information expert | Which unit already holds the data the responsibility needs? | Callers pull data out to compute what the owner should answer |
| Creator | Which unit aggregates, records or closely uses the created object? | Construction knowledge duplicated across unrelated callers |
| Controller | Which non-UI unit receives and coordinates a system operation? | UI or transport handlers contain domain decisions |
| Low coupling | Does the assignment minimize what changes together? | One requirement edits many units; cyclic dependencies |
| High cohesion | Are the unit's responsibilities strongly related? | Large unit whose methods use disjoint state |
| Polymorphism | Does behavior vary by type at a stable operation? | Repeated type or mode switches for the same variation |
| Pure fabrication | Is a non-domain unit justified to keep cohesion and coupling sound? | Persistence or messaging logic pushed into domain objects, or helpers with no clear owner |
| Indirection | Does an intermediary remove a harmful direct dependency? | Pass-through layers that add no decoupling |
| Protected variations | Is a real, named instability hidden behind a stable boundary? | A vendor, protocol or format detail leaks to many callers |

## Recording and conflicts

Record the result in the owning artifact (LLD module entry, `PATTERN-*`
record, or the object-oriented profile's findings) as:

```yaml
responsibility_checks:
  - boundary: ''
    principle: SRP | OCP | LSP | ISP | DIP | information_expert | creator | controller | low_coupling | high_cohesion | polymorphism | pure_fabrication | indirection | protected_variations
    status: satisfied | violated | not_applicable
    evidence: ''
    consequence: ''
    action: keep | change | defer_with_reason
```

Principles can conflict (for example low coupling against information expert).
Decide by the recorded quality scenarios and change drivers, state the
trade-off, and prefer the simpler assignment when evidence is equal. Accepted
ADRs, external contracts, framework lifecycle rules and language safety take
precedence, as in the pattern skill's precedence order. A design-pattern
selection must name the checks it improves and the ones it worsens.
