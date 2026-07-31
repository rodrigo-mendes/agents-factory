# Always-Do Patterns — AWS Well-Architected Framework

> Source: AWS WAF research file `research_aws_waf_2025.md`, accessed 2026-07-31.
> Framework edition: November 6, 2024 (current stable).

These 8 patterns are mandatory for production AWS workloads (multi-tenant SaaS, web APIs, data pipelines).
Each entry specifies the pillar, exact AWS service names, architecture decision, verification steps, and trade-offs.

---

## AD-1 — Centralize identity and eliminate long-term static credentials

| Field | Detail |
|---|---|
| **Why (pillar)** | Security — "Implement a strong identity foundation" design principle |
| **AWS services** | AWS IAM Identity Center (workforce SSO), IAM roles + IAM Roles Anywhere, Amazon Cognito (application end-users), AWS Security Token Service (STS) for temporary credentials |
| **Architecture decision** | Human access via IAM Identity Center federation; workload access via IAM roles (EC2 instance profiles, IRSA on Amazon EKS, task roles on Amazon ECS). Never embed IAM user access keys in code or AMIs. |
| **Verification** | `aws iam list-users` shows near-zero long-lived users; IAM Access Analyzer unused-access findings = 0; AWS Config rules `iam-user-no-policies-check` / `access-keys-rotated` compliant |
| **Trade-offs** | Federation setup adds initial complexity and an IdP dependency; temporary credentials require SDK/role-assumption plumbing |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31 |

---

## AD-2 — Encrypt data at rest and in transit by default

| Field | Detail |
|---|---|
| **Why (pillar)** | Security — "Protect data in transit and at rest" |
| **AWS services** | AWS KMS (customer-managed keys), Amazon S3 default encryption (SSE-KMS), Amazon RDS / Amazon Aurora storage encryption, Amazon EBS encryption-by-default, AWS Certificate Manager (ACM) for TLS, Amazon DynamoDB encryption at rest |
| **Architecture decision** | Enable account-level EBS encryption-by-default and S3 default encryption; terminate TLS at Elastic Load Balancing (ALB/NLB) or Amazon CloudFront with ACM certificates; enforce TLS ≥ 1.2 |
| **Verification** | AWS Config rules `encrypted-volumes`, `s3-bucket-server-side-encryption-enabled`, `rds-storage-encrypted` compliant; ELB security policy = `ELBSecurityPolicy-TLS13-*` |
| **Trade-offs** | KMS request costs and key-management overhead; envelope encryption adds minor latency |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31 |

---

## AD-3 — Design for Multi-AZ high availability

| Field | Detail |
|---|---|
| **Why (pillar)** | Reliability — "Scale horizontally to increase aggregate workload availability" |
| **AWS services** | Amazon RDS Multi-AZ (or Amazon Aurora across multiple AZs), Amazon EC2 Auto Scaling across ≥ 2 AZs, Elastic Load Balancing, Amazon EKS / Amazon ECS across AZs, Amazon S3 (11 9s durability, multi-AZ by design) |
| **Architecture decision** | Deploy every stateful and stateless tier across at least two (preferably three) Availability Zones in a Region; use Amazon RDS Multi-AZ for automatic failover of the database tier |
| **Verification** | RDS instance `MultiAZ = true`; Auto Scaling group spans ≥ 2 subnets in distinct AZs; run a failover game day (reboot-with-failover) and confirm recovery within RTO |
| **Trade-offs** | Multi-AZ roughly doubles standby compute/storage cost for RDS; cross-AZ data transfer charges apply |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-principles.html — accessed 2026-07-31 |

---

## AD-4 — Manage infrastructure and operations as code

| Field | Detail |
|---|---|
| **Why (pillar)** | Operational Excellence — "Safely automate where possible"; Security — "Automate security best practices" |
| **AWS services** | AWS CloudFormation / AWS CDK, AWS Systems Manager (patching, runbooks/Automation documents), AWS CodePipeline + AWS CodeBuild, AWS Config for drift/compliance |
| **Architecture decision** | All infrastructure defined in version-controlled templates; changes flow through CI/CD with automated tests; no console ("ClickOps") changes in production |
| **Verification** | CloudFormation drift detection reports no drift; every prod change traces to a merged commit + pipeline execution; AWS Config timeline shows IaC-driven changes only |
| **Trade-offs** | Upfront authoring effort and learning curve; emergency break-glass paths must be governed and audited |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31 |

