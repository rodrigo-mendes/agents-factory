# Cloud Research Scope §3–10 — Patterns, Security, Networking & Reference

## 3. Cloud-Native Design Patterns

Architectural patterns for building cloud-native applications on `{{CLOUD_PROVIDER}}` within `{{ARCHITECTURE_CONTEXT}}`:

- **12-Factor App Compliance**: How each factor maps to `{{CLOUD_PROVIDER}}` services
- **Microservices Patterns**: Service decomposition, inter-service communication (sync vs async), API gateway, service mesh
- **Event-Driven Patterns**: Event sourcing, CQRS, saga/choreography vs orchestration, dead letter queues
- **Resilience Patterns**: Circuit breaker, bulkhead, retry with exponential backoff, timeout, fallback
- **Scalability Patterns**: Horizontal scaling, auto-scaling policies, queue-based load leveling, sharding
- **Data Patterns**: Database-per-service, shared database, event-driven data sync, CQRS read models
- **Strangler Fig**: Incremental migration from monolith to microservices

**Format**:
```
Pattern: [Name]
Category: [Resilience | Scalability | Data | Communication | Migration]
Problem: [What architectural challenge this solves]
Solution on {{CLOUD_PROVIDER}}:
  [Pattern implementation using specific {{CLOUD_PROVIDER}} services]
Services Used: [Exact service names and their roles in the pattern]
When to Apply: [Context indicators from {{ARCHITECTURE_CONTEXT}}]
When NOT to Apply: [Counter-indicators — over-engineering signals]
Trade-offs:
  | Dimension | Benefit | Cost |
  |-----------|---------|------|
Complements: [Other patterns this pairs with]
Source: [Official reference architecture or pattern guide URL]
```

---

## 4. Cloud Security Architecture

Security architecture patterns specific to `{{CLOUD_PROVIDER}}` for `{{ARCHITECTURE_CONTEXT}}`:

- **Identity & Access Management**: Identity providers, federation (SAML/OIDC), service-to-service auth, cross-account/cross-project access
  - AWS: IAM, STS, Organizations SCPs, Identity Center
  - GCP: Cloud IAM, Workload Identity, Organization Policies
  - Azure: Entra ID (Azure AD), Managed Identities, RBAC, Azure Policy
  - OCI: IAM, Identity Domains, Compartment Policies, Dynamic Groups
- **Network Security**: VPC/VCN/VNet segmentation, security groups/NSGs, WAF, DDoS protection, private endpoints, PrivateLink/Private Service Connect/Private Link/Service Gateway
- **Data Security**: Encryption (KMS/Cloud KMS/Key Vault/OCI Vault), key rotation, data classification, DLP
- **Detection & Response**: GuardDuty/Security Command Center/Defender for Cloud/Cloud Guard, SIEM integration, automated remediation
- **Zero Trust Architecture**: Principles and implementation using `{{CLOUD_PROVIDER}}` native services
- **Compliance Mapping**: How framework pillars map to compliance frameworks (SOC2, HIPAA, PCI-DSS, GDPR) — structure only, not legal advice

**Format**:
```
Security Domain: [Identity | Network | Data | Detection | Compliance]
Pattern: [Name]
{{CLOUD_PROVIDER}} Services:
  [List of services and their security role]
Architecture:
  [How services compose to implement the security pattern]
Configuration Essentials:
  [Key configuration parameters — not full IaC, but architecture-level settings]
Verification:
  [Security audit check — tool, command, or console validation]
Compliance Alignment: [Which compliance controls this satisfies — framework reference only]
Source: [Official security best practices URL]
```

---

## 5. Cloud Operational Patterns

Operational architecture for running production workloads on `{{CLOUD_PROVIDER}}`:

- **Observability Stack**: Metrics, logs, traces — provider-native services and integration points
  - AWS: CloudWatch (Metrics, Logs, Traces), X-Ray, CloudWatch Synthetics
  - GCP: Cloud Monitoring, Cloud Logging, Cloud Trace, Uptime Checks
  - Azure: Azure Monitor, Log Analytics, Application Insights, Availability Tests
  - OCI: Monitoring, Logging, Logging Analytics, Application Performance Monitoring
- **Disaster Recovery Patterns**: Backup & restore, pilot light, warm standby, multi-region active-active — with RTO/RPO tradeoffs per pattern
- **High Availability Patterns**: Multi-AZ, multi-region, load balancing, health checks, auto-healing
- **FinOps / Cost Optimization**: Right-sizing, reserved instances/committed use, spot/preemptible, savings plans, cost allocation tags, budgets and alerts
- **Change Management**: Deployment strategies (blue-green, canary, rolling), feature flags, rollback procedures
- **Incident Management**: Runbook automation, escalation patterns, post-mortem templates

