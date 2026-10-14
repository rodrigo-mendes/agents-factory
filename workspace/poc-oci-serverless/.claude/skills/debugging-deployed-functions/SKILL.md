---
name: debugging-deployed-functions
description: Diagnoses runtime issues in deployed OCI Functions using systematic elimination by HTTP status code, OCI CLI investigation, and common root cause database. Use when a deployed function returns 502/503/504/500, when post-deploy validation fails, or when IAM, Vault, or network access is suspect.
---

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) — ✅⚠️🚫 patterns
- [Diagnostic Methodology](#diagnostic-methodology-classify--investigate--eliminate--fix) — classification workflow
- [OCI CLI Diagnostic Commands](#oci-cli-diagnostic-commands) — investigation commands
- [Quick Diagnostic Checklist](#quick-diagnostic-checklist) — ordered check list
- [Direct Function Invocation](#direct-function-invocation-bypass-api-gateway) — bypass API Gateway
- [Decision Trees & Root Causes](./blueprints/diagnostic-decision-trees.md) — full trees, error database, cascade pattern
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md) — canonical, edge, misuse test cases
- [Version Context](#version-context)
- [External Resources](#external-resources)

---

## Blueprints & Guardrails

### ✅ Always Do

- **Classify by HTTP status first.** 502 = container crash, 503 = dependency unavailable, 504 = timeout, 500 = application/init error. Each status points to a different diagnostic layer. Never skip classification.
- **Read the response body before doing anything else.** The `detalhe` field contains the exact exception. Match it to the [root cause database](./blueprints/diagnostic-decision-trees.md#common-root-causes-database).
- **Fix Layer 0 (502 + empty body) before investigating any other error.** A missing CMD in Dockerfile silences all other errors — fixing it unmasks the real stack. See [Cascading Failures](./blueprints/diagnostic-decision-trees.md#cascading-failures-the-invisibility-amplifier-pattern).
- **Verify Dynamic Group before blaming code for IAM errors.** `BmcException 401` from Vault = the function's identity is not authorized, not a code bug.
- **Check function config values before checking secrets.** `oci fn application get --query 'data.config'` shows what the function actually sees — missing keys cause "X is required" before Vault is ever reached.
- **Apply the timeout budget calculator for 504s.** Budget = `FunctionTimeout - 15s (cold start) - HandlerReserve`. SDK calls with default retries commonly exceed this. See [Timeout Budget](./blueprints/diagnostic-decision-trees.md#timeout-budget-calculator).

### ⚠️ Ask First

- **Is the error new or was this function ever working?** New functions commonly hide cascading failures (CMD → httpclient → Vault → OAuth). Previously working functions point to a recent change (config, IAM, network).
- **Is the OCI session token still valid?** `oci session validate --profile poc --auth security_token --local`. An expired session produces misleading auth errors in CLI diagnostics.
- **Is this a cold start or warm invocation?** Cold starts add ~15s overhead. If the function only times out on first call, the timeout budget (not downstream latency) is the issue.
- **Is API Gateway involved?** Some 502s originate at API Gateway, not the function. Use [direct invocation](#direct-function-invocation-bypass-api-gateway) to isolate.
- **What changed since last successful deploy?** Narrowing to the delta (code, config, IAM, Terraform) prevents unnecessary full-stack investigation.

### 🚫 Never Do

**Never assume 502 = code bug without checking CMD and classpath first.**
```
# 🚫 WRONG: jumping to code review on 502
grep -r "NullPointerException" src/

# ✅ CORRECT: check Layer 0 first
grep "^CMD" Dockerfile          # CMD must exist
grep "httpclient-jersey" pom.xml # HTTP provider must exist
```

**Never use `<scope>provided</scope>` for runtime SDK dependencies.**
```xml
<!-- 🚫 WRONG: marks dependency as provided by container (it isn't) -->
<dependency>
  <artifactId>oci-java-sdk-secrets</artifactId>
  <scope>provided</scope>
</dependency>

<!-- ✅ CORRECT: no scope = compile+runtime, dependency is in the fat jar -->
<dependency>
  <artifactId>oci-java-sdk-secrets</artifactId>
</dependency>
```

**Never leave `configure()` without an initError guard — silent crashes produce zero diagnostics.**
```java
// 🚫 WRONG: uncaught exception in configure() kills the container silently
@FnConfiguration
public void configure(RuntimeContext ctx) {
    this.secret = vaultService.getSecret(ctx.getAttributeAsString("SECRET_OCID").get());
}

// ✅ CORRECT: initError pattern surfaces the exception as a 500 with detail
@FnConfiguration
public void configure(RuntimeContext ctx) {
    try {
        this.secret = vaultService.getSecret(ctx.getAttributeAsString("SECRET_OCID").get());
    } catch (Exception e) {
        this.initError = e.getMessage();
    }
}
```

**Never run ARM-native Docker images locally to reproduce OCI crashes.** OCI Functions run on `linux/amd64`. Build and test with `--platform linux/amd64` or use `oci fn function invoke` directly.

---

## Diagnostic Methodology: Classify → Investigate → Eliminate → Fix

### Step 1: Classify the Symptom

Invoke the function and capture the full response:

```bash
curl -s -w "\nHTTP_STATUS: %{http_code}\n" \
  -X POST "https://<gateway>/v1/<path>" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

| HTTP Status | Classification | Likely Layer |
|-------------|---------------|-------------|
| **502** | Container crash | Build/Dockerfile/classpath |
| **503** | Dependency unavailable | Vault/OAuth/external APIs |
| **504** | Timeout exceeded | Retry config/budget |
| **500 + "init failed"** | Initialization error | configure() exception |
| **500 + exception detail** | Code error | Handler logic bug |

For per-status decision trees, see [Decision Trees](./blueprints/diagnostic-decision-trees.md#decision-tree-by-http-status).

---

## OCI CLI Diagnostic Commands

### Check Function Configuration

```bash
oci fn application get \
  --application-id <APP_OCID> \
  --auth security_token \
  --profile poc \
  --query 'data.config'
```

### Check Function Image & Timeout

```bash
oci fn function get \
  --function-id <FUNC_OCID> \
  --auth security_token \
  --profile poc \
  --query 'data.{"image":image,"timeout":"timeout-in-seconds","memory":"memory-in-mbs"}'
```

### Verify Vault Secret Exists and Is Active

```bash
oci vault secret get \
  --secret-id <SECRET_OCID> \
  --auth security_token \
  --profile poc \
  --query 'data.{"state":"lifecycle-state","name":"secret-name"}'
```

### Read Secret Content (verify value)

```bash
oci secrets secret-bundle get \
  --secret-id <SECRET_OCID> \
  --auth security_token \
  --profile poc \
  --query 'data."secret-bundle-content".content'

echo "<base64-value>" | base64 -d
```

### Check IAM Dynamic Group

```bash
oci iam dynamic-group list \
  --compartment-id <TENANCY_OCID> \
  --auth security_token \
  --profile poc \
  --query 'data[*].{"name":"name","rule":"matching-rule"}'
```

### Check IAM Policies

```bash
oci iam policy list \
  --compartment-id <COMPARTMENT_OCID> \
  --auth security_token \
  --profile poc \
  --query 'data[*].{"name":"name","statements":"statements"}'
```

---

## Quick Diagnostic Checklist

When a deployed function fails, check in this order:

1. ☐ **Response body** — Does it contain error details? (`detalhe` field)
2. ☐ **HTTP status** — 502 vs 503 vs 504 vs 500 (different root causes)
3. ☐ **Function config** — Are all required values present? (`oci fn application get`)
4. ☐ **Image version** — Is the latest image deployed? (`oci fn function get`)
5. ☐ **Vault secrets** — Are secrets ACTIVE? Can they be read? (`oci vault secret get`)
6. ☐ **IAM** — Does dynamic group include function? Does policy grant access?
7. ☐ **Network** — Service Gateway for OCI services? NAT Gateway for internet?
8. ☐ **Dependencies** — httpclient-jersey present? All SDKs in pom.xml?
9. ☐ **Dockerfile** — CMD present? Matches func.yaml cmd?
10. ☐ **Timeout** — Budget calculation shows calls fit within function timeout?

---

## Direct Function Invocation (Bypass API Gateway)

When API Gateway adds complexity, invoke the function directly:

```bash
echo '{"httpMethod":"POST","path":"/proxy/store/create","queryParameters":{"store":"1001"}}' | \
  oci fn function invoke \
    --function-id <FUNC_OCID> \
    --body file:///dev/stdin \
    --auth security_token \
    --profile poc
```

This bypasses API Gateway routing and hits the function directly, isolating whether the issue is
in the function or the gateway configuration.

---

## Version Context

**OCI Functions FDK**: Java FDK current stable (`com.fnproject.fn:api` + `runtime`)
**OCI Java SDK**: current stable (`com.oracle.oci.sdk` BOM, group artifacts)
**OCI CLI**: current stable — verify with `oci --version`
**Terraform OCI provider**: `oracle/oci` — see [provisioning-oci-functions](../provisioning-oci-functions/SKILL.md) for version lock

**Key compatibility notes:**
- `oci-java-sdk-common-httpclient-jersey` must be present for any function using the OCI SDK — it is
  not pulled transitively by the BOM
- Cold start overhead is approximately 15s (JVM + FDK init) — this is a fixed platform cost, not
  a code issue

---

## External Resources

- [OCI Functions — Troubleshooting](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionstroubleshooting.htm) — official troubleshooting guide (verified 2026-07-26)
- [OCI Functions — Logging](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsexportingfunctionlogfiles.htm) — enabling and reading function logs (verified 2026-07-26)
- [OCI CLI — Functions commands](https://docs.oracle.com/en-us/iaas/tools/oci-cli/latest/oci_cli_docs/cmdref/fn.html) — complete CLI reference (fn application, fn function, fn function invoke) (verified 2026-07-26)
- [OCI Vault — Secret management](https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Tasks/managingsecrets.htm) — secret lifecycle, states, bundles (verified 2026-07-26)
- [OCI IAM — Dynamic Groups](https://docs.oracle.com/en-us/iaas/Content/Identity/Tasks/managingdynamicgroups.htm) — matching rules and policy authoring (verified 2026-07-26)
