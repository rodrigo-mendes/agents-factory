#!/usr/bin/env bash
# =============================================================================
# OCI Function Pre-Flight Checks
# Run from a function's service directory (e.g., services/func-rr-rest-proxy/)
# Or pass the function directory as argument: ./scripts/preflight.sh services/func-rr-rest-proxy
# =============================================================================
set -euo pipefail

# Resolve target directory
if [[ -n "${1:-}" ]]; then
  TARGET_DIR="$1"
else
  TARGET_DIR="."
fi

if [[ ! -f "${TARGET_DIR}/func.yaml" ]]; then
  echo "ERROR: No func.yaml found in ${TARGET_DIR}"
  echo "Usage: $0 [path/to/function/directory]"
  exit 1
fi

ERRORS=0
WARNINGS=0

echo "=== OCI Function Pre-Flight Checks ==="
echo "    Target: ${TARGET_DIR}"
echo ""

# ---------------------------------------------------------------------------
# 1. Dockerfile CMD exists
# ---------------------------------------------------------------------------
if [[ ! -f "${TARGET_DIR}/Dockerfile" ]]; then
  echo "❌ FATAL: No Dockerfile found"
  ERRORS=$((ERRORS + 1))
elif ! grep -q "^CMD" "${TARGET_DIR}/Dockerfile"; then
  echo "❌ FATAL: Missing CMD instruction in Dockerfile"
  echo "   Without CMD, container starts and dies → 502 with zero logs"
  echo "   Fix: Add CMD [\"com.brx.functions.<package>.<Class>::handler\"]"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ Dockerfile CMD present"
fi

# ---------------------------------------------------------------------------
# 2. CMD consistency between func.yaml and Dockerfile
# ---------------------------------------------------------------------------
if [[ -f "${TARGET_DIR}/func.yaml" ]] && [[ -f "${TARGET_DIR}/Dockerfile" ]]; then
  FUNC_CMD=$(grep '^cmd:' "${TARGET_DIR}/func.yaml" 2>/dev/null | awk '{print $2}' || true)
  DOCKER_CMD=$(grep '^CMD' "${TARGET_DIR}/Dockerfile" 2>/dev/null | sed 's/CMD \["\(.*\)"\]/\1/' || true)
  if [[ -n "$FUNC_CMD" ]] && [[ -n "$DOCKER_CMD" ]] && [[ "$FUNC_CMD" != "$DOCKER_CMD" ]]; then
    echo "⚠️  CMD mismatch: func.yaml='${FUNC_CMD}' vs Dockerfile='${DOCKER_CMD}'"
    WARNINGS=$((WARNINGS + 1))
  fi
fi

# ---------------------------------------------------------------------------
# 3. OCI SDK HTTP provider present (if SDK used)
# ---------------------------------------------------------------------------
if [[ -f "${TARGET_DIR}/pom.xml" ]]; then
  if grep -q "oci-java-sdk-" "${TARGET_DIR}/pom.xml"; then
    if ! grep -q "httpclient-jersey" "${TARGET_DIR}/pom.xml"; then
      echo "❌ FATAL: Missing oci-java-sdk-common-httpclient-jersey in pom.xml"
      echo "   OCI SDK 3.x requires explicit HTTP transport provider"
      echo "   Without it: 'NoSuchElementException: No http provider available' at runtime"
      echo "   Fix: Add <dependency><groupId>com.oracle.oci.sdk</groupId>"
      echo "        <artifactId>oci-java-sdk-common-httpclient-jersey</artifactId></dependency>"
      ERRORS=$((ERRORS + 1))
    else
      echo "✅ OCI SDK HTTP provider (httpclient-jersey) present"
    fi
  fi
fi

# ---------------------------------------------------------------------------
# 4. No credentials in func.yaml
# ---------------------------------------------------------------------------
if [[ -f "${TARGET_DIR}/func.yaml" ]]; then
  if grep -iEq "(client_secret|password|api_key|private_key):\s*['\"]?[a-zA-Z0-9]" "${TARGET_DIR}/func.yaml" 2>/dev/null; then
    echo "❌ SECURITY: Plain text credentials detected in func.yaml"
    echo "   func.yaml is tracked by Git — credentials MUST be in OCI Vault"
    echo "   Fix: Remove value, store in Vault, reference by OCID in Terraform app config"
    ERRORS=$((ERRORS + 1))
  else
    echo "✅ No credentials in func.yaml"
  fi
fi

# ---------------------------------------------------------------------------
# 5. services/.env exists (for build-push.sh)
# ---------------------------------------------------------------------------
ENV_FILE="${TARGET_DIR}/../.env"
if [[ ! -f "${ENV_FILE}" ]]; then
  echo "❌ Missing services/.env (required by build-push.sh)"
  echo "   Fix: cp services/.env.example services/.env && fill OCIR credentials"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ services/.env exists"
fi

# ---------------------------------------------------------------------------
# 6. Docker is running
# ---------------------------------------------------------------------------
if ! docker info > /dev/null 2>&1; then
  echo "❌ Docker is not running"
  echo "   Fix: Start Docker Desktop"
  ERRORS=$((ERRORS + 1))
else
  echo "✅ Docker is running"
fi

# ---------------------------------------------------------------------------
# 7. initError pattern in handler (warning only)
# ---------------------------------------------------------------------------
HANDLER_FILES=$(find "${TARGET_DIR}/src/main/java" -name "*.java" -exec grep -l "extends.*Function" {} \; 2>/dev/null || true)
if [[ -n "$HANDLER_FILES" ]]; then
  HAS_INIT_ERROR=false
  for f in $HANDLER_FILES; do
    if grep -q "initError" "$f"; then
      HAS_INIT_ERROR=true
      break
    fi
  done
  if [[ "$HAS_INIT_ERROR" == "false" ]]; then
    echo "⚠️  No initError pattern found in handler"
    echo "   Without it, configure() exceptions kill the container with zero diagnostics"
    echo "   Recommended: Add 'private String initError;' + try-catch in configure()"
    WARNINGS=$((WARNINGS + 1))
  else
    echo "✅ initError pattern present in handler"
  fi
fi

# ---------------------------------------------------------------------------
# 8. Timeout budget sanity (warning only)
# ---------------------------------------------------------------------------
if [[ -f "${TARGET_DIR}/func.yaml" ]]; then
  FUNC_TIMEOUT=$(grep '^timeout:' "${TARGET_DIR}/func.yaml" 2>/dev/null | awk '{print $2}' || echo "30")
  if [[ "$FUNC_TIMEOUT" -le 30 ]] 2>/dev/null; then
    if [[ -f "${TARGET_DIR}/pom.xml" ]] && grep -q "oci-java-sdk-" "${TARGET_DIR}/pom.xml"; then
      echo "⚠️  Timeout ${FUNC_TIMEOUT}s may be insufficient for OCI SDK calls (default SDK read timeout is 60s)"
      echo "   Recommended: Set timeout to 60s+ and configure SDK readTimeoutMillis < function timeout"
      WARNINGS=$((WARNINGS + 1))
    fi
  fi
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""
echo "─────────────────────────────────────"
if [[ $ERRORS -eq 0 ]] && [[ $WARNINGS -eq 0 ]]; then
  echo "✅ All pre-flight checks passed — safe to build"
  exit 0
elif [[ $ERRORS -eq 0 ]]; then
  echo "⚠️  ${WARNINGS} warning(s) — build allowed but review recommended"
  exit 0
else
  echo "❌ ${ERRORS} error(s), ${WARNINGS} warning(s) — FIX BEFORE BUILDING"
  exit 1
fi
