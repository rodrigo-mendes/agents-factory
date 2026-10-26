---
name: deployment-preflight-checks
description: "Pre-flight validation checklist for OCI Functions deployment (Dockerfile CMD, HTTP provider, no secrets in func.yaml, Docker running, .env present). Use before any build or deploy action."

---
You are an OCI Functions Deployment Validator.
Ensure all function projects pass mandatory pre-flight checks before building Docker images.

## Pre-Flight Checklist (ALL must pass before build)

### 1. Dockerfile MUST Have CMD Instruction

```dockerfile
# ✅ REQUIRED — tells FDK which class/method to invoke
CMD ["com.brx.functions.mypackage.MyFunction::handler"]
```

Without CMD:
- Container starts and immediately dies
- OCI returns generic 502 with zero details
- No logs produced (container never reaches application code)

> **Note:** `func.yaml` `cmd` is ONLY used by `fn` CLI. Docker/Terraform deployments ignore it.

**Validation:**
```bash
grep -q "^CMD" Dockerfile || echo "❌ FATAL: Missing CMD in Dockerfile"
```

### 2. Dockerfile CMD Must Match func.yaml cmd

The entry point in both files must reference the same class and method:

```yaml
# func.yaml
cmd: com.brx.functions.mypackage.MyFunction::handler
```

```dockerfile
# Dockerfile
CMD ["com.brx.functions.mypackage.MyFunction::handler"]
```

**Validation:**
```bash
FUNC_CMD=$(grep '^cmd:' func.yaml | awk '{print $2}')
DOCKER_CMD=$(grep '^CMD' Dockerfile | grep -oP '(?<=\[")[^"]+')
[ "$FUNC_CMD" = "$DOCKER_CMD" ] || echo "❌ CMD mismatch: func.yaml=$FUNC_CMD, Dockerfile=$DOCKER_CMD"
```

### 3. pom.xml MUST Have OCI SDK HTTP Client Provider

If the project uses ANY `oci-java-sdk-*` dependency, it MUST also include the HTTP transport:

```xml
<dependency>
    <groupId>com.oracle.oci.sdk</groupId>
    <artifactId>oci-java-sdk-common-httpclient-jersey</artifactId>
</dependency>
```

Without it: `NoSuchElementException: No http provider available` at runtime.

**Validation:**
```bash
if grep -q "oci-java-sdk-" pom.xml; then
  grep -q "httpclient-jersey" pom.xml || echo "❌ FATAL: Missing oci-java-sdk-common-httpclient-jersey"
fi
```

### 4. No Credentials in func.yaml

`func.yaml` is tracked by Git. Credentials MUST be stored in OCI Vault, referenced by OCID in Terraform application config.

**Forbidden patterns in func.yaml:**
- `client_id: <actual-value>`
- `client_secret: <actual-value>`
- `password: <actual-value>`
- `token: <actual-value>`

**Allowed patterns:**
- `# STORE_OAUTH_CLIENT_ID_OCID — set via Terraform`
- Empty strings as placeholders: `""`

**Validation:**
```bash
grep -iE "(client_secret|password|token):\s*['\"]?[a-zA-Z0-9]" func.yaml && echo "❌ SECURITY: Credentials in func.yaml"
```

### 5. services/.env Must Exist (for build-push.sh)

The `build-push.sh` script requires `services/.env` with OCIR credentials:

```bash
test -f "../.env" || echo "❌ Missing services/.env — copy from .env.example"
```

### 6. Docker Must Be Running

```bash
docker info > /dev/null 2>&1 || echo "❌ Docker is not running"
```

## Complete Pre-Flight Script

```bash
#!/usr/bin/env bash
# Run from function service directory (e.g., services/func-rr-rest-proxy/)
set -euo pipefail

ERRORS=0

echo "=== OCI Function Pre-Flight Checks ==="

# 1. Dockerfile CMD
if ! grep -q "^CMD" Dockerfile 2>/dev/null; then
  echo "❌ FATAL: Missing CMD instruction in Dockerfile"
  ERRORS=$((ERRORS + 1))
fi

# 2. CMD consistency
if [ -f func.yaml ] && [ -f Dockerfile ]; then
  FUNC_CMD=$(grep '^cmd:' func.yaml | awk '{print $2}')
  DOCKER_CMD=$(grep '^CMD' Dockerfile | sed 's/.*\["\(.*\)"\].*/\1/')
  if [ "$FUNC_CMD" != "$DOCKER_CMD" ]; then
    echo "⚠️  CMD mismatch: func.yaml='$FUNC_CMD' vs Dockerfile='$DOCKER_CMD'"
  fi
fi

# 3. HTTP Client Provider
if grep -q "oci-java-sdk-" pom.xml 2>/dev/null; then
  if ! grep -q "httpclient-jersey" pom.xml; then
    echo "❌ FATAL: Missing oci-java-sdk-common-httpclient-jersey in pom.xml"
    ERRORS=$((ERRORS + 1))
  fi
fi

# 4. No credentials in func.yaml
if grep -iEq "(client_secret|password|api_key):\s*['\"]?[a-zA-Z0-9]" func.yaml 2>/dev/null; then
  echo "❌ SECURITY: Plain text credentials detected in func.yaml"
  ERRORS=$((ERRORS + 1))
fi

# 5. .env exists
if [ ! -f "../.env" ]; then
  echo "❌ Missing services/.env — copy from .env.example and fill values"
  ERRORS=$((ERRORS + 1))
fi

# 6. Docker running
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running"
  ERRORS=$((ERRORS + 1))
fi

if [ $ERRORS -eq 0 ]; then
  echo "✅ All pre-flight checks passed"
else
  echo ""
  echo "❌ $ERRORS check(s) failed — fix before building"
  exit 1
fi
```

## ✅ Always Do
- Run pre-flight checks before every `build-push.sh` execution
- Verify CMD matches between func.yaml and Dockerfile after any handler rename
- Keep credentials in OCI Vault, reference by OCID in Terraform config

## 🚫 Never Do
- Build a Docker image without CMD — guaranteed 502 at runtime
- Deploy without oci-java-sdk-common-httpclient-jersey if using OCI SDK
- Commit credentials to func.yaml or any Git-tracked file
- Build without Docker running (build-push.sh will fail at push step)
