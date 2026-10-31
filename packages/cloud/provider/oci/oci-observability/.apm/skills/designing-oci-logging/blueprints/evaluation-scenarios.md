# Evaluation Scenarios — provisioning-oci-logging

## Scenario 1: Production 3-Tier Application Full-Stack Logging Setup

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "Set up OCI Logging for a production 3-tier web application: API Gateway, Load Balancer, compute instances running a Java Spring Boot app (writing structured JSON logs to /var/log/app/app.log), and an Autonomous Database. We need 90-day retention for app and infra logs, 180-day for DB audit, and the team requires developer, SRE, and security-auditor access tiers.",
  "expected_behavior": [
    "Creates three separate log groups: one for app (CUSTOM logs), one for infra (SERVICE logs for LB + API GW), one for DB audit — not a single shared group",
    "Sets retention_duration explicitly: app=90, infra=90, db=180 — never omits or defaults to 30",
    "Configures UMA LOG_TAIL with JSON parser (not NONE) for compute instances, associated via dynamic group not instance OCIDs",
    "Generates three-tier IAM policy: instances=use log-content, SRE=read log-content, terraform=manage logging-family (not log-content)",
    "Reminds that API Gateway and LB service logging must be enabled separately in their own configs, referencing the Log object OCID",
    "Recommends deploying Connector Hub → Object Storage archival pipeline before enabling DB audit logs (180-day + compliance)"
  ]
}
```

---

## Scenario 2: PCI-DSS Compliance Log Archival Beyond 180 Days

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "We need to meet PCI-DSS requirements for 1-year log retention. We currently have OCI Logging configured with 180-day retention on VCN flow logs, API Gateway execution logs, and database audit logs. How do I extend beyond 180 days?",
  "expected_behavior": [
    "Explains that OCI Logging's hard ceiling is 180 days — not a configurable limit",
    "Presents the Ask First Decision #3: asks whether archived data needs active search or is purely produce-on-demand",
    "For audit-only PCI compliance: recommends Connector Hub → Object Storage with Retention Rules (WORM) + CMK encryption — cheapest option",
    "For active search: recommends Connector Hub → Logging Analytics (separate service, per-GB cost)",
    "Warns that Connector Hub archival pipeline must be deployed BEFORE the log objects if not already in place — retroactive recovery is impossible",
    "Provides Terraform code using depends_on to ensure connector is created before logs are enabled",
    "Notes Object Storage Retention Rules must be locked immediately after creation — locked rules cannot be shortened"
  ]
}
```

---

## Scenario 3: Enable VCN Flow Logs Across All Production Subnets

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "Enable VCN Flow Logs on all 12 subnets in our production VCN to maximize network security visibility.",
  "expected_behavior": [
    "Triggers Never Do #5 warning: alerts that enabling `all` category on all 12 subnets will generate very high log volume and cost overrun",
    "Asks the architect: which subnets are perimeter/internet-facing vs internal application subnets?",
    "Recommends `reject` category for internal app subnets (security events without accepted-traffic noise)",
    "Recommends `all` category only for perimeter/internet-facing subnets where forensics-grade capture is justified",
    "Requires archival pipeline (Connector Hub → Object Storage) be deployed BEFORE enabling any flow logs — especially high-volume `all` category",
    "Provides Terraform with depends_on ordering: bucket → connector → log",
    "Sets retention_duration explicitly (90 days minimum for VCN flow, 180 for perimeter with archival)"
  ]
}
```

---

## Scenario 4 (Bonus): Migrating UMA Configuration from Instance OCIDs to Dynamic Group

```json
{
  "skills": ["provisioning-oci-logging"],
  "query": "Our current UMA configuration has group_list hardcoded with 5 specific instance OCIDs. We just enabled auto-scaling and new instances are not shipping logs. Fix this.",
  "expected_behavior": [
    "Identifies root cause: Never Do #6 — UMA config targeting individual instance OCIDs breaks on instance replacement/auto-scaling",
    "Creates oci_identity_dynamic_group resource (tenancy-level, not compartment) with matching_rule = 'ALL {instance.compartment.id = ...}'",
    "Updates group_association.group_list to reference the dynamic group OCID (not instance OCIDs)",
    "Notes that changing group_association is an in-place update — no log data gap during apply",
    "Adds verification steps: check configurationState = SUCCEEDED after apply; confirm new instances enroll within 2-3 minutes",
    "Ensures IAM policy 'use log-content' applies to the new dynamic group name"
  ]
}
```
