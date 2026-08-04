# AWS Well-Architected Framework — General Framework Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS Well-Architected Framework"
Cloud_Provider: "AWS"
Architecture_Domain: "Well-Architected Framework"
Target_Edition: "AWS WAF 2024 (Publication date: November 6, 2024)"
Architecture_Context: "Production cloud-native workloads on AWS spanning compute, storage, database, networking, security, and observability — covering multi-tier web applications, microservices, data pipelines, and hybrid architectures"
Official_Source_URL: "https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to AWS service evolution velocity"
```

---

## Executive Summary

The AWS Well-Architected Framework is a structured set of best practices and architectural guidelines that enables cloud architects to evaluate and improve workloads deployed on AWS. Published and maintained by AWS Solutions Architects, the framework provides a consistent approach to assessing architectures against six quality pillars: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, and Sustainability. The framework is not prescriptive in mandating a single "correct" architecture — instead, it surfaces trade-offs between pillars, provides assessment questions to identify improvement areas, and offers remediation guidance calibrated to the workload's business context. The AWS Well-Architected Tool (console service) operationalizes the framework through workload reviews, milestone tracking, and improvement plans.

The 2024 edition (published November 6, 2024) consolidates several evolutionary changes: (1) **Sustainability pillar maturation** — sustainability guidance now includes concrete service-level recommendations (Graviton instance selection, right-sizing automation, data lifecycle policies) rather than purely principled guidance; (2) **AI/ML workload integration** — the framework now explicitly addresses generative AI workload patterns (model hosting, inference optimization, responsible AI guardrails) across Security, Performance Efficiency, and Cost pillars; (3) **Enhanced automation emphasis** — "Safely automate where possible" replaces older guidance, introducing the concept of automation guardrails (rate control, error thresholds, approval gates) as first-class architectural constructs; (4) **Observability over monitoring** — the framework shifts from "monitor everything" to "implement observability for actionable insights," emphasizing KPIs tied to business value rather than infrastructure metrics; (5) **Evolutionary architecture** — explicit recognition that architectures must evolve through data-driven decisions rather than upfront design perfection.

The three most critical architecture guardrails for production AWS workloads are: (1) **Security at all layers with least-privilege identity** — implement defense-in-depth from network edge to application code, with IAM policies scoped to specific resources and actions (no wildcard permissions in production); (2) **Multi-AZ deployment with automated failure recovery** — stateful services must span at least two Availability Zones with health-check-driven auto-recovery, and recovery procedures must be tested regularly through game days; (3) **Observability with business-aligned KPIs and cost attribution** — every workload must have CloudWatch dashboards tracking business outcomes (not just CPU/memory), billing alarms per workload via cost allocation tags, and automated alerting that triggers investigation workflows.

---

## Cloud Architecture Glossary

```
Term: Well-Architected Framework
Definition: A set of best practices across six pillars (Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability) that provides a consistent approach for evaluating architectures and implementing designs that scale with application needs on AWS.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/welcome.html
Architect Usage: Use as the primary evaluation framework during architecture reviews, pre-launch assessments, and quarterly operational reviews. Apply to every production workload — the framework is workload-centric, not account-centric.
Common Confusion: WAF (Well-Architected Framework) is frequently confused with AWS WAF (Web Application Firewall). In architecture discussions, "WAF" refers to the framework; in security configurations, "WAF" refers to the firewall service.

Term: Pillar
Definition: One of six categories of architectural best practices in the Well-Architected Framework. Each pillar has design principles, a definition, best practices organized by focus areas, and assessment questions. Pillars are: Operational Excellence, Security, Reliability, Performance Efficiency, Cost Optimization, Sustainability.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/the-pillars-of-the-framework.html
Architect Usage: Evaluate every architectural decision against all six pillars simultaneously. Trade-offs between pillars are expected and acceptable — but Security and Operational Excellence should rarely be traded off against other pillars.
Common Confusion: Pillars are not independent — they interact. Improving reliability (multi-AZ) increases cost. Improving performance (larger instances) increases cost and sustainability impact. The framework acknowledges this and requires conscious trade-off documentation.

Term: Workload
Definition: A set of components that together deliver business value. A workload is usually the level of detail that business and technology leaders communicate about. It is the unit of architecture review in the Well-Architected Framework.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html
Architect Usage: Define workload boundaries before conducting a Well-Architected Review. A workload may span multiple AWS accounts, regions, or services — but should represent a coherent business capability. Reviews are conducted per-workload, not per-account or per-service.
Common Confusion: A workload is NOT synonymous with an AWS account or a CloudFormation stack. A workload is defined by business value delivery, not by deployment artifact boundaries.

Term: Component
Definition: The code, configuration, and AWS Resources that together deliver against a requirement. A component is often the unit of technical ownership and is decoupled from other components.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html
Architect Usage: Components are the building blocks of workloads. Each component should have clear ownership, well-defined interfaces, and independent deployment capability. Use component boundaries to inform IAM role boundaries, monitoring boundaries, and blast radius isolation.
Common Confusion: A component is not necessarily a microservice. A component could be a shared database, a CDN configuration, or a CI/CD pipeline — anything that has clear ownership and delivers against a requirement.

Term: Lens
Definition: A supplemental perspective that extends the Well-Architected Framework with domain-specific guidance. Lenses (e.g., Serverless, SaaS, Machine Learning, Financial Services, IoT) provide additional best practices and assessment questions for specific workload types. Applied on top of — not instead of — the base framework.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/userguide/lenses.html
Architect Usage: Apply the relevant Lens(es) after completing the base framework review. A workload can have multiple Lenses applied simultaneously (e.g., SaaS Lens + Serverless Lens). Custom Lenses can be authored for organization-specific governance requirements.
Common Confusion: A Lens does not override the base framework — it supplements it. Skipping the base framework review and only applying a Lens leaves foundational gaps unaddressed.

Term: High Risk Issue (HRI)
Definition: A finding from a Well-Architected Review that represents a significant risk to the workload's security, reliability, performance, or cost posture. HRIs require immediate attention and remediation planning. Tracked in the AWS Well-Architected Tool with improvement plans and milestones.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/userguide/improvement-plan.html
Architect Usage: Prioritize HRI remediation over Medium Risk Issues (MRIs). Assign HRIs to specific team members with target resolution dates. Track progress through milestones in the Well-Architected Tool. HRIs in the Security pillar should be escalated to security teams immediately.
Common Confusion: An HRI is not a compliance failure — it is a risk indicator. The Well-Architected Review is a self-assessment, not an audit. HRIs indicate areas where the architecture deviates from best practices, but the business context may justify accepting certain risks.

Term: Milestone
Definition: A snapshot of a workload's Well-Architected Review state at a point in time. Milestones mark key changes in architecture as it evolves through the product lifecycle (design, implementation, testing, go-live, production). Used to track improvement over time.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html
Architect Usage: Create milestones at significant architecture decision points: initial design, pre-launch, post-launch, after major changes, quarterly reviews. Compare milestones to measure improvement and identify regression. Share milestone comparisons with leadership.
Common Confusion: Milestones are not deployment releases. They are architecture review snapshots. A single deployment release may or may not warrant a new milestone — create milestones when the architecture itself changes, not just the code.

Term: Shared Responsibility Model
Definition: The division of security and compliance responsibilities between AWS (security OF the cloud — physical infrastructure, hypervisor, managed services) and the customer (security IN the cloud — data, identity, application, network configuration, OS patching for EC2). The exact division varies by service type (IaaS vs PaaS vs SaaS).
Provider Docs Section: https://aws.amazon.com/compliance/shared-responsibility-model/
Architect Usage: For every AWS service in your architecture, understand which security responsibilities are yours. EC2: you patch the OS. RDS: AWS patches the engine (but you manage access, encryption, backups). Lambda: AWS manages everything below your code (but you manage IAM, code security, dependencies).
Common Confusion: "AWS manages security" does NOT mean you have no security responsibility. The customer always retains responsibility for data classification, identity management, network configuration, and application-level security — regardless of service type.

Term: Blast Radius
Definition: The scope of impact when a failure, misconfiguration, or security breach occurs in a component. Managed through isolation patterns: separate AWS accounts (organizational blast radius), separate VPCs (network blast radius), per-service IAM roles (identity blast radius), multi-AZ deployment (availability blast radius).
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/rel-dp.html
Architect Usage: Every architecture decision should be evaluated for blast radius. Use AWS Organizations with separate accounts for production/staging/development. Use separate VPCs for separate trust boundaries. Ensure a single component failure cannot cascade to unrelated workloads.
Common Confusion: Blast radius is not just about availability. A compromised IAM role with wildcard permissions has a blast radius of the entire AWS account — potentially all workloads in that account, regardless of VPC isolation.

Term: Level of Effort
Definition: A categorization of the time, effort, and complexity required to implement a remediation recommendation from a Well-Architected Review. Three levels: High (weeks-months, multiple stories), Medium (days-weeks, multiple tasks), Low (hours-days, single task).
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html
Architect Usage: Use Level of Effort to prioritize improvement plans. High-risk issues with low effort should be remediated first (quick wins). High-risk issues with high effort need project planning and resource allocation. Low-risk issues with high effort should be evaluated for ROI before investing.
Common Confusion: Level of Effort is organization-dependent — a small team may rate something as "High" that a large team rates as "Medium." The framework provides guidance, but each organization must calibrate based on their team size, expertise, and workload complexity.

Term: Well-Architected Tool
Definition: An AWS console service that provides a structured process for conducting Well-Architected Reviews. Allows defining workloads, applying Lenses, answering assessment questions, generating improvement plans, tracking milestones, and producing PDF reports. Available at no additional charge.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html
Architect Usage: Use the Well-Architected Tool to formalize and track reviews rather than conducting them ad-hoc. Share workload reviews across team members. Generate improvement plans with assigned owners. Use the API for programmatic access and integration with governance dashboards.
Common Confusion: The Well-Architected Tool is not a security scanner or compliance auditor. It is a questionnaire-driven self-assessment tool. It does not automatically inspect your AWS resources — you answer questions about your architecture and it generates recommendations.

Term: Trade-off
Definition: A conscious architectural decision to optimize one pillar at the expense of another, based on business context. The Well-Architected Framework explicitly acknowledges that trade-offs are necessary and acceptable — the key requirement is that they are conscious, documented, and aligned with business priorities.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/definitions.html
Architect Usage: Document all trade-offs in Architecture Decision Records (ADRs). Common trade-offs: Reliability ↔ Cost (multi-AZ costs more), Performance ↔ Cost (larger instances cost more), Security ↔ Developer Velocity (approval gates slow deployment). The framework states that Security and Operational Excellence should RARELY be traded off.
Common Confusion: A trade-off is not the same as technical debt. Trade-offs are conscious, documented, and aligned with business priorities. Technical debt is unintentional, undocumented, and misaligned with best practices. The Well-Architected Review helps distinguish between the two.

