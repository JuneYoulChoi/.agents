# Object-oriented profile

Use only when classes, interfaces, polymorphism, or responsibility boundaries
are in scope. Evaluate cohesion, coupling, information hiding, dependency
direction, substitutability, interface size, and ownership. Apply the
[SOLID and GRASP checks](../../architecture-and-design-patterns/references/solid-grasp.md)
to the changed boundaries and record violated items with evidence in
`findings`; they are diagnostic lenses rather than mandatory shapes. Prefer composition when it
keeps behavior and lifecycle explicit; do not introduce an interface or named
pattern for a single stable implementation without a real variation or test
boundary.
