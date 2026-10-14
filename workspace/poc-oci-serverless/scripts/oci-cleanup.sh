#!/usr/bin/env bash
# ==============================================================================
# oci-cleanup.sh — Remove all OCI resources created by this serverless project
#
# Usage:
#   ./scripts/oci-cleanup.sh              # Execute cleanup
#   ./scripts/oci-cleanup.sh --dry-run    # List only, no deletions
#
# Prerequisites: oci (CLI configured), jq
# ==============================================================================
set -uo pipefail

# --- Configuration -----------------------------------------------------------
COMPARTMENT_OCID="ocid1.compartment.oc1..aaaaaaaat3d6o3oron7jqrztl572jjrsdobf6bimutf57jirbzetc4magzja"
TENANCY_OCID="ocid1.tenancy.oc1..aaaaaaaamjcayr5bxznhi3lqeekvlokgw6se5rb3g6rr4jjbzqe7wl2ebe5a"
NAMESPACE="gr2o2hdgzoxw"
REGION="sa-saopaulo-1"

# OCI CLI profile (session token auth)
OCI_PROFILE="poc"
OCI_AUTH="security_token"

# Project identifiers (used to filter IAM resources at tenancy level)
# Matches by compartment name, project name, or compartment OCID in rules
COMPARTMENT_NAME="mom-fast-track-poc-oci-serverless"
PROJECT_FILTER="serverless|mom-fast-track"

# The compartment is a child of brxretailbrazil (root tenancy).
# IAM policies/dynamic-groups may live at tenancy root level.
# We search both tenancy root and the compartment itself.
IAM_SEARCH_COMPARTMENTS=("$TENANCY_OCID" "$COMPARTMENT_OCID")

# Vault deletion schedule (minimum 7 days from now)
VAULT_DELETE_DAYS=7
SECRET_DELETE_DAYS=2

# --- Runtime -----------------------------------------------------------------
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

FOUND=0
DELETED=0
FAILED=0
SKIPPED=0

# --- Colors ------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# --- OCI wrapper (injects profile + auth into every call) --------------------
oci() {
  command oci --profile "$OCI_PROFILE" --auth "$OCI_AUTH" "$@"
}