Term: Game Day
Definition: A planned event where teams simulate failure scenarios in production-like environments to validate recovery procedures, test monitoring/alerting, and build operational muscle memory. Recommended by both the Operational Excellence and Reliability pillars as a core practice.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/general-design-principles.html
Architect Usage: Schedule game days quarterly at minimum. Scenarios should include: AZ failure simulation, service degradation, security incident response, runbook validation, and communication protocol testing. Use AWS Fault Injection Service (FIS) for controlled chaos engineering experiments.
Common Confusion: A game day is not a tabletop exercise — it involves actual failure injection in test/staging environments (or production with controlled blast radius). It is not a disaster recovery drill alone — it tests the entire incident response chain from detection through resolution.

Term: Evolutionary Architecture
Definition: A design approach that accepts architecture decisions will change over time as business requirements evolve, new AWS services become available, and operational insights accumulate. The Well-Architected Framework explicitly states that architectures should evolve based on data, not be designed for perfection upfront.
Provider Docs Section: https://docs.aws.amazon.com/wellarchitected/latest/framework/general-design-principles.html
Architect Usage: Design for change: use loosely-coupled components, prefer managed services that reduce operational burden, automate infrastructure as code for reproducibility, and conduct regular reviews (quarterly) to identify evolution opportunities. Avoid premature optimization and over-engineering for scale you don't yet have.
Common Confusion: Evolutionary architecture ≠ no upfront design. It means making decisions that are reversible where possible, investing in foundational guardrails (security, networking, identity) that are hard to change later, and designing for the current scale with a clear path to the next scale.
```

---

## Architecture Framework Analysis: AWS Well-Architected Framework (2024 Edition)

### General Design Principles

The Well-Architected Framework identifies six general design principles that apply across all pillars:

1. **Stop guessing your capacity needs** — Use cloud elasticity to scale on demand rather than making fixed capacity decisions that result in idle resources or performance degradation
2. **Test systems at production scale** — Create production-scale test environments on demand, run tests, then decommission resources — paying only for active test time
3. **Automate with architectural experimentation in mind** — Define workloads and operations as code; automate responses to events; track and audit automation changes
4. **Consider evolutionary architectures** — Accept that architecture decisions evolve; leverage automation and testing to reduce risk of design changes; permit systems to evolve as standard practice
5. **Drive architectures using data** — Collect data on how architectural choices affect workload behavior; make fact-based improvement decisions over time
6. **Improve through game days** — Regularly simulate production events to test architecture and processes; build organizational experience in dealing with failures

Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/general-design-principles.html

---

### Pillar 1: Operational Excellence

```
Pillar: Operational Excellence
Definition: The ability to support development and run workloads effectively, gain insight into their operations, and to continuously improve supporting processes and procedures to deliver business value.
Key Design Principles:
  1. Organize teams around business outcomes
  2. Implement observability for actionable insights
  3. Safely automate where possible
  4. Make frequent, small, reversible changes
  5. Refine operations procedures frequently
  6. Anticipate failure
  7. Learn from all operational events and metrics
  8. Use managed services
Applies To Production Cloud-Native Workloads:
  - CloudWatch dashboards with business KPIs (order throughput, API latency p99, error rates)
  - CI/CD pipelines with automated testing, canary deployments, and automatic rollback
  - Infrastructure as Code (CloudFormation/CDK/Terraform) with drift detection
  - Runbooks and playbooks in Systems Manager for operational procedures
  - Post-incident reviews with corrective action tracking
Assessment Questions:
  1. How do you determine what your priorities are?
  2. How do you structure your organization to support your business outcomes?
  3. How do you know that you are ready to support a workload?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/operational-excellence.html
```

---

### Pillar 2: Security

```
Pillar: Security
Definition: The security pillar describes how to take advantage of cloud technologies to protect data, systems, and assets in a way that can improve your security posture.
Key Design Principles:
  1. Implement a strong identity foundation (least privilege, separation of duties, centralized identity, no long-term static credentials)
  2. Maintain traceability (monitor, alert, audit in real time; automate investigation)
  3. Apply security at all layers (defense in depth — edge, VPC, load balancer, instance, OS, application, code)
  4. Automate security best practices (security as code, version-controlled controls)
  5. Protect data in transit and at rest (encryption, tokenization, access control)
  6. Keep people away from data (reduce direct access, automate data processing)
  7. Prepare for security events (incident management policies, response simulations, automation for detection/investigation/recovery)
Applies To Production Cloud-Native Workloads:
  - IAM roles with resource-level permissions (no wildcard * actions/resources in production)
  - AWS Organizations with SCPs enforcing guardrails (deny root usage, require encryption)
  - VPC with private subnets, security groups, NACLs, and VPC Flow Logs
  - KMS customer-managed keys with key rotation for all data stores
  - GuardDuty + Security Hub for continuous threat detection and security posture management
  - CloudTrail enabled in all regions with log file validation
Assessment Questions:
  1. How do you manage identities for people and machines?
  2. How do you manage permissions for people and machines?
  3. How do you detect and investigate security events?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/security.html
```

---

### Pillar 3: Reliability

```
Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently when it's expected to. This includes the ability to operate and test the workload through its total lifecycle.
Key Design Principles:
  1. Automatically recover from failure (KPI monitoring triggers automation)
  2. Test recovery procedures (simulate failures, validate recovery strategies)
  3. Scale horizontally to increase aggregate workload availability
  4. Stop guessing capacity (monitor demand, auto-scale resources)
  5. Manage change through automation (infrastructure changes via automation, tracked and reviewed)
Applies To Production Cloud-Native Workloads:
  - Multi-AZ deployment for all stateful services (RDS Multi-AZ, ElastiCache Multi-AZ, EFS)
  - Auto Scaling Groups with health checks and minimum/maximum capacity
  - Route 53 health checks with failover routing policies
  - Circuit breaker patterns for inter-service communication
  - Regular backup testing and restore validation
  - Service quota monitoring with proactive increase requests
Assessment Questions:
  1. How do you manage service quotas and constraints?
  2. How do you plan your network topology?
  3. How do you design your workload service architecture?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/reliability.html
```

---

### Pillar 4: Performance Efficiency

```
Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements, and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles:
  1. Democratize advanced technologies (consume as services rather than building/maintaining)
  2. Go global in minutes (deploy in multiple AWS Regions for lower latency)
  3. Use serverless architectures (remove operational burden of server management)
  4. Experiment more often (leverage virtual resources for comparative testing)
  5. Consider mechanical sympathy (align technology choices with workload access patterns)
Applies To Production Cloud-Native Workloads:
  - Right-sized compute instances based on workload profiling (CPU, memory, network, storage IOPS)
  - CloudFront CDN for static assets and API caching
  - ElastiCache / DAX for frequently accessed data with sub-millisecond requirements
  - Graviton instances for ARM-compatible workloads (40% better price/performance)
  - Purpose-built databases selected by access pattern (DynamoDB for key-value, Aurora for relational, Neptune for graph)
Assessment Questions:
  1. How do you select appropriate cloud resources?
  2. How do you select your compute solution?
  3. How do you monitor your resources to ensure they are performing?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/performance-efficiency.html
```

---

### Pillar 5: Cost Optimization

```
Pillar: Cost Optimization
Definition: The ability to run systems to deliver business value at the lowest price point.
Key Design Principles:
  1. Implement Cloud Financial Management (invest in FinOps capability — people, processes, tools)
  2. Adopt a consumption model (pay for what you use, scale with demand, stop idle resources)
  3. Measure overall efficiency (business output ÷ cost = efficiency metric)
  4. Stop spending money on undifferentiated heavy lifting (use managed services for commodity operations)
  5. Analyze and attribute expenditure (cost allocation tags, per-workload cost visibility)
Applies To Production Cloud-Native Workloads:
  - Cost allocation tags on all resources (Environment, Team, Workload, CostCenter)
  - AWS Budgets with alerting thresholds (80%, 100%, forecast alerts)
  - Savings Plans / Reserved Instances for steady-state compute
  - Spot Instances for fault-tolerant batch processing
  - S3 Intelligent-Tiering for variable access patterns
  - Resource right-sizing through Compute Optimizer recommendations
  - Dev/test environment scheduling (stop after hours — 75% potential savings)
Assessment Questions:
  1. How do you implement cloud financial management?
  2. How do you govern usage?
  3. How do you evaluate cost when you select services?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/cost-optimization.html
```

---

### Pillar 6: Sustainability

```
Pillar: Sustainability
Definition: The ability to continually improve sustainability impacts by reducing energy consumption and increasing efficiency across all components of a workload by maximizing the benefits from the provisioned resources and minimizing the total resources required.
Key Design Principles:
  1. Understand your impact (measure workload carbon footprint)
  2. Establish sustainability goals (set reduction targets per workload)
  3. Maximize utilization (right-size to minimize idle resources)
  4. Anticipate and adopt new, more efficient offerings (Graviton, new instance families)
  5. Use managed services (shared infrastructure = higher utilization = less waste)
  6. Reduce the downstream impact of your cloud workloads (optimize data transfer, reduce storage)
Applies To Production Cloud-Native Workloads:
  - Graviton-based instances wherever ARM-compatible (reduced energy per compute unit)
  - Auto-scaling to minimize over-provisioning and idle capacity
  - Data lifecycle policies (S3 lifecycle rules, DynamoDB TTL, RDS snapshot retention)
  - Efficient code practices (avoid busy-wait polling, batch operations)
  - Region selection considering carbon intensity where business requirements allow
  - Customer Carbon Footprint Tool for measurement and reporting
Assessment Questions:
  1. How do you select Regions to support your sustainability goals?
  2. How do you take advantage of user behavior patterns to support sustainability?
  3. How do you select and use cloud hardware and services to support sustainability?
Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/sustainability.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Multi-AZ Deployment for Stateful Services**
- Pillar Alignment: Reliability
- Why: "Scale horizontally to increase aggregate workload availability. Replace one large resource with multiple small resources to reduce the impact of a single failure on the overall workload. Distribute requests across multiple, smaller resources to verify that they don't share a common point of failure." — Reliability Design Principles
- AWS Services: RDS Multi-AZ, ElastiCache Multi-AZ, EFS, Aurora Multi-AZ, DynamoDB (global tables for multi-region)
- Architecture Decision:
  Deploy all stateful services across at least two Availability Zones within a single Region. Use Active-Standby (RDS Multi-AZ) or Active-Active (Aurora, DynamoDB) depending on workload requirements. Load balancers (ALB/NLB) distribute traffic across AZs with cross-zone load balancing enabled.
- Verification:
  `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,MultiAZ]'` — verify all production RDS instances show MultiAZ: true. For ElastiCache: verify cluster has nodes in multiple AZs via `describe-cache-clusters`.
- Trade-offs: 2x cost for RDS Multi-AZ (standby instance), cross-AZ data transfer charges (~$0.01/GB), slightly higher write latency for synchronous replication.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-your-network-topology.html

---

