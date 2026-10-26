# Reference Architectures — applying-aws-well-architected

Source: AWS Well-Architected Framework, November 6, 2024 edition (research date 2026-08-27).
Sources without a publish date below were accessed 2026-08-27.

---

## RA-1 — Three-Tier Highly-Available Web Application

**Context**: Web/API workloads requiring SQL, stateful sessions, and high availability within a single Region.

| Layer | Service | Purpose |
|-------|---------|---------|
| DNS | Route 53 | Latency/failover routing; health checks |
| Edge | CloudFront + AWS WAF + Shield | CDN, DDoS protection, WAF rules |
| Load balancing | ALB (multi-AZ) | Layer-7 routing, SSL termination |
| Compute | EC2 Auto Scaling / ECS Fargate (multi-AZ) | Stateless app tier; scales with demand |
| Database | RDS Multi-AZ / Aurora | Relational data; automatic failover |
| Cache | ElastiCache (multi-AZ) | Session store, hot data |
| Object store | S3 | Static assets, backups |

**Key decisions**:
- Multi-AZ must be explicitly enabled for RDS and ElastiCache (S3 and DynamoDB are Multi-AZ by default).
- Route 53 health checks with ELB + TTL ≤ 60 s for DNS failover.
- ELB is the single entry point — no direct EC2 exposure.

**Scaling path**: Single Region multi-AZ → read replicas → Aurora Global DB for multi-Region → Active/Active with ARC.

**Source**: REL10-BP01 https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/rel_fault_isolation_multiaz_region_system.html + AWS Solutions Library Containerized Web App Guidance

---

## RA-2 — Serverless Web / API Application

**Context**: Event-driven, variable-traffic, API-first workloads requiring minimal operational overhead.

| Layer | Service | Purpose |
|-------|---------|---------|
| Frontend | CloudFront + S3 (SPA) | Static asset delivery; cache |
| Auth | Amazon Cognito user pools | Authentication; JWT issuance |
| API | API Gateway | REST/HTTP API; Cognito/JWT authorizer |
| Compute | Lambda | Business logic; scales to 0 |
| Database | DynamoDB | Single-digit ms KV access |
| Cache (optional) | ElastiCache / DAX | Hot path acceleration |
| Event routing | EventBridge | Decoupled async processing |
| Buffering | SQS | Spike absorption; at-least-once delivery |

**Key decisions**:
- Cognito user pools → JWT authorizer in API Gateway (no custom auth code).
- EventBridge for cross-service decoupling (up to 5 targets per rule); SQS for load leveling before Lambda consumers — consumers must be idempotent.
- DynamoDB PITR enabled from day 1.
- Lambda max timeout is 15 minutes — use Fargate/ECS for longer work.

**Scaling path**: Single Region → DynamoDB global tables → CloudFront multi-Region origins → Route 53 latency routing for multi-Region active/active API.

**Source**: Serverless Applications Lens https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/ + API Gateway Cognito integration docs + Lambda reference architecture

---

## RA-3 — Multi-Account Landing Zone (Security Reference Architecture)

**Context**: Enterprise-scale AWS organization with multiple teams, workloads, and compliance requirements.

| Layer | Service | Purpose |
|-------|---------|---------|
| Org root | AWS Organizations | Account hierarchy; SCP/RCP attachment |
| Baseline | Control Tower | Automated account vending; StackSets |
| Identity | IAM Identity Center | SSO for all accounts |
| Security OU | CloudTrail org trail → S3 (Log Archive) | Immutable audit log |
| Security OU | GuardDuty + Security Hub + Config (delegated admin in Audit account) | Centralized threat detection |
| Infrastructure OU | Transit Gateway (Network account) | Hub-and-spoke connectivity |
| Workloads OU | One account per workload × env | Blast radius isolation |

**Key decisions**:
- Management account holds no workloads. SCPs/RCPs do not apply to the management account — enforce via separate preventive controls.
- From Control Tower Landing Zone v4.0, mandatory controls are NOT applied by default — verify active controls per version.
- RCPs (launched 2024-11-13; ~40 services as of 2026-08-27) cap resource access, including by external principals.
- Transit Gateway for hub-and-spoke at scale; VPC peering for a small number of high-throughput VPC pairs (peering is not transitive).

**Scaling path**: Control Tower landing zone → workload accounts via Account Factory → Security Hub as org-wide aggregator → Network Firewall in the Network account.

**Source**: https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/recommended-ous-and-accounts.html + AWS SRA https://docs.aws.amazon.com/prescriptive-guidance/latest/security-reference-architecture/architecture.html + RCPs https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_rcps.html

---

## Supporting Cloud-Native Patterns

| Pattern | AWS Implementation | Key Trade-off | Source |
|---------|-------------------|---------------|--------|
| Event-driven | EventBridge bus; up to 5 targets per rule; Pipes for point-to-point | Eventual consistency; schema discipline required | https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html |
| Circuit breaker | Step Functions (Express) + DynamoDB CircuitStatus table with TTL auto-reset; CLOSED/OPEN/HALF-OPEN | Added latency per state check | https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html |
| Queue-based load leveling | SQS + queue-depth alarm → Auto Scaling consumers; retention default 4 days, 60 s–14 days | At-least-once delivery; idempotent consumers | https://docs.aws.amazon.com/AWSSimpleQueueService/latest/SQSDeveloperGuide/welcome.html |
| CQRS | DynamoDB → Streams → Lambda → Aurora, or RDS + read replicas | Eventual consistency — confirm with the business; specific lag guarantees are (unverified) per implementation | https://docs.aws.amazon.com/prescriptive-guidance/latest/modernization-data-persistence/cqrs-pattern.html |
