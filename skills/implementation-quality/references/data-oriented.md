# Data-oriented profile

Use only when data volume, memory layout, locality, batching, serialization, or
throughput is a recorded driver. Design access patterns and representation from
measured workload evidence, distinguish hot and cold data, bound allocations
and copies, and preserve correctness at conversion boundaries. Do not trade
clarity for speculative locality gains without a benchmark or resource budget.
