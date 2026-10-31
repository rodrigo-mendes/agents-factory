### ⚠️ Ask First

**Decision Point**: Event Transport Selection — which OCI service to use for outbound messages

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| OCI Streaming | Throughput, ordering, replay, Kafka compatibility | Exactly-once delivery | High-volume event streams, analytics pipelines, event sourcing |
| OCI Queue | Exactly-once delivery, dead-letter queues, visibility timeout | Throughput, ordering | Task queues, reliable async processing, downstream workers |
| OCI Notifications (ONS) | Fan-out, multi-protocol (email, SMS, HTTPS, PagerDuty) | Throughput (60 TPM/topic), replay | Alerts, human notifications, webhooks |
| OCI Monitoring | Time-series, alarms, dashboards | Arbitrary data storage | Metrics, KPIs, threshold-based alerting |
| OCI Logging | Structured search, retention, compliance | Real-time processing | Audit trails, debug logs, event archives |

**Agent Behavior**:
"Before implementing event publishing, ask the user:
'What is the downstream consumer pattern for these events?
- Stream processing / analytics pipeline → OCI Streaming
- Reliable async task queue → OCI Queue
- Alert / human notification (email/SMS) → OCI Notifications
- Business metrics / KPI tracking → OCI Monitoring
- Audit trail / structured logs → OCI Logging'"

**Decision Factors**:
- Expected message volume (messages/second)
- Ordering requirements (per-entity ordering vs. none)
- Delivery guarantee needed (at-least-once vs. exactly-once)
- Target consumers (machines vs. humans)

**Source**: https://docs.oracle.com/en-us/iaas/api/

---

**Decision Point**: Streaming Message Key Strategy — determines partition placement and ordering

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| Null key | Even distribution across partitions | Ordering | Independent events, maximum throughput |
| Entity ID as key | Per-entity ordering guarantee | Even distribution | Order-sensitive entity events (e.g., order lifecycle) |
| Random UUID key | Even distribution | Any ordering | Load balancing, no ordering needed |

**Agent Behavior**:
"Before choosing a Streaming key strategy, ask:
'Do events for the same entity (e.g., same order, same customer) need to be processed in order?
- Yes → use Entity ID as the message key
- No → use null key for maximum throughput'"

**Decision Factors**:
- Whether downstream consumers require per-entity ordering
- Number of distinct entities vs. partitions
- Risk of hot partitions with skewed entity distribution

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/streaming/20180418/Message/PutMessages

---

**Decision Point**: Monitoring BatchAtomicity — controls partial failure behavior

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| `NON_ATOMIC` | Availability, partial success accepted | Consistency (some metrics may fail) | Best-effort metric reporting (default for most functions) |
| `ATOMIC` | Data consistency, all-or-nothing | Availability (entire batch fails if one metric invalid) | Critical metrics that must be published together |

**Agent Behavior**:
"Before configuring PostMetricData, ask:
'Is it acceptable for some metrics to succeed while others fail in the same batch?
- Yes → use NON_ATOMIC (recommended default)
- No, all must succeed or fail together → use ATOMIC'"

**Source**: https://docs.oracle.com/en-us/iaas/api/#/en/monitoring/20180401/MetricData/PostMetricData

---

