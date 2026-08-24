# Concurrency profile

Use for threads, async tasks, shared state, queues, cancellation, or shutdown.
Define ownership and synchronization, bound queues and work, propagate
cancellation, avoid orphan work, and test race/deadlock and shutdown behavior
where relevant. Prefer the project's structured concurrency or executor model;
do not add concurrency when sequential work meets the requirement.
