# Kubernetes engineering practices

## Desired state and workload structure

- Pin supported Kubernetes API/version/provider features and CRD/operator
  ownership. Prefer stable APIs and validate deprecation before upgrades.
- Select Deployment, StatefulSet, DaemonSet, Job/CronJob, or a custom controller
  from lifecycle/state/reconciliation needs. Do not encode an imperative script
  as a declarative controller without idempotent convergence semantics.
- Use stable labels/selectors and clear namespaces/ownership. Separate reusable
  base, environment overlays/values, generated manifests, and secret material.

## Runtime, availability, and data

- Use immutable image identities according to release policy. Define command,
  user/security context, filesystem, termination grace, and application drain.
- Design startup/readiness/liveness probes for distinct semantics; a liveness
  probe must not turn dependency slowness into restart storms.
- Set requests/limits from evidence; define autoscaling metrics/stabilization,
  scheduling/affinity/topology, quotas, priority, and disruption budgets from
  QAS rather than copied defaults.
- Own Service/Gateway/Ingress/DNS/TLS/network policy and client timeout/retry
  behavior. Own PVC/storage class/access mode/backup/restore/migration and
  StatefulSet identity before claiming stateless replaceability.

## Security, delivery, and verification

- Apply least-privilege service accounts/RBAC, non-root/restricted security
  context, secret references, network isolation, image/admission policy, and
  audit requirements. ConfigMaps are not secret stores.
- Define declarative delivery owner, ordering/dependencies, progressive rollout,
  health gates, rollback, schema/data compatibility, drift, and break-glass
  authority. Backward-compatible application rollout may be required before
  manifest rollout.
- Verify rendered/schema/policy output, API compatibility, probes and graceful
  termination, requests/limits/scaling, RBAC/network/storage, rollout/rollback,
  node/pod/dependency failures, observability/alerts, backup/restore, and runbook.
- Reject mutable tags without release ownership, missing requests/probes,
  default service-account privilege, secrets in manifests, broad cluster-admin,
  local-only state, and `kubectl` success as the sole acceptance evidence.

Primary sources: version-matched Kubernetes concepts/API/task documentation,
provider/controller documentation, and project security/SRE policies.