# --- Helpers -----------------------------------------------------------------
log_phase() { echo -e "\n${BLUE}═══════════════════════════════════════════════════════════${NC}"; echo -e "${BLUE}  Phase: $1${NC}"; echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"; }
log_info()  { echo -e "${CYAN}  [INFO]${NC} $1"; }
log_found() { echo -e "${YELLOW}  [FOUND]${NC} $1"; FOUND=$((FOUND + 1)); }
log_delete(){ echo -e "${RED}  [DELETE]${NC} $1"; DELETED=$((DELETED + 1)); }
log_skip()  { echo -e "${GREEN}  [SKIP]${NC} $1"; SKIPPED=$((SKIPPED + 1)); }
log_fail()  { echo -e "${RED}  [FAIL]${NC} $1"; FAILED=$((FAILED + 1)); }
log_dry()   { echo -e "${YELLOW}  [DRY-RUN]${NC} Would delete: $1"; }
log_none()  { echo -e "${GREEN}  [NONE]${NC} No resources found."; }

check_deps() {
  for cmd in oci jq; do
    if ! command -v "$cmd" &>/dev/null; then
      echo -e "${RED}ERROR: '$cmd' is required but not installed.${NC}" >&2
      exit 1
    fi
  done
}

# Safe extraction: returns empty if .data is null/empty
extract_ids() {
  local json="$1"
  echo "$json" | jq -r '.data // [] | .[].id // empty' 2>/dev/null || true
}

extract_ids_field() {
  local json="$1" field="$2"
  echo "$json" | jq -r ".data // [] | .[].$field // empty" 2>/dev/null || true
}

# Delete with retry (for resources that may need time to release dependencies)
delete_with_retry() {
  local cmd="$1" label="$2" retries="${3:-1}" delay="${4:-30}"
  for ((i=1; i<=retries; i++)); do
    if eval "$cmd" &>/dev/null; then
      log_delete "$label"
      return 0
    fi
    if ((i < retries)); then
      log_info "Retry $i/$retries for $label (waiting ${delay}s)..."
      sleep "$delay"
    fi
  done
  log_fail "$label"
  return 0
}

# ==============================================================================
# Phase 1: Monitoring & Observability
# ==============================================================================
cleanup_observability() {
  log_phase "1/8 — Observability (Alarms, Logs, Notifications)"

  # --- Monitoring Alarms ---
  log_info "Listing monitoring alarms..."
  local alarms
  alarms=$(oci monitoring alarm list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local alarm_ids
  alarm_ids=$(extract_ids "$alarms")

  if [[ -z "$alarm_ids" ]]; then
    log_none
  else
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$alarms" | jq -r ".data[] | select(.id==\"$id\") | .\"display-name\" // .id")
      log_found "Alarm: $name"
      if $DRY_RUN; then
        log_dry "Alarm $name ($id)"
      else
        delete_with_retry "oci monitoring alarm delete --alarm-id '$id' --force" "Alarm: $name"
      fi
    done <<< "$alarm_ids"
  fi

  # --- Logging: Logs & Log Groups ---
  log_info "Listing log groups..."
  local log_groups
  log_groups=$(oci logging log-group list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local lg_ids
  lg_ids=$(extract_ids "$log_groups")

  if [[ -z "$lg_ids" ]]; then
    log_none
  else
    while IFS= read -r lg_id; do
      [[ -z "$lg_id" ]] && continue
      local lg_name
      lg_name=$(echo "$log_groups" | jq -r ".data[] | select(.id==\"$lg_id\") | .\"display-name\" // .id")
      log_found "Log Group: $lg_name"

      # Delete logs inside the group first
      local logs
      logs=$(oci logging log list --log-group-id "$lg_id" --all 2>/dev/null || echo '{"data":[]}')
      local log_ids
      log_ids=$(extract_ids "$logs")
      while IFS= read -r log_id; do
        [[ -z "$log_id" ]] && continue
        local log_name
        log_name=$(echo "$logs" | jq -r ".data[] | select(.id==\"$log_id\") | .\"display-name\" // .id")
        log_found "  Log: $log_name"
        if $DRY_RUN; then
          log_dry "Log $log_name"
        else
          delete_with_retry "oci logging log delete --log-group-id '$lg_id' --log-id '$log_id' --force" "Log: $log_name"
        fi
      done <<< "$log_ids"

      # Delete log group
      if $DRY_RUN; then
        log_dry "Log Group $lg_name"
      else
        delete_with_retry "oci logging log-group delete --log-group-id '$lg_id' --force" "Log Group: $lg_name"
      fi
    done <<< "$lg_ids"
  fi

  # --- Notification Subscriptions & Topics ---
  log_info "Listing notification topics..."
  local topics
  topics=$(oci ons topic list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local topic_ids
  topic_ids=$(echo "$topics" | jq -r '.data // [] | .[]."topic-id" // empty' 2>/dev/null || true)

  if [[ -z "$topic_ids" ]]; then
    log_none
  else
    while IFS= read -r topic_id; do
      [[ -z "$topic_id" ]] && continue
      local topic_name
      topic_name=$(echo "$topics" | jq -r ".data[] | select(.\"topic-id\"==\"$topic_id\") | .name // .\"topic-id\"")
      log_found "Topic: $topic_name"

      # Delete subscriptions first
      local subs
      subs=$(oci ons subscription list --compartment-id "$COMPARTMENT_OCID" --topic-id "$topic_id" --all 2>/dev/null || echo '{"data":[]}')
      local sub_ids
      sub_ids=$(extract_ids "$subs")
      while IFS= read -r sub_id; do
        [[ -z "$sub_id" ]] && continue
        log_found "  Subscription: $sub_id"
        if $DRY_RUN; then
          log_dry "Subscription $sub_id"
        else
          delete_with_retry "oci ons subscription delete --subscription-id '$sub_id' --force" "Subscription: $sub_id"
        fi
      done <<< "$sub_ids"

      # Delete topic
      if $DRY_RUN; then
        log_dry "Topic $topic_name"
      else
        delete_with_retry "oci ons topic delete --topic-id '$topic_id' --force" "Topic: $topic_name"
      fi
    done <<< "$topic_ids"
  fi
}

# ==============================================================================
# Phase 2: API Gateway
# ==============================================================================
cleanup_apigateway() {
  log_phase "2/8 — API Gateway (Deployments, Gateways)"

  # --- Deployments ---
  log_info "Listing API Gateway deployments..."
  local deployments
  deployments=$(oci apigateway deployment list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local dep_ids
  dep_ids=$(extract_ids "$deployments")

  if [[ -z "$dep_ids" ]]; then
    log_none
  else
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$deployments" | jq -r ".data[] | select(.id==\"$id\") | .\"display-name\" // .id")
      log_found "Deployment: $name"
      if $DRY_RUN; then
        log_dry "Deployment $name ($id)"
      else
        delete_with_retry "oci apigateway deployment delete --deployment-id '$id' --force --wait-for-state SUCCEEDED --wait-interval-seconds 5" "Deployment: $name" 2 15
      fi
    done <<< "$dep_ids"
  fi

  # --- Gateways ---
  log_info "Listing API Gateways..."
  local gateways
  gateways=$(oci apigateway gateway list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local gw_ids
  gw_ids=$(extract_ids "$gateways")

  if [[ -z "$gw_ids" ]]; then
    log_none
  else
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$gateways" | jq -r ".data[] | select(.id==\"$id\") | .\"display-name\" // .id")
      log_found "Gateway: $name"
      if $DRY_RUN; then
        log_dry "Gateway $name ($id)"
      else
        delete_with_retry "oci apigateway gateway delete --gateway-id '$id' --force --wait-for-state SUCCEEDED --wait-interval-seconds 5" "Gateway: $name" 2 20
      fi
    done <<< "$gw_ids"
  fi
}

# ==============================================================================
# Phase 3: Functions
# ==============================================================================
cleanup_functions() {
  log_phase "3/8 — Functions (Functions, Applications)"

  log_info "Listing Function applications..."
  local apps
  apps=$(oci fn application list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local app_ids
  app_ids=$(extract_ids "$apps")

  if [[ -z "$app_ids" ]]; then
    log_none
    return
  fi

  # Delete functions in each application first
  while IFS= read -r app_id; do
    [[ -z "$app_id" ]] && continue
    local app_name
    app_name=$(echo "$apps" | jq -r ".data[] | select(.id==\"$app_id\") | .\"display-name\" // .id")
    log_found "Application: $app_name"

    local funcs
    funcs=$(oci fn function list --application-id "$app_id" --all 2>/dev/null || echo '{"data":[]}')
    local fn_ids
    fn_ids=$(extract_ids "$funcs")

    while IFS= read -r fn_id; do
      [[ -z "$fn_id" ]] && continue
      local fn_name
      fn_name=$(echo "$funcs" | jq -r ".data[] | select(.id==\"$fn_id\") | .\"display-name\" // .id")
      log_found "  Function: $fn_name"
      if $DRY_RUN; then
        log_dry "Function $fn_name ($fn_id)"
      else
        delete_with_retry "oci fn function delete --function-id '$fn_id' --force" "Function: $fn_name"
      fi
    done <<< "$fn_ids"

    # Delete the application
    if $DRY_RUN; then
      log_dry "Application $app_name ($app_id)"
    else
      sleep 5 # Wait for functions to fully terminate
      delete_with_retry "oci fn application delete --application-id '$app_id' --force" "Application: $app_name" 3 10
    fi
  done <<< "$app_ids"
}

# ==============================================================================
# Phase 4: Vault & Secrets
# ==============================================================================
cleanup_vault() {
  log_phase "4/8 — Vault & Secrets (scheduled deletion)"

  local delete_date_secret
  delete_date_secret=$(date -v+${SECRET_DELETE_DAYS}d -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -d "+${SECRET_DELETE_DAYS} days" -u +"%Y-%m-%dT%H:%M:%SZ")
  local delete_date_vault
  delete_date_vault=$(date -v+${VAULT_DELETE_DAYS}d -u +"%Y-%m-%dT%H:%M:%SZ" 2>/dev/null || date -d "+${VAULT_DELETE_DAYS} days" -u +"%Y-%m-%dT%H:%M:%SZ")

  # --- Secrets ---
  log_info "Listing Vault secrets..."
  local secrets
  secrets=$(oci vault secret list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  # Filter out already-deleted secrets
  local active_secrets
  active_secrets=$(echo "$secrets" | jq '.data // [] | [.[] | select(."lifecycle-state" != "DELETED" and ."lifecycle-state" != "PENDING_DELETION")]' 2>/dev/null || echo '[]')
  local secret_ids
  secret_ids=$(echo "$active_secrets" | jq -r '.[].id // empty' 2>/dev/null || true)

  if [[ -z "$secret_ids" ]]; then
    log_none
  else
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$active_secrets" | jq -r ".[] | select(.id==\"$id\") | .\"secret-name\" // .id")
      log_found "Secret: $name (will enter PENDING_DELETION for ${SECRET_DELETE_DAYS} days)"
      if $DRY_RUN; then
        log_dry "Secret $name → schedule deletion for $delete_date_secret"
      else
        if oci vault secret schedule-secret-deletion --secret-id "$id" --time-of-deletion "$delete_date_secret" &>/dev/null; then
          log_delete "Secret: $name (pending until $delete_date_secret)"
        else
          log_fail "Secret: $name"
        fi
      fi
    done <<< "$secret_ids"
  fi

  # --- Vaults ---
  log_info "Listing KMS Vaults..."
  local vaults
  vaults=$(oci kms vault list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local active_vaults
  active_vaults=$(echo "$vaults" | jq '.data // [] | [.[] | select(."lifecycle-state" == "ACTIVE" or ."lifecycle-state" == "CREATING")]' 2>/dev/null || echo '[]')
  local vault_ids
  vault_ids=$(echo "$active_vaults" | jq -r '.[].id // empty' 2>/dev/null || true)

  if [[ -z "$vault_ids" ]]; then
    log_none
  else
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$active_vaults" | jq -r ".[] | select(.id==\"$id\") | .\"display-name\" // .id")
      log_found "Vault: $name (will enter PENDING_DELETION for ${VAULT_DELETE_DAYS} days)"
      if $DRY_RUN; then
        log_dry "Vault $name → schedule deletion for $delete_date_vault"
      else
        if oci kms vault schedule-vault-deletion --vault-id "$id" --time-of-deletion "$delete_date_vault" &>/dev/null; then
          log_delete "Vault: $name (pending until $delete_date_vault)"
        else
          log_fail "Vault: $name"
        fi
      fi
    done <<< "$vault_ids"
  fi
}

# ==============================================================================
# Phase 5: Object Storage
# ==============================================================================
cleanup_objectstorage() {
  log_phase "5/8 — Object Storage (Buckets)"

  log_info "Listing buckets..."
  local buckets
  buckets=$(oci os bucket list --compartment-id "$COMPARTMENT_OCID" --namespace-name "$NAMESPACE" 2>/dev/null || echo '{"data":[]}')
  local bucket_names
  bucket_names=$(echo "$buckets" | jq -r '.data // [] | .[].name // empty' 2>/dev/null || true)

  if [[ -z "$bucket_names" ]]; then
    log_none
    return
  fi

  while IFS= read -r name; do
    [[ -z "$name" ]] && continue
    log_found "Bucket: $name"
    if $DRY_RUN; then
      log_dry "Bucket $name (bulk-delete objects + delete bucket)"
    else
      # Delete all objects first
      log_info "  Bulk-deleting objects in $name..."
      oci os object bulk-delete --bucket-name "$name" --namespace-name "$NAMESPACE" --force &>/dev/null || true
      # Delete the bucket
      if oci os bucket delete --bucket-name "$name" --namespace-name "$NAMESPACE" --force &>/dev/null; then
        log_delete "Bucket: $name"
      else
        log_fail "Bucket: $name (may have versioned objects — try purging versions)"
      fi
    fi
  done <<< "$bucket_names"
}

# ==============================================================================
# Phase 6: Networking
# ==============================================================================
cleanup_networking() {
  log_phase "6/8 — Networking (NSGs, Subnets, Route Tables, Gateways, VCN)"

  log_info "Listing VCNs..."
  local vcns
  vcns=$(oci network vcn list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local vcn_ids
  vcn_ids=$(extract_ids "$vcns")

  if [[ -z "$vcn_ids" ]]; then
    log_none
    return
  fi

  while IFS= read -r vcn_id; do
    [[ -z "$vcn_id" ]] && continue
    local vcn_name
    vcn_name=$(echo "$vcns" | jq -r ".data[] | select(.id==\"$vcn_id\") | .\"display-name\" // .id")
    log_found "VCN: $vcn_name"

    # Get default route table and security list (cannot delete these, they go with VCN)
    local default_rt default_sl
    default_rt=$(echo "$vcns" | jq -r ".data[] | select(.id==\"$vcn_id\") | .\"default-route-table-id\" // empty")
    default_sl=$(echo "$vcns" | jq -r ".data[] | select(.id==\"$vcn_id\") | .\"default-security-list-id\" // empty")

    # --- NSGs ---
    log_info "  Listing NSGs..."
    local nsgs
    nsgs=$(oci network nsg list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    local nsg_ids
    nsg_ids=$(extract_ids "$nsgs")
    while IFS= read -r nsg_id; do
      [[ -z "$nsg_id" ]] && continue
      local nsg_name
      nsg_name=$(echo "$nsgs" | jq -r ".data[] | select(.id==\"$nsg_id\") | .\"display-name\" // .id")
      log_found "  NSG: $nsg_name"

      # Remove rules first (required before NSG deletion if referenced by other NSGs)
      local rules
      rules=$(oci network nsg rules list --nsg-id "$nsg_id" --all 2>/dev/null || echo '{"data":[]}')
      local rule_ids
      rule_ids=$(echo "$rules" | jq -r '.data // [] | .[].id // empty' 2>/dev/null || true)
      if [[ -n "$rule_ids" ]]; then
        local rule_array
        rule_array=$(echo "$rule_ids" | jq -R -s -c 'split("\n") | map(select(length > 0))')
        if $DRY_RUN; then
          log_dry "NSG rules in $nsg_name"
        else
          oci network nsg rules remove --nsg-id "$nsg_id" --security-rule-ids "$rule_array" &>/dev/null || true
        fi
      fi

      if $DRY_RUN; then
        log_dry "NSG $nsg_name"
      else
        delete_with_retry "oci network nsg delete --nsg-id '$nsg_id' --force" "NSG: $nsg_name" 3 10
      fi
    done <<< "$nsg_ids"

    # --- Subnets ---
    log_info "  Listing subnets..."
    local subnets
    subnets=$(oci network subnet list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    local subnet_ids
    subnet_ids=$(extract_ids "$subnets")
    while IFS= read -r subnet_id; do
      [[ -z "$subnet_id" ]] && continue
      local subnet_name
      subnet_name=$(echo "$subnets" | jq -r ".data[] | select(.id==\"$subnet_id\") | .\"display-name\" // .id")
      log_found "  Subnet: $subnet_name"
      if $DRY_RUN; then
        log_dry "Subnet $subnet_name"
      else
        delete_with_retry "oci network subnet delete --subnet-id '$subnet_id' --force --wait-for-state TERMINATED --wait-interval-seconds 5" "Subnet: $subnet_name" 5 30
      fi
    done <<< "$subnet_ids"

    # --- Route Tables (non-default) ---
    log_info "  Listing route tables..."
    local rts
    rts=$(oci network route-table list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    local rt_ids
    rt_ids=$(extract_ids "$rts")
    while IFS= read -r rt_id; do
      [[ -z "$rt_id" ]] && continue
      [[ "$rt_id" == "$default_rt" ]] && { log_skip "  Default RT (deleted with VCN)"; continue; }
      local rt_name
      rt_name=$(echo "$rts" | jq -r ".data[] | select(.id==\"$rt_id\") | .\"display-name\" // .id")
      log_found "  Route Table: $rt_name"
      if $DRY_RUN; then
        log_dry "Route Table $rt_name"
      else
        # Clear rules before deleting (may be required)
        oci network route-table update --rt-id "$rt_id" --route-rules '[]' --force &>/dev/null || true
        delete_with_retry "oci network route-table delete --rt-id '$rt_id' --force" "Route Table: $rt_name" 2 10
      fi
    done <<< "$rt_ids"

    # --- Security Lists (non-default) ---
    log_info "  Listing security lists..."
    local sls
    sls=$(oci network security-list list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    local sl_ids
    sl_ids=$(extract_ids "$sls")
    while IFS= read -r sl_id; do
      [[ -z "$sl_id" ]] && continue
      [[ "$sl_id" == "$default_sl" ]] && { log_skip "  Default SL (deleted with VCN)"; continue; }
      local sl_name
      sl_name=$(echo "$sls" | jq -r ".data[] | select(.id==\"$sl_id\") | .\"display-name\" // .id")
      log_found "  Security List: $sl_name"
      if $DRY_RUN; then
        log_dry "Security List $sl_name"
      else
        delete_with_retry "oci network security-list delete --security-list-id '$sl_id' --force" "Security List: $sl_name" 2 10
      fi
    done <<< "$sl_ids"

    # --- Internet Gateway ---
    log_info "  Listing internet gateways..."
    local igws
    igws=$(oci network internet-gateway list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    local igw_ids
    igw_ids=$(extract_ids "$igws")
    while IFS= read -r igw_id; do
      [[ -z "$igw_id" ]] && continue
      log_found "  Internet Gateway: $igw_id"
      if $DRY_RUN; then
        log_dry "Internet Gateway $igw_id"
      else
        delete_with_retry "oci network internet-gateway delete --ig-id '$igw_id' --force" "Internet Gateway" 2 10
      fi
    done <<< "$igw_ids"

    # --- NAT Gateway ---
    log_info "  Listing NAT gateways..."
    local nats
    nats=$(oci network nat-gateway list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    local nat_ids
    nat_ids=$(extract_ids "$nats")
    while IFS= read -r nat_id; do
      [[ -z "$nat_id" ]] && continue
      log_found "  NAT Gateway: $nat_id"
      if $DRY_RUN; then
        log_dry "NAT Gateway $nat_id"
      else
        delete_with_retry "oci network nat-gateway delete --nat-gateway-id '$nat_id' --force" "NAT Gateway" 2 10
      fi
    done <<< "$nat_ids"

    # --- Service Gateway ---
    log_info "  Listing service gateways..."
    local sgws
    sgws=$(oci network service-gateway list --compartment-id "$COMPARTMENT_OCID" --vcn-id "$vcn_id" --all 2>/dev/null || echo '{"data":[]}')
    local sgw_ids
    sgw_ids=$(extract_ids "$sgws")
    while IFS= read -r sgw_id; do
      [[ -z "$sgw_id" ]] && continue
      log_found "  Service Gateway: $sgw_id"
      if $DRY_RUN; then
        log_dry "Service Gateway $sgw_id"
      else
        delete_with_retry "oci network service-gateway delete --service-gateway-id '$sgw_id' --force" "Service Gateway" 2 10
      fi
    done <<< "$sgw_ids"

    # --- Delete VCN ---
    if $DRY_RUN; then
      log_dry "VCN $vcn_name ($vcn_id)"
    else
      log_info "  Deleting VCN..."
      delete_with_retry "oci network vcn delete --vcn-id '$vcn_id' --force --wait-for-state TERMINATED --wait-interval-seconds 5" "VCN: $vcn_name" 3 20
    fi
  done <<< "$vcn_ids"
}

# ==============================================================================
# Phase 7: IAM (Tenancy level)
# ==============================================================================
cleanup_iam() {
  log_phase "7/8 — IAM (Policies, Dynamic Groups)"

  # --- Policies (compartment level — direct) ---
  log_info "Listing policies in compartment..."
  local policies
  policies=$(oci iam policy list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local pol_ids
  pol_ids=$(extract_ids "$policies")

  if [[ -n "$pol_ids" ]]; then
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$policies" | jq -r ".data[] | select(.id==\"$id\") | .name // .id")
      log_found "Policy (compartment): $name"
      if $DRY_RUN; then
        log_dry "Policy $name ($id)"
      else
        delete_with_retry "oci iam policy delete --policy-id '$id' --force" "Policy: $name"
      fi
    done <<< "$pol_ids"
  fi

  # --- Policies (tenancy root level, filtered by compartment/project) ---
  # The compartment mom-fast-track-poc-oci-serverless is a child of brxretailbrazil (root).
  # Policies granting access to this compartment are typically created at the tenancy root.
  log_info "Listing policies at tenancy root (filtered by '$PROJECT_FILTER' or compartment references)..."
  local tenancy_policies
  tenancy_policies=$(oci iam policy list --compartment-id "$TENANCY_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local filtered_pol_ids
  # Match by name OR by statements referencing the compartment name or OCID
  filtered_pol_ids=$(echo "$tenancy_policies" | jq -r ".data // [] | .[] | select((.name | test(\"$PROJECT_FILTER\"; \"i\")) or (.statements[]? | test(\"$COMPARTMENT_NAME\"; \"i\")) or (.statements[]? | test(\"$COMPARTMENT_OCID\"))) | .id" 2>/dev/null | sort -u || true)

  if [[ -z "$filtered_pol_ids" ]]; then
    log_info "No tenancy-level policies matching filter"
  else
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$tenancy_policies" | jq -r ".data[] | select(.id==\"$id\") | .name // .id")
      log_found "Policy (tenancy root): $name"
      if $DRY_RUN; then
        log_dry "Policy $name ($id)"
      else
        delete_with_retry "oci iam policy delete --policy-id '$id' --force" "Policy: $name"
      fi
    done <<< "$filtered_pol_ids"
  fi

  # --- Dynamic Groups (always at tenancy level, filtered by name or compartment OCID in matching-rule) ---
  log_info "Listing dynamic groups at tenancy root (filtered by '$PROJECT_FILTER' or compartment OCID in matching-rule)..."
  local dgs
  dgs=$(oci iam dynamic-group list --compartment-id "$TENANCY_OCID" --all 2>/dev/null || echo '{"data":[]}')
  local filtered_dg_ids
  # Match by name OR by matching-rule referencing the compartment OCID
  filtered_dg_ids=$(echo "$dgs" | jq -r ".data // [] | .[] | select((.name | test(\"$PROJECT_FILTER\"; \"i\")) or (.\"matching-rule\" // \"\" | test(\"$COMPARTMENT_OCID\"))) | .id" 2>/dev/null | sort -u || true)

  if [[ -z "$filtered_dg_ids" ]]; then
    log_info "No dynamic groups matching '$PROJECT_FILTER'"
  else
    while IFS= read -r id; do
      [[ -z "$id" ]] && continue
      local name
      name=$(echo "$dgs" | jq -r ".data[] | select(.id==\"$id\") | .name // .id")
      log_found "Dynamic Group: $name"
      if $DRY_RUN; then
        log_dry "Dynamic Group $name ($id)"
      else
        delete_with_retry "oci iam dynamic-group delete --dynamic-group-id '$id' --force" "Dynamic Group: $name"
      fi
    done <<< "$filtered_dg_ids"
  fi
}

# ==============================================================================
# Phase 8: OCIR (Container Registry)
# ==============================================================================
cleanup_ocir() {
  log_phase "8/8 — OCIR (Container Images & Repositories)"

  log_info "Listing container repositories..."
  local repos
  repos=$(oci artifacts container repository list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null || echo '{"data":{"items":[]}}')

  # OCIR list returns data.items not data[]
  local repo_data
  repo_data=$(echo "$repos" | jq -r '.data.items // .data // [] | .[] | "\(.id)|\(.\"display-name\" // .\"repository-name\" // .id)"' 2>/dev/null || true)

  if [[ -z "$repo_data" ]]; then
    # Try tenancy-level with filter
    log_info "Trying tenancy-level search for 'serverless-app' repos..."
    repos=$(oci artifacts container repository list --compartment-id "$TENANCY_OCID" --all 2>/dev/null || echo '{"data":{"items":[]}}')
    repo_data=$(echo "$repos" | jq -r '.data.items // .data // [] | .[] | select(."display-name" // ."repository-name" // "" | test("serverless-app")) | "\(.id)|\(.\"display-name\" // .\"repository-name\" // .id)"' 2>/dev/null || true)
  fi

  if [[ -z "$repo_data" ]]; then
    log_none
    return
  fi

  while IFS='|' read -r repo_id repo_name; do
    [[ -z "$repo_id" ]] && continue
    log_found "Repository: $repo_name"

    # List images in the repository
    local images
    images=$(oci artifacts container image list --compartment-id "$COMPARTMENT_OCID" --repository-name "$repo_name" --all 2>/dev/null || \
             oci artifacts container image list --compartment-id "$TENANCY_OCID" --repository-name "$repo_name" --all 2>/dev/null || echo '{"data":{"items":[]}}')
    local image_ids
    image_ids=$(echo "$images" | jq -r '.data.items // .data // [] | .[].id // empty' 2>/dev/null || true)

    while IFS= read -r img_id; do
      [[ -z "$img_id" ]] && continue
      local img_version
      img_version=$(echo "$images" | jq -r ".data.items // .data // [] | .[] | select(.id==\"$img_id\") | .version // .\"display-name\" // .id" 2>/dev/null || echo "$img_id")
      log_found "  Image: $repo_name:$img_version"
      if $DRY_RUN; then
        log_dry "Image $repo_name:$img_version"
      else
        if oci artifacts container image delete --image-id "$img_id" --force 2>/dev/null; then
          log_delete "Image: $repo_name:$img_version"
        else
          log_fail "Image: $repo_name:$img_version"
        fi
        sleep 1 # Rate limiting
      fi
    done <<< "$image_ids"

    # Delete repository
    if $DRY_RUN; then
      log_dry "Repository $repo_name ($repo_id)"
    else
      sleep 2
      if oci artifacts container repository delete --repository-id "$repo_id" --force 2>/dev/null; then
        log_delete "Repository: $repo_name"
      else
        log_fail "Repository: $repo_name (may still have images)"
      fi
    fi
  done <<< "$repo_data"
}

# ==============================================================================
# Main
# ==============================================================================
main() {
  check_deps

  echo -e "${BLUE}"
  echo "╔═══════════════════════════════════════════════════════════════╗"
  echo "║          OCI RESOURCE CLEANUP — poc-oci-serverless           ║"
  echo "╠═══════════════════════════════════════════════════════════════╣"
  echo "║  Compartment: mom-fast-track-poc-oci-serverless              ║"
  echo "║  Region:      sa-saopaulo-1                                  ║"
  echo "║  Namespace:   gr2o2hdgzoxw                                   ║"
  if $DRY_RUN; then
  echo -e "║  Mode:        ${YELLOW}DRY-RUN (no deletions)${BLUE}                        ║"
  else
  echo -e "║  Mode:        ${RED}LIVE (resources WILL be deleted)${BLUE}                ║"
  fi
  echo "╚═══════════════════════════════════════════════════════════════╝"
  echo -e "${NC}"

  if ! $DRY_RUN; then
    echo -e "${RED}⚠️  WARNING: This will PERMANENTLY delete OCI resources.${NC}"
    echo -e "${RED}   Vault/Secrets enter pending-deletion (7d/2d minimum).${NC}"
    echo -e "${RED}   All other deletions are IRREVERSIBLE.${NC}"
    echo ""
    read -rp "Type 'DELETE' to confirm: " confirm
    if [[ "$confirm" != "DELETE" ]]; then
      echo "Aborted."
      exit 0
    fi
    echo ""
  fi

  cleanup_observability  || log_fail "Phase 1 (Observability) had errors — continuing..."
  cleanup_apigateway     || log_fail "Phase 2 (API Gateway) had errors — continuing..."
  cleanup_functions      || log_fail "Phase 3 (Functions) had errors — continuing..."
  cleanup_vault          || log_fail "Phase 4 (Vault) had errors — continuing..."
  cleanup_objectstorage  || log_fail "Phase 5 (Object Storage) had errors — continuing..."
  cleanup_networking     || log_fail "Phase 6 (Networking) had errors — continuing..."
  cleanup_iam            || log_fail "Phase 7 (IAM) had errors — continuing..."
  cleanup_ocir           || log_fail "Phase 8 (OCIR) had errors — continuing..."

  # --- Summary ---
  echo ""
  echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
  echo -e "${BLUE}  SUMMARY${NC}"
  echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
  echo -e "  Resources found:   ${YELLOW}${FOUND}${NC}"
  if $DRY_RUN; then
    echo -e "  Mode:              ${YELLOW}DRY-RUN (nothing was deleted)${NC}"
  else
    echo -e "  Deleted:           ${GREEN}${DELETED}${NC}"
    echo -e "  Failed:            ${RED}${FAILED}${NC}"
    echo -e "  Skipped:           ${CYAN}${SKIPPED}${NC}"
  fi
  echo ""

  if ! $DRY_RUN && ((FAILED == 0)) && ((DELETED > 0)); then
    echo -e "${GREEN}✓ Cleanup complete.${NC}"
    echo ""
    echo -e "  Next steps:"
    echo -e "  • Vault/Secrets will be fully deleted in ${VAULT_DELETE_DAYS}/${SECRET_DELETE_DAYS} days"
    echo -e "  • To clean local Terraform state:"
    echo -e "    rm -f infra/environments/dev/terraform.tfstate*"
    echo -e "    rm -rf infra/environments/dev/.terraform/"
  elif $DRY_RUN && ((FOUND > 0)); then
    echo -e "${YELLOW}Run without --dry-run to execute deletions.${NC}"
  elif ((FOUND == 0)); then
    echo -e "${GREEN}✓ No resources found — compartment is clean.${NC}"
  fi
}

main "$@"
