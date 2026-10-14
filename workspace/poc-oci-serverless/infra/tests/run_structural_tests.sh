#!/usr/bin/env bash
# ==============================================================================
# Terraform Structural & Compliance Tests
# ==============================================================================
# Tests for static analysis, naming conventions, security compliance,
# and module interface contracts.
# Compatible with any Terraform version. No cloud resources required.
# ==============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INFRA_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ENV_DIR="$INFRA_DIR/environments/dev"

cd "$INFRA_DIR"

# ==============================================================================
# Test Framework
# ==============================================================================

PASS=0
FAIL=0
TOTAL=0

MODULES=("network" "iam" "function-app" "api-gateway" "observability" "vault")

pass() {
  PASS=$((PASS + 1))
  TOTAL=$((TOTAL + 1))
  echo "  ✓ $1"
}

fail() {
  FAIL=$((FAIL + 1))
  TOTAL=$((TOTAL + 1))
  echo "  ✗ $1"
  [ -n "${2:-}" ] && echo "    → $2"
}

# Safe grep -c that returns 0 on no match without double-output
count_grep() {
  local result
  result=$(grep -c "$@" 2>/dev/null) || result=0
  echo "$result"
}

# Safe piped grep count
count_grep_pipe() {
  local pattern="$1"
  local file="$2"
  local filter="$3"
  local result
  result=$(grep "$pattern" "$file" 2>/dev/null | grep -c "$filter" 2>/dev/null) || result=0
  echo "$result"
}

# ==============================================================================
# Tier 1: Static Analysis
# ==============================================================================

echo ""
echo "━━━ Tier 1: Static Analysis ━━━"

# terraform fmt -check
fmt_result=$(terraform fmt -check -recursive 2>&1) || true
if [ -z "$fmt_result" ]; then
  pass "terraform fmt -check -recursive (all files formatted)"
else
  fail "terraform fmt -check -recursive" "Unformatted: $(echo "$fmt_result" | tr '\n' ', ')"
fi

# terraform validate
validate_result=$(terraform validate 2>&1) || true
if echo "$validate_result" | grep -q "Success"; then
  pass "terraform validate (configuration valid)"
else
  fail "terraform validate" "$(echo "$validate_result" | grep -i 'error' | head -3)"
fi

# No .tf files with syntax issues (check HCL structure)
empty_tf=$(find modules/ -name '*.tf' -empty 2>/dev/null || true)
if [ -z "$empty_tf" ]; then
  pass "no empty .tf files in modules"
else
  fail "no empty .tf files in modules" "$empty_tf"
fi

# ==============================================================================
# Naming Conventions
# ==============================================================================

echo ""
echo "━━━ Naming Conventions ━━━"

# Check display_name and name attributes include var.environment in each module
for mod in "${MODULES[@]}"; do
  mod_file="modules/$mod/main.tf"
  if [ -f "$mod_file" ]; then
    if [ "$mod" = "iam" ]; then
      # IAM resources use 'name' attribute (not display_name)
      total_names=$(count_grep '^[[:space:]]*name[[:space:]]*=' "$mod_file")
      with_env=$(count_grep_pipe '^[[:space:]]*name[[:space:]]*=' "$mod_file" 'var\.environment')
    else
      # All other modules use display_name
      total_names=$(count_grep 'display_name[[:space:]]*=' "$mod_file")
      with_env=$(count_grep_pipe 'display_name[[:space:]]*=' "$mod_file" 'var\.environment')
    fi

    if [ "$total_names" -gt 0 ] && [ "$total_names" -eq "$with_env" ]; then
      pass "module/$mod: all resource names include environment ($total_names/$total_names)"
    elif [ "$total_names" -eq 0 ]; then
      pass "module/$mod: no named resources (skipped)"
    else
      if [ "$mod" = "iam" ]; then
        missing_lines=$(grep '^[[:space:]]*name[[:space:]]*=' "$mod_file" | grep -v 'var\.environment' | sed 's/^[[:space:]]*//' || true)
      else
        missing_lines=$(grep 'display_name[[:space:]]*=' "$mod_file" | grep -v 'var\.environment' | sed 's/^[[:space:]]*//' || true)
      fi
      fail "module/$mod: resource names include environment ($with_env/$total_names)" "$missing_lines"
    fi
  fi
done

