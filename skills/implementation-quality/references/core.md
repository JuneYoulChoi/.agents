# Core implementation quality

Apply these checks proportionally to the changed authored boundary:

- preserve observable correctness and established contracts before cleanup;
- keep the smallest clear implementation that meets current requirements;
- remove knowledge duplication, not merely similar-looking syntax;
- keep responsibilities cohesive and dependencies explicit;
- make invalid input, errors, state transitions, ownership, and lifecycle
  visible at the boundary where they matter;
- prefer reversible composition over speculative abstraction;
- make the slice testable and keep diagnostics sufficient to explain failure.

Do not perform unrelated cleanup, generalize for hypothetical consumers, or
replace a maintained project convention without recorded evidence and impact.