---

## AD-5 — Implement observability (metrics, logs, traces) with actionable alarms

| Field | Detail |
|---|---|
| **Why (pillar)** | Operational Excellence — "Implement observability for actionable insights" |
| **AWS services** | Amazon CloudWatch (metrics, Logs, alarms, dashboards), AWS X-Ray (distributed tracing), Amazon Managed Service for Prometheus + Amazon Managed Grafana (containerized workloads), AWS CloudTrail (API audit) |
| **Architecture decision** | Emit structured logs to Amazon CloudWatch Logs; define business-KPI alarms (not just CPU); enable AWS X-Ray tracing across API → service → data tiers |
| **Verification** | Each critical user journey has ≥ 1 CloudWatch alarm tied to a KPI; CloudTrail enabled in all Regions with log-file validation; alarms route to a notification/on-call path (e.g., Amazon SNS → incident tool) |
| **Trade-offs** | Log ingestion/retention and custom-metric costs grow with volume; high-cardinality metrics need budgeting |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/oe-design-principles.html — accessed 2026-07-31 |

---

## AD-6 — Store secrets in a managed secrets service, not in code or environment files

| Field | Detail |
|---|---|
| **Why (pillar)** | Security — "Keep people away from data" + "Implement a strong identity foundation" |
| **AWS services** | AWS Secrets Manager (with automatic rotation), AWS Systems Manager Parameter Store (SecureString) for lower-sensitivity config, AWS KMS for encryption |
| **Architecture decision** | Applications fetch secrets at runtime via IAM-scoped calls to AWS Secrets Manager; enable automatic rotation for database credentials; never commit secrets to Git or bake into container images |
| **Verification** | Secret scanning (e.g., in CodeBuild/GitHub Actions) shows no committed secrets; Secrets Manager rotation `RotationEnabled = true` on DB secrets; IAM policies scope `secretsmanager:GetSecretValue` to specific ARNs |
| **Trade-offs** | Secrets Manager per-secret monthly cost + API calls; rotation Lambda functions add maintenance; Parameter Store is cheaper but lacks native rotation |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html — accessed 2026-07-31 |

---

## AD-7 — Establish multi-account governance and guardrails

| Field | Detail |
|---|---|
| **Why (pillar)** | Security + Operational Excellence — separation of duties, blast-radius isolation |
| **AWS services** | AWS Organizations (with Service Control Policies), AWS Control Tower, AWS IAM Identity Center, AWS CloudTrail organization trail, centralized Amazon S3 log-archive account |
| **Architecture decision** | Separate accounts per environment (prod/non-prod) and per workload; enforce guardrails with Service Control Policies; centralize logging and security tooling in dedicated accounts |
| **Verification** | SCPs deny disabling CloudTrail/GuardDuty; Control Tower shows no non-compliant accounts; each production workload isolated in its own account/OU |
| **Trade-offs** | Cross-account networking and IAM complexity; more accounts to operate (offset by Control Tower automation) |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/framework/sec-design.html — accessed 2026-07-31 |

---

## AD-8 — Set budgets, cost-allocation tags, and right-sizing reviews

| Field | Detail |
|---|---|
| **Why (pillar)** | Cost Optimization — "Analyze and attribute expenditure"; Sustainability — "Maximize utilization" |
| **AWS services** | AWS Budgets, AWS Cost Explorer, AWS Cost and Usage Report (CUR), AWS Compute Optimizer, AWS Trusted Advisor, cost-allocation tags |
| **Architecture decision** | Apply mandatory cost-allocation tags (owner, environment, workload); create AWS Budgets alerts per account/workload; review AWS Compute Optimizer recommendations quarterly and right-size |
| **Verification** | > 95% of spend covered by cost-allocation tags; each account has an active AWS Budget with alert thresholds; Compute Optimizer over-provisioned findings actioned |
| **Trade-offs** | Tagging discipline requires enforcement (tag policies via AWS Organizations); right-sizing needs performance validation before applying |
| **Source** | https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/design-principles.html — accessed 2026-07-31 |