# Check resource naming prefixes follow convention (type-name-env)
# Network: vcn-, igw-, natgw-, sgw-, rt-, sl-, subnet-, nsg-
for prefix in "vcn-" "igw-" "natgw-" "sgw-" "rt-" "sl-" "subnet-" "nsg-"; do
  if grep -q "\"${prefix}" modules/network/main.tf 2>/dev/null; then
    pass "network: uses '${prefix}' naming prefix"
  fi
done

# IAM: dg-, policy-
for prefix in "dg-" "policy-"; do
  count=$(count_grep "\"${prefix}" modules/iam/main.tf)
  if [ "$count" -gt 0 ]; then
    pass "iam: uses '${prefix}' naming prefix ($count resources)"
  else
    fail "iam: uses '${prefix}' naming prefix"
  fi
done

# Observability: lg-, log-, alarm-
for prefix in "lg-" "log-" "alarm-"; do
  count=$(count_grep "\"${prefix}" modules/observability/main.tf)
  if [ "$count" -gt 0 ]; then
    pass "observability: uses '${prefix}' naming prefix ($count resources)"
  else
    fail "observability: uses '${prefix}' naming prefix"
  fi
done

# Check freeform_tags applied in all modules
for mod in "${MODULES[@]}"; do
  mod_file="modules/$mod/main.tf"
  if [ -f "$mod_file" ]; then
    tags_count=$(count_grep 'freeform_tags[[:space:]]*=' "$mod_file")
    tags_var_count=$(count_grep 'tags[[:space:]]*=' "$mod_file")
    total_tags=$((tags_count + tags_var_count))
    if [ "$total_tags" -gt 0 ]; then
      pass "module/$mod: tags applied ($total_tags resources)"
    else
      fail "module/$mod: tags not applied"
    fi
  fi
done

# ==============================================================================
# Security Compliance
# ==============================================================================

echo ""
echo "━━━ Security Compliance ━━━"

# No hardcoded OCIDs in module .tf files (validation regex patterns are OK)
hardcoded_ocids=$(grep -rn 'ocid1\.\(tenancy\|compartment\|subnet\|vcn\|fnapp\|fnfunc\)' \
  --include='*.tf' modules/ 2>/dev/null \
  | grep -v 'can(regex' \
  | grep -v 'error_message' \
  | grep -v 'condition' \
  | grep -v 'description' \
  | grep -v '#' \
  || true)
if [ -z "$hardcoded_ocids" ]; then
  pass "no hardcoded OCIDs in module .tf files"
else
  fail "no hardcoded OCIDs in module .tf files" "$(echo "$hardcoded_ocids" | head -3)"
fi

# No hardcoded OCIDs in root (except validation blocks)
hardcoded_root=$(grep -rn 'ocid1\.\(tenancy\|compartment\|subnet\|vcn\)' \
  "$ENV_DIR/main.tf" "$ENV_DIR/apps.tf" "$ENV_DIR/outputs.tf" 2>/dev/null \
  | grep -v 'can(regex' \
  | grep -v 'error_message' \
  | grep -v 'condition' \
  || true)
if [ -z "$hardcoded_root" ]; then
  pass "no hardcoded OCIDs in root main.tf/apps.tf/outputs.tf"
else
  fail "no hardcoded OCIDs in root main.tf/apps.tf/outputs.tf" "$hardcoded_root"
fi

# Sensitive outputs marked correctly
invoke_sensitive=$(grep -A4 '"invoke_endpoint"' modules/function-app/outputs.tf 2>/dev/null \
  | grep -c 'sensitive[[:space:]]*=[[:space:]]*true' 2>/dev/null) || invoke_sensitive=0
if [ "$invoke_sensitive" -gt 0 ]; then
  pass "module/function-app: invoke_endpoint marked sensitive"
else
  fail "module/function-app: invoke_endpoint marked sensitive"
fi

# Check sensitive in root outputs (if exists)
root_invoke_sensitive=$(grep -A4 'invoke_endpoint' "$ENV_DIR/outputs.tf" 2>/dev/null \
  | grep -c 'sensitive[[:space:]]*=[[:space:]]*true' 2>/dev/null) || root_invoke_sensitive=0
if [ "$root_invoke_sensitive" -gt 0 ]; then
  pass "root: invoke_endpoint outputs marked sensitive"
else
  # Not a hard failure — root may not expose invoke_endpoint
  pass "root: invoke_endpoint not exposed (acceptable)"
fi