**Encryption at Rest and in Transit for All Data Paths**
- Pillar Alignment: Security
- Why: "Protect data in transit and at rest. Classify your data into sensitivity levels and use mechanisms, such as encryption, tokenization, and access control where appropriate." — Security Design Principles
- AWS Services: KMS (customer-managed keys), ACM (TLS certificates), S3 (SSE-KMS/SSE-S3), RDS (encryption at rest), EBS (encryption), CloudFront (HTTPS only), ALB (TLS termination)
- Architecture Decision:
  Enable encryption at rest on every data store (S3 buckets, RDS instances, EBS volumes, DynamoDB tables, EFS file systems, ElastiCache clusters). Enforce TLS 1.2+ for all data in transit. Use KMS customer-managed keys (CMKs) for sensitive data requiring key rotation and audit trails. Use S3 bucket policies to deny unencrypted uploads (`aws:SecureTransport` condition).
- Verification:
  `aws s3api get-bucket-encryption --bucket <bucket-name>` — verify SSE configuration. `aws rds describe-db-instances --query 'DBInstances[*].[DBInstanceIdentifier,StorageEncrypted]'` — verify all instances show StorageEncrypted: true. Check ALB listeners for HTTPS-only (no port 80 without redirect).
- Trade-offs: Marginal latency increase for KMS API calls (~5-10ms per encrypt/decrypt operation), KMS key management overhead, cost for CMK usage ($1/month per key + per-request charges).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

---

**Least-Privilege IAM with Resource-Scoped Policies**
- Pillar Alignment: Security
- Why: "Implement a strong identity foundation. Implement the principle of least privilege and enforce separation of duties with appropriate authorization for each interaction with your AWS resources. Centralize identity management, and aim to eliminate reliance on long-term static credentials." — Security Design Principles
- AWS Services: IAM (roles, policies, permission boundaries), AWS Organizations (SCPs), IAM Identity Center (SSO), STS (temporary credentials), IAM Access Analyzer
- Architecture Decision:
  Every workload component uses a dedicated IAM role with policies scoped to specific resources (ARNs) and actions. No IAM users with long-term access keys for applications — use IAM roles with STS AssumeRole. Enable IAM Access Analyzer to detect unused permissions and external access. Apply permission boundaries to limit maximum possible permissions. Use SCPs at the Organization level to enforce account-wide guardrails (deny root API calls, require encryption, restrict regions).
- Verification:
  IAM Access Analyzer: review findings for overly permissive policies and external access. `aws iam get-account-authorization-details` — scan for policies with `"Effect": "Allow", "Action": "*", "Resource": "*"`. Review IAM credential reports for unused access keys older than 90 days.
- Trade-offs: Initial overhead to define granular policies (more complex than permissive policies), potential for permission-denied errors during development (mitigated by permission boundaries in dev accounts), requires ongoing maintenance as resource ARNs change.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html

---

**Centralized Logging and Monitoring with Business KPIs**
- Pillar Alignment: Operational Excellence
- Why: "Implement observability for actionable insights. Gain a comprehensive understanding of workload behavior, performance, reliability, cost, and health. Establish key performance indicators (KPIs) and leverage observability telemetry to make informed decisions and take prompt action when business outcomes are at risk." — Operational Excellence Design Principles
- AWS Services: CloudWatch (Metrics, Logs, Alarms, Dashboards, Synthetics, RUM), CloudTrail (API audit), X-Ray (distributed tracing), AWS Config (resource configuration history)
- Architecture Decision:
  Centralize all application and infrastructure logs to CloudWatch Logs with structured JSON format. Define business-aligned KPIs (order completion rate, API latency p99, error rate by customer segment) in CloudWatch dashboards. Configure composite alarms that trigger OpsCenter OpsItems or SNS notifications for automated incident response. Enable X-Ray tracing for all inter-service calls. Enable CloudTrail in all regions with log file validation and S3 delivery.
- Verification:
  Verify CloudTrail is enabled: `aws cloudtrail describe-trails --query 'trailList[*].[Name,IsMultiRegionTrail,LogFileValidationEnabled]'`. Verify CloudWatch alarms exist: `aws cloudwatch describe-alarms --state-value INSUFFICIENT_DATA` — should return no critical alarms in insufficient state. Review dashboards for business KPI widgets (not just infrastructure metrics).
- Trade-offs: CloudWatch Logs ingestion costs ($0.50/GB), log retention costs, X-Ray trace sampling trade-off (full sampling = high cost, low sampling = gaps in observability). Mitigate with log filters, sampling strategies, and retention policies.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html

---

**Infrastructure as Code with Automated Deployment Pipelines**
- Pillar Alignment: Operational Excellence, Reliability
- Why: "Safely automate where possible. Define your entire workload and its operations as code, and update it. Automate your workload's operations by initiating them in response to events." — Operational Excellence Design Principles. "Manage change through automation. Changes to your infrastructure should be made using automation." — Reliability Design Principles
- AWS Services: CloudFormation / CDK / Terraform (IaC), CodePipeline + CodeBuild + CodeDeploy (CI/CD), AWS Config (drift detection), Service Catalog (standardized provisioning)
- Architecture Decision:
  Define all infrastructure in version-controlled IaC templates (CloudFormation/CDK for AWS-native, Terraform for multi-cloud). No manual console changes to production infrastructure. Deploy through automated pipelines with stages: lint/validate → test (unit + integration) → staging deployment → approval gate → production deployment (canary/blue-green). Enable CloudFormation drift detection or `terraform plan` as pipeline validation step.
- Verification:
  `aws cloudformation detect-stack-drift --stack-name <stack>` — verify DETECTION_STATUS: DETECTION_COMPLETE with IN_SYNC status. Review CodePipeline execution history for consistent automated deployments. Verify no manual AWS Console actions via CloudTrail event filtering (`userIdentity.type != AssumedRole` in production).
- Trade-offs: Initial IaC development investment (higher upfront effort than console clicks), pipeline maintenance overhead, potential for pipeline failures blocking deployments (mitigate with break-glass manual deployment procedures for critical incidents).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/prepare.html

---

**Network Segmentation with VPC Design**
- Pillar Alignment: Security, Reliability
- Why: "Apply security at all layers. Apply a defense in depth approach with multiple security controls." — Security Design Principles
- AWS Services: VPC (subnets, route tables), Security Groups (stateful firewall), NACLs (stateless firewall), NAT Gateway, VPC Endpoints (PrivateLink), VPC Flow Logs, AWS Network Firewall
- Architecture Decision:
  Design VPCs with at least three subnet tiers: public (load balancers, bastion hosts only), private (application compute), isolated/data (databases, caches — no internet access). Use Security Groups as the primary firewall (allow-list specific ports/sources). Use NACLs for subnet-level deny rules. Route private subnet internet access through NAT Gateway. Use VPC Endpoints for AWS service access without internet traversal (S3, DynamoDB, KMS, STS, CloudWatch). Enable VPC Flow Logs to CloudWatch for network forensics.
- Verification:
  Review route tables: verify private subnets route 0.0.0.0/0 through NAT Gateway (not Internet Gateway directly). Verify Security Groups: no inbound rules with 0.0.0.0/0 on management ports (22, 3389). Verify VPC Flow Logs enabled: `aws ec2 describe-flow-logs --filter Name=resource-id,Values=<vpc-id>`.
- Trade-offs: NAT Gateway costs ($0.045/hour + $0.045/GB data processed), VPC Endpoint costs per AZ, increased complexity in network troubleshooting, cross-AZ data transfer for NAT Gateway.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html

---

**Automated Backup and Recovery Testing**
- Pillar Alignment: Reliability
- Why: "Test recovery procedures. In the cloud, you can test how your workload fails, and you can validate your recovery procedures." — Reliability Design Principles
- AWS Services: AWS Backup (centralized backup management), RDS Automated Backups, S3 Versioning, DynamoDB Point-in-Time Recovery, EBS Snapshots, AWS Backup Vault Lock (immutable backups)
- Architecture Decision:
  Configure AWS Backup with backup plans covering all stateful resources (RDS, DynamoDB, EFS, EBS, S3). Define RTO/RPO per workload tier (Tier 1: RPO 1h/RTO 4h, Tier 2: RPO 24h/RTO 24h). Enable S3 Versioning and DynamoDB PITR for all production tables. Test restore procedures quarterly — validate data integrity post-restore. Use Backup Vault Lock for compliance-sensitive data (immutable retention).
- Verification:
  `aws backup list-backup-jobs --by-state COMPLETED` — verify backups are executing per schedule. Quarterly: execute restore to test environment, validate application functionality against restored data. Verify DynamoDB PITR: `aws dynamodb describe-continuous-backups --table-name <table>`.
- Trade-offs: Storage costs for backup retention (cross-region backup doubles storage cost), restore testing requires compute resources and time, Backup Vault Lock prevents early deletion (plan retention carefully).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/back-up-data.html

---

**Cost Allocation and Budget Alerting**
- Pillar Alignment: Cost Optimization
- Why: "Analyze and attribute expenditure. The cloud makes it simple to accurately identify the usage and cost of systems, which then permits transparent attribution of IT costs to individual workload owners." — Cost Optimization Design Principles
- AWS Services: AWS Cost Explorer, AWS Budgets, Cost Allocation Tags, AWS Cost and Usage Report (CUR), Compute Optimizer, Savings Plans
- Architecture Decision:
  Implement mandatory cost allocation tags on all resources: `Environment` (prod/staging/dev), `Team`, `Workload`, `CostCenter`. Configure AWS Budgets per workload with alerts at 80% and 100% of monthly forecast. Enable Cost and Usage Report delivery to S3 for detailed analysis. Review Compute Optimizer recommendations monthly for right-sizing opportunities. Establish a FinOps review cadence (weekly cost anomaly review, monthly optimization review, quarterly commitment planning).
- Verification:
  Verify tag compliance: `aws resourcegroupstaggingapi get-resources --tag-filters Key=Environment` — audit resources missing mandatory tags. Verify budgets exist: `aws budgets describe-budgets --account-id <account>`. Review Cost Explorer for untagged spend (should be <5% of total).
- Trade-offs: Tagging enforcement requires governance processes (tag policies via AWS Organizations), Cost Explorer/CUR analysis requires dedicated time, Savings Plans commit to 1-3 year spend (risk of over-commitment if workload shrinks).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/expenditure-and-usage-awareness.html

---

**DNS and Certificate Management via Managed Services**
- Pillar Alignment: Reliability, Security
- Why: Reliability: ensures DNS failover capabilities and high-availability resolution. Security: automated certificate provisioning and renewal eliminates certificate expiration as an outage vector.
- AWS Services: Route 53 (DNS management, health checks, traffic routing), ACM (certificate provisioning and auto-renewal), CloudFront (TLS termination at edge)
- Architecture Decision:
  Host all public DNS zones in Route 53. Configure health checks with failover routing for critical endpoints. Use ACM for all TLS certificates (auto-renewal eliminates expiration incidents). Associate ACM certificates with ALB, CloudFront, and API Gateway. Use Route 53 private hosted zones for internal service discovery.
- Verification:
  `aws route53 list-health-checks` — verify health checks exist for all critical endpoints. `aws acm list-certificates --certificate-statuses ISSUED` — verify certificates are issued and associated. Check ACM renewal status: certificates should show `PENDING_VALIDATION` well before expiration.