**Format**:
```
Operational Domain: [Observability | DR | HA | FinOps | Change Management | Incident]
Pattern: [Name]
RTO/RPO (if DR/HA): [Recovery time/point objectives per pattern tier]
{{CLOUD_PROVIDER}} Services:
  [Service composition for this operational pattern]
Architecture:
  [How services are wired together — data flow, alerting chain, recovery sequence]
Cost Profile: [Relative cost of operating this pattern — low/medium/high + primary cost driver]
Automation:
  [What can and should be automated vs. manual decision points]
Runbook Skeleton:
  [Key steps for operating this pattern — detection, triage, resolution, post-mortem]
Source: [Official operational best practices URL]
```

### DR Pattern Cost-Benefit Matrix

| DR Pattern | RTO | RPO | Relative Cost | Complexity | Best For |
|------------|-----|-----|---------------|------------|----------|
| **Backup & Restore** | Hours | Hours | $ | Low | Non-critical workloads |
| **Pilot Light** | Minutes-Hours | Minutes | $$ | Medium | Core business systems |
| **Warm Standby** | Minutes | Seconds-Minutes | $$$ | Medium-High | Business-critical workloads |
| **Multi-Region Active-Active** | Seconds | Near-zero | $$$$ | High | Mission-critical, global workloads |

---

## 6. Cloud Migration Patterns

Migration architecture strategies for moving to `{{CLOUD_PROVIDER}}`:

- **6 Rs Assessment**: Rehost, Replatform, Refactor, Repurchase, Retire, Retain — decision framework
- **Migration Waves**: How to sequence workload migration (dependency mapping, blast radius, business criticality)
- **Landing Zone Architecture**: Account/project structure, networking foundation, security baseline, shared services
- **Database Migration**: Schema conversion, data replication, cutover strategies, validation
- **Application Migration**: Lift-and-shift tooling, containerization, modernization paths
- **Hybrid Connectivity**: VPN, dedicated interconnect (Direct Connect / Interconnect / ExpressRoute / FastConnect), DNS resolution

**Format**:
```
Migration Strategy: [R-category]
When: [Decision criteria — technical debt level, team skill, timeline, budget]
{{CLOUD_PROVIDER}} Tools:
  [Migration-specific services and tools]
Architecture Before: [Source architecture pattern]
Architecture After: [Target architecture on {{CLOUD_PROVIDER}}]
Risk Assessment:
  | Risk | Probability | Impact | Mitigation |
  |------|------------|--------|------------|
Validation: [How to verify migration completeness and correctness]
Rollback Plan: [How to revert if migration fails]
Source: [Official migration guide URL]
```

---

## 7. Cloud Networking Architecture

Network architecture patterns for `{{CLOUD_PROVIDER}}`:

- **VPC/VCN/VNet Design**: CIDR planning, subnet strategy (public/private/isolated), availability zone distribution
- **Network Topologies**: Hub-spoke, transit gateway/interconnect, mesh, hybrid
- **Connectivity**: VPN, dedicated interconnect, peering, service endpoints/private endpoints
- **Load Balancing**: Application load balancer, network load balancer, global load balancing, traffic management
- **DNS Architecture**: Public/private hosted zones, split-horizon DNS, service discovery
- **CDN & Edge**: Content delivery, edge computing, edge locations, caching strategies
- **Network Security**: Network ACLs, security groups/NSGs, firewall services, flow logs, traffic mirroring

**Format**:
```
Network Pattern: [Name]
Topology: [Hub-spoke | Mesh | Transit | Hybrid]
{{CLOUD_PROVIDER}} Services:
  [Network services and their roles]
CIDR Strategy:
  [IP planning guidance — non-overlapping ranges, subnet sizing]
Architecture:
  [Network topology description with data flow paths]
Connectivity:
  | Connection Type | Bandwidth | Latency | Cost | Redundancy |
  |----------------|-----------|---------|------|------------|
Security Controls:
  [Network-level security — ACLs, security groups, firewall rules]
Monitoring:
  [Flow logs, traffic analytics, network monitoring]
Source: [Official networking best practices URL]
```

---

## 8. Reference Architectures & Landing Zones

