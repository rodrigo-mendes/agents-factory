# Observability, Strimzi 1.3.x

Back to [SKILL.md](../SKILL.md). Doc base: `https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/`. Example file contents (Prometheus rules, dashboards) were not read (register U12).

## Kafka metrics on port 9404

Sources: [Strimzi Metrics Reporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-strimzi-metrics-reporter-kafka-deploy-options.adoc), [JMX exporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-jmx-exporter-metrics-kafka-deploy-options.adoc), [listener authentication](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/security/con-securing-kafka-authentication.adoc).

- `spec.kafka.metricsConfig` with `type: strimziMetricsReporter`, or `type: jmxPrometheusExporter` (ConfigMap-backed). Both expose metrics on port 9404 over HTTP.
- Port 9404 is reserved for Prometheus metrics, so no listener may use it.
- Example files named in the JMX exporter page: `kafka-metrics.yaml`, `kafka-connect-metrics.yaml`, `kafka-mirror-maker-2-metrics.yaml`, `kafka-bridge-metrics.yaml`, `kafka-cruise-control-metrics.yaml`.

```yaml
spec:
  kafka:
    metricsConfig:
      type: strimziMetricsReporter
```

## Prometheus, Grafana, exporters

Sources: [metrics assembly](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/assemblies/metrics/assembly-metrics.adoc), [Prometheus options](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/con_metrics-prometheus-options.adoc), [Kafka Exporter](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/metrics/proc-kafka-exporter-deploy.adoc), [1.3.0 notes](https://github.com/strimzi/strimzi-kafka-operator/releases/tag/1.3.0). Single pages for some items (medium confidence, M12 and M17).

- The Prometheus Operator must be deployed first. Strimzi ships `prometheus.yaml`, `pod-monitors/*.yaml`, `prometheus-additional.yaml` and `prometheus-rules/*.yaml` examples (medium confidence).
- Grafana dashboards are provided; 1.3.0 adds panels for fenced brokers, offline replicas and ISR changes.
- Kafka Exporter (`spec.kafkaExporter`) gives only consumer-group and lag metrics (medium confidence, M12). The example setup scrapes it with the `kafka-resources-metrics` PodMonitor.
- Operators expose Prometheus metrics by default. Cruise Control metrics are covered in the metrics assembly.
- Custom resource state comes from kube-state-metrics; the Strimzi resource-state metrics were removed in 1.2.0 (medium confidence, M18).
- Entity Operator health-check port names changed from `healthcheck` to `healthcheck-to` in 1.1.0; update custom monitors and NetworkPolicies (medium confidence, M18).

## Operational signals

Sources: [manual roll](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-manual-rolling-update-pods.adoc), [recovery procedure](https://raw.githubusercontent.com/strimzi/strimzi-kafka-operator/1.3.0/documentation/modules/managing/proc-cluster-recovery-volume.adoc).

- Reconciliation runs every two minutes by default; Topic Operator `reconciliationIntervalMs` default is 120000 (medium confidence, M17).
- Pause reconciliation with `strimzi.io/pause-reconciliation="true"` (medium confidence, M17).
- Strimzi sets no resource requests or limits by default (medium confidence, M1).
- Heap goes in `jvmOptions` (`-Xms`, `-Xmx`); GC logging through `gcLoggingEnabled` (medium confidence, M1 page).

## Verification commands

All assembled (unverified, U6); pod names per register I4.

```bash
kubectl get kafkatopics -o wide -w          # READY True
kubectl get kafkausers -o wide -w           # READY True
kubectl get kafkarebalance -o wide -w -n kafka   # ProposalReady / Ready
kubectl exec -n kafka <broker-pod> -- bin/kafka-topics.sh --bootstrap-server localhost:9092 --describe --under-replicated-partitions
# Expected: no output (path and listener are assumptions)
```

## Quality control

- There is no documented mocking framework for Strimzi custom resources (unverified, U12). For disposable clusters the official examples `kafka/kafka-single-node.yaml` and `kafka/kafka-ephemeral.yaml` exist (medium confidence, named in the deploying guide). Ephemeral storage is unsuitable for replication factor 1 topics.
- Test MirrorMaker 2 active/passive failover "in a controlled environment" ([deploying guide](https://strimzi.io/docs/operators/1.3.0/deploying.html), medium confidence).
