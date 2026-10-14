---
description: 'Generic entry point for OCI observability infra and design (APM & tracing, Logging, Monitoring alarms, Connector Hub, Management/APM Dashboards). Collects the pillar, environment, and compartment context, then routes to the oci-observability agent.'
agent: oci-observability
argument-hint: 'Describe the observability capability you need (APM, logging, alarms, connector-hub, dashboard)'
---

# OCI Observability

## Context Collection

Before starting, I need to understand your observability request.

**Answer these questions:**

1. **Which pillar(s)?**
   - APM & distributed tracing (domain, synthetic monitors, Apdex)
   - Logging (Log Groups, Logs, UMA)
   - Monitoring alarms (thresholds, suppressions, custom metric ingestion)
   - Connector Hub (log routing to Object Storage / Logging Analytics / Functions)
   - Management / APM Dashboards (widgets, APM QL, global filters)
   - Full observability stack (dashboards + APM + logging + alarms integrated)

2. **Design or provision?** Architecture advisory, Terraform provisioning, or both?

3. **Environment**: dev / staging / prod?

4. **Compartment**: Which OCI compartment will host these resources?

5. **Existing observability**: Any APM domain, log groups, alarms, or dashboards already provisioned to reference?

## Workflow

Once I have your answers, I will follow the P0–P5 workflow:
- **P0**: Load `observability-skills.instructions.md` and the right design/provisioning skill(s)
- **P1**: Analyze existing .tf files and observability resources
- **P2**: Consult skill patterns (✅/🚫 rules)
- **P3**: Propose a plan for your approval
- **P4**: Generate Terraform / dashboard JSON (and design docs)
- **P5**: Validate with `terraform fmt`/`validate` and, when applied, the live 4-pillar scripts
