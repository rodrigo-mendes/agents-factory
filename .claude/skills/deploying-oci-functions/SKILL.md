---
name: deploying-oci-functions
description: "Builds, pushes, deploys, and validates OCI Function images to existing infrastructure using Docker, OCIR, and Terraform. Use when updating function versions, running rollbacks, or validating post-deploy behavior."
---

## Quick Navigation

- [Blueprints & Guardrails](#blueprints--guardrails) — ✅⚠️🚫 patterns
- [Pre-Flight Checks](#pre-flight-checks-mandatory-before-every-build) — mandatory validation script
- [Build & Push Protocol](#build--push-protocol) — docker build + OCIR push
- [Deploy Protocol (Terraform)](#deploy-protocol-terraform) — tfvars update + plan + apply
- [Post-Deploy Validation](#post-deploy-validation-smoke-test) — smoke tests + success criteria
- [Rollback Protocol](#rollback-protocol) — revert and verify
- [Common Issues](#common-issues-during-deploy) — error table
- [Evaluation Scenarios](./blueprints/evaluation-scenarios.md) — canonical, edge, misuse test cases
- [Version Context](#version-context)
- [External Resources](#external-resources)

---

## Blueprints & Guardrails

### ✅ Always Do

- **Run pre-flight checks before every build, without exception.** The pre-flight script catches CMD absence, missing httpclient-jersey, and credential leaks before a failed image is pushed.
- **Build with `--platform linux/amd64`.** OCI Functions run on `linux/amd64`. Images built for ARM (Apple Silicon default) produce exec format errors at runtime.
- **Increment the version tag on every build.** Use monotonically increasing semantic versions (patch for dev iterations: `0.0.N`). Never reuse a tag.
- **Run `terraform plan` and confirm exactly 1 resource change before applying.** A clean version bump changes only the `image` attribute of `oci_functions_function`. More changes require investigation.
- **Smoke test after every deploy.** HTTP 200 or 400 (business validation) = function is alive. HTTP 502/500-initError = deploy failed, trigger rollback.

### ⚠️ Ask First

- **Using `-auto-approve` on `terraform apply`.** Safe for single-function image bumps where plan confirms 1 change. Ask before using when plan shows multiple changes or in shared environments.
- **Rollback strategy when smoke test fails.** Default is revert `terraform.tfvars` to the previous tag and re-apply. If the previous image was also bad, ask before rolling forward vs. rebuilding.
- **Managing multiple functions in one apply.** A single `terraform apply` can deploy all functions at once. Ask whether to deploy all or `-target` a single function to reduce blast radius.
- **OCI session expiry during long applies.** Session tokens last ~1h. For applies with many resources (dashboards, networking), validate session first: `oci session validate --profile poc --auth security_token --local`. Ask before starting a large apply near expiry.
- **Corporate proxy configuration.** The build script strips proxy vars (`HTTP_PROXY`, `HTTPS_PROXY`) during `docker build`. Confirm this behavior is desired if running in a different network environment.

### 🚫 Never Do

**Never reuse a version tag, even in development.**
```bash
# 🚫 WRONG: rebuilding with the same tag after a failed build
./build-push.sh 0.0.15   # first attempt failed
./build-push.sh 0.0.15   # reusing same tag — overwrites OCIR, loses audit trail

# ✅ CORRECT: always increment
./build-push.sh 0.0.16   # next patch version
```

**Never build without running pre-flight first.**
```bash
# 🚫 WRONG: skipping pre-flight to save time
docker build --platform linux/amd64 -t <image> .

# ✅ CORRECT: pre-flight → build
bash scripts/preflight.sh && ./build-push.sh <version>
```

**Never commit `.env` or any file containing OCIR credentials.**
```bash
# 🚫 WRONG: .env in repository (contains OCIR_USERNAME, OCIR_PASSWORD)
git add services/.env

# ✅ CORRECT: .env is git-ignored; source from .env.example; credentials from CI secrets or Vault
echo ".env" >> .gitignore
```

**Never apply Terraform when plan shows unexpected resource changes.**
```bash
# 🚫 WRONG: apply without reviewing the plan
terraform apply -auto-approve   # when plan showed 5 changes

# ✅ CORRECT: investigate unexpected changes before applying
terraform plan                  # review each change
# If only function image needs updating:
terraform apply -target=oci_functions_function.this -auto-approve
```

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
  echo "   Fix: Add CMD [\"com.example.<package>.<Class>::handler\"]"
  ERRORS=$((ERRORS + 1))
fi

# 2. OCI SDK HTTP provider present (if SDK used)
if grep -q "oci-java-sdk-" pom.xml; then
  if ! grep -q "httpclient-jersey" pom.xml; then
    echo "❌ FATAL: Missing oci-java-sdk-common-httpclient-jersey in pom.xml"
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
  echo "❌ Missing ../.env — copy from .env.example"
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

### Standard Build

```bash
# From the function's service directory
cd services/<function-name>/

# Build with explicit version tag
./build-push.sh <version>
# Example: ./build-push.sh 0.0.12
```

**build-push.sh behavior:**
1. Loads `services/.env` for OCIR credentials
2. Logs into OCIR (`docker login`)
3. Reads function name from `func.yaml` `name:` field
4. Builds with `docker build --platform linux/amd64` (proxy vars stripped)
5. Pushes to `<region>.ocir.io/<namespace>/<repo>/<function-name>:<version>`

### Corporate Proxy Note

The build script strips proxy environment variables during `docker build`:
```bash
env -u HTTP_PROXY -u HTTPS_PROXY -u http_proxy -u https_proxy docker build ...
```

Required when a corporate proxy (e.g., Zscaler) interferes with Docker layer downloads.

---

## Deploy Protocol (Terraform)

### Step 1: Update terraform.tfvars

Edit `infra/environments/dev/terraform.tfvars` to reference the new image tag:

```hcl
# Before
rest_proxy_image = "<region>.ocir.io/<namespace>/<repo>/func-rr-rest-proxy:0.0.11"

# After
rest_proxy_image = "<region>.ocir.io/<namespace>/<repo>/func-rr-rest-proxy:0.0.12"
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

If plan shows MORE than 1 change, investigate before applying.

### Step 3: Apply

```bash
terraform apply -auto-approve
```

> **OCI session expiry mid-apply** — `SecurityToken` auth lasts ~1h. Before a long apply, validate:
> `oci session validate --profile poc --auth security_token --local`. Re-auth if near expiry:
> `oci session authenticate --profile poc --region <region>`. In CI/CD prefer InstancePrincipal.
> If it dies mid-apply, re-auth and re-run `apply` (idempotent); see `managing-terraform-state`
> for partial state recovery.

---

## Post-Deploy Validation (Smoke Test)

### Smoke Test Sequence

```bash
# 1. Wait for cold start readiness (~5s)
sleep 5

# 2. Health check
curl -s -o /dev/null -w "HTTP: %{http_code}\n" "https://<gateway>/v1/health"
# Expected: 200

# 3. Business endpoint test
curl -s -w "\nHTTP: %{http_code}\n" \
  -X POST "https://<gateway>/v1/<path>?<params>" \
  -H "Content-Type: application/json" \
  -d '{}' | python3 -m json.tool
```

### Status Code Interpretation

| HTTP Status | Meaning | Action |
|-------------|---------|--------|
| **200** | Success | Deploy complete |
| **400** | Business validation error | Function works, input was invalid |
| **500 + initError** | Init failed | Read `detalhe` field for root cause |
| **502** | Container crash | Check CMD, classpath, dependencies |
| **503** | Dependency unavailable | Check Vault access, external APIs |
| **504** | Timeout | Check timeout budget, retry config |

**Deploy is successful** if the function returns 200 or 400.
**Deploy failed** if it returns 502 or 500 with "Function init failed".

---

## Rollback Protocol

### When smoke test fails:

```bash
# Step 1: Revert image tag in terraform.tfvars
rest_proxy_image = "<region>.ocir.io/<namespace>/<repo>/func-rr-rest-proxy:0.0.11"

# Step 2: Apply rollback
cd infra/environments/dev/
terraform apply -auto-approve

# Step 3: Verify rollback
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

---

## Common Issues During Deploy

| Issue | Symptom | Fix |
|-------|---------|-----|
| Docker not logged in | `denied: Anonymous users` during push | Re-run `docker login` or check .env |
| Wrong platform | Function crashes (exec format error) | Ensure `PLATFORM=linux/amd64` |
| Stale Docker layer cache | Old code deployed despite changes | `docker build --no-cache ...` |
| Terraform state lock | `Error acquiring the state lock` | Wait or force-unlock (carefully) |
| OCI CLI session expired | Terraform auth fails | `oci session authenticate --profile poc` |

---

## Version Context

**Docker**: 20.10+ required for `--platform linux/amd64` cross-platform builds
**OCI CLI**: current stable — verify with `oci --version`
**Terraform**: >= 1.5 (required for `oci` provider features used by this project)
**oracle/oci Terraform provider**: current stable — declared in `infra/versions.tf`
**OCI Functions API**: REST API version `20181201` (stable)

**Breaking change notes:**
- Docker `--platform` flag: requires BuildKit (enabled by default in Docker 23+); on older Docker
  versions set `DOCKER_BUILDKIT=1`
- Terraform `oci_functions_function.image` attribute: immutable at plan time — any tag change
  forces an in-place update (not destroy/create); this is the expected behavior

---

## External Resources

- [OCI Functions — Deploying Functions](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionsdeployingfunctions.htm) — official deploy guide (verified 2026-07-26)
- [OCI Container Registry — Pushing Images](https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm) — OCIR docker push reference (verified 2026-07-26)
- [Terraform OCI Provider — oci_functions_function](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/functions_function) — resource reference (verified 2026-07-26)
- [Docker Buildx — Multi-platform builds](https://docs.docker.com/build/building/multi-platform/) — `--platform linux/amd64` reference (verified 2026-07-26)
- [OCI Functions — Pre-built images and Dockerfile](https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscustomdockerfiles.htm) — Dockerfile requirements for OCI Functions (verified 2026-07-26)
- [OCI CLI — Session authentication](https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm) — token-based auth for CLI (verified 2026-07-26)