- Trade-offs: Route 53 hosted zone cost ($0.50/month per zone), health check costs ($0.50-$0.75/month per check), ACM certificates are free but locked to AWS services (cannot export private key for use on non-AWS infrastructure).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-your-network-topology.html

---

**Secrets Management via AWS Secrets Manager**
- Pillar Alignment: Security
- Why: "Keep people away from data. Use mechanisms and tools to reduce or eliminate the need for direct access or manual processing of data." — Security Design Principles. Eliminates hardcoded credentials as an attack vector.
- AWS Services: Secrets Manager (rotation, access control, cross-account sharing), Systems Manager Parameter Store (non-sensitive configuration), KMS (encryption of secret values)
- Architecture Decision:
  Store all credentials, API keys, database passwords, and tokens in Secrets Manager with automatic rotation configured. Application code retrieves secrets at runtime via SDK/API — never baked into container images, environment variables, or source code. Use resource-based policies for cross-account access. Configure rotation Lambda functions for RDS credentials (supported natively). Use Parameter Store for non-sensitive configuration (feature flags, endpoints, environment-specific settings).
- Verification:
  `aws secretsmanager list-secrets --query 'SecretList[*].[Name,RotationEnabled,LastRotatedDate]'` — verify rotation is enabled for all database credentials. Scan source code and CI/CD pipelines for hardcoded secrets (use git-secrets or similar pre-commit hooks). Review IAM policies: only application roles should have `secretsmanager:GetSecretValue` permission on their specific secrets.
- Trade-offs: Secrets Manager cost ($0.40/secret/month + $0.05/10K API calls), cold-start latency for secret retrieval (mitigate with caching in application), rotation Lambda development for custom secret types.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

---

### ⚠️ Architectural Decisions

**Compute Model Selection**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Serverless | Lambda | Operational simplicity, cost at low-medium scale, time-to-market | Cold start latency, execution duration (15min max), control over runtime environment | Event-driven workloads, variable traffic, rapid iteration |
  | Containers | ECS/Fargate or EKS | Portability, long-running processes, team familiarity with Docker | Operational complexity (especially EKS), cluster management overhead | Microservices with consistent traffic, existing containerized workloads |
  | Virtual Machines | EC2 + ASG | Full control, specialized hardware (GPU/FPGA), legacy compatibility | Operational burden (patching, scaling, monitoring), slower scaling | HPC, GPU workloads, license-bound software, legacy migrations |

- Cost Profile: Lambda — pay-per-invocation ($0.20/1M requests + duration); Fargate — pay-per-vCPU-hour ($0.04/vCPU/hour); EC2 — pay-per-instance-hour (varies by type, Reserved/Spot/On-Demand). Lambda cheapest for <1M requests/day; Fargate cheaper for steady-state 24/7; EC2 cheapest with Reserved Instances for predictable load.
- Lock-in Assessment: Lambda — high lock-in (event source integrations, runtime-specific); Containers — low lock-in (portable to any Kubernetes/container platform); EC2 — medium lock-in (AMIs, instance types, but workload is portable).
- Architect Instruction: "Ask 'What is the workload's traffic pattern (spiky/steady), execution duration requirement, and team's container orchestration experience?' before choosing compute model."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/perf-compute.html

---

**Database Selection Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Managed Relational | RDS (PostgreSQL/MySQL) or Aurora | ACID compliance, complex queries, joins, developer familiarity | Horizontal scaling, schema flexibility, cost at extreme scale | Transactional workloads, complex relationships, existing SQL expertise |
  | Key-Value/Document | DynamoDB | Single-digit ms latency, infinite scale, zero admin | Complex queries, joins, flexible indexing (limited GSI/LSI), cost for scans | High-throughput, predictable access patterns, session/cart/profile stores |
  | In-Memory | ElastiCache (Redis/Valkey) | Sub-millisecond latency, caching, session store | Durability (volatile), cost per GB, limited query capabilities | Caching layers, session management, leaderboards, real-time analytics |
  | Data Warehouse | Redshift | Complex analytical queries, petabyte-scale, columnar storage | Write latency, not for OLTP, cluster management | Business intelligence, reporting, historical analytics |
  | Graph | Neptune | Relationship traversal, connected data queries | Limited ecosystem, specialized query language (Gremlin/SPARQL) | Social networks, fraud detection, knowledge graphs, recommendation engines |

- Cost Profile: DynamoDB — pay-per-request ($1.25/1M writes) or provisioned capacity; Aurora — instance-hour + I/O ($0.20/1M requests); RDS — instance-hour + storage; Redshift — node-hour (starts ~$0.25/hour). DynamoDB cheapest for predictable key-value access; Aurora for moderate relational workloads; Redshift for analytics.
- Lock-in Assessment: DynamoDB — high (proprietary API, no equivalent elsewhere); Aurora — medium (MySQL/PostgreSQL compatible wire protocol); RDS — low (standard engines, portable); Redshift — medium (SQL-based but proprietary optimizations).
- Architect Instruction: "Ask 'What are the primary access patterns (key-value, relational joins, full-text search, time-series)?' and 'What is the consistency requirement (strong/eventual)?' before selecting database."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/perf-data.html

---

**Region Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Single Region | Standard deployment | Simplicity, cost, data residency compliance | Availability (region failure = total outage), latency for global users | Regulatory data residency, cost-sensitive, single-geography users |
  | Multi-Region Active-Passive | Route 53 failover, cross-region replication | DR capability, RTO minutes-hours | Cost (standby infrastructure), RPO (replication lag), complexity | Business continuity required, regulatory DR mandates |
  | Multi-Region Active-Active | Global Accelerator, DynamoDB Global Tables, Aurora Global Database | Lowest latency globally, highest availability, near-zero RTO/RPO | Significant cost (2x+ infrastructure), data consistency complexity, operational overhead | Global user base, mission-critical SLA (99.99%+), latency-sensitive |

- Cost Profile: Single-region — baseline; Active-Passive — 1.3-1.5x (standby + replication); Active-Active — 2-3x (full duplicate + cross-region transfer + conflict resolution).
- Lock-in Assessment: Multi-region architectures use more AWS-specific features (Global Tables, Aurora Global, Route 53 failover policies) — increasing lock-in proportionally.
- Architect Instruction: "Ask 'What is the required availability SLA? Where are users geographically? Are there data residency requirements? What is the maximum acceptable RPO/RTO?' before deciding region strategy."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-your-network-topology.html

---

**Account Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Single Account | N/A | Simplicity, zero cross-account overhead | Security (no blast radius isolation), cost attribution, governance | Proof-of-concept only — never production |
  | Multi-Account (Environment) | AWS Organizations, Control Tower | Blast radius isolation, environment separation (dev/staging/prod) | Cross-account complexity, IAM role assumption overhead | Standard production workloads — minimum viable account strategy |
  | Multi-Account (Workload) | AWS Organizations, Control Tower, RAM | Per-workload isolation, granular cost attribution, team autonomy | Higher account management overhead, cross-account networking complexity | Enterprise scale, multiple teams, strict compliance requirements |

- Cost Profile: No per-account AWS cost. Overhead comes from: cross-account networking (Transit Gateway at $0.05/hour/attachment), account vending automation (Control Tower setup), IAM role complexity.
- Lock-in Assessment: AWS Organizations and SCPs are AWS-specific. The multi-account pattern itself is portable (Azure uses Management Groups + Subscriptions, GCP uses Folders + Projects), but the implementation details are not.
- Architect Instruction: "Ask 'How many teams share this infrastructure? What compliance requirements exist? What is the current organizational maturity for account management?' before defining account strategy."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/aws-account-management-and-separation.html

---

**Messaging Architecture**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | Point-to-Point Queue | SQS | Decoupling, load leveling, guaranteed delivery, dead letter queue | No fan-out, FIFO ordering costs more, single consumer group | Worker pools, task distribution, request buffering |
  | Pub/Sub Fan-out | SNS + SQS | Multiple consumers, loose coupling, broadcast | Ordering not guaranteed (standard), no message replay | Event notification to multiple subscribers, fan-out patterns |
  | Event Bus | EventBridge | Content-based routing, schema registry, SaaS integration | Higher latency than SQS, message size limit (256KB), cost at high volume | Event-driven architectures, cross-service integration, SaaS events |
  | Event Streaming | Kinesis Data Streams | Ordered, replayable, multiple consumers, high throughput | Shard management, cost at low volume, 7-day default retention | Real-time analytics, log aggregation, ordered event processing |

- Cost Profile: SQS — $0.40/1M requests; SNS — $0.50/1M publishes; EventBridge — $1.00/1M events; Kinesis — $0.015/shard/hour + $0.014/1M PUT. SQS cheapest for simple queueing; EventBridge for complex routing; Kinesis for high-throughput streaming.
- Lock-in Assessment: SQS/SNS — medium (queue/pub-sub patterns exist everywhere); EventBridge — high (proprietary routing rules, schema registry); Kinesis — medium (Kafka-compatible alternatives exist).
- Architect Instruction: "Ask 'Do you need fan-out (multiple consumers for one event)? Is message ordering required? Do you need replay capability? What is the expected message volume?' before selecting messaging."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/framework/perf-networking.html

---

**Caching Strategy**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|------------|-----------|------------|-----------|
  | CDN / Edge Cache | CloudFront | Global latency, origin offload, static asset delivery | Stale data (TTL-based), limited dynamic content caching | Static assets, API response caching, global distribution |
  | In-Memory Data Store | ElastiCache (Redis/Valkey) | Sub-ms read latency, complex data structures, session store | Cost per GB of cache, cache invalidation complexity, data loss on eviction | Database query caching, session management, rate limiting, leaderboards |
  | Application-Level | DAX (DynamoDB Accelerator) | Transparent caching for DynamoDB, microsecond reads | DynamoDB-only, write-through latency, cluster management | DynamoDB workloads with read-heavy access patterns |

- Cost Profile: CloudFront — $0.085/GB transfer (varies by region); ElastiCache — $0.017/hour (cache.t3.micro) to $4.60/hour (cache.r6g.16xlarge); DAX — $0.269/hour (dax.t3.small) per node.
- Lock-in Assessment: CloudFront — medium (CDN patterns portable); ElastiCache Redis — low (Redis protocol is standard); DAX — high (DynamoDB-specific).
- Architect Instruction: "Ask 'What is the cache-hit ratio target? What is the data freshness requirement (seconds/minutes/hours)? Is the caching for read-heavy database queries or for edge delivery?' before selecting caching strategy."
- Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/caching.html

---

### 🚫 Anti-Patterns

**Wildcard IAM Policies in Production**
- Risk Level: CRITICAL
- Why: Violates Security pillar — "Implement a strong identity foundation. Implement the principle of least privilege." Wildcard policies (`"Action": "*", "Resource": "*"`) grant unrestricted access to all AWS services, creating a blast radius equal to the entire AWS account.
- Instead: Define granular IAM policies with specific Actions and Resource ARNs per component. Use IAM Access Analyzer to generate least-privilege policies from CloudTrail access logs. Apply permission boundaries as a safety net.
- Detection: `aws iam get-account-authorization-details | jq '.Policies[].PolicyVersionList[].Document.Statement[] | select(.Effect=="Allow" and .Action=="*" and .Resource=="*")'`. Also: enable IAM Access Analyzer and review findings for overly-permissive policies.
- Impact: Data breach (access to all data stores), privilege escalation (create new admin users), resource destruction (terminate all instances), compliance violation (PCI-DSS, SOC2, HIPAA all require least privilege).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html

