# Ask First Decisions — securing-aws-secrets-certificates

Full decision matrices for architectural crossroads. Summary in [../SKILL.md](../SKILL.md).

---

## Decision 1 — KMS Key Type Selection

**Ask**: "Does this secret or data store need to be shared across AWS accounts, or does it require a custom key policy (cross-account, compliance-mandated rotation schedule, fine-grained audit)?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| AWS owned key | Zero management; free; automatic | No CloudTrail in your account; no key policy control | Default encryption; no compliance requirement; lowest overhead |
| AWS managed key (`aws/<service>`) | No monthly storage cost; auditable in your CloudTrail | Key policy not modifiable; no cross-account sharing; annual rotation only | Single-account workloads; standard compliance; Secrets Manager single-account |
| Customer Managed Key (CMK) | Full control: key policies, grants, custom rotation, cross-account | $1.00/month/key + $0.03/10K symmetric API calls; operational overhead | Cross-account access; compliance mandates (PCI DSS, HIPAA); fine-grained audit; custom rotation period |

**Cost profile**:
- AWS owned = $0
- AWS managed = $0 storage, auditable API calls count toward free tier
- CMK = $1.00/month/key + $0.03/10K symmetric API calls

**Lock-in**: KMS is AWS-specific. Keys cannot be exported in plaintext. CMK material stays within FIPS 140-3 Level 3 HSMs.

**Architect instruction**: If "yes" to cross-account or custom key policy → CMK required. If single-account workload with standard compliance → AWS managed key. If zero compliance overhead needed → AWS owned.

---

## Decision 2 — Secrets Manager Rotation Strategy

**Ask**: "Can the application tolerate a brief credential rejection during rotation? (Seconds during which new password is in Secrets Manager but old connections still use the old password)"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Managed rotation (RDS) | Zero Lambda management; AWS-owned rotation logic | Limited to RDS-supported databases | Amazon RDS managed secrets; simplest path |
| Single-user Lambda rotation | Simplicity; works for all secret types; AWS-provided templates | Brief rotation-window auth-denial risk (seconds) | Batch jobs; dev/staging; low-traffic; applications with retry logic |
| Alternating-users Lambda rotation | Zero auth denial during rotation; both credentials valid simultaneously | Requires superuser secret (+$0.40/month); manual permission sync if original user permissions change | Production databases; SLA > 99.9%; HA applications |

**Cost profile**:
- Lambda invocation: ~$0.0000002/request × rotation frequency
- Alternating-users: +$0.40/month for superuser secret

**Architect instruction**: If application has SLA requirement or retry logic is not implemented → alternating-users. If RDS and simplicity prioritized → managed rotation. Single-user acceptable for non-production.

**Rotation templates**: AWS provides Lambda rotation function templates for RDS MySQL, PostgreSQL, Oracle, SQL Server, MariaDB, DocumentDB, Redshift, and MongoDB (alternating-users and single-user variants).

---

## Decision 3 — Secret Retrieval Pattern for Compute

**Ask**: "Must the secret refresh in the running application without a container restart after rotation?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| ECS task definition `secrets` array (env var injection) | Zero application code; ECS control plane handles retrieval | Secret static at task start; rotation requires `force-new-deployment` | Simple apps; infrequently rotating secrets; acceptable restart-on-rotation |
| Lambda Parameters and Secrets Extension | Runtime-agnostic caching (TTL 300s default); no code SDK calls; reduces API costs | Slightly higher cold-start; 300s stale window | Lambda functions (all runtimes); moderate rotation frequency |
| Language-specific SDK caching | Fine-grained TTL control; in-process cache; live refresh on TTL expiry | Application code dependency on AWS SDK | Long-running ECS/EC2 services needing live refresh without restart |
| Workload Credentials Provider sidecar | HTTP API at localhost; role chaining; post-quantum ML-KEM by default | Not encrypted in local cache; sidecar container overhead | ECS/EKS sidecar pattern; polyglot environments; post-quantum requirement |

**Cost profile**: Extension and sidecar reduce API call cost by caching (300s TTL vs per-request at $0.05/10K calls for Secrets Manager API).

**Architect instruction**: If secret must refresh without container restart → SDK caching or Workload Credentials Provider. If restart on rotation is acceptable → ECS secrets injection (simplest). Lambda → Lambda extension.

---

## Decision 4 — ACM Certificate Scope: Wildcard vs SAN