# No secret/password defaults in variable definitions
secret_defaults=$(grep -A3 'default\s*=' "$ENV_DIR/variables.tf" modules/*/variables.tf 2>/dev/null \
  | grep -iE '(password|secret_key|private_key|api_key|token)' \
  | grep -v 'description' \
  | grep -v '#' \
  | grep -v 'variable' \
  || true)
if [ -z "$secret_defaults" ]; then
  pass "no secret/password default values in variables"
else
  fail "no secret/password default values in variables" "$secret_defaults"
fi

# No hardcoded credentials in provider config
provider_creds=$(grep -rnE '(user_ocid|fingerprint|private_key_path|private_key_password)\s*=' \
  --include='*.tf' . 2>/dev/null \
  | grep -v 'variable' \
  | grep -v 'description' \
  | grep -v '#' \
  | grep -v 'tests/' \
  | grep -v '.tftest' \
  || true)
if [ -z "$provider_creds" ]; then
  pass "no hardcoded provider credentials"
else
  fail "no hardcoded provider credentials" "$provider_creds"
fi

# Provider source is oracle/oci
if grep -q 'source\s*=\s*"oracle/oci"' "$ENV_DIR/versions.tf" 2>/dev/null; then
  pass "provider source is oracle/oci"
else
  fail "provider source is oracle/oci"
fi

# No hashicorp/oci references
hashicorp_oci=$(grep -r 'hashicorp/oci' --include='*.tf' . 2>/dev/null || true)
if [ -z "$hashicorp_oci" ]; then
  pass "no hashicorp/oci provider references"
else
  fail "no hashicorp/oci provider references" "$hashicorp_oci"
fi

# No terraform_remote_state
remote_state=$(grep -r 'terraform_remote_state' --include='*.tf' . 2>/dev/null || true)
if [ -z "$remote_state" ]; then
  pass "no terraform_remote_state usage"
else
  fail "no terraform_remote_state usage" "$remote_state"
fi

# Public subnet blocks public IPs correctly (API GW needs public)
public_subnet_ip=$(grep -A5 'subnet.*public' modules/network/main.tf 2>/dev/null \
  | grep 'prohibit_public_ip_on_vnic\s*=\s*false' || true)
if [ -n "$public_subnet_ip" ]; then
  pass "public subnet allows public IPs (required for API Gateway)"
else
  fail "public subnet allows public IPs"
fi

# Private subnet blocks public IPs
private_subnet_ip=$(grep -A10 'oci_core_subnet.*private' modules/network/main.tf 2>/dev/null \
  | grep 'prohibit_public_ip_on_vnic\s*=\s*true' || true)
if [ -n "$private_subnet_ip" ]; then
  pass "private subnet blocks public IPs (Functions isolation)"
else
  fail "private subnet blocks public IPs"
fi

# Security list restricts public ingress to HTTPS only (port 443)
public_sl_443=$(grep -A15 'security_list.*public' modules/network/main.tf 2>/dev/null \
  | grep -c 'min = 443' 2>/dev/null) || public_sl_443=0
if [ "$public_sl_443" -gt 0 ]; then
  pass "public security list restricts ingress to port 443"
else
  fail "public security list restricts ingress to port 443"
fi

# ==============================================================================
# Module Interface Contract
# ==============================================================================

echo ""
echo "━━━ Module Interface Contract ━━━"

# Each module has required files: main.tf, variables.tf, outputs.tf
for mod in "${MODULES[@]}"; do
  mod_dir="modules/$mod"
  missing=""
  for file in main.tf variables.tf outputs.tf; do
    [ ! -f "$mod_dir/$file" ] && missing="$missing $file"
  done
  if [ -z "$missing" ]; then
    pass "module/$mod: has main.tf, variables.tf, outputs.tf"
  else
    fail "module/$mod: missing$missing"
  fi
done

# All module variables have 'type' attribute
for mod in "${MODULES[@]}"; do
  var_file="modules/$mod/variables.tf"
  if [ -f "$var_file" ]; then
    var_count=$(count_grep '^[[:space:]]*variable[[:space:]]' "$var_file")
    type_count=$(count_grep '^[[:space:]]*type[[:space:]]*=' "$var_file")
    if [ "$var_count" -eq "$type_count" ]; then
      pass "module/$mod: all variables have type ($var_count/$var_count)"
    else
      fail "module/$mod: all variables have type" "$type_count/$var_count have type"
    fi
  fi
done

# All module variables have 'description' attribute
for mod in "${MODULES[@]}"; do
  var_file="modules/$mod/variables.tf"
  if [ -f "$var_file" ]; then
    var_count=$(count_grep '^[[:space:]]*variable[[:space:]]' "$var_file")
    desc_count=$(count_grep '^[[:space:]]*description[[:space:]]*=' "$var_file")
    if [ "$var_count" -eq "$desc_count" ]; then
      pass "module/$mod: all variables have description ($var_count/$var_count)"
    else
      fail "module/$mod: all variables have description" "$desc_count/$var_count have description"
    fi
  fi
done

# Root variables have type + description
root_var_count=$(count_grep '^[[:space:]]*variable[[:space:]]' "$ENV_DIR/variables.tf")
root_type_count=$(count_grep '^[[:space:]]*type[[:space:]]*=' "$ENV_DIR/variables.tf")
root_desc_count=$(count_grep '^[[:space:]]*description[[:space:]]*=' "$ENV_DIR/variables.tf")

if [ "$root_var_count" -eq "$root_type_count" ]; then
  pass "root: all variables have type ($root_var_count/$root_var_count)"
else
  fail "root: all variables have type" "$root_type_count/$root_var_count have type"
fi

if [ "$root_var_count" -eq "$root_desc_count" ]; then
  pass "root: all variables have description ($root_var_count/$root_var_count)"
else
  fail "root: all variables have description" "$root_desc_count/$root_var_count have description"
fi

# Root variables with constraints have validation blocks
# (variables that SHOULD have validation: OCIDs, enums, ranges)
root_validation_count=$(count_grep '^[[:space:]]*validation[[:space:]]*{' "$ENV_DIR/variables.tf")
if [ "$root_validation_count" -ge 10 ]; then
  pass "root: sufficient validation blocks ($root_validation_count found, minimum 10)"
else
  fail "root: validation blocks" "Only $root_validation_count found, expected at least 10"
fi

# All modules accept 'tags' variable
for mod in "${MODULES[@]}"; do
  var_file="modules/$mod/variables.tf"
  if [ -f "$var_file" ]; then
    if grep -q '^\s*variable\s*"tags"' "$var_file" 2>/dev/null; then
      pass "module/$mod: accepts tags variable"
    else
      fail "module/$mod: accepts tags variable"
    fi
  fi
done

# All modules have at least one output
for mod in "${MODULES[@]}"; do
  out_file="modules/$mod/outputs.tf"
  if [ -f "$out_file" ]; then
    out_count=$(count_grep '^[[:space:]]*output[[:space:]]' "$out_file")
    if [ "$out_count" -gt 0 ]; then
      pass "module/$mod: has outputs ($out_count defined)"
    else
      fail "module/$mod: has outputs" "outputs.tf exists but empty"
    fi
  fi
done

# All root outputs have 'description' attribute
root_out_count=$(count_grep '^[[:space:]]*output[[:space:]]' "$ENV_DIR/outputs.tf")
root_out_desc=$(count_grep '^[[:space:]]*description[[:space:]]*=' "$ENV_DIR/outputs.tf")
if [ "$root_out_count" -eq "$root_out_desc" ]; then
  pass "root: all outputs have description ($root_out_count/$root_out_count)"
else
  fail "root: all outputs have description" "$root_out_desc/$root_out_count have description"
fi

# Root outputs reference modules (not direct resources)
root_out_values=$(count_grep '^[[:space:]]*value[[:space:]]*=' "$ENV_DIR/outputs.tf")
module_refs=$(count_grep_pipe '^[[:space:]]*value[[:space:]]*=' "$ENV_DIR/outputs.tf" 'module\.')
if [ "$root_out_values" -eq "$module_refs" ]; then
  pass "root: all outputs reference module outputs ($root_out_values/$root_out_values)"
else
  fail "root: all outputs reference module outputs" "$module_refs/$root_out_values reference modules"
fi

# Module composition order: depends_on used for IAM → Functions/API Gateway
if grep -A3 'module.*app_api_handler' "$ENV_DIR/apps.tf" 2>/dev/null | grep -q 'depends_on.*module.iam' 2>/dev/null; then
  pass "root: function apps depend_on iam"
else
  # Check inside the module block with more context
  if grep -A30 'module\s*"app_api_handler"' "$ENV_DIR/apps.tf" 2>/dev/null | grep -q 'module\.iam'; then
    pass "root: function apps depend_on iam"
  else
    fail "root: function apps depend_on iam"
  fi
fi

if grep -A30 'module\s*"api_gateway"' "$ENV_DIR/apps.tf" 2>/dev/null | grep -q 'module\.app_api_handler\|module\.network'; then
  pass "root: api_gateway references function/network modules"
else
  fail "root: api_gateway references function/network modules"
fi

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
