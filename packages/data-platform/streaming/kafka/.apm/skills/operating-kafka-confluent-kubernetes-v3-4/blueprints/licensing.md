# Licensing, CFK 3.4.0

Back to [SKILL.md](../SKILL.md). Statements come from the CFK license page (S3, https://docs.confluent.io/operator/3.4/co-license.html) and the Confluent Platform license page (S4, https://docs.confluent.io/platform/current/installation/license.html, CP 8.4 per its breadcrumb). Rows based on the Confluent Platform license page (S4) are (medium confidence, M32); rows that cite only the CFK license page (S3) or the supported environments page (S2) are (medium confidence, M31). This skill adds no license claims of its own. If the user needs a legal answer, send them to Confluent.

## What runs without a key, what needs Enterprise

| Question | Answer | Source |
|---|---|---|
| What runs with no license key? | "You can use Confluent Platform for a 30-day trial period without a license key" (medium confidence, M32) | S3, S4 |
| Developer license | Free, no expiry, single broker per cluster; adding a broker starts a 30-day trial (medium confidence, M32) | S4 |
| Developer license with CFK | CFK needs at least 3 brokers (S22), so the single-broker developer license does not fit a supported CFK topology (medium confidence, inferred) | S4, S22 |
| Is CFK itself licensed? | CFK is listed under the Confluent Platform (Enterprise) subscription; "CFK is not affected by license expiration" (medium confidence, M32) | S4 |
| Enterprise features (Confluent Server) | Cluster Linking, Multi-Region Clusters, RBAC, Structured Audit Logs, Schema Validation, Secrets Protection, Self-Balancing Clusters, Tiered Storage. Also Schema Linking, Data Contracts, Control Center, CFK, Replicator, MQTT Proxy (medium confidence, M32) | S4 |
| Only if in the order | Flink, CSFLE, Health+, USM, Confluent Gateway, Premium and Commercial connectors (medium confidence, M32) | S4 |
| Community License | Admin REST API, Confluent CLI, REST Proxy, ksqlDB, Schema Registry, Community connectors (medium confidence, M32) | S4 |
| Apache 2.0 | Apache Kafka (with Connect and Streams), Apache ZooKeeper, Confluent clients, open source connectors (medium confidence, M32) | S4 |
| Multi-tenancy | Up to three Logical Kafka Clusters per Physical Kafka Cluster without a license; more need a Confluent Private Cloud license (medium confidence, M31) | S3 |
| Confluent Cloud enterprise license | Allows self-managed components "exclusively with Confluent Cloud services" (medium confidence, M31) | S3 |
| Support tier | "Platinum tier support is not offered for CFK" (medium confidence, M31) | S2 |

## What happens on expiry

On restart after trial or license expiry (S4) (medium confidence, M32):
- Control Center and MQTT Proxy fail to start.
- Replicator stops or fails to start.
- Connectors and security plugins fail to start.
- Confluent Server starts but logs frequent errors.
- Community components keep working unless security plugins are used.
- CFK itself is not affected (S4).

Conflict kept as published: the same page also says a trial license "stops functioning when it expires" while Confluent Server "starts but logs frequent errors" (medium confidence). Do not choose between them; test on a lab cluster.

## Flagged conflicts and gaps

| Item | State | Tag |
|---|---|---|
| Self-Balancing is enabled by default in CFK (S20) and is an Enterprise feature (S4), so a default CFK Kafka uses an Enterprise feature | Inference | (medium confidence) |
| Schema Registry ACL authorizer is enabled through the "Schema Registry Security Plugin" (S19) and security plugins fail to start after expiry (S4), so it needs a valid license | Inference | (medium confidence) |
| Simple ACLs after license expiry | Not stated on any page read | (unverified) |
| CFK running the community `cp-kafka` broker image (a no-license path) | Not documented; the custom registry page names only `cp-server` for brokers (S28) | (unverified) |
| Licensing of Schema Registry features | Out of scope: use `managing-event-schemas-confluent-v8-4` | none |

Register ids: [I1, I2 and M23, M24](./unverified-and-risks.md#irresolvable-i1i4-4-items). Do not tell a user that a fully Community-licensed Kafka runs under CFK: treat CFK as deploying Confluent Server (`cp-server`) and plan for the 30-day trial or a subscription.

## Delivering a license (S3)

```bash
# Representative: global license at install
helm upgrade --install confluent-operator \
  confluentinc/confluent-for-kubernetes \
  --namespace confluent \
  --set licenseKey=<CFK license key>
kubectl confluent cluster license --secret-name confluent-operator-licensing --namespace confluent
```

Delivery options and cautions (global, per-component secret, Vault; do not delete the licensing secrets; use the Kafka restart procedure after a change) are in [ask-first-decisions](./ask-first-decisions.md#license-delivery-c5) (medium confidence). The Centralized Connect License needs `cp-server-connect`: see [always-do A13](./always-do-patterns.md#a13).
