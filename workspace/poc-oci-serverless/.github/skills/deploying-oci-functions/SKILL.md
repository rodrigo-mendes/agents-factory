# Skill: Deploying OCI Functions

**Description:** Builds, pushes, deploys, and validates OCI Function images to existing infrastructure using Docker, OCIR, and Terraform.

**Use when:**
- Building and pushing function Docker images to OCIR
- Deploying function version updates via Terraform
- Running post-deployment smoke tests
- Rolling back to previous versions
- Running pre-flight checks before build

---

## Pre-Flight Checks (MANDATORY before every build)

Run these validations from the function's service directory:

```bash
#!/usr/bin/env bash
# Pre-flight validation script
ERRORS=0

echo "=== Pre-Flight Checks ==="

# 1. Dockerfile CMD exists
if ! grep -q "^CMD" Dockerfile; then
  echo "❌ FATAL: Missing CMD in Dockerfile"
  echo "   Fix: Add CMD [\"com.brx.functions.<package>.<Class>::handler\"]"
  ERRORS=$((ERRORS + 1))
fi

# 2. OCI SDK HTTP provider present (if SDK used)
if grep -q "oci-java-sdk-" pom.xml; then
  if ! grep -q "httpclient-jersey" pom.xml; then
    echo "❌ FATAL: Missing oci-java-sdk-common-httpclient-jersey in pom.xml"
    echo "   Fix: Add <dependency><groupId>com.oracle.oci.sdk</groupId><artifactId>oci-java-sdk-common-httpclient-jersey</artifactId></dependency>"
    ERRORS=$((ERRORS + 1))
  fi
fi

# 3. CMD consistency with func.yaml
if [ -f func.yaml ]; then
  FUNC_CMD=$(grep '^cmd:' func.yaml | awk '{print $2}')
  DOCKER_CMD=$(grep '^CMD' Dockerfile | sed 's/CMD \["\(.*\)"\]/\1/')
  if [ -n "$FUNC_CMD" ] && [ -n "$DOCKER_CMD" ] && [ "$FUNC_CMD" != "$DOCKER_CMD" ]; then
    echo "⚠️  CMD mismatch: func.yaml='$FUNC_CMD' vs Dockerfile='$DOCKER_CMD'"
  fi
fi

# 4. No secrets in func.yaml
if grep -iEq "(client_secret|password|api_key|token):\s*['\"]?[a-zA-Z0-9]" func.yaml 2>/dev/null; then
  echo "❌ SECURITY: Credentials in func.yaml — move to OCI Vault"
  ERRORS=$((ERRORS + 1))
fi

# 5. services/.env exists
if [ ! -f "../.env" ]; then
  echo "❌ Missing ../. env — copy from .env.example"
  ERRORS=$((ERRORS + 1))
fi

# 6. Docker running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker Desktop is not running"
  ERRORS=$((ERRORS + 1))
fi

[ $ERRORS -eq 0 ] && echo "✅ All checks passed" || { echo "❌ $ERRORS failed"; exit 1; }
```

---

## Build & Push Protocol

### Standard Build (using build-push.sh)

```bash
# From the function's service directory
cd services/<function-name>/

# Build with explicit version tag
./build-push.sh <version>

# Example:
./build-push.sh 0.0.12
```

**build-push.sh behavior:**
1. Loads `services/.env` for OCIR credentials
2. Logs into OCIR (`docker login`)
3. Reads function name from `func.yaml` `name:` field
4. Builds with `docker build --platform linux/amd64` (proxy vars stripped)
5. Pushes to `${OCIR_REGION}.ocir.io/${OCIR_NAMESPACE}/${OCIR_REPO}/${FUNC_NAME}:${TAG}`

### Image URI Format

```
gru.ocir.io/<namespace>/<repo>/<function-name>:<version>
```

Example: `gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-rr-rest-proxy:0.0.11`

### Corporate Proxy Note

The build script strips proxy environment variables during `docker build`:
```bash
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy docker build ...
```

This is required when corporate proxy interferes with Docker builds (e.g., Zscaler proxy `zsuser.eci.geci`).

---

## Deploy Protocol (Terraform)

### Step 1: Update terraform.tfvars

Edit `infra/environments/dev/terraform.tfvars` to reference the new image tag:

```hcl
# Before
rest_proxy_image = "gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-rr-rest-proxy:0.0.11"

# After
rest_proxy_image = "gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-rr-rest-proxy:0.0.12"
```

### Step 2: Terraform Plan (verify single change)

```bash
cd infra/environments/dev/
terraform plan
```

**Expected output:** Exactly 1 resource change (the function's `image` attribute):
```
~ resource "oci_functions_function" "this" {
    ~ image = "...:0.0.11" -> "...:0.0.12"
  }

Plan: 0 to add, 1 to change, 0 to destroy.
```

⚠️ If plan shows MORE than 1 change, investigate before applying.

### Step 3: Apply

```bash
terraform apply -auto-approve
```

---

## Post-Deploy Validation (Smoke Test)

### Step 1: Wait for cold start readiness (~5s)

```bash
sleep 5
```

### Step 2: Health check (if endpoint exists)

```bash
curl -s -o /dev/null -w "HTTP: %{http_code}\n" \
  "https://<gateway>/v1/health"
# Expected: 200
```

### Step 3: Business endpoint test

```bash
curl -s -w "\nHTTP: %{http_code}\n" \
  -X POST "https://<gateway>/v1/<path>?<params>" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

### Status Code Interpretation

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| **200** | ✅ Success | Deploy complete |
| **400** | ✅ Business validation error | Function works, input was invalid |
| **500 + initError** | ❌ Init failed | Read `detalhe` field for root cause |
| **502** | ❌ Container crash | Check CMD, classpath, dependencies |
| **503** | ❌ Dependency unavailable | Check Vault access, external APIs |
| **504** | ❌ Timeout | Check timeout budget, retry config |

### Success Criteria

A deploy is **successful** if the function returns:
- 200 (success), OR
- 400 (business validation — proves function is running and processing)

A deploy **failed** if:
- 502 (container crash)
- 500 with "Function init failed" (initialization error)

---

## Rollback Protocol

If validation fails:

### Step 1: Revert image tag

```bash
# In infra/environments/dev/terraform.tfvars — revert to previous version
rest_proxy_image = "gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-rr-rest-proxy:0.0.11"
```

### Step 2: Apply rollback

```bash
cd infra/environments/dev/
terraform apply -auto-approve
```

### Step 3: Verify rollback

```bash
curl -s -o /dev/null -w "HTTP: %{http_code}\n" "https://<gateway>/v1/<path>"
# Should return previous behavior
```

---

## Version Tagging Strategy

| Environment | Format | Example |
|-------------|--------|---------|
| Development | 0.0.X (patch) | 0.0.12 |
| Staging | 0.X.0 (minor) | 0.1.0 |
| Production | X.0.0 (major) | 1.0.0 |

### Tagging Rules

- NEVER reuse a version tag (even in dev)
- Always increment from current version in func.yaml/tfvars
- Use monotonically increasing numbers
- For debugging iterations, use patch versions (0.0.N)

---

## End-to-End Deploy Workflow (Summary)

```
1. Pre-flight checks → PASS
2. ./build-push.sh <version> → Image pushed to OCIR
3. Update terraform.tfvars → New image reference
4. terraform plan → Verify single change
5. terraform apply → Function updated
6. Smoke test → Verify HTTP status
7. If fail → Rollback to previous version
```

---

## Common Issues During Deploy

| Issue | Symptom | Fix |
|-------|---------|-----|
| Docker not logged in | `denied: Anonymous users` during push | Re-run `docker login` or check .env |
| Wrong platform | Function crashes (exec format error) | Ensure `PLATFORM=linux/amd64` |
| Stale Docker layer cache | Old code deployed despite changes | `docker build --no-cache ...` |
| Terraform state lock | `Error acquiring the state lock` | Wait or force-unlock (careful!) |
| OCI CLI session expired | Terraform auth fails | `oci session authenticate --profile poc` |

---

## Known Error Patterns Database (Post-Deploy Failures)

Use this table when P5 (smoke test) fails. Match the error signal to identify root cause and fix action.

### Auto-Fixable Errors (code/config — can be fixed and redeployed)

| Error Signal | How to Detect | Root Cause | Fix Action | Time to Fix |
|-------------|---------------|-----------|------------|-------------|
| 502 + empty response body | `curl` returns 502, no JSON | Missing CMD in Dockerfile | Add `CMD ["class::handler"]` to Dockerfile | 2 min |
| 500 + "No http provider available" | `detalhe` contains "NoSuchElementException" | Missing httpclient-jersey in pom.xml | Add `oci-java-sdk-common-httpclient-jersey` dependency | 3 min |
| 500 + "JAXBContext" exception | `detalhe` contains "JAXBContext" | JAXB init crashes in Java 17 without --add-opens | Wrap JAXB init in try-catch (non-fatal) OR add `--add-opens` to Dockerfile | 5 min |
| 500 + "X is required" | `detalhe` contains "is required" | Missing config key in Terraform app config | Add key to `oci_functions_application.config` in Terraform | 5 min |
| 500 + "@FnConfiguration called twice" or NPE in init | Double init, fields partially initialized | Method named `config()` instead of `configure()` | Rename to `configure()` with `@Override` | 3 min |
| 500 + "ClassNotFoundException" | `detalhe` contains "ClassNotFoundException" | Dependency scope wrong or missing | Check pom.xml — remove `<scope>provided</scope>` from runtime deps | 3 min |

### Infra-Fixable Errors (require Terraform or OCI CLI — cannot auto-fix in deploy cycle)

| Error Signal | How to Detect | Root Cause | Fix Action | Delegate To |
|-------------|---------------|-----------|------------|-------------|
| 503 + "OAuth2...status: 401" | `detalhe` contains "status: 401" | Vault secrets null or invalid | Verify secrets via `oci secrets secret-bundle get` → update Vault content | @oci-terraform |
| 503 + "OAuth2...status: 400" | `detalhe` contains "status: 400" | Wrong OAuth scope or token URL | Check STORE_OAUTH_SCOPE, STORE_OAUTH_TOKEN_URL in app config | @oci-terraform |
| 503 + "connect timed out" to OCI | `detalhe` contains "connect timed out" | Missing Service Gateway in VCN | Add `oci_core_service_gateway` + route table entry | @oci-terraform |
| 503 + "connect timed out" to internet | `detalhe` + target is non-OCI URL | Missing NAT Gateway | Add `oci_core_nat_gateway` + route table entry | @oci-terraform |
| 503 + "BmcException 401/403" | `detalhe` contains "BmcException" + 401/403 | IAM policy missing for function | Add IAM policy for dynamic group | @oci-terraform |
| 504 + no response (timeout) | No response after function timeout | SDK retry budget exceeds function timeout | Reduce MaxAttempts/timeouts OR increase function timeout_in_seconds | @oci-terraform (timeout) or code fix |
| 503 + "BmcException 404" on secret | `detalhe` contains "404" + secret OCID | Secret OCID incorrect or deleted | Verify/recreate secret in Vault | @oci-terraform |

### Escalation Errors (require investigation — no known auto-fix)

| Error Signal | How to Detect | Investigation Path |
|-------------|---------------|--------------------|
| 502 + function worked before, no code change | Image tag correct in tfvars vs OCIR | Check if image was overwritten (tag reuse), check OCI platform issues |
| 500 + novel exception class | Unknown exception in `detalhe` | Read source code, reproduce locally with FnTestingRule |
| 503 + intermittent (works sometimes) | Same request succeeds/fails randomly | Check rate limits (429 retried as 503), connection pool exhaustion, or cold start race |
| 504 + downstream confirmed fast | External API <1s but function times out | Check if function timeout was reduced, or SDK retries are in a loop |

### Error Pattern Matching Algorithm

```
1. GET response body (JSON)
2. EXTRACT: http_status, erro, detalhe
3. MATCH by priority:
   a. http_status == 502 AND body is empty → CMD missing
   b. detalhe CONTAINS "No http provider" → httpclient-jersey
   c. detalhe CONTAINS "is required" → missing config key
   d. detalhe CONTAINS "OAuth2" + "401" → Vault credentials
   e. detalhe CONTAINS "connect timed out" → network/gateway
   f. detalhe CONTAINS "BmcException" + extract status code → IAM or resource issue
   g. http_status == 504 → timeout budget
   h. NO MATCH → escalate to user with full error details
```