Production-ready reference architectures for `{{ARCHITECTURE_CONTEXT}}` on `{{CLOUD_PROVIDER}}`:

- **Landing Zone**: Account/project structure, organizational hierarchy, shared services, security baseline
  - AWS: Control Tower, Organizations, Service Catalog
  - GCP: Cloud Foundation Toolkit, Organization hierarchy, Shared VPC
  - Azure: Azure Landing Zones (CAF), Management Groups, Azure Policy
  - OCI: Landing Zones, Compartments, Tenancy structure
- **Workload Reference Architectures**: Provider-published architectures for common workload types (web apps, data pipelines, ML/AI, IoT, SaaS)
- **Account/Project Strategy**: Organizational units, environment isolation, shared services, security accounts
- **Governance & Guardrails**: Service control policies, organization policies, management policies, preventive vs detective controls

**Format**:
```
Reference Architecture: [Name — e.g., "Three-Tier Web Application" or "Data Lake"]
{{CLOUD_PROVIDER}} Source: [Official reference architecture URL]
Context: [What workload type this applies to]
Services Composition:
  | Layer | Service | Purpose | Alternative |
  |-------|---------|---------|-------------|
Architecture Diagram Description:
  [Textual description of the architecture — components, data flow, boundaries]
Key Decisions:
  [Architectural choices embedded in this reference — and what to customize]
Scaling Path:
  [How this architecture evolves as the workload grows]
Cost Baseline:
  [Relative cost profile — order of magnitude, not exact pricing]
Source: [Official reference architecture URL]
```

---

## 9. Cloud Service Equivalence Map

Cross-provider service mapping for architects evaluating or planning multi-cloud strategies:

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
| **IaC** | CloudFormation | Deployment Manager | ARM / Bicep | Resource Manager |
| **Security Posture** | Security Hub / GuardDuty | Security Command Center | Defender for Cloud | Cloud Guard |
| **WAF** | AWS WAF | Cloud Armor | Azure WAF | OCI WAF |
| **DDoS Protection** | Shield | Cloud Armor | DDoS Protection | OCI DDoS Protection |

> **⚠️ Important**: Service equivalence does NOT mean feature parity. Each service has unique capabilities, limits, pricing models, and regional availability. Always validate against `{{TARGET_EDITION}}` documentation before architectural decisions.

---

## 10. Provider-Specific Differentiators

Unique architectural capabilities of `{{CLOUD_PROVIDER}}` that have no direct equivalent or represent significant differentiation:

### AWS Differentiators
- **AWS Outposts**: On-premises AWS infrastructure extension
- **AWS Local Zones**: Low-latency edge locations in metro areas
- **AWS Wavelength**: 5G edge computing
- **Amazon Aurora Serverless v2**: Auto-scaling relational database
- **AWS Graviton**: ARM-based custom processors for cost optimization

### Google Cloud Differentiators
- **BigQuery**: Serverless data warehouse with built-in ML
- **Anthos**: Multi-cloud Kubernetes management
- **Spanner**: Globally distributed relational database
- **Cloud Run**: Fully managed serverless containers
- **Vertex AI**: Unified ML platform

### Azure Differentiators
- **Azure Arc**: Multi-cloud and on-premises resource management
- **Azure DevOps**: Integrated CI/CD platform
- **Cosmos DB**: Multi-model globally distributed database
- **Azure Active Directory (Entra ID)**: Enterprise identity with Office 365 integration
- **Azure Stack**: Hybrid cloud computing

### Oracle Cloud (OCI) Differentiators
- **Autonomous Database**: Self-driving, self-securing, self-repairing database
- **OCI Dedicated Region (Cloud@Customer)**: Full cloud region deployed on-premises
- **Exadata Cloud Service**: High-performance Oracle Database infrastructure
- **OCI Ampere A1 Compute**: ARM-based compute with competitive pricing
- **Oracle Database@Cloud Partners**: Oracle Database managed on AWS/Azure/GCP
- **OCI Flexible Shapes**: Granular CPU/memory allocation for compute instances
- **Maximum Security Zones**: Enforced security policies at compartment level

**Format**:
```
Differentiator: [Service or capability name]
Category: [Compute | Data | AI/ML | Hybrid | Edge | Security]
Unique Value: [What it does that other providers don't — or do significantly differently]
Architecture Impact: [How this changes architecture decisions when available]
When to Leverage: [Workload types or contexts where this is the decisive factor]
Caveat: [Limitations, regional availability, pricing model]
Source: [Official documentation URL]
```

---
