# Real-time and embedded profile

Use for deadlines, determinism, bounded memory, hardware I/O, interrupt or
control loops, or safety-related behavior. Record worst-case timing and resource
bounds, avoid unbounded blocking/allocation in critical paths, make failure and
degraded modes explicit, and separate non-real-time diagnostics from critical
execution. Validate on representative hardware or state that such verification
is unavailable; average latency is not a deadline guarantee.
