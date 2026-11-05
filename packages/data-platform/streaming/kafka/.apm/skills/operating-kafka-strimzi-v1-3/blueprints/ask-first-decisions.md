# Ask-first decisions, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Part 1 holds the High options (choose with the user). Part 2 holds single-source recommendations and prohibitions, all (medium confidence): one official document, or a page read only partly. They are not Always Do or Never Do. Doc base for the AsciiDoc pages: `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/`.

## Part 1. Decisions

### C1. Operator install method

Sources: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md), [upgrade assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/upgrading/assembly-upgrade-cluster-operator.adoc), [Helm index](https://strimzi.io/charts/index.yaml).

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| YAML files (`install/cluster-operator`) | Full control of every env var | Upgrade overwrites local edits; record them first | GitOps with patched manifests |
| Helm OCI chart `oci://quay.io/strimzi-helm/strimzi-kafka-operator` | Values (`watchNamespaces`, `featureGates`, `resources`) | CRDs are not upgraded; chart 1.3.0 is in the classic index, 1.3.1 not confirmed (unverified) | Teams standardized on Helm |
| OLM / OperatorHub | Channel updates | Automatic updates on the stable channel are discouraged; use version-specific channels | OpenShift or OLM clusters |

The upgrade must use the same method as the first install. Ask: "Which install method does the cluster already use or allow?"

### C2. Watched namespaces

Sources: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [operator upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-cluster-operator.adoc).

- One namespace, a comma-separated list (RoleBindings `020`, `023`, `031` in each), or all (`STRIMZI_NAMESPACE="*"`, three ClusterRoleBindings).
- If the Topic or User Operator watches another namespace, set `STRIMZI_ENTITY_OPERATOR_WATCHED_NAMESPACE_ENABLED=true`, otherwise the Entity Operator deployment is deleted during the upgrade.
- Ask: "How many teams or namespaces host Kafka clusters?"

### C3. Storage layout

Sources: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html), [official example](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/examples/kafka/kafka-persistent.yaml). Details: [storage-and-scaling](./storage-and-scaling.md).

- `ephemeral`, `persistent-claim` or `jbod`. The type cannot change after deploy; volumes can grow, not shrink.
- Ask: "Which storage class, expected per-broker size, and is JBOD needed? Choose before the first deploy."

### C4. Client authentication

Sources: [listener authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authentication.adoc), [client authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-client-authentication.adoc), [certificate renewal](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-certificate-renewal.adoc), [OAuth server config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/oauth/con-oauth-server-config.adoc).

| Option | Optimizes | Sacrifices |
|---|---|---|
| `tls` (mTLS) | No passwords; User Operator issues certificates | Clients must rotate keystores before certificates expire |
| `tls-external` (KafkaUser) | Bring your own certificates; ACLs use `CN=<username>` | No secret or credentials generated |
| `scram-sha-512` | Works over TLS and plain; generated 32-character password | Password distribution |
| OAuth 2.0 via `custom` | Central identity provider | More configuration; secrets via config providers |

Ask: "Which identity system do the clients already use?"

### C5. External exposure

Source: [deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html). Types: `loadbalancer`, `nodeport`, `route` (OpenShift), `tlsroute` (Gateway API, maturity: medium confidence), deprecated `ingress`. TLS is required for `route` and `ingress`. Scaling a cluster with external listeners may roll all brokers. Ask: "How do clients outside Kubernetes reach the cluster?"

### C6. Rebalancing on scale

Sources: [optimization proposals](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-generating-optimization-proposals.adoc), [approval](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-approving-optimization-proposal.adoc), [auto-rebalance](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/cruise-control/proc-automating-rebalances.adoc). Manual approval, `strimzi.io/rebalance-auto-approval: "true"`, or `spec.cruiseControl.autoRebalance` (runs only when `spec.replicas` of an existing pool changes). Ask: "Must a human review data movement in production?"

### C7. Certificate authorities

Sources: [certificate renewal](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-certificate-renewal.adoc), [API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html), [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0). Strimzi CAs (365 days, renewal 30 days before expiry), own CA (`generateCertificateAuthority: false`), or cert-manager (Early Access, not recommended for production). Ask: "Must a corporate PKI or cert-manager issue the certificates?"

### Open conflicts to put to the user

