#!/usr/bin/env bash
# ==============================================================================
# Terraform Variable Validation Tests (Legacy Shell Script)
# ==============================================================================
# Tests that variable validation blocks correctly reject invalid inputs.
# Compatible with Terraform >= 1.5 (uses terraform plan for validation).
#
# PREFERRED: For Terraform >= 1.6, use native tests instead:
#   cd infra/environments/dev && terraform test
#
# This script is maintained for environments without terraform test support.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/../environments/dev" && pwd)"

cd "$INFRA_DIR"

# ==============================================================================
# Test Framework
# ==============================================================================

PASS=0
FAIL=0
TOTAL=0

# Valid baseline variables (used as defaults in all tests)
VALID_VARS=(
  -var 'tenancy_ocid=ocid1.tenancy.oc1..test'
  -var 'compartment_ocid=ocid1.compartment.oc1..test'
  -var 'compartment_name=test-compartment'
  -var 'region=sa-saopaulo-1'
  -var 'api_handler_image=gru.ocir.io/namespace/repo/api-handler:latest'
  -var 'api_facade_image=gru.ocir.io/namespace/repo/api-facade:latest'
  -var 'rest_proxy_image=gru.ocir.io/namespace/repo/rest-proxy:latest'
)

run_test() {
  local test_name="$1"
  local expected_error="$2"
  shift 2
  local extra_vars=("$@")

  TOTAL=$((TOTAL + 1))

  # Run terraform plan with valid baseline + overridden variable
  local output
  output=$(terraform plan "${VALID_VARS[@]}" "${extra_vars[@]}" -input=false -lock=false 2>&1) || true

  if echo "$output" | grep -qi "$expected_error"; then
    PASS=$((PASS + 1))
    echo "  ✓ $test_name"
  else
    FAIL=$((FAIL + 1))
    echo "  ✗ $test_name"
    echo "    Expected error containing: $expected_error"
    echo "    Got: $(echo "$output" | grep -i 'error' | head -3)"
  fi
}

# ==============================================================================
# Tests: Required Variables
# ==============================================================================

echo ""
echo "━━━ Required Variable Validations ━━━"

run_test "rejects invalid tenancy_ocid" \
  "tenancy_ocid must be a valid tenancy OCID" \
  -var 'tenancy_ocid=invalid-ocid'

run_test "rejects empty tenancy_ocid" \
  "tenancy_ocid must be a valid tenancy OCID" \
  -var 'tenancy_ocid='

run_test "rejects compartment OCID as tenancy_ocid" \
  "tenancy_ocid must be a valid tenancy OCID" \
  -var 'tenancy_ocid=ocid1.compartment.oc1..wrongtype'

run_test "rejects invalid compartment_ocid" \
  "compartment_ocid must be a valid compartment OCID" \
  -var 'compartment_ocid=not-a-valid-ocid'

run_test "rejects empty compartment_ocid" \
  "compartment_ocid must be a valid compartment OCID" \
  -var 'compartment_ocid='

run_test "rejects tenancy OCID as compartment_ocid" \
  "compartment_ocid must be a valid compartment OCID" \
  -var 'compartment_ocid=ocid1.tenancy.oc1..wrongtype'

run_test "rejects DockerHub image as api_handler_image" \
  "api_handler_image must be a valid OCIR URI" \
  -var 'api_handler_image=docker.io/library/nginx:latest'

run_test "rejects non-OCIR image as api_facade_image" \
  "api_facade_image must be a valid OCIR URI" \
  -var 'api_facade_image=my-registry.com/namespace/repo:tag'

run_test "rejects non-OCIR image as rest_proxy_image" \
  "rest_proxy_image must be a valid OCIR URI" \
  -var 'rest_proxy_image=my-registry.com/namespace/repo:tag'

# ==============================================================================
# Tests: Functions Variables
# ==============================================================================

echo ""
echo "━━━ Functions Variable Validations ━━━"

run_test "rejects invalid function_shape" \
  "function_shape must be one of" \
  -var 'function_shape=INVALID_SHAPE'

run_test "rejects lowercase function_shape" \
  "function_shape must be one of" \
  -var 'function_shape=generic_x86'

# ==============================================================================
# Tests: API Gateway Variables
# ==============================================================================

echo ""
echo "━━━ API Gateway Variable Validations ━━━"

run_test "rejects invalid api_gateway_endpoint_type" \
  "api_gateway_endpoint_type must be PUBLIC or PRIVATE" \
  -var 'api_gateway_endpoint_type=INTERNAL'

run_test "rejects lowercase api_gateway_endpoint_type" \
  "api_gateway_endpoint_type must be PUBLIC or PRIVATE" \
  -var 'api_gateway_endpoint_type=public'

run_test "rejects rate_limit below minimum (-1)" \
  "rate_limit_requests_per_second must be between 0 and 10000" \
  -var 'rate_limit_requests_per_second=-1'

run_test "rejects rate_limit above maximum (10001)" \
  "rate_limit_requests_per_second must be between 0 and 10000" \
  -var 'rate_limit_requests_per_second=10001'

# ==============================================================================
# Tests: General Variables
# ==============================================================================

echo ""
echo "━━━ General Variable Validations ━━━"

run_test "rejects invalid environment" \
  "environment must be one of" \
  -var 'environment=production'

run_test "rejects uppercase environment" \
  "environment must be one of" \
  -var 'environment=DEV'

run_test "rejects empty environment" \
  "environment must be one of" \
  -var 'environment='

run_test "rejects invalid vault_key_protection_mode" \
  "vault_key_protection_mode must be SOFTWARE or HSM" \
  -var 'vault_key_protection_mode=INVALID'

# ==============================================================================
# Tests: Networking Variables
# ==============================================================================

echo ""
echo "━━━ Networking Variable Validations ━━━"

run_test "rejects invalid vcn_cidr_block" \
  "vcn_cidr_block must be a valid CIDR" \
  -var 'vcn_cidr_block=not-a-cidr'

run_test "rejects invalid subnet_public_cidr" \
  "subnet_public_cidr must be a valid CIDR" \
  -var 'subnet_public_cidr=not-a-cidr'

run_test "rejects invalid subnet_private_cidr" \
  "subnet_private_cidr must be a valid CIDR" \
  -var 'subnet_private_cidr=not-a-cidr'

# ==============================================================================
# Summary
# ==============================================================================

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Results: $PASS passed, $FAIL failed, $TOTAL total"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

if [ "$FAIL" -gt 0 ]; then
  exit 1
fi
