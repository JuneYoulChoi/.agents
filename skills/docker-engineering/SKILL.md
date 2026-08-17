---
name: docker-engineering
description: Design, implement, review, debug, harden, optimize, migrate, or verify Docker container images and Compose-based workflows. Use for Dockerfiles, build contexts, multi-stage builds, BuildKit/Buildx, image provenance, container users and permissions, secrets, health checks, signals, volumes, networks, Docker Compose, development/CI images, image size/cache, SBOM or vulnerability analysis, and container runtime configuration.
---

# Docker Engineering

Treat an image as an immutable, reproducible deployment artifact and a
container as a constrained process. Docker use does not imply Kubernetes.

## Entry gate

Require intake, architecture/deployment evidence, and the Docker `TECH-*`
record. Brownfield work requires Docker/Compose/Build versions, current images,
Dockerfiles, contexts, registries, runtime users, mounts/networks, configuration,
CI/release flow, and baseline image/runtime behavior.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Define build, runtime, development/test, and release image responsibilities;
   minimize context, stages, packages, privileges, and mutable state.
3. Define PID 1/signal/shutdown, health, filesystem, user, network, resource,
   logging, and secret behavior.
4. Invoke `$language-engineering` for the contained application and Shell only
   for authored scripts. Treat Dockerfile/Compose as ecosystem/config contracts.
5. Route public runtime settings and secret references through
   `$configuration-and-environment-management`; never bake secrets into layers.
6. Verify deterministic build, cache behavior, image contents/SBOM, policy scan,
   non-root runtime, health/shutdown, configuration, mounts/networks, Compose
   integration, and rollback/tag/digest behavior.

## Result and exit

Return builder/runtime profiles, base/image policy, stages, user/filesystem/
network, configuration/secrets, health/shutdown, supply-chain evidence,
verification, docs, and open points. Block release when secrets, provenance,
runtime user, health/shutdown, or mutable-state ownership is unresolved.