---

**Single-AZ Deployment for Production Stateful Workloads**
- Risk Level: CRITICAL
- Why: Violates Reliability pillar — "Scale horizontally to increase aggregate workload availability. Distribute requests across multiple, smaller resources to verify that they don't share a common point of failure." A single AZ failure causes complete workload outage for all stateful components.
- Instead: Deploy all stateful services in Multi-AZ configuration. RDS: enable Multi-AZ. ElastiCache: use Multi-AZ with automatic failover. EBS: use cross-AZ replication or multi-attach. Application: deploy across multiple AZs behind a load balancer.
- Detection: `aws rds describe-db-instances --query 'DBInstances[?MultiAZ==`false`].[DBInstanceIdentifier,AvailabilityZone]'`. Review ASG: verify subnets span multiple AZs.
- Impact: Service outage (complete data unavailability during AZ disruption), data loss (if EBS volume is in affected AZ without snapshots), SLA breach (AWS SLA commitments require Multi-AZ architecture).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-your-workload-service-architecture.html

---

**Hardcoded Credentials in Source Code or Configuration**
- Risk Level: CRITICAL
- Why: Violates Security pillar — "Keep people away from data" and "Automate security best practices." Credentials in source code persist in version control history, are visible to all repository contributors, and cannot be rotated without code changes.
- Instead: Use Secrets Manager for all credentials with automatic rotation. Use IAM roles for service-to-service authentication (no static keys). Use Parameter Store for non-sensitive configuration. Use environment-specific Secrets Manager secrets referenced by name (not value) in IaC templates.
- Detection: Use `git-secrets` pre-commit hooks to scan for AWS access keys, database connection strings, and API tokens. Use Amazon CodeGuru Reviewer or third-party tools (TruffleHog, detect-secrets) for repository scanning. AWS Config rule: `iam-user-no-policies-check` to detect static IAM user credentials.
- Impact: Data breach (leaked credentials in public repositories indexed within minutes), lateral movement (one credential leak → access to connected systems), compliance violation (all major frameworks prohibit hardcoded secrets), inability to rotate (requires code deployment to change credentials).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

---

**Disabled or Missing CloudTrail Audit Logging**
- Risk Level: CRITICAL
- Why: Violates Security pillar — "Maintain traceability. Monitor, alert, and audit actions and changes to your environment in real time." Without CloudTrail, there is no record of who did what in the AWS account — making incident investigation, compliance auditing, and threat detection impossible.
- Instead: Enable CloudTrail in ALL regions (multi-region trail) with log file validation. Deliver logs to a centralized S3 bucket in a separate security/audit account with restricted access. Enable CloudTrail Lake or integrate with Security Hub/GuardDuty for automated analysis.
- Detection: `aws cloudtrail describe-trails --query 'trailList[?IsMultiRegionTrail==`false`]'` — any single-region trails are insufficient. `aws cloudtrail get-trail-status --name <trail> --query 'IsLogging'` — verify logging is active. Check for gaps in log delivery.
- Impact: Undetectable security breaches (no forensic evidence), compliance violation (SOC2, PCI-DSS, HIPAA all require audit logging), inability to investigate incidents (no attribution of changes), regulatory penalties (GDPR requires access logging for personal data).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

---

**Unencrypted S3 Buckets with Public Access**
- Risk Level: CRITICAL
- Why: Violates Security pillar — "Protect data in transit and at rest" and "Apply security at all layers." Unencrypted, publicly accessible S3 buckets are the #1 source of cloud data breaches in public reporting.
- Instead: Enable S3 Block Public Access at the account level. Enable default encryption (SSE-S3 minimum, SSE-KMS for sensitive data). Use bucket policies requiring `aws:SecureTransport` (HTTPS-only). Use S3 Access Points for granular access control. Enable S3 server access logging or CloudTrail data events.
- Detection: `aws s3control get-public-access-block --account-id <account>` — verify all four block settings are `true`. `aws s3api get-bucket-encryption --bucket <bucket>` — verify encryption configuration exists. AWS Config rule: `s3-bucket-public-read-prohibited`, `s3-bucket-server-side-encryption-enabled`.
- Impact: Data breach (publicly accessible customer data, PII, credentials), regulatory fines (GDPR, CCPA penalties for exposed personal data), reputational damage (public data breach disclosure requirements), ransom (threat actors encrypt data and demand payment).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-data-at-rest.html

---

**No Budget Alerts or Cost Monitoring**
- Risk Level: HIGH
- Why: Violates Cost Optimization pillar — "Implement Cloud Financial Management" and "Analyze and attribute expenditure." Without cost alerting, cloud spend can grow unbounded — a single misconfiguration (e.g., infinite loop triggering Lambda, unthrottled Kinesis shard scaling) can generate six-figure bills before detection.
- Instead: Configure AWS Budgets with alerting at 80% and 100% of monthly forecast per workload. Enable Cost Anomaly Detection for automated identification of unusual spending. Configure billing alarms in CloudWatch for account-level thresholds. Review Cost Explorer weekly for trends.
- Detection: `aws budgets describe-budgets --account-id <account>` — verify budgets exist for production workloads. `aws ce get-cost-and-usage` — verify cost data is being tracked. Check for Cost Anomaly Detection monitors.
- Impact: Cost overrun (unbounded cloud spend from misconfigurations, crypto-mining on compromised instances, run-away auto-scaling), budget surprise (monthly bills 10-100x expected), organizational credibility loss (cloud migration ROI undermined), service disruption (if billing threshold triggers service suspension).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/expenditure-and-usage-awareness.html

---

**Security Groups with Unrestricted Inbound on Management Ports**
- Risk Level: HIGH
- Why: Violates Security pillar — "Apply security at all layers." Allowing 0.0.0.0/0 inbound on SSH (22), RDP (3389), or database ports (3306, 5432, 1521, 27017) exposes management interfaces to the entire internet — enabling brute-force attacks, exploitation of unpatched vulnerabilities, and unauthorized access.
- Instead: Restrict management port access to specific CIDR blocks (corporate VPN, bastion host security group). Use Systems Manager Session Manager for shell access (no open ports required). Use Client VPN or PrivateLink for administrative access. Remove all direct internet access to database ports — databases should be in private subnets only.
- Detection: `aws ec2 describe-security-groups --query 'SecurityGroups[*].IpPermissions[?contains(IpRanges[].CidrIp, `0.0.0.0/0`) && (FromPort==`22` || FromPort==`3389` || FromPort==`3306` || FromPort==`5432`)]'`. AWS Config rules: `restricted-ssh`, `restricted-common-ports`.
- Impact: Unauthorized access (brute-force SSH/RDP), data breach (direct database access from internet), crypto-mining (compromised instances used for mining), lateral movement (compromised management access → pivot to other resources).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html

---

**Monolithic Account with No Environment Isolation**
- Risk Level: HIGH
- Why: Violates Security pillar (blast radius isolation) and Operational Excellence (safe experimentation). A single account containing dev, staging, and production workloads means: a developer error can impact production, resource limits are shared, IAM policies cannot isolate environments, and cost attribution is impossible.
- Instead: Implement multi-account strategy using AWS Organizations with Control Tower. Minimum: separate accounts for production, staging, development, security/audit, and shared services. Apply SCPs per OU to enforce guardrails (production OU: deny resource deletion without MFA, require encryption).
- Detection: Review AWS Organizations structure — if all workloads share one account, this anti-pattern is present. Check for resource tagging substituting for account isolation (insufficient — tags are not security boundaries).
- Impact: Production outage from development activity (shared resource limits, accidental deletion), security breach escalation (compromised dev credentials access production data), compliance failure (no environment separation violates PCI-DSS, SOC2), cost confusion (cannot attribute spend to environments).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/aws-account-management-and-separation.html

---

**Missing Health Checks and Auto-Recovery**
- Risk Level: MEDIUM
- Why: Violates Reliability pillar — "Automatically recover from failure. By monitoring a workload for key performance indicators (KPIs), you can start automation when a threshold is breached." Without health checks, failed instances continue receiving traffic (load balancer) or remain undetected (standalone instances).
- Instead: Configure ALB health checks with application-specific endpoints (not just TCP connect — use HTTP 200 from `/health` endpoint that validates downstream dependencies). Configure ASG health checks combining EC2 status checks AND ELB health checks. Use Route 53 health checks for DNS failover. Enable EC2 auto-recovery for standalone instances.
- Detection: Review ALB target group health check configuration: `aws elbv2 describe-target-health --target-group-arn <arn>`. Verify ASG health check type includes `ELB` (not just `EC2`). Check Route 53 health checks exist for failover routing.
- Impact: Serving errors to users (unhealthy instance continues receiving traffic), silent failures (no detection = no response), extended outage (manual intervention required to replace failed instance), degraded performance (partially-failed instances handling requests slowly).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/monitor-workload-resources.html

---

## Cloud-Native Design Patterns

**Circuit Breaker**
- Category: Resilience
- Problem: Cascading failures when a downstream service is degraded — upstream services exhaust connection pools, timeout threads, and degrade themselves while waiting for responses from an already-failed dependency.
- Solution on AWS:
  Implement circuit breaker logic in application code (using libraries like resilience4j, Polly, or custom implementation) that tracks downstream failure rates and opens the circuit (returns fallback response immediately) when failure threshold is exceeded. Complements with: API Gateway throttling, Lambda reserved concurrency (prevents downstream exhaustion), App Mesh circuit breaking policies (Envoy-based), and CloudWatch alarms monitoring error rates.
- Services Used: App Mesh (Envoy sidecar with circuit breaking), CloudWatch (failure rate metrics), Lambda (reserved concurrency as passive circuit breaker), API Gateway (request throttling)
- When to Apply: Any synchronous inter-service call where downstream degradation can cascade upstream. Critical for microservices architectures with deep call chains.
- When NOT to Apply: Asynchronous messaging patterns (SQS-based) — the queue provides natural decoupling and backpressure. Internal Lambda-to-Lambda via Step Functions (the orchestrator handles retries).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Prevents cascading failure — localizes impact | Users may receive degraded (fallback) responses |
  | Complexity | Protects upstream services | Requires fallback logic, threshold tuning, half-open state management |
  | Observability | Clear signal when dependency is degraded | Requires monitoring of circuit state (open/closed/half-open) |

- Complements: Retry with exponential backoff (closed state), Bulkhead (isolate failure domains), Timeout (bound wait time), Fallback (degraded response when open)
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/circuit-breaker.html

---

