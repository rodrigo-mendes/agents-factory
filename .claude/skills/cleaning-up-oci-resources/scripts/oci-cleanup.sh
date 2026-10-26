#!/usr/bin/env bash
# ==============================================================================
# oci-cleanup.sh — Remove all OCI resources in a given compartment
#
# Usage:
#   export OCI_COMPARTMENT_OCID="ocid1.compartment.oc1...<value>"
#   export OCI_TENANCY_OCID="ocid1.tenancy.oc1...<value>"
#   export OCI_NAMESPACE="<object-storage-namespace>"
#   ./scripts/oci-cleanup.sh              # Execute cleanup (requires confirmation)
#   ./scripts/oci-cleanup.sh --dry-run    # List resources only, no deletions
#
# Required environment variables:
#   OCI_COMPARTMENT_OCID   Compartment to clean   (e.g. ocid1.compartment.oc1....)
#   OCI_TENANCY_OCID       Root tenancy OCID      (e.g. ocid1.tenancy.oc1....)
#   OCI_NAMESPACE          Object Storage namespace
#
# Optional environment variables:
#   OCI_REGION             OCI region (default: sa-saopaulo-1)
#   OCI_PROFILE            OCI CLI profile name (default: DEFAULT)
#   OCI_AUTH               OCI CLI auth method  (default: api_key)
#   OCI_COMPARTMENT_NAME   Compartment display name for IAM filter (default: "")
#   OCI_PROJECT_FILTER     Regex for IAM resource name filter (default: "project")
#   VAULT_DELETE_DAYS      Days before vault deletion, min 7 (default: 7)
#   SECRET_DELETE_DAYS     Days before secret deletion, min 2 (default: 2)
#
# Prerequisites: oci (CLI configured), jq
# ==============================================================================
set -uo pipefail

# --- Validate required env vars ----------------------------------------------
: "${OCI_COMPARTMENT_OCID:?OCI_COMPARTMENT_OCID must be set (ocid1.compartment.oc1....)}"
: "${OCI_TENANCY_OCID:?OCI_TENANCY_OCID must be set (ocid1.tenancy.oc1....)}"
: "${OCI_NAMESPACE:?OCI_NAMESPACE must be set (Object Storage namespace)}"

# --- Configuration (all from env vars) ---------------------------------------
COMPARTMENT_OCID="${OCI_COMPARTMENT_OCID}"
TENANCY_OCID="${OCI_TENANCY_OCID}"
NAMESPACE="${OCI_NAMESPACE}"
REGION="${OCI_REGION:-sa-saopaulo-1}"
OCI_PROFILE="${OCI_PROFILE:-DEFAULT}"
OCI_AUTH="${OCI_AUTH:-api_key}"
COMPARTMENT_NAME="${OCI_COMPARTMENT_NAME:-}"
PROJECT_FILTER="${OCI_PROJECT_FILTER:-project}"
VAULT_DELETE_DAYS="${VAULT_DELETE_DAYS:-7}"
SECRET_DELETE_DAYS="${SECRET_DELETE_DAYS:-2}"

# --- Runtime -----------------------------------------------------------------
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

FOUND=0; DELETED=0; FAILED=0; SKIPPED=0

# --- Colors ------------------------------------------------------------------
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; CYAN='\033[0;36m'; NC='\033[0m'

# --- OCI wrapper -------------------------------------------------------------
oci() { command oci --profile "$OCI_PROFILE" --auth "$OCI_AUTH" "$@"; }

# --- Helpers -----------------------------------------------------------------
log_phase()  { echo -e "\n${BLUE}═══════════════════════════════════════════${NC}"; echo -e "${BLUE}  Phase: $1${NC}"; echo -e "${BLUE}═══════════════════════════════════════════${NC}"; }
log_info()   { echo -e "${CYAN}  [INFO]${NC} $1"; }
log_found()  { echo -e "${YELLOW}  [FOUND]${NC} $1"; FOUND=$((FOUND + 1)); }
log_delete() { echo -e "${RED}  [DELETE]${NC} $1"; DELETED=$((DELETED + 1)); }
log_skip()   { echo -e "${GREEN}  [SKIP]${NC} $1"; SKIPPED=$((SKIPPED + 1)); }
log_fail()   { echo -e "${RED}  [FAIL]${NC} $1"; FAILED=$((FAILED + 1)); }
log_dry()    { echo -e "${YELLOW}  [DRY-RUN]${NC} Would delete: $1"; }
log_none()   { echo -e "${GREEN}  [NONE]${NC} No resources found."; }

