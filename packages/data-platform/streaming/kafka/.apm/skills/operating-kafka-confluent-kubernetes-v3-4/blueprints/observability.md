# Observability, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). Source: the CFK 3.4 monitoring page (S23, https://docs.confluent.io/operator/3.4/co-monitor-cp.html), read in full on 2026-11-04. It is the only monitoring page read, so recommendations here carry (medium confidence). S-ids are in the [bibliography](./unverified-and-risks.md#source-bibliography).

## What CFK exposes (S23)

| Item | Value |
|---|---|
| JMX | disabled by default since CFK 3.2.1; port 7203 |
| Jolokia | port 7777 |
| JMX Prometheus exporter | port 7778 |
| Metric selection | `spec.metrics.prometheus` rules, blacklist and whitelist |
| Health+ telemetry | off by default |
| Credential changes | JMX credential changes need a pod restart |

Enable JMX explicitly, and pair JMX authentication with TLS in production (medium confidence).

## Stack options (medium confidence)

| Option | Note |
|---|---|
| Control Center with bundled Prometheus and Alertmanager | The bundled Prometheus cannot feed Grafana |
| Bring-your-own Prometheus | Control Center 2.7 with CFK 3.4 or later; no alerting |
| JMX, Jolokia, JMX Prometheus exporter | The exporter has no authentication, encryption or disable option in CFK |
| Health+ telemetry | Off by default |

Control Center is an Enterprise component (medium confidence, M32): see [licensing](./licensing.md). Prometheus has no TLS or mTLS in CFK (S23).

## Operational checks

```bash
# Representative: adapt namespace and names
kubectl get pods -n <namespace>                      # confluent-operator Running (S5)
kubectl get kafka -n <namespace>                     # STATUS RUNNING (S8)
kubectl exec kafka-0 -n <namespace> -- kafka-features --bootstrap-server kafka:9071 describe   # metadata version (S8)
kubectl get kafka <name> -n <namespace> -o jsonpath='{.metadata.annotations.platform\.confluent\.io/block-reconcile}'   # block state (S6)
```

## Gaps

- No alert thresholds are given on the page. Set them from your own baseline.
- Logs are lost on pod restart (S24); plan retention before the first deploy.
- The liveness probe in 3.4.0 is the `cfkprober` exec probe from the init container; with an old init image it fails open ([always-do A10](./always-do-patterns.md#a10)).
- No official CFK test harness or mock is documented. Rendering with `helm template` and checking with `kubectl apply --dry-run=server` is a suggestion, not a Confluent step (unverified, U11).