**Strangler Fig Migration**
- Category: Migration
- Problem: Migrating a monolithic application to microservices or cloud-native architecture in a single "big bang" deployment is high-risk — long development cycles, all-or-nothing cutover, and limited rollback options.
- Solution on AWS:
  Incrementally replace monolith functionality with new microservices behind a routing layer. Use API Gateway or ALB path-based routing to direct specific API paths to new microservices while routing everything else to the legacy monolith. As each capability is migrated, the routing layer directs traffic to the new service — gradually "strangling" the monolith.
- Services Used: API Gateway (path-based routing), ALB (path-based routing, weighted target groups), Route 53 (DNS-level routing for gradual migration), CloudFront (origin-based routing per path)
- When to Apply: Migrating legacy monoliths to AWS, modernizing to microservices architecture, re-platforming from on-premises to cloud. Ideal when the monolith has clear domain boundaries identifiable by URL path or API surface.
- When NOT to Apply: Small applications where full rewrite is faster than incremental migration. Applications with deeply coupled data models that cannot be decomposed per-path. Workloads under extreme time pressure requiring "lift and shift" first.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Risk | Incremental, reversible migration | Longer total migration timeline |
  | Complexity | Each piece can be validated independently | Running two systems simultaneously (monolith + microservices) |
  | Cost | Gradual resource allocation | Dual infrastructure costs during migration period |

- Complements: Anti-Corruption Layer (protect new services from legacy data models), Database-per-Service (data decomposition), Event-Driven Integration (decouple data sync between legacy and new)
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/cloud-design-patterns/strangler-fig.html

---

**Event-Driven Architecture with EventBridge**
- Category: Communication
- Problem: Tight coupling between services through synchronous API calls creates fragile architectures where changes to one service require changes to all callers, and failure in one service cascades to all dependents.
- Solution on AWS:
  Services emit events (state changes) to EventBridge as the central event bus. Downstream services subscribe to events via EventBridge rules with content-based filtering. Each subscriber processes events independently — decoupled in time (async), interface (content-based routing), and failure domain (DLQ per subscriber). Schema registry provides contract evolution visibility.
- Services Used: EventBridge (event bus, rules, schema registry), SQS (subscriber buffering, DLQ), Lambda (event processing), Step Functions (complex event-driven workflows), CloudWatch (delivery metrics)
- When to Apply: Multi-service architectures where services need to react to business events without direct knowledge of each other. Fan-out patterns where one event triggers multiple independent actions. Cross-domain integration where schema evolution must be managed.
- When NOT to Apply: Single-service applications. Workflows requiring immediate synchronous response. Scenarios requiring strict global ordering guarantees (use Kinesis instead). Sub-millisecond latency requirements between producer and consumer.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Coupling | Services are independently deployable and evolvable | Debugging distributed event flows is harder than tracing synchronous calls |
  | Reliability | Failure in one subscriber doesn't affect others | Eventual consistency — consumers process events at different rates |
  | Scalability | Each subscriber scales independently | Event schema evolution requires governance (schema registry) |

- Complements: Dead Letter Queue (handle processing failures), Event Sourcing (reconstruct state from event history), Saga Pattern (coordinate multi-service transactions via events)
- Source: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-what-is.html

---

**Queue-Based Load Leveling**
- Category: Scalability
- Problem: Burst traffic overwhelming downstream services that cannot scale as fast as the front-end, causing timeouts, throttling, and potential data loss.
- Solution on AWS:
  Place SQS queues between producers and consumers. Producers write to SQS at burst rate (SQS scales automatically). Consumers process at their sustainable rate, with the queue absorbing traffic spikes. Configure visibility timeout, message retention, and dead letter queues for poison messages. Use SQS FIFO for ordered processing when required.
- Services Used: SQS (Standard or FIFO), Lambda (auto-scaling consumer via Event Source Mapping), ASG (EC2 consumers scaled by ApproximateNumberOfMessagesVisible metric), CloudWatch (queue depth alarms)
- When to Apply: APIs that accept requests for asynchronous processing (order submission, file processing, notification sending). Workloads with predictable downstream throughput limits (database write capacity, third-party API rate limits). Lambda-based processing that benefits from batching.
- When NOT to Apply: Synchronous request-response where the client needs an immediate result. Sub-second latency requirements for end-to-end processing. Simple pass-through operations that don't need buffering.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Front-end never fails due to backend overload | Users don't get immediate results (async response model) |
  | Scalability | Absorbs any traffic burst (SQS scales infinitely) | Adds latency — message sits in queue until consumer processes it |
  | Reliability | Messages are durably stored until successfully processed | Requires idempotent consumers (at-least-once delivery for standard queues) |

- Complements: Circuit Breaker (protect consumers from downstream failures), Auto-scaling (scale consumers based on queue depth), Dead Letter Queue (isolate poison messages)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-interactions-in-a-distributed-system-to-mitigate-or-withstand-failures.html

---

**Multi-AZ Active-Active with Auto-Scaling**
- Category: Scalability, Resilience
- Problem: Single-AZ architectures have a blast radius of one AZ failure causing complete outage. Fixed-size deployments cannot handle traffic variability — either wasting resources at low traffic or degrading at high traffic.
- Solution on AWS:
  Deploy application tier across multiple AZs using Auto Scaling Groups (ASG) with Application Load Balancer distributing traffic. ASG maintains minimum instances across AZs, scales out based on metrics (CPU, request count, custom metrics), and replaces unhealthy instances automatically. ALB performs health checks and routes only to healthy targets.
