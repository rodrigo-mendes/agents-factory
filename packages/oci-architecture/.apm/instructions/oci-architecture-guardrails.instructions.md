---
name: oci-architecture-guardrails
description: "OCI serverless architecture guardrails for platform, API Gateway, networking and Vault/IAM design (rules OCI-R34 to OCI-R54, R65 to R71, R73 to R81, R86 to R88, R93 to R103, R107 to R110). Use when editing or reviewing OCI Terraform or architecture handoff work-orders."
applyTo: "**/oci/**/*.tf,**/*oci*/**/*.tf,docs/handoff/**"
---

# OCI Architecture Guardrails — Platform, API Gateway, Networking, Vault

Technical facts live in the architecture skills of the `oci-architecture` package. This rule states
what to check and where to look; it does not duplicate skill bodies. Tags `(unverified)` and
`(medium confidence)` from a skill apply here too. Rule IDs come from the OCI family rules
(Architecture Rules section). Object Storage and event-driven rules are in
`oci-architecture-data-events-guardrails`.

Skill abbreviations: **SRV** `architecting-oci-serverless`, **GW** `designing-oci-api-gateway`,
**NET** `designing-oci-networking`, **VLT** `designing-oci-vault-security`.

## Always

- **OCI-R34** — All client traffic enters through API Gateway; invoke endpoints never exposed. (SRV, GW)
- **OCI-R35** — Functions in private subnets with NSGs; gateway in a separate public subnet. (SRV, NET)
- **OCI-R36** — Dynamic Group + IAM policies + Resource Principal; no credentials in code/env/config. (SRV)
- **OCI-R37** — Segregate compartments (network, security, per-environment serverless). (SRV)
- **OCI-R38** — Explicit memory and timeout (never the 300s default); pinned image. (SRV)
- **OCI-R39** — TLS 1.2+; custom domains via OCI Certificates with auto-renewal; mTLS for B2B/financial. (SRV, GW)
- **OCI-R40** — Tracing on the Functions Application; access + execution logs on every deployment; alarms. (SRV, GW)
- **OCI-R41** — Tag all serverless resources for cost attribution. (SRV)
- **OCI-R42** — Gateway→function IAM trio: `fn-invocation`, FaaS `virtual-network-family`, FaaS `read repos`. (GW, SRV)
- **OCI-R43** — Restrictive NSGs: gateway ingress 443 only; functions ingress only from the gateway. (GW, NET, SRV)
- **OCI-R44** — CORS with explicit origins/methods/headers. (GW)
- **OCI-R45** — Service Gateway in every VCN with private subnets. (NET)
- **OCI-R46** — NSGs, not Security Lists, as the primary segmentation mechanism. (NET)
- **OCI-R47** — NAT Gateway (never IGW) for private-subnet egress. (NET)
- **OCI-R48** — VCN Flow Logs on subnets with sensitive traffic. (NET)
- **OCI-R49** — CMEK for data at rest; required for regulated data. (VLT)
- **OCI-R50** — Secrets from Vault at runtime via Resource Principal; config holds only non-sensitive values. (VLT, SRV)
- **OCI-R51** — Automated secret rotation and expiry rule on production secrets. (VLT)
- **OCI-R52** — Workload dynamic groups get `use keys` / `read secret-bundles` only; never `manage`. (VLT)
- **OCI-R53** — Separate keys per purpose with distinct rotation intervals. (VLT)
- **OCI-R54** — Cache secrets with TTL; do not fetch per invocation. (VLT)

## Ask First

Resolve each as `[Decision] → Recommendation`, or return a numbered question if the request does
not settle it. Options and trade-offs are in the named skill.

- **OCI-R93 / R94 / R95** — Compute shape; cold-start mitigation (needs the P99 SLA); sync vs detached. (SRV)
- **OCI-R96** — Authentication strategy (needs identity provider and token format). (GW, SRV)
- **OCI-R97** — Gateway endpoint type: external or internal consumers. (GW, SRV)
- **OCI-R98** — Function subnet egress: NAT or Service Gateway only. (SRV)
- **OCI-R99** — Rate-limiting strategy beyond the `CLIENT_IP` baseline. (GW)
- **OCI-R100** — Network security model: NSGs / Security Lists / Network Firewall / WAF. (NET)
- **OCI-R101 / R102 / R103** — VCN topology; on-premises connectivity; load-balancing approach. (NET)
- **OCI-R107** — Vault type (needs compliance framework, key count, replication need). (VLT)
- **OCI-R108** — Key protection mode; immutable after creation. (VLT)
- **OCI-R109 / R110** — Secret storage (Vault vs config); key algorithm (only for signing/wrapping). (VLT)

## Never

- **OCI-R65** — Hardcoded credentials in code or function config. (SRV, VLT)
- **OCI-R66** — Functions in a public subnet. (SRV)
- **OCI-R67** — Wildcard IAM (`manage all-resources`, `manage keys in tenancy`). (SRV, VLT)
- **OCI-R68** — Function timeout left unconfigured. (SRV)
- **OCI-R69** — Gateway deployment without rate limiting. (SRV, GW)
- **OCI-R70** — Logging or tracing disabled in production. (SRV, GW)
- **OCI-R71** — Single compartment for all resources. (SRV)
- **OCI-R73** — Functions exposed without API Gateway. (GW)
- **OCI-R74** — Wildcard CORS origin with credentials enabled. (GW)
- **OCI-R75** — Monolithic deployment with all routes; flag more than 20 routes. (GW)
- **OCI-R76** — Hardcoded backend IPs in `HTTP_BACKEND` routes. (GW)
- **OCI-R77** — Security List with `0.0.0.0/0` ingress on all ports. (NET)
- **OCI-R78** — Private subnet routed to an Internet Gateway. (NET)
- **OCI-R79** — Missing Service Gateway. (NET)
- **OCI-R80** — NSG with unrestricted egress. (NET)
- **OCI-R81** — Insufficient or overlapping VCN CIDR blocks. (NET)
- **OCI-R86** — Oracle-managed keys for regulated data. (VLT)
- **OCI-R87** — One encryption key for all purposes. (VLT)
- **OCI-R88** — Secrets without expiry or rotation. (VLT)

For each violation found in a review, name the rule ID and the governing skill, and prefer the
correct approach stated in that skill over ad-hoc fixes.
