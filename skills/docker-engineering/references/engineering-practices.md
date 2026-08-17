# Docker engineering practices

## Build and image structure

- Use a small intentional build context and `.dockerignore`. Separate build,
  test, and runtime stages; copy only required runtime artifacts and metadata.
- Pin base-image policy at the level required by reproducibility and update
  operations. Tags ease updates; digests prove identity. Record how both are
  refreshed rather than choosing silently.
- Order stable dependency inputs before frequently changing source to improve
  cache reuse. Use BuildKit cache/secret/SSH mounts where supported; secrets
  must not enter `ARG`, `ENV`, copied files, logs, or committed layers.
- Remove package-manager caches in the same layer where created and avoid
  unnecessary shells, compilers, package managers, or debug tools in runtime.

## Runtime and Compose

- Run as a deliberate non-root UID/GID where feasible, with minimum filesystem
  permissions/capabilities and an explicit writable-data strategy.
- Use an exec-form entrypoint/command or a correct init wrapper. Define signal
  handling, graceful shutdown deadline, exit codes, restart semantics, and
  health checks that reflect service readiness rather than process existence.
- Keep application data in declared volumes/external services; treat containers
  as replaceable. Bound resources and logging where the runtime supports it.
- Use Compose for an owned multi-service development/test or bounded deployment
  profile. Keep environment overrides, secrets, dependencies, health, networks,
  volumes, and profiles explicit; do not assume startup order equals readiness.

## Supply chain and verification

- Record Dockerfile/base/source revision, builder/platform, generated SBOM or
  equivalent inventory, vulnerability/policy result, provenance/signing policy,
  and registry/tag/digest ownership as required.
- Verify clean and cached builds, target architectures, expected files only,
  non-root/permission behavior, no secret residue, health/start/stop/signals,
  read-only/minimal privilege where required, configuration validation, Compose
  integration, scan policy, and rollback by immutable artifact.
- Reject `latest` as an unowned production identity, secrets in layers, package
  upgrades without reproducibility, privileged/root-by-default containers,
  shell-form signal loss, mutable patching inside running containers, and
  Docker socket exposure without an approved security boundary.

Primary sources: version-matched Dockerfile, BuildKit/Buildx, Compose, runtime,
and supply-chain documentation plus project deployment/security policy.