- Services Used: Auto Scaling Groups (instance lifecycle), ALB (traffic distribution, health checks), CloudWatch (scaling metrics, alarms), Launch Templates (instance configuration), EC2 or Fargate (compute)
- When to Apply: Any production workload requiring high availability and cost-efficient scaling. Web applications, API services, and worker fleets that need to handle variable traffic patterns.
- When NOT to Apply: Serverless architectures (Lambda handles scaling natively). Single-instance workloads with no HA requirement (dev environments). Stateful workloads where horizontal scaling requires additional coordination (database sharding — use managed services instead).
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Survives AZ failure with zero downtime | Cross-AZ data transfer costs ($0.01/GB) |
  | Cost | Scale-in during low traffic saves money | Minimum capacity across AZs for HA (can't go to zero in prod) |
  | Complexity | Auto-healing and auto-scaling reduce manual ops | Scaling policies require tuning (cooldown, step adjustments) |

- Complements: Predictive Scaling (pre-warm for known traffic patterns), Target Tracking (simple scaling policy), Spot Instances (cost optimization for fault-tolerant workloads)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/design-your-workload-service-architecture.html

---

## Security Architecture

**Identity & Access Management**
- AWS Services: IAM (roles, policies, permission boundaries), IAM Identity Center (SSO/federation), STS (temporary credentials), Organizations (SCPs), IAM Access Analyzer (unused access, external access findings)
- Architecture:
  Human access: federate via IAM Identity Center (SAML/OIDC) with MFA required. No IAM users for human access. Application access: IAM roles assumed by compute services (Lambda execution role, EC2 instance profile, ECS task role). Cross-account access: role assumption with ExternalId condition. Service-to-service: IAM roles (not access keys). Guardrails: SCPs at Organization level deny dangerous actions (root usage, CloudTrail deletion, regions outside approved list). Permission boundaries on all IAM entities created by teams (cap maximum possible permissions). IAM Access Analyzer runs continuously to detect overly-permissive policies and external access.
- Compliance Alignment: SOC2 CC6.1 (logical access), PCI-DSS 7.1 (least privilege), HIPAA 164.312(a) (access control), GDPR Art. 32 (access management)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/identity-and-access-management.html

---

**Network Security**
- AWS Services: VPC (subnets, route tables), Security Groups (stateful firewall), NACLs (stateless subnet-level), AWS Network Firewall (managed IDS/IPS), WAF (layer 7 protection), Shield (DDoS protection), VPC Endpoints/PrivateLink (private connectivity), VPC Flow Logs (network forensics)
- Architecture:
  Three-tier VPC: public subnets (ALB only), private subnets (application compute), isolated subnets (databases — no internet route). Security Groups as primary control (allow specific port/source combinations). NACLs as defense-in-depth deny rules (block known bad CIDRs). VPC Endpoints for all AWS service access from private subnets (S3, DynamoDB, KMS, STS — avoid NAT Gateway for AWS API calls). WAF on ALB/CloudFront with managed rule sets (AWSManagedRulesCommonRuleSet, SQLi protection, rate limiting). Shield Advanced for DDoS protection on internet-facing resources. Network Firewall for advanced IDS/IPS requirements. Flow Logs to CloudWatch/S3 for forensics and anomaly detection.
- Compliance Alignment: PCI-DSS 1.3 (network segmentation), SOC2 CC6.6 (network security), HIPAA 164.312(e) (transmission security)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/protecting-networks.html

---

**Data Security**
- AWS Services: KMS (key management, encryption), CloudHSM (dedicated HSM), Macie (data classification), S3 (server-side encryption, bucket policies), RDS (encryption at rest, SSL connections), Certificate Manager (TLS certificates)
- Architecture:
  Classification: Use Macie to discover and classify sensitive data (PII, financial data, credentials) in S3. Encryption at rest: all data stores use KMS encryption (CMK for regulated data, AWS-managed key for other data). Key rotation: enable automatic annual rotation for CMKs. Encryption in transit: TLS 1.2+ for all connections (ALB → backend, application → database, service → service). Certificate management: ACM for auto-renewing certificates on AWS services. Data access: bucket policies, IAM resource policies, and VPC endpoint policies enforce access boundaries. Backup encryption: all backups encrypted with same or separate CMK (cross-account backup vault for ransomware protection).
- Compliance Alignment: PCI-DSS 3.4 (encryption of stored cardholder data), HIPAA 164.312(a)(2)(iv) (encryption at rest), GDPR Art. 32 (encryption of personal data), SOC2 CC6.7 (data protection)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/data-protection.html

---

**Detection & Response**
- AWS Services: GuardDuty (threat detection), Security Hub (security posture aggregation), Detective (investigation), CloudTrail (audit trail), Config (resource compliance), Macie (data security), Inspector (vulnerability assessment), EventBridge (automated response)
- Architecture:
  Detection: GuardDuty enabled in all accounts and regions (detects reconnaissance, credential compromise, crypto-mining, data exfiltration). Security Hub aggregates findings from GuardDuty, Inspector, Macie, IAM Access Analyzer, Config, and third-party tools into a single pane. Inspector scans EC2, ECR images, and Lambda for vulnerabilities. Automated response: EventBridge rules on Security Hub findings trigger Lambda remediation (e.g., auto-isolate compromised instance by modifying security group, auto-disable compromised access key). Investigation: Detective builds behavior graphs from CloudTrail, VPC Flow Logs, and GuardDuty findings for root cause analysis. Continuous compliance: AWS Config rules evaluate resource configurations against security standards (CIS Benchmark, PCI-DSS).
- Compliance Alignment: SOC2 CC7.2 (security monitoring), PCI-DSS 10.6 (log review), HIPAA 164.312(b) (audit controls), GDPR Art. 33 (breach notification — requires detection capability)
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/detection.html

---

## Operational Patterns

**Observability Stack**
- RTO/RPO: N/A (preventive — reduces incident duration through faster detection and diagnosis)
- AWS Services: CloudWatch Metrics (infrastructure + custom), CloudWatch Logs (centralized logging), X-Ray (distributed tracing), CloudWatch Synthetics (synthetic monitoring), CloudWatch RUM (real user monitoring), CloudWatch ServiceLens (service map)
- Architecture:
  Metrics: CloudWatch agent on EC2/ECS collects system metrics. Custom metrics from application code for business KPIs. Composite alarms combine multiple signals to reduce alert noise. Logs: Structured JSON logs from all services → CloudWatch Logs → Logs Insights for ad-hoc queries. Log subscriptions → Kinesis Firehose → S3 for long-term retention. Traces: X-Ray SDK in application code, X-Ray daemon on compute. Traces provide end-to-end request path across services. Synthetic: CloudWatch Synthetics canaries test critical user paths every 5 minutes from multiple regions. Dashboards: per-workload dashboards with business KPIs (not just infrastructure metrics) as the top-level view.
- Cost Profile: Medium — CloudWatch Metrics ($0.30/metric/month), Logs ($0.50/GB ingestion + $0.03/GB storage), X-Ray ($5/1M traces). Primary cost driver: log volume. Mitigate with sampling and retention policies.
- Automation: Auto-scale alarms → SNS → Lambda (automated remediation). OpsCenter integration for incident tracking. Runbook automation via Systems Manager for common remediation procedures (restart service, clear cache, failover).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/implement-observability.html

---

**Disaster Recovery — Multi-Tier Strategy**
- RTO/RPO: Varies by pattern (see matrix below)
- AWS Services: AWS Backup (centralized), S3 Cross-Region Replication, RDS Cross-Region Read Replicas, Aurora Global Database, DynamoDB Global Tables, Route 53 (DNS failover), CloudFormation StackSets (multi-region deployment)
- Architecture:

  | DR Pattern | RTO | RPO | Relative Cost | Complexity | Best For |
  |------------|-----|-----|---------------|------------|----------|
  | **Backup & Restore** | Hours (4-24h) | Hours (1-24h) | $ | Low | Non-critical workloads, dev/staging |
  | **Pilot Light** | Minutes-Hours (30min-2h) | Minutes (5-15min) | $$ | Medium | Core business systems with moderate RTO tolerance |
  | **Warm Standby** | Minutes (5-30min) | Seconds-Minutes (near-zero with sync replication) | $$$ | Medium-High | Business-critical workloads, regulated industries |
  | **Multi-Region Active-Active** | Seconds (near-zero) | Near-zero | $$$$ | High | Mission-critical, global workloads, 99.99%+ SLA |

  Backup & Restore: AWS Backup with cross-region copy rules. Restore from backups in DR region when needed. Pilot Light: Core infrastructure running in DR region (DB replicas, base networking), but compute scaled to zero. Scale up on failover. Warm Standby: Full environment in DR region at reduced scale. Route 53 health checks trigger failover. Scale up to production capacity on activation. Active-Active: Full production capacity in both regions. Global load balancing (Route 53, Global Accelerator). DynamoDB Global Tables or Aurora Global Database for data synchronization.
- Cost Profile: Pilot Light — ~20% of primary region cost; Warm Standby — ~40-60% of primary; Active-Active — 100%+ (dual regions + cross-region data transfer).
- Automation: Route 53 health checks with automated failover (DNS-level). CloudWatch alarms → Step Functions → automate scaling in DR region. Regular DR drills automated via AWS Fault Injection Service (FIS).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/plan-for-disaster-recovery-dr.html

---

**FinOps / Cost Optimization Operations**
- RTO/RPO: N/A
- AWS Services: Cost Explorer (analysis), Budgets (alerting), Compute Optimizer (right-sizing), Savings Plans (commitment discounts), Trusted Advisor (optimization checks), Cost Anomaly Detection (automated anomaly alerts), Cost and Usage Report (detailed billing data)
- Architecture:
  Visibility: Cost allocation tags on all resources (mandatory: Environment, Team, Workload, CostCenter). Cost and Usage Report (CUR) delivered to S3, analyzed via Athena/QuickSight for custom reporting. Alerting: AWS Budgets per workload with 80%/100% actual and forecast alerts. Cost Anomaly Detection monitors for unexpected spend spikes. Optimization: Compute Optimizer reviews monthly (instance right-sizing, EBS optimization). Savings Plans for steady-state compute (1-year or 3-year commitment). Spot Instances for fault-tolerant batch workloads. S3 Intelligent-Tiering for variable access patterns. Scheduling: dev/test environments stopped outside business hours (potential 75% savings).
- Cost Profile: Properly implemented FinOps typically saves 20-40% of cloud spend through: right-sizing (10-15%), commitment discounts (20-30%), waste elimination (5-10%), and scheduling (5-15% for dev/test).
- Automation: Lambda scheduled rules for environment start/stop. AWS Instance Scheduler for EC2/RDS scheduling. Tag compliance enforcement via AWS Config rules with auto-remediation. Trusted Advisor checks integrated with EventBridge for automated ticket creation.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/practice-cloud-financial-management.html

---

**Change Management — Deployment Strategies**
- RTO/RPO: N/A (risk reduction — deployment failures should have sub-minute rollback)
- AWS Services: CodePipeline (orchestration), CodeBuild (build), CodeDeploy (deployment strategies), CloudFormation (IaC deployment), AppConfig (feature flags), CloudWatch (deployment monitoring)
- Architecture:
  Blue-Green: Two identical production environments (blue=current, green=new). ALB weighted target group or Route 53 weighted routing shifts traffic from blue to green. Instant rollback by shifting traffic back to blue. Canary: Deploy new version to small percentage of traffic (5-10%). Monitor error rates, latency, and business metrics. If healthy, gradually increase to 100%. CodeDeploy canary configuration: `Canary10Percent5Minutes`. Rolling: Update instances in batches. Each batch is health-checked before proceeding. Minimum healthy percentage ensures availability during deployment. Feature Flags: AppConfig with gradual rollout percentages. Decouple code deployment from feature activation. Instant disable without redeployment.
- Cost Profile: Blue-Green — briefly 2x compute during deployment (minutes); Canary — minimal overhead (few instances); Rolling — no additional cost. Primary cost: build/test infrastructure (CodeBuild compute minutes).
- Automation: CodePipeline fully automates: source → build → test → stage → approve → deploy → validate. CloudWatch alarms configured as deployment gates — automatic rollback if error rate exceeds threshold within deployment window. AppConfig deployment strategies with automatic rollback on CloudWatch alarm.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/mitigate-deployment-risks.html

---

## Reference Architectures

**Three-Tier Web Application**
- Context: Standard web application with presentation tier (CDN + static hosting), application tier (API/business logic), and data tier (database + cache).
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge/CDN | CloudFront + S3 | Static asset delivery, global caching, DDoS protection |
  | DNS | Route 53 | Domain management, health checks, failover routing |
  | Load Balancing | Application Load Balancer | HTTPS termination, path-based routing, health checks |
  | Compute | ECS Fargate / EC2 ASG | Application containers/instances, auto-scaling |
  | Caching | ElastiCache Redis | Session management, query caching, rate limiting |
  | Database | Aurora PostgreSQL Multi-AZ | Persistent data store, read replicas for read-scaling |
  | Storage | S3 | User uploads, generated reports, backups |
  | Security | WAF + Shield | Layer 7 protection, DDoS mitigation |
  | Observability | CloudWatch + X-Ray | Metrics, logs, traces, alarms |

- Key Decisions: Container (Fargate) vs VM (EC2) for compute tier; Aurora vs RDS for database tier; Redis caching strategy (write-through vs lazy-loading); CDN caching TTL per content type.
- Scaling Path: Vertical scaling (larger instances) → Horizontal scaling (more instances across AZs) → Read replicas for database → Multi-region deployment for global reach → Microservices decomposition for independent scaling per domain.
- Cost Baseline: Small ($500-1500/month): t3.medium instances, db.t3.medium Aurora, small ElastiCache. Medium ($3000-8000/month): m5.large instances, db.r5.large Aurora with read replica, r5.large ElastiCache. Large ($15000+/month): multiple m5.xlarge, db.r5.2xlarge Aurora cluster, multi-AZ ElastiCache cluster.
- Source: https://docs.aws.amazon.com/architecture-diagrams/latest/three-tier-web-application-using-amazon-ecs/three-tier-web-application-using-amazon-ecs.html

---

**Serverless API Backend**
- Context: API-driven application using fully managed services with zero server management, pay-per-request pricing, and automatic scaling.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | API Management | API Gateway (REST/HTTP) | Request routing, throttling, authentication, CORS |
  | Compute | Lambda | Business logic execution, event processing |
  | Database | DynamoDB | Low-latency key-value/document store, auto-scaling |
  | Authentication | Cognito | User registration, authentication, JWT token issuance |
  | File Storage | S3 + presigned URLs | User file uploads/downloads without Lambda proxy |
  | Messaging | SQS + EventBridge | Async processing, event-driven integration |
  | Orchestration | Step Functions | Complex workflows, saga patterns |
  | Observability | CloudWatch + X-Ray | Structured logs, traces, custom metrics |

- Key Decisions: REST API vs HTTP API (cost and feature trade-off); DynamoDB single-table design vs multiple tables; Cognito vs custom auth (identity requirements); Lambda function granularity (per-route vs per-domain).
- Scaling Path: Single-region → Reserved concurrency for critical functions → Provisioned concurrency for latency-sensitive paths → Multi-region with DynamoDB Global Tables → Edge-optimized API Gateway with CloudFront.
- Cost Baseline: Low traffic ($10-50/month): API Gateway HTTP API, Lambda free tier, DynamoDB on-demand. Medium ($200-800/month): millions of requests, DynamoDB provisioned capacity with auto-scaling. High ($2000+/month): hundreds of millions of requests, Provisioned Concurrency, multiple DynamoDB tables.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/serverless-applications-lens/reference-architecture.html

---

**Data Lake Architecture**
- Context: Centralized repository for structured, semi-structured, and unstructured data at scale — supporting analytics, machine learning, and reporting workloads.
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Ingestion | Kinesis Firehose, DMS, DataSync | Stream/batch data ingestion from various sources |
  | Storage | S3 (raw/processed/curated zones) | Durable, scalable data storage with lifecycle management |
  | Catalog | Glue Data Catalog + Crawlers | Schema discovery, metadata management, table definitions |
  | Processing | Glue ETL, EMR, Athena | Batch/streaming transformation, ad-hoc querying |
  | Analytics | Athena, Redshift Spectrum | SQL analytics over S3 data without loading |
  | Visualization | QuickSight | Dashboards and reports for business users |
  | Governance | Lake Formation | Fine-grained access control, data sharing, audit |
  | Security | KMS, Macie, IAM | Encryption, PII detection, access management |

- Key Decisions: Medallion architecture (bronze/silver/gold zones) vs domain-oriented zones; Glue vs EMR for processing (managed vs customizable); Athena vs Redshift for analytics (serverless vs provisioned); Lake Formation permission model vs S3 bucket policies.
- Scaling Path: Single-account data lake → Multi-account with Lake Formation cross-account sharing → Data mesh with domain-owned datasets → Real-time streaming layer addition (Kinesis) → ML feature store integration (SageMaker Feature Store).
- Cost Baseline: S3 storage dominates at scale ($0.023/GB/month for Standard, $0.0125/GB for IA). Athena queries ($5/TB scanned — reduce with partitioning and columnar formats). Glue ETL ($0.44/DPU-hour). QuickSight ($24/author/month, $5/reader/month).
- Source: https://docs.aws.amazon.com/prescriptive-guidance/latest/defining-bucket-names-data-lakes/welcome.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **Compute — VMs** | EC2 | Compute Engine | Virtual Machines | OCI Compute |
| **Compute — Containers** | ECS / EKS | Cloud Run / GKE | Container Apps / AKS | Container Instances / OKE |
| **Compute — Serverless** | Lambda | Cloud Functions | Azure Functions | OCI Functions |
| **Object Storage** | S3 | Cloud Storage | Blob Storage | Object Storage |
| **Block Storage** | EBS | Persistent Disk | Managed Disks | Block Volumes |
| **Relational DB — Managed** | RDS / Aurora | Cloud SQL / AlloyDB | Azure SQL / PostgreSQL | Autonomous Database / DB System |
| **NoSQL DB** | DynamoDB | Firestore / Bigtable | Cosmos DB | NoSQL Database |
| **Messaging — Queue** | SQS | Cloud Tasks | Service Bus Queues | OCI Queue |
| **Messaging — Pub/Sub** | SNS / EventBridge | Pub/Sub / Eventarc | Event Grid / Service Bus Topics | OCI Streaming / Events |
| **Streaming** | Kinesis | Dataflow | Event Hubs | OCI Streaming |
| **API Gateway** | API Gateway | API Gateway / Apigee | API Management | API Gateway |
| **Identity** | IAM / Identity Center | Cloud IAM / Workforce Identity | Entra ID / RBAC | IAM / Identity Domains |
| **Secrets** | Secrets Manager | Secret Manager | Key Vault | OCI Vault |
| **Key Management** | KMS | Cloud KMS | Key Vault | OCI Vault / Key Management |
| **Monitoring** | CloudWatch | Cloud Monitoring | Azure Monitor | OCI Monitoring |
| **Logging** | CloudWatch Logs | Cloud Logging | Log Analytics | OCI Logging |
| **CDN** | CloudFront | Cloud CDN | Front Door / CDN | OCI CDN |
| **DNS** | Route 53 | Cloud DNS | Azure DNS | DNS |
| **Load Balancer** | ALB / NLB | Cloud Load Balancing | Application Gateway / LB | Load Balancer |
| **VPN / Interconnect** | Direct Connect / VPN | Interconnect / VPN | ExpressRoute / VPN | FastConnect / VPN |
| **Container Registry** | ECR | Artifact Registry | Container Registry | Container Registry |
| **CI/CD** | CodePipeline / CodeBuild | Cloud Build | Azure DevOps / Pipelines | OCI DevOps |
| **IaC** | CloudFormation / CDK | Deployment Manager / Terraform | ARM / Bicep | Resource Manager |
| **Security Posture** | Security Hub / GuardDuty | Security Command Center | Defender for Cloud | Cloud Guard |
| **WAF** | AWS WAF | Cloud Armor | Azure WAF | OCI WAF |
| **DDoS Protection** | Shield | Cloud Armor | DDoS Protection | OCI DDoS Protection |
| **Well-Architected Tool** | AWS WA Tool | Architecture Framework (no tool) | Azure Advisor / WAF Review | OCI Best Practices (no tool) |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. Each service has unique capabilities, limits, pricing models, and regional availability. Always validate against specific provider documentation before architectural decisions.

---

## Provider Differentiators

**AWS Graviton Processors**
- Category: Compute
- Unique Value: Custom ARM-based processors (Graviton3/Graviton4) designed by AWS offering up to 40% better price-performance versus comparable x86 instances. Available across EC2, RDS, ElastiCache, Lambda, and ECS/EKS.
- Architecture Impact: Default instance selection for ARM-compatible workloads (Linux, containerized applications, managed services). Reduces compute costs without architectural changes — same APIs, same networking, same storage.
- When to Leverage: Any Linux workload without x86-specific binary dependencies. Containerized applications (ARM multi-arch builds). Managed services that support Graviton (RDS, ElastiCache). Lambda functions (arm64 architecture selection).
- Caveat: Not all software has ARM builds. Windows workloads not supported. Some legacy binary dependencies require x86. Verify compatibility before migration.
- Source: https://aws.amazon.com/ec2/graviton/

**AWS Organizations with Service Control Policies (SCPs)**
- Category: Security / Governance
- Unique Value: Hierarchical organizational structure with preventive guardrails (SCPs) that set maximum possible permissions for all identities in member accounts — regardless of IAM policies. No other provider offers this exact combination of hierarchy + preventive controls at the same granularity.
- Architecture Impact: Enables account-level isolation with enforced security boundaries. SCPs can deny: specific regions (data residency), specific services (unapproved services), specific actions (CloudTrail deletion, root API usage), and require conditions (encryption, tagging).
- When to Leverage: Multi-account strategies for enterprise workloads. Compliance requirements mandating preventive controls (not just detective). Team autonomy within guardrails — teams manage their accounts but cannot violate organizational policies.
- Caveat: SCPs are deny-only effective patterns (Allow SCPs are just max permissions). Complex SCP inheritance can be difficult to reason about. SCP evaluation adds milliseconds to API calls. Maximum 5 SCPs per target.
- Source: https://docs.aws.amazon.com/organizations/latest/userguide/orgs_manage_policies_scps.html

**Amazon Aurora Serverless v2**
- Category: Data
- Unique Value: Auto-scaling relational database (MySQL/PostgreSQL compatible) that scales compute capacity in fine-grained increments (0.5 ACU) based on workload demand — from minimum to maximum ACU in seconds. No cold start, no connection disruption during scaling.
- Architecture Impact: Eliminates database capacity planning for variable workloads. Combines RDS reliability (Multi-AZ, automated backups) with serverless cost efficiency (scale to near-zero during low usage). Ideal for workloads with unpredictable or cyclical database load.
- When to Leverage: Variable traffic patterns (business hours heavy, nights/weekends idle). New applications where database load is unpredictable. Multi-tenant SaaS with per-tenant databases. Development environments that should minimize cost when idle.
- Caveat: Cost per ACU-hour higher than equivalent provisioned Aurora. Minimum 0.5 ACU (never scales to true zero like Lambda). Not available for all Aurora features. Maximum 128 ACU per instance.
- Source: https://docs.aws.amazon.com/AmazonRDS/latest/AuroraUserGuide/aurora-serverless-v2.html

**AWS Well-Architected Tool**
- Category: Governance
- Unique Value: Native AWS service for conducting structured architecture reviews against the Well-Architected Framework and Lenses. Tracks improvement plans, milestones, and produces reports. No other provider has an equivalent in-console review tool integrated with their architecture framework.
- Architecture Impact: Formalizes architecture review as an ongoing operational practice rather than a one-time assessment. Integrates with Trusted Advisor for automated checks. Supports custom Lenses for organization-specific governance standards.
- When to Leverage: All production workloads should have a Well-Architected Review tracked in the tool. Pre-launch assessments, quarterly reviews, and post-incident architecture evaluations.
- Caveat: Self-assessment tool — does not automatically scan or validate infrastructure. Requires architectural knowledge to answer questions accurately. Custom Lenses require development effort.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/userguide/intro.html

**AWS Control Tower**
- Category: Governance / Security
- Unique Value: Automated landing zone deployment and account governance for multi-account AWS environments. Provides account factory (automated provisioning), mandatory guardrails (preventive SCPs + detective Config rules), and centralized logging — out of the box.
- Architecture Impact: Accelerates multi-account setup from weeks to hours. Enforces consistent security baseline across all accounts. Provides pre-configured guardrails for common compliance requirements. Account Factory integrates with Service Catalog for self-service account creation.
- When to Leverage: Any new multi-account AWS deployment. Organizations adopting AWS Organizations for the first time. Compliance-driven environments requiring consistent guardrails across all accounts.
- Caveat: Opinionated — may conflict with existing custom landing zone implementations. Limited customization of mandatory guardrails. Region selection at setup time is difficult to change later. Not all AWS regions supported.
- Source: https://docs.aws.amazon.com/controltower/latest/userguide/what-is-control-tower.html

---

## Scenario Coverage

**Standard Case**: Production three-tier web application on AWS
- Approach: Multi-AZ VPC with public/private/isolated subnets → ALB (HTTPS, WAF) → ECS Fargate (auto-scaling) → Aurora PostgreSQL Multi-AZ → ElastiCache Redis → CloudFront CDN → Route 53 DNS → CloudWatch observability → AWS Backup for DR
- Key Decisions:
  1. Container orchestration: Fargate (zero ops) vs ECS on EC2 (cost optimization at scale) vs EKS (Kubernetes required)
  2. Database: Aurora vs RDS (Aurora for >100GB, high availability requirements)
  3. Caching: Redis (complex data structures, persistence) vs Memcached (simple key-value, multi-threaded)
  4. DR strategy: Pilot Light (cost-sensitive) vs Warm Standby (low RTO required)
  5. Account strategy: Minimum production + staging + development + security accounts

**Edge Case**: Global financial services application with regulatory constraints
- Approach: Multi-region active-active with data residency controls. Aurora Global Database (write in primary region, read replicas in secondary). DynamoDB Global Tables for session data. CloudFront with geographic restrictions. SCPs restricting resources to approved regions. AWS Config rules for continuous compliance (PCI-DSS, SOX). Dedicated accounts per regulatory domain. AWS Artifact for compliance reports. Separate encryption keys per region (KMS multi-region keys for cross-region access, single-region keys for data residency).
- Key Decisions: Data residency requirements per region (which data can replicate where), RTO/RPO requirements driving DR pattern selection, compliance framework mapping (which AWS services are in-scope for which controls), key management strategy (per-region vs cross-region), audit log retention requirements

**Anti-Pattern Case**: Single-account, single-AZ, public-subnet deployment with wildcard IAM
- Clarification: Before proceeding with any architecture that has: (1) all resources in one AWS account with no environment separation, (2) production databases in public subnets with internet-facing security groups, (3) IAM policies using `"Action": "*", "Resource": "*"`, (4) no CloudTrail, no encryption, no backup strategy — the architect MUST refuse to proceed and require:
  - Separate production account (at minimum)
  - Private subnets for all data stores
  - Granular IAM policies with specific resource ARNs
  - CloudTrail enabled multi-region
  - Encryption at rest on all data stores
  - Defined backup/recovery strategy with tested restore procedures
  - Budget alerts configured

  These are non-negotiable prerequisites for any production workload. The Well-Architected Framework explicitly states: "Security and Operational Excellence are generally not traded-off against the other pillars."
