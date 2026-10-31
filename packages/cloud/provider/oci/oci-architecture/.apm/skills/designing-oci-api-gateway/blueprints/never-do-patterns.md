### 🚫 Never Do

**1. Anti-Pattern: Functions Exposed Without API Gateway**

Functions directly accessible via invoke endpoint have zero rate limiting, zero WAF, and zero centralized auth.

**Detection**:
```bash
# Check if Function invoke endpoint is publicly accessible
INVOKE_EP=$(oci fn function get --function-id <func_ocid> | jq -r '.data["invoke-endpoint"]')
curl "$INVOKE_EP/actions/invoke"
# If this returns 401/200 (not timeout), the Function IS exposed to the internet
```

**Why it is prohibited**: A single bot can trigger unlimited invocations causing cost explosion.
**Actual impact**: Cost overrun (invocations without limit), DDoS, unauthorized data access.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Concepts/apigatewayoverview.htm

---

**2. Anti-Pattern: Wildcard CORS with Credentials Enabled**

`allowed_origins = ["*"]` combined with `is_allow_credentials_enabled = true` violates the CORS specification and enables CSRF from ANY domain.

**Correct approach**: Always list explicit origins when credentials are enabled.

**Why it is prohibited**: Violates CORS spec; allows cross-site request forgery.
**Actual impact**: CSRF attacks, credential theft, session hijacking via malicious origins.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingcors.htm

---

**3. Anti-Pattern: No Rate Limiting in Production**

A deployment without `rate_limiting` block allows unlimited requests, exhausting backend capacity and generating uncontrolled costs on pay-per-invoke services.

**Correct approach**: Always configure `rate_limiting` at deployment level with `rate_key = CLIENT_IP` as minimum baseline.

**Why it is prohibited**: Single client/attacker can consume all backend capacity, throttle legitimate users, and generate uncontrolled costs.
**Actual impact**: Cost overrun, service degradation for all clients, DDoS amplification.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingratelmiting.htm

---

**4. Anti-Pattern: Single Monolithic Deployment with All Routes**

30+ routes in a single Deployment creates high blast radius — changes to one route redeploy all.

**Correct approach**: One Deployment per domain/bounded context (e.g., `/v1/orders`, `/v1/users`, `/v1/products` as separate deployments). Flag deployments with >20 routes.

**Why it is prohibited**: Prevents independent versioning and team ownership.
**Actual impact**: High blast radius on changes, team coupling, versioning difficulty.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaycreatingdeployment.htm

---

**5. Anti-Pattern: Hardcoded Backend IPs in Deployments**

`HTTP_BACKEND` with hardcoded IPs (e.g., `http://10.0.1.42:8080/orders`) breaks on environment promotion.

**Correct approach**: Use `ORACLE_FUNCTIONS_BACKEND` (abstracts URL — uses function_id) or DNS-based discovery for HTTP backends.

**Why it is prohibited**: IPs change between environments, requiring manual URL changes.
**Actual impact**: Environment promotion failures, manual URL changes, operational overhead.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewayaddingroutes.htm

---

**6. Anti-Pattern: Logging Disabled in Production**

**Detection**:
```bash
oci api-gateway deployment get --deployment-id <dep_ocid> | \
  jq '.data.specification.logging_policies | {access: .access_log.is_enabled, execution: .execution_log.is_enabled}'
# Flag if any value is false or null
```

**Why it is prohibited**: Without logs, incident diagnosis is blind, compliance audit trails are missing.
**Actual impact**: Blind to incidents, compliance violations (missing audit trail), slow MTTR.
**Source**: https://docs.oracle.com/en-us/iaas/Content/APIGateway/Tasks/apigatewaymanaginglogs.htm

---