**Ask**: "Do test or staging environments use dynamically generated subdomain names (e.g., `feature-branch-name.staging.example.com`)?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Wildcard (`*.example.com`) | One cert covers all subdomains at one level; one DNS CNAME validation record | Does not cover the apex domain (`example.com`) or nested subdomains (`a.b.example.com`) | Many ephemeral subdomains; test/staging environments with dynamic subdomain names |
| SAN cert (multiple FQDNs) | Covers exact domains including apex + different hostname patterns | One CNAME validation record per FQDN; cannot add new domains to an existing cert (must request new cert) | Known, stable set of domains (apex + www + api + admin); production environments |

**Cost profile**: Both options are free for ACM-managed certificates associated with AWS services.

**Architect instruction**: If subdomain names are dynamically generated → wildcard. If domain set is stable and known at provisioning time → SAN cert. Production best practice: SAN cert (explicit domain list reduces blast radius if cert compromised).

**Note**: Wildcard covers `*.example.com` but NOT `example.com` — a SAN entry for the apex domain must be added if needed.

---

## Decision 5 — Public ACM Certificate vs Private CA

**Ask**: "Is the certificate for a public internet-facing endpoint, or is it for internal service communication, mTLS, Kubernetes pods, or on-premises IAM authentication?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| ACM public cert | Free; browser-trusted; fully automated renewal; no export needed | Cannot be exported; no `clientAuth` EKU (removed June 2025); no mTLS client certs | Internet-facing HTTPS: CloudFront, ALB, API Gateway |
| Private CA General-purpose | Full PKI control; exportable certs; mTLS; IAM Roles Anywhere; code signing | $400/month + $0.75/cert; no browser trust by default; CA hierarchy design required | Internal mTLS; Kubernetes pod identity; on-premises IAM credentials; code signing |
| Private CA Short-lived | Lower fixed cost; $0.058/cert for high-volume short-lived workloads | $50/month; short validity requires automated renewal pipeline; no long-lived use cases | Short-lived cert workloads (hours to days validity); frequent rotation; service mesh |

**Cost profile**:
- ACM public = $0 (free)
- Private CA General = $400/month + $0.75/cert issued
- Private CA Short-lived = $50/month + $0.058/cert issued (min 7-day validity up to 30 days)

**Architect instruction**: Public internet endpoint → ACM public. Internal/mTLS → Private CA. High-volume short-lived → Private CA Short-lived for cost optimization.

**Private CA hierarchy**: Always deploy each CA level in a separate AWS account. Root CA account → offline between operations. Intermediate CA accounts → issue end-entity certs.

---

## Decision 6 — Multi-Region Secrets Architecture

**Ask**: "Must each region retrieve secrets with sub-second latency, OR must the application operate independently (read secrets locally) during a primary-region outage?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Single-region; cross-region SDK calls | Simplicity; single source of truth; no replication cost | Cross-region latency for non-primary deployments; dependency on primary region availability | Single-region workloads; primary-region-only active traffic |
| Multi-region replication | Local read latency; regional resilience; rotation propagates automatically | +$0.40/secret/month per replica region; separate CMK per region; promotion required for DR | Active-active multi-region; DR with fast RPO; applications that need local read during primary outage |
| Centralized secrets account | Central governance; single audit trail; separation of duties | Cross-account complexity; CMK required (AWS managed key cannot be shared cross-account); PrivateLink needed | Large organizations; shared platform teams; compliance requiring central secrets governance |

**Cost profile**:
- Replication: +$0.40/secret/month per replica region + per-region KMS CMK cost ($1/month)
- Centralized account: CMK required; cross-account PrivateLink adds ~$0.01/hour/AZ

**Failover procedure (replication)**:
```bash
# Promote replica to standalone in DR region
aws secretsmanager stop-replication-to-replica \
  --secret-id arn:aws:secretsmanager:us-west-2:123456789:secret:prod/myapp/db-credentials

# After recovery: re-establish replication from original primary
# OR treat promoted secret as new primary and re-create replication from us-west-2
```

**Note**: Rotation runs only in the primary region and propagates to all replicas automatically. After DR promotion, configure rotation in the promoted region manually.

**Constraint**: Replication cannot cross commercial/GovCloud/China region boundaries. As of April 2026, the Secrets Manager console accepts cross-account CMK ARN input directly (simplifying the centralized account pattern).
