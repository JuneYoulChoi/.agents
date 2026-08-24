# Functional profile

Use for functional pipelines, immutable state, or explicit side-effect
boundaries. Keep pure transformations separate from I/O, make state transitions
and failure values explicit, handle variants exhaustively where supported, and
avoid hidden mutation. Do not force a functional rewrite across an established
imperative boundary when a local pure function or immutable value is enough.
