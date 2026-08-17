---
name: kubernetes-engineering
description: Design, implement, review, debug, harden, optimize, migrate, operate, or verify Kubernetes workloads and platform integration. Use for Pods, Deployments, StatefulSets, Jobs, Services, Ingress or Gateway, ConfigMaps, Secrets, probes, resources, autoscaling, scheduling, storage, namespaces, RBAC, security contexts, network policies, rollout/rollback, observability, operators/controllers, Helm or Kustomize-managed manifests, and containerized workload orchestration.
---

# Kubernetes Engineering

Model desired state, reconciliation, failure, and operations explicitly. Select
Kubernetes only when orchestration capabilities justify its platform cost; it
does not require the Docker runtime even when images are built with Docker.

## Entry gate

Require intake, infrastructure/architecture QAS, and a Kubernetes `TECH-*`
record. Brownfield work requires cluster/version/provider, APIs/CRDs,
namespaces/tenancy, workloads, delivery controller, policies, storage/network,
observability, incidents, and rollback baseline. Production/credential/cluster
mutation requires explicit authority.

## Workflow

1. Read [references/engineering-practices.md](references/engineering-practices.md).
2. Select workload/controller, service/network, storage, identity, and tenancy
   boundaries from state, availability, scaling, and failure requirements.
3. Define immutable artifact identity, configuration/secret delivery, probes,
   resources, disruption, rollout/rollback, scheduling, and observability.
4. Invoke `$docker-engineering` only when image build/Compose migration is in
   scope and `$language-engineering` only for application/operator code.
5. Route environment-specific manifests/values and secret references through
   `$configuration-and-environment-management`; keep cluster credentials out.
6. Verify schema/policy/rendering, server-side compatibility where authorized,
   probes/resources/security, rollout/rollback, failure/disruption, storage/
   network, observability, cost/capacity QAS, and runbooks.

## Result and exit

Return cluster/API assumptions, tenancy, workloads/services/storage,
configuration/secrets, health/resources/scaling, security, delivery/rollback,
verification, docs, and open points. Block production changes when identity,
secret, data ownership, probes/resources, rollout/rollback, or authority is
undefined.
