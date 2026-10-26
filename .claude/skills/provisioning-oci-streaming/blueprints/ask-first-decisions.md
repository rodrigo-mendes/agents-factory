### ⚠️ Ask First

**Decision Point**: Public vs Private Stream Pool

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **Public** (no `private_endpoint_settings`) | Accessibility — any client with credentials can connect | Security — endpoint exposed to internet | Dev/test, PoC, producers external to VCN |
| **Private** (`private_endpoint_settings { subnet_id, nsg_ids }`) | Security — accessible only from within VCN | Accessibility — requires VPN/FastConnect for external access | Production, sensitive data, compliance |

**Agent Behavior**:
"Before provisioning the Stream Pool, ask:
'Will this streaming infrastructure carry sensitive data or be used in production? If yes, a private endpoint with NSG controls is required. Note that this setting is **immutable** — changing from public to private later requires destroying and recreating the pool and all its streams.'"

**Decision Factors**:
- Data sensitivity (PII, business events, audit logs)
- Network topology (VCN-only vs external access needed)
- Compliance requirements (PCI-DSS, SOC2)
- Immutability constraint — cannot change after creation

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream_pool

---

**Decision Point**: Oracle-Managed Key vs Customer-Managed Key (KMS)

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|---------------|------------|-------------|
| **Oracle-Managed** (no `custom_encryption_key` block) | Simplicity — zero configuration | Control — Oracle manages rotation and access | Dev/test, non-sensitive data |
| **Customer-Managed KMS** (`custom_encryption_key { kms_key_id }`) | Full control — key rotation, audit, revocation | Complexity — requires Vault + IAM policy | Production, compliance, sensitive data |

**Agent Behavior**:
"Before configuring encryption, ask:
'Do you need customer-managed encryption keys for compliance? Note: if the KMS key is disabled or deleted, the entire Stream Pool becomes inaccessible and irrecoverable.'"

**Decision Factors**:
- Compliance requirements (key rotation audit trail)
- Operational readiness for Vault/KMS management
- Risk tolerance for key lifecycle events

**IAM Policy Required for KMS**:
```hcl
# Required when using customer-managed key (OCI Provider v6.x+)
"Allow service streaming to use keys in compartment ${var.compartment_name} where target.key.id = '${var.kms_key_ocid}'"
```

**Source**: https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/streaming_stream_pool

---

**Decision Point**: Partition Count Sizing (IMMUTABLE — cannot change after creation)

> ⚠️ This decision is included in this Terraform skill because partitions are **immutable** — changing them requires destroy/recreate with data loss. No separate `oci-streaming-architecture` skill exists yet.
| Partitions | Write Throughput | Read Throughput | Consumer Parallelism | Choose When |
|------------|-----------------|-----------------|---------------------|-------------|
| 1 | 1 MB/s | 2 MB/s | 1 thread | Low-traffic, strict ordering |
| 5 | 5 MB/s | 10 MB/s | 5 threads | Medium traffic, serverless APIs |
| 20 | 20 MB/s | 40 MB/s | 20 threads | High-throughput, event sourcing |
| 50 (max) | 50 MB/s | 100 MB/s | 50 threads | Extreme throughput |

**Agent Behavior**:
"Before setting partitions, ask:
'What is your expected peak write throughput (MB/s) and how many concurrent consumers do you need? Remember: partitions are **immutable** — they cannot be changed after creation without destroying and recreating the stream (data loss). Plan for peak load + growth margin.'"

**Decision Factors**:
- Expected peak write throughput (1 MB/s per partition)
- Required consumer parallelism (1 consumer per partition per group)
- Cost impact (billed per partition-hour)
- Ordering requirements (ordering guaranteed only within a partition)
- Immutability — cannot increase/decrease after creation

**Source**: https://docs.oracle.com/en-us/iaas/Content/Streaming/Concepts/streamingoverview.htm

---