check_deps() {
  for cmd in oci jq; do
    command -v "$cmd" &>/dev/null || { echo -e "${RED}ERROR: '$cmd' not installed${NC}" >&2; exit 1; }
  done
}

extract_ids() {
  echo "$1" | jq -r '.data // [] | .[].id // empty' 2>/dev/null || true
}

delete_with_retry() {
  local cmd="$1" label="$2" retries="${3:-1}" delay="${4:-30}"
  for ((i=1; i<=retries; i++)); do
    eval "$cmd" &>/dev/null && { log_delete "$label"; return 0; }
    ((i < retries)) && { log_info "Retry $i/$retries for $label (${delay}s)..."; sleep "$delay"; }
  done
  log_fail "$label"
}

# ==============================================================================
# Phase 1: Monitoring & Observability
# ==============================================================================
cleanup_observability() {
  log_phase "1/8 — Observability (Alarms, Logs, Notifications)"

  local alarms alarm_ids
  alarms=$(oci monitoring alarm list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  alarm_ids=$(extract_ids "$alarms")
  [[ -z "$alarm_ids" ]] && log_none || while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$alarms" | jq -r ".data[] | select(.id==\"$id\") | .\"display-name\" // .id")
    log_found "Alarm: $name"
    $DRY_RUN && log_dry "Alarm $name" || delete_with_retry "oci monitoring alarm delete --alarm-id '$id' --force" "Alarm: $name"
  done <<< "$alarm_ids"

  local log_groups lg_ids
  log_groups=$(oci logging log-group list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  lg_ids=$(extract_ids "$log_groups")
  [[ -z "$lg_ids" ]] && log_none || while IFS= read -r lg_id; do
    [[ -z "$lg_id" ]] && continue
    local lg_name; lg_name=$(echo "$log_groups" | jq -r ".data[] | select(.id==\"$lg_id\") | .\"display-name\" // .id")
    log_found "Log Group: $lg_name"
    local logs log_ids
    logs=$(oci logging log list --log-group-id "$lg_id" --all 2>/dev/null || echo '{"data":[]}')
    log_ids=$(extract_ids "$logs")
    while IFS= read -r log_id; do
      [[ -z "$log_id" ]] && continue
      local log_name; log_name=$(echo "$logs" | jq -r ".data[] | select(.id==\"$log_id\") | .\"display-name\" // .id")
      log_found "  Log: $log_name"
      $DRY_RUN && log_dry "Log $log_name" || delete_with_retry "oci logging log delete --log-group-id '$lg_id' --log-id '$log_id' --force" "Log: $log_name"
    done <<< "$log_ids"
    $DRY_RUN && log_dry "Log Group $lg_name" || delete_with_retry "oci logging log-group delete --log-group-id '$lg_id' --force" "Log Group: $lg_name"
  done <<< "$lg_ids"

  local topics topic_ids
  topics=$(oci ons topic list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  topic_ids=$(echo "$topics" | jq -r '.data // [] | .[]."topic-id" // empty' 2>/dev/null || true)
  [[ -z "$topic_ids" ]] && log_none || while IFS= read -r topic_id; do
    [[ -z "$topic_id" ]] && continue
    local topic_name; topic_name=$(echo "$topics" | jq -r ".data[] | select(.\"topic-id\"==\"$topic_id\") | .name // .\"topic-id\"")
    log_found "Topic: $topic_name"
    local subs sub_ids
    subs=$(oci ons subscription list --compartment-id "$COMPARTMENT_OCID" --topic-id "$topic_id" --all 2>/dev/null || echo '{"data":[]}')
    sub_ids=$(extract_ids "$subs")
    while IFS= read -r sub_id; do
      [[ -z "$sub_id" ]] && continue
      log_found "  Subscription: $sub_id"
      $DRY_RUN && log_dry "Subscription $sub_id" || delete_with_retry "oci ons subscription delete --subscription-id '$sub_id' --force" "Subscription: $sub_id"
    done <<< "$sub_ids"
    $DRY_RUN && log_dry "Topic $topic_name" || delete_with_retry "oci ons topic delete --topic-id '$topic_id' --force" "Topic: $topic_name"
  done <<< "$topic_ids"
}

# ==============================================================================
# Phase 2: API Gateway
# ==============================================================================
cleanup_apigateway() {
  log_phase "2/8 — API Gateway (Deployments, Gateways)"

  local deployments dep_ids
  deployments=$(oci apigateway deployment list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  dep_ids=$(extract_ids "$deployments")
  [[ -z "$dep_ids" ]] && log_none || while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$deployments" | jq -r ".data[] | select(.id==\"$id\") | .\"display-name\" // .id")
    log_found "Deployment: $name"
    $DRY_RUN && log_dry "Deployment $name" || delete_with_retry "oci apigateway deployment delete --deployment-id '$id' --force --wait-for-state SUCCEEDED --wait-interval-seconds 5" "Deployment: $name" 2 15
  done <<< "$dep_ids"

  local gateways gw_ids
  gateways=$(oci apigateway gateway list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  gw_ids=$(extract_ids "$gateways")
  [[ -z "$gw_ids" ]] && log_none || while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$gateways" | jq -r ".data[] | select(.id==\"$id\") | .\"display-name\" // .id")
    log_found "Gateway: $name"
    $DRY_RUN && log_dry "Gateway $name" || delete_with_retry "oci apigateway gateway delete --gateway-id '$id' --force --wait-for-state SUCCEEDED --wait-interval-seconds 5" "Gateway: $name" 2 20
  done <<< "$gw_ids"
}

# ==============================================================================
# Phase 3: Functions
# ==============================================================================
cleanup_functions() {
  log_phase "3/8 — Functions (Functions, Applications)"

  local apps app_ids
  apps=$(oci fn application list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  app_ids=$(extract_ids "$apps")
  [[ -z "$app_ids" ]] && { log_none; return; }

  while IFS= read -r app_id; do
    [[ -z "$app_id" ]] && continue
    local app_name; app_name=$(echo "$apps" | jq -r ".data[] | select(.id==\"$app_id\") | .\"display-name\" // .id")
    log_found "Application: $app_name"
    local funcs fn_ids
    funcs=$(oci fn function list --application-id "$app_id" --all 2>/dev/null || echo '{"data":[]}')
    fn_ids=$(extract_ids "$funcs")
    while IFS= read -r fn_id; do
      [[ -z "$fn_id" ]] && continue
      local fn_name; fn_name=$(echo "$funcs" | jq -r ".data[] | select(.id==\"$fn_id\") | .\"display-name\" // .id")
      log_found "  Function: $fn_name"
      $DRY_RUN && log_dry "Function $fn_name" || delete_with_retry "oci fn function delete --function-id '$fn_id' --force" "Function: $fn_name"
    done <<< "$fn_ids"
    if $DRY_RUN; then
      log_dry "Application $app_name"
    else
      sleep 5
      delete_with_retry "oci fn application delete --application-id '$app_id' --force" "Application: $app_name" 3 10
    fi
  done <<< "$app_ids"
}

# ==============================================================================
# Phase 4: Vault & Secrets
# ==============================================================================
cleanup_vault() {
  log_phase "4/8 — Vault & Secrets (scheduled deletion)"

  local delete_date_secret delete_date_vault
  delete_date_secret=$(date -v+${SECRET_DELETE_DAYS}d -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -d "+${SECRET_DELETE_DAYS} days" -u +"%Y-%m-%dT%H:%M:%SZ")
  delete_date_vault=$(date -v+${VAULT_DELETE_DAYS}d -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -d "+${VAULT_DELETE_DAYS} days" -u +"%Y-%m-%dT%H:%M:%SZ")

  local secrets active_secrets secret_ids
  secrets=$(oci vault secret list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  active_secrets=$(echo "$secrets" | jq '.data // [] | [.[] | select(."lifecycle-state" != "DELETED" and ."lifecycle-state" != "PENDING_DELETION")]' 2>/dev/null || echo '[]')
  secret_ids=$(echo "$active_secrets" | jq -r '.[].id // empty' 2>/dev/null || true)

  [[ -z "$secret_ids" ]] && log_none || while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$active_secrets" | jq -r ".[] | select(.id==\"$id\") | .\"secret-name\" // .id")
    log_found "Secret: $name (pending ${SECRET_DELETE_DAYS}d)"
    if $DRY_RUN; then
      log_dry "Secret $name → schedule $delete_date_secret"
    else
      oci vault secret schedule-secret-deletion --secret-id "$id" --time-of-deletion "$delete_date_secret" &>/dev/null \
        && log_delete "Secret: $name (pending until $delete_date_secret)" || log_fail "Secret: $name"
    fi
  done <<< "$secret_ids"

  local vaults active_vaults vault_ids
  vaults=$(oci kms vault list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  active_vaults=$(echo "$vaults" | jq '.data // [] | [.[] | select(."lifecycle-state" == "ACTIVE" or ."lifecycle-state" == "CREATING")]' 2>/dev/null || echo '[]')
  vault_ids=$(echo "$active_vaults" | jq -r '.[].id // empty' 2>/dev/null || true)

  [[ -z "$vault_ids" ]] && log_none || while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$active_vaults" | jq -r ".[] | select(.id==\"$id\") | .\"display-name\" // .id")
    log_found "Vault: $name (pending ${VAULT_DELETE_DAYS}d)"
    if $DRY_RUN; then
      log_dry "Vault $name → schedule $delete_date_vault"
    else
      oci kms vault schedule-vault-deletion --vault-id "$id" --time-of-deletion "$delete_date_vault" &>/dev/null \
        && log_delete "Vault: $name (pending until $delete_date_vault)" || log_fail "Vault: $name"
    fi
  done <<< "$vault_ids"
}

# ==============================================================================
# Phase 5: Object Storage
# ==============================================================================
cleanup_objectstorage() {
  log_phase "5/8 — Object Storage (Buckets)"

  local buckets bucket_names
  buckets=$(oci os bucket list --compartment-id "$COMPARTMENT_OCID" --namespace-name "$NAMESPACE" 2>/dev/null || echo '{"data":[]}')
  bucket_names=$(echo "$buckets" | jq -r '.data // [] | .[].name // empty' 2>/dev/null || true)
  [[ -z "$bucket_names" ]] && { log_none; return; }

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    log_found "Bucket: $name"
    if $DRY_RUN; then
      log_dry "Bucket $name"
    else
      oci os object bulk-delete --bucket-name "$name" --namespace-name "$NAMESPACE" --force &>/dev/null || true
      oci os bucket delete --bucket-name "$name" --namespace-name "$NAMESPACE" --force &>/dev/null \
        && log_delete "Bucket: $name" || log_fail "Bucket: $name"
    fi
  done <<< "$bucket_names"
}

# ==============================================================================
# Phase 6: Networking
# ==============================================================================
cleanup_networking() {
  log_phase "6/8 — Networking (NSGs, Subnets, Route Tables, Gateways, VCN)"

  local vcns vcn_ids
  vcns=$(oci network vcn list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  vcn_ids=$(extract_ids "$vcns")
  [[ -z "$vcn_ids" ]] && { log_none; return; }

  while IFS= read -r vcn_id; do
    [[ -z "$vcn_id" ]] && continue
    local vcn_name default_rt default_sl
    vcn_name=$(echo "$vcns" | jq -r ".data[] | select(.id==\"$vcn_id\") | .\"display-name\" // .id")
    default_rt=$(echo "$vcns" | jq -r ".data[] | select(.id==\"$vcn_id\") | .\"default-route-table-id\" // empty")
    default_sl=$(echo "$vcns" | jq -r ".data[] | select(.id==\"$vcn_id\") | .\"default-security-list-id\" // empty")
    log_found "VCN: $vcn_name"

    # NSGs
    local nsgs nsg_ids
    nsgs=$(oci network nsg list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    nsg_ids=$(extract_ids "$nsgs")
    while IFS= read -r nsg_id; do
      [[ -z "$nsg_id" ]] && continue
      local nsg_name; nsg_name=$(echo "$nsgs" | jq -r ".data[] | select(.id==\"$nsg_id\") | .\"display-name\" // .id")
      log_found "  NSG: $nsg_name"
      local rules rule_ids
      rules=$(oci network nsg rules list --nsg-id "$nsg_id" --all 2>/dev/null || echo '{"data":[]}')
      rule_ids=$(echo "$rules" | jq -r '.data // [] | .[].id // empty' 2>/dev/null || true)
      if [[ -n "$rule_ids" ]] && ! $DRY_RUN; then
        local rule_array; rule_array=$(echo "$rule_ids" | jq -R -s -c 'split("\n")|map(select(length>0))')
        oci network nsg rules remove --nsg-id "$nsg_id" --security-rule-ids "$rule_array" &>/dev/null || true
      fi
      $DRY_RUN && log_dry "NSG $nsg_name" || delete_with_retry "oci network nsg delete --nsg-id '$nsg_id' --force" "NSG: $nsg_name" 3 10
    done <<< "$nsg_ids"

    # Subnets
    local subnets subnet_ids
    subnets=$(oci network subnet list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    subnet_ids=$(extract_ids "$subnets")
    while IFS= read -r subnet_id; do
      [[ -z "$subnet_id" ]] && continue
      local subnet_name; subnet_name=$(echo "$subnets" | jq -r ".data[] | select(.id==\"$subnet_id\") | .\"display-name\" // .id")
      log_found "  Subnet: $subnet_name"
      $DRY_RUN && log_dry "Subnet $subnet_name" || delete_with_retry "oci network subnet delete --subnet-id '$subnet_id' --force --wait-for-state TERMINATED --wait-interval-seconds 5" "Subnet: $subnet_name" 5 30
    done <<< "$subnet_ids"

    # Route Tables (skip default)
    local rts rt_ids
    rts=$(oci network route-table list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    rt_ids=$(extract_ids "$rts")
    while IFS= read -r rt_id; do
      [[ -z "$rt_id" ]] && continue
      [[ "$rt_id" == "$default_rt" ]] && { log_skip "  Default RT (deleted with VCN)"; continue; }
      local rt_name; rt_name=$(echo "$rts" | jq -r ".data[] | select(.id==\"$rt_id\") | .\"display-name\" // .id")
      log_found "  Route Table: $rt_name"
      if $DRY_RUN; then
        log_dry "Route Table $rt_name"
      else
        oci network route-table update --rt-id "$rt_id" --route-rules '[]' --force &>/dev/null || true
        delete_with_retry "oci network route-table delete --rt-id '$rt_id' --force" "Route Table: $rt_name" 2 10
      fi
    done <<< "$rt_ids"

    # Security Lists (skip default)
    local sls sl_ids
    sls=$(oci network security-list list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    sl_ids=$(extract_ids "$sls")
    while IFS= read -r sl_id; do
      [[ -z "$sl_id" ]] && continue
      [[ "$sl_id" == "$default_sl" ]] && { log_skip "  Default SL (deleted with VCN)"; continue; }
      local sl_name; sl_name=$(echo "$sls" | jq -r ".data[] | select(.id==\"$sl_id\") | .\"display-name\" // .id")
      log_found "  Security List: $sl_name"
      $DRY_RUN && log_dry "Security List $sl_name" || delete_with_retry "oci network security-list delete --security-list-id '$sl_id' --force" "Security List: $sl_name" 2 10
    done <<< "$sl_ids"

    # Internet / NAT / Service Gateways
    for gw_type in internet-gateway nat-gateway service-gateway; do
      local gws gw_ids
      case "$gw_type" in
        internet-gateway) gws=$(oci network internet-gateway list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}');;
        nat-gateway)      gws=$(oci network nat-gateway      list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}');;
        service-gateway)  gws=$(oci network service-gateway  list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}');;
      esac
      gw_ids=$(extract_ids "$gws")
      while IFS= read -r gw_id; do
        [[ -z "$gw_id" ]] && continue
        log_found "  $gw_type: $gw_id"
        if $DRY_RUN; then
          log_dry "$gw_type $gw_id"
        else
          case "$gw_type" in
            internet-gateway) delete_with_retry "oci network internet-gateway delete --ig-id '$gw_id' --force" "$gw_type" 2 10;;
            nat-gateway)      delete_with_retry "oci network nat-gateway delete --nat-gateway-id '$gw_id' --force" "$gw_type" 2 10;;
            service-gateway)  delete_with_retry "oci network service-gateway delete --service-gateway-id '$gw_id' --force" "$gw_type" 2 10;;
          esac
        fi
      done <<< "$gw_ids"
    done

    # VCN
    $DRY_RUN && log_dry "VCN $vcn_name" || delete_with_retry "oci network vcn delete --vcn-id '$vcn_id' --force --wait-for-state TERMINATED --wait-interval-seconds 5" "VCN: $vcn_name" 3 20
  done <<< "$vcn_ids"
}

# ==============================================================================
# Phase 7: IAM (compartment + tenancy root, filtered)
# ==============================================================================
cleanup_iam() {
  log_phase "7/8 — IAM (Policies, Dynamic Groups)"

  # Compartment-level policies
  local policies pol_ids
  policies=$(oci iam policy list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  pol_ids=$(extract_ids "$policies")
  [[ -n "$pol_ids" ]] && while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$policies" | jq -r ".data[] | select(.id==\"$id\") | .name // .id")
    log_found "Policy (compartment): $name"
    $DRY_RUN && log_dry "Policy $name" || delete_with_retry "oci iam policy delete --policy-id '$id' --force" "Policy: $name"
  done <<< "$pol_ids"

  # Tenancy-root policies filtered by project name or compartment OCID in statements
  local tenancy_policies filtered_pol_ids
  tenancy_policies=$(oci iam policy list --compartment-id "$TENANCY_OCID" --all 2>/dev/null || echo '{"data":[]}')
  filtered_pol_ids=$(echo "$tenancy_policies" | jq -r \
    ".data // [] | .[] | select(
       (.name | test(\"$PROJECT_FILTER\";\"i\")) or
       (.statements[]? | test(\"$COMPARTMENT_NAME\";\"i\")) or
       (.statements[]? | test(\"$COMPARTMENT_OCID\"))
     ) | .id" 2>/dev/null | sort -u || true)

  [[ -z "$filtered_pol_ids" ]] && log_info "No tenancy-level policies matching filter" || while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$tenancy_policies" | jq -r ".data[] | select(.id==\"$id\") | .name // .id")
    log_found "Policy (tenancy): $name"
    $DRY_RUN && log_dry "Policy $name" || delete_with_retry "oci iam policy delete --policy-id '$id' --force" "Policy: $name"
  done <<< "$filtered_pol_ids"

  # Dynamic groups (tenancy level, filtered)
  local dgs filtered_dg_ids
  dgs=$(oci iam dynamic-group list --compartment-id "$TENANCY_OCID" --all 2>/dev/null || echo '{"data":[]}')
  filtered_dg_ids=$(echo "$dgs" | jq -r \
    ".data // [] | .[] | select(
       (.name | test(\"$PROJECT_FILTER\";\"i\")) or
       (.\"matching-rule\" // \"\" | test(\"$COMPARTMENT_OCID\"))
     ) | .id" 2>/dev/null | sort -u || true)

  [[ -z "$filtered_dg_ids" ]] && log_info "No dynamic groups matching '$PROJECT_FILTER'" || while IFS= read -r id; do
    [[ -z "$id" ]] && continue
    local name; name=$(echo "$dgs" | jq -r ".data[] | select(.id==\"$id\") | .name // .id")
    log_found "Dynamic Group: $name"
    $DRY_RUN && log_dry "Dynamic Group $name" || delete_with_retry "oci iam dynamic-group delete --dynamic-group-id '$id' --force" "Dynamic Group: $name"
  done <<< "$filtered_dg_ids"
}

# ==============================================================================
# Phase 8: OCIR (Container Registry)
# ==============================================================================
cleanup_ocir() {
  log_phase "8/8 — OCIR (Container Images & Repositories)"

  local repos repo_data
  repos=$(oci artifacts container repository list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":{"items":[]}}')
  repo_data=$(echo "$repos" | jq -r '.data.items // .data // [] | .[] | "\(.id)|\(.\"display-name\" // .\"repository-name\" // .id)"' 2>/dev/null || true)

  if [[ -z "$repo_data" ]]; then
    log_info "Trying tenancy-level search (filter: $PROJECT_FILTER)..."
    repos=$(oci artifacts container repository list --compartment-id "$TENANCY_OCID" --all 2>/dev/null || echo '{"data":{"items":[]}}')
    repo_data=$(echo "$repos" | jq -r \
      ".data.items // .data // [] | .[] | select(.\"display-name\" // .\"repository-name\" // \"\" | test(\"$PROJECT_FILTER\")) | \"\(.id)|\(.\"display-name\" // .\"repository-name\" // .id)\"" \
      2>/dev/null || true)
  fi

  [[ -z "$repo_data" ]] && { log_none; return; }

  while IFS='|' read -r repo_id repo_name; do
    [[ -z "$repo_id" ]] && continue
    log_found "Repository: $repo_name"
    local images image_ids
    images=$(oci artifacts container image list --compartment-id "$COMPARTMENT_OCID" --repository-name "$repo_name" --all 2>/dev/null || \
             oci artifacts container image list --compartment-id "$TENANCY_OCID"      --repository-name "$repo_name" --all 2>/dev/null || echo '{"data":{"items":[]}}')
    image_ids=$(echo "$images" | jq -r '.data.items // .data // [] | .[].id // empty' 2>/dev/null || true)
    while IFS= read -r img_id; do
      [[ -z "$img_id" ]] && continue
      local img_ver; img_ver=$(echo "$images" | jq -r ".data.items // .data // [] | .[] | select(.id==\"$img_id\") | .version // .id" 2>/dev/null || echo "$img_id")
      log_found "  Image: $repo_name:$img_ver"
      if $DRY_RUN; then
        log_dry "Image $repo_name:$img_ver"
      else
        oci artifacts container image delete --image-id "$img_id" --force 2>/dev/null \
          && log_delete "Image: $repo_name:$img_ver" || log_fail "Image: $repo_name:$img_ver"
        sleep 1
      fi
    done <<< "$image_ids"
    if $DRY_RUN; then
      log_dry "Repository $repo_name"
    else
      sleep 2
      oci artifacts container repository delete --repository-id "$repo_id" --force 2>/dev/null \
        && log_delete "Repository: $repo_name" || log_fail "Repository: $repo_name"
    fi
  done <<< "$repo_data"
}

# ==============================================================================
# Main
# ==============================================================================
main() {
  check_deps

  echo -e "${BLUE}"
  echo "╔═══════════════════════════════════════════════════════════╗"
  echo "║           OCI RESOURCE CLEANUP                           ║"
  echo "╠═══════════════════════════════════════════════════════════╣"
  printf "║  Compartment: %-44s ║\n" "${COMPARTMENT_NAME:-${COMPARTMENT_OCID:0:44}}"
  printf "║  Region:      %-44s ║\n" "$REGION"
  printf "║  Namespace:   %-44s ║\n" "$NAMESPACE"
  if $DRY_RUN; then
    echo -e "║  Mode:        ${YELLOW}DRY-RUN (no deletions)${BLUE}                  ║"
  else
    echo -e "║  Mode:        ${RED}LIVE (resources WILL be deleted)${BLUE}         ║"
  fi
  echo "╚═══════════════════════════════════════════════════════════╝"
  echo -e "${NC}"

  if ! $DRY_RUN; then
    echo -e "${RED}WARNING: This PERMANENTLY deletes OCI resources.${NC}"
    echo -e "${RED}  Vault/Secrets: pending-deletion (${VAULT_DELETE_DAYS}d/${SECRET_DELETE_DAYS}d).${NC}"
    echo -e "${RED}  All other resources: IRREVERSIBLE.${NC}\n"
    read -rp "Type 'DELETE' to confirm: " confirm
    [[ "$confirm" == "DELETE" ]] || { echo "Aborted."; exit 0; }
    echo ""
  fi

  cleanup_observability  || log_fail "Phase 1 errors — continuing"
  cleanup_apigateway     || log_fail "Phase 2 errors — continuing"
  cleanup_functions      || log_fail "Phase 3 errors — continuing"
  cleanup_vault          || log_fail "Phase 4 errors — continuing"
  cleanup_objectstorage  || log_fail "Phase 5 errors — continuing"
  cleanup_networking     || log_fail "Phase 6 errors — continuing"
  cleanup_iam            || log_fail "Phase 7 errors — continuing"
  cleanup_ocir           || log_fail "Phase 8 errors — continuing"

  echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}  SUMMARY${NC}"
  echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
  echo -e "  Found:   ${YELLOW}${FOUND}${NC}"
  if $DRY_RUN; then
    echo -e "  Mode:    ${YELLOW}DRY-RUN — nothing deleted${NC}"
  else
    echo -e "  Deleted: ${GREEN}${DELETED}${NC}  Failed: ${RED}${FAILED}${NC}  Skipped: ${CYAN}${SKIPPED}${NC}"
  fi
  echo ""
  ((FOUND == 0)) && echo -e "${GREEN}Compartment is clean.${NC}"
  $DRY_RUN && ((FOUND > 0)) && echo -e "${YELLOW}Re-run without --dry-run to execute.${NC}"
  ! $DRY_RUN && ((FAILED == 0)) && ((DELETED > 0)) && {
    echo -e "${GREEN}Cleanup complete.${NC}"
    echo -e "  Vault/Secrets fully deleted in ${VAULT_DELETE_DAYS}d/${SECRET_DELETE_DAYS}d."
    echo -e "  Local state: rm -f infra/environments/dev/terraform.tfstate*"
  }
}

main "$@"
