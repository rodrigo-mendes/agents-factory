### 🚫 Never Do

**1. Hardcoded Credentials in Function Configuration**: Credentials in function config vars are visible in OCI Console, API, and Terraform state. Credentials in code are exposed via source control and log leaks.

**Correct approach**: Use Resource Principal + OCI Vault. Store only non-sensitive config (OCIDs, bucket names, environment) in function config. Fetch secrets from Vault at runtime.

**Detection**:
```bash
# Scan function configs for leaked secrets
oci fn function list --application-id <APP_OCID> --all \
  --query 'data[*].config' | grep -iE 'password|secret|key|token'
# Expected: No matches for actual credential values (OCIDs are acceptable)

# Scan Function config for suspicious variables
oci fn application get --application-id <app_ocid> | jq '.data.config' | grep -i "password\|secret\|key\|token"
```

**Actual impact**: Data breach, credential compromise, lateral movement across services.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsstoringsecretsinvault.htm

---

**2. Functions in Public Subnet**: Functions in public subnets may receive direct internet traffic, bypassing API Gateway's protections entirely.

**Correct approach**: Functions in private subnet with NSG allowing ingress only from API Gateway subnet CIDR.

**Detection**:
```bash
oci fn application get --application-id <OCID> --query 'data."subnet-ids"'
oci network subnet get --subnet-id <SUBNET_OCID> --query 'data."prohibit-public-ip-on-vnic"'
# Must return true
```

**Actual impact**: Unauthorized invocation, DDoS exposure, authentication bypass.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsconfiguringnetworking.htm

---

**3. Wildcard IAM Policies for Functions**: `manage all-resources in tenancy` violates least-privilege. OCI policies are additive-only (no explicit deny) — broad grants cannot be scoped down.

**Correct approach**: Specific verbs on specific resource types in specific compartments with conditions.

**Detection**:
```bash
oci iam policy list --compartment-id <TENANCY_OCID> --all \
  | grep -i "manage all-resources\|use all-resources"
# Expected: empty (no matches)
```

**Actual impact**: Privilege escalation, lateral movement, data exfiltration.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/policyreference.htm

---

**4. No Timeout Configuration**: Functions without explicit timeouts consume resources during hung connections or infinite loops, running until the 300s platform maximum.

**Correct approach**: Set `timeout_in_seconds` to minimum viable value. API-facing: 30–60s. Background: scale appropriately.

**Detection**:
```bash
oci fn function list --application-id <app_ocid> \
  | jq '.data[] | {name: .["display-name"], timeout: .["timeout-in-seconds"], memory: .["memory-in-mbs"]}'
# Flag any function with timeout=300 or null
```

**Actual impact**: Cost overrun, resource exhaustion, cascading timeouts.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscustomizing.htm

---

**5. API Gateway Without Rate Limiting**: Unbounded request rates exhaust function concurrency limits, causing cascading failures and cost spikes.

**Correct approach**: Configure `rate_limiting` at deployment level with `rate_key = CLIENT_IP` as minimum baseline.

**Actual impact**: Service degradation, cost overrun, denial of service.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingratelmiting.htm

---

**6. Logging and Tracing Disabled in Production**: Functions are ephemeral — without observability, MTTR increases dramatically.

**Correct approach**: Enable `trace_config.is_enabled = true` at Application level. Enable both `access_log` and `execution_log` on API Gateway deployments.

**Actual impact**: Extended incident resolution, inability to diagnose issues, SLA violations.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsexportingfunctionlogfiles.htm

---

**7. Single Compartment for All Resources**: Without segregation, any policy change or compromise affects all resources.

**Correct approach**: Separate compartments per environment and function (Network, Security, Serverless-Dev/Staging/Prod).

**Detection**:
```bash
oci search resource structured-search \
  --query-text "query all resources where compartmentId = '<root_compartment>'"
# If this returns ALL resources — segregation is missing
```

**Actual impact**: Blast radius = entire tenancy; impossible to do granular auditing or billing.
**Source**: https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingcompartments.htm

---

**8. SCH→Function Architecture Without Cold-Start Ceiling Awareness**

> **Risk Level**: HIGH — permanent ErrorsAtTarget loop; consumers never process events.

When Service Connector Hub (SCH) is configured to invoke an OCI Function as a target, SCH uses a **synchronous invoke with a hard deadline of ~30-60 s**. Standard JVM Functions built with OTel + Jersey3 + OCI SDK (67+ dependency jars) require approximately **55-62 s of platform container provisioning + JVM pre-main class-loading** before any application code runs. This pre-main phase happens before the FDK even starts; it cannot be shortened by moving application init to `configure()`.

**Failure pattern**:
```
SCH invokes Function (cold container) →
  ~55s: platform provisions container + JVM loads classpath (pre-main) →
  SCH deadline expires → 444 Client request aborted (no app log) →
  ErrorsAtTarget increments → SCH retries next poll cycle → new cold start → loop
```

**What does NOT fix the ceiling**:
- Memory 256 → 1024 MB: reduces JVM class-load time under more CPU but does NOT eliminate the ~55-60 s pre-main gap
- Function timeout 60 → 300 s: the SCH timeout is on the SCH side (~30-60 s hard); the function's own timeout is irrelevant for this failure
- Moving OTel init to `configure()`: reduces app-init from ~2.3 s to ~0.96 s; pre-main gap unchanged

**Diagnostic signature** (distinguish from missing fn-function verb):

| Metric / Log | Missing fn-function (auth reject) | SCH cold-start ceiling |
|---|---|---|
| `ErrorsAtTarget` | Incrementing | Incrementing |
| Function logs — "Received" line | ABSENT (never entered pipeline) | PRESENT (platform started, then abort) |
| `LatencyAtTarget` | Not emitted | May emit partial |
| Warm direct-invoke result | Success (proves code OK) | Success (proves code OK) |

**Correct approaches** (pick one based on cost/complexity):

1. **timeout=300s + memory=1024MB** (cheapest, recommended first): SCH deadline is ~30-60 s for the sync call, but with 1024 MB the cold-provision completes within 60 s and the function timeout (300 s) gives headroom. Confirmed working in dev (cycle 10). Cost: pay-per-use only.

2. **Provisioned Concurrency** (zero cold start, costly): keeps containers warm → no cold-provision phase → SCH delivers every time. Caveat: OCI Functions requires count to be a multiple of 10; `count = 1` is rejected (`400 InvalidParameter`). Minimum viable = 10 containers per function.

3. **GraalVM native image** (~2-5 s cold start): eliminates JVM pre-main overhead entirely. Requires native compilation build pipeline and OCI SDK native config; feasible for dedicated teams.

4. **Async decouple** (highest flexibility): SCH → ONS / OCI Queue (tolerates cold latency) → Function invoked asynchronously. No sync deadline on the SCH side.

**Evidence**: `docs/handoff/event-pubsub/diagnosis-report.md` (55 s pre-main gap measured live), `deploy-report.md` cycles 3b-6 (memory+timeout insufficient alone; cycle 10 confirmed fix with timeout=300s+memory=1024MB).