- `UseBackgroundPodDeletion`: the 1.3.0 release notes and the feature-gate reference disagree on the default (register I3). Ask: "Set the gate explicitly with `+` or `-` in `STRIMZI_FEATURE_GATES`?"
- Pod names: two patterns appear in the docs (register I4). Ask: "Can you run `kubectl get pods -l strimzi.io/cluster=<name>`?" (label selector unverified).

## Part 2. Single-source recommendations (medium confidence)

All (medium confidence). Ask before applying; do not present as mandatory.

- M1. Set CPU and memory requests and limits on every Strimzi container; Strimzi sets none by default ([common config](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-common-configuration.adoc)). The Helm chart's own operator defaults are a 384Mi request and 384Mi / 1000m limits ([Helm README](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/packaging/helm-charts/helm3/strimzi-kafka-operator/README.md)).
- M2. One namespace per Kafka cluster and per Connect cluster ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- M3. `auto.create.topics.enable: false` when topics come from `KafkaTopic` ([topic handling](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/operators/con-application-topic-handling.adoc)).
- M4. Block storage only: "Strimzi is only tested for use with block storage" ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- M5. Set `strimzi.io/use-connector-resources: "true"` before you create connectors you want to keep ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- M6. A `sha512sum` on every `spec.build.plugins[].artifacts[]` entry ([Connect build](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-config-kafka-connect-build.adoc)).
- M7. Set `spec.version` on `KafkaConnect` and `KafkaMirrorMaker2`; unset defaults to Kafka 4.3.1 on 1.3.0 (the 1.3.1 default is unverified) ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- M8. Harden Connect with `org.apache.kafka.disallowed.login.modules` and `connector.client.config.override.policy: None` ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- M9. `spec.maintenanceTimeWindows` (cron, UTC), each at least as long as the reconciliation interval ([maintenance windows](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-maintenance-time-window-definition.adoc)).
- M10. `networkPolicyPeers` on listeners; by default Strimzi creates a per-listener NetworkPolicy that allows all namespaces ([network policies](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/proc-restricting-access-to-listeners-using-network-policies.adoc)).
- M11. Set `replica.selector.class` yourself for closest-replica fetching; Strimzi does not set it, and the class name is from Kafka, not the Strimzi page ([API reference](https://strimzi.io/docs/operators/1.3.0/configuring.html)).
- M12. Kafka Exporter (`spec.kafkaExporter`) for consumer-lag metrics ([Kafka Exporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-kafka-exporter-deploy.adoc)).
- M13. Quote `metadataVersion` as a string ([Kafka upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-kafka-kraft.adoc)).
- M14. Keep `min.insync.replicas` in `spec.kafka.config`; if removed the operator falls back to 1 ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- M15. Use a `RackAwareGoal` rebalance after moving nodes between pools in a rack-aware cluster ([node pool racks](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/configuring/con-node-pools-racks.adoc)).

## Single-source prohibitions (medium confidence)

All (medium confidence), register M21 (the ZooKeeper migration item: M22). Each has an alternative.

- Do not use the `ingress` listener for new deployments (deprecated; the Ingress NGINX Controller is archived). Use `tlsroute` or `loadbalancer` ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), [CHANGELOG](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/main/CHANGELOG.md), read partly).
- Do not edit ConfigMaps that Strimzi creates; change the custom resource instead ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- Do not raise `metadataVersion` until you accept that downgrade may be impossible; the downgrade modules were not read ([Kafka upgrade](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/upgrading/proc-upgrade-kafka-kraft.adoc)).
- Do not change Connect internal topic replication factors after the topics exist; it has no effect. Set them at creation ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- Do not enable MirrorMaker 2 ACL sync together with the User Operator; manage ACLs with `KafkaUser` ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- Do not use PKCS12 user keystores for new clients (deprecated in 1.3.0); use the PEM entries in the user secret. The replacement guidance is inferred ([1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0)).
- Do not use encrypted private keys for TLS; Strimzi does not support them. Use an unencrypted key in a Secret ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html)).
- For an existing ZooKeeper-based cluster, migrate to KRaft on Strimzi 0.45.x before moving to 1.3.x; ZooKeeper support was removed in 0.46 (register M22; one page and the 0.46 boundary). Ask: "Is the existing cluster still on ZooKeeper?"
