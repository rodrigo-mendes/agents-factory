#!/usr/bin/env bash
# ==============================================================================
# lib-rms.sh — config + helpers compartilhados pelos scripts de integração RMS/MFCS.
# Uso: os demais scripts fazem `source "$(dirname "${BASH_SOURCE[0]}")/lib-rms.sh"`.
# Todas as variáveis podem ser sobrescritas por env antes de chamar.
# ==============================================================================
set -uo pipefail

# ------------------------------------------------------------------------------
# Config base (sobrescrevível por env var)
# ------------------------------------------------------------------------------
OCI_PROFILE="${OCI_PROFILE:-poc}"
OCI_AUTH="${OCI_AUTH:-security_token}"
OCI_REGION="${OCI_REGION:-sa-saopaulo-1}"

# Base MerchIntegrations (IRMÃ de RmsReSTServices — NÃO filha).
RMS_MERCH_BASE="${RMS_MERCH_BASE:-https://rex-npe.retail.sa-vinhedo-1.ocs.oraclecloud.com/rgbu-rex-brxs-par1-mfcs/MerchIntegrations}"
# OAuth2 IDCS.
RMS_TOKEN_URL="${RMS_TOKEN_URL:-https://idcs-a23fd2fe5f18408c865bfc16a04cddb8.identity.oraclecloud.com/oauth2/v1/token}"
RMS_SCOPE="${RMS_SCOPE:-rgbu:merch:MFCS-PAR1}"

# Nomes dos recursos Vault no terraform state (creds OAuth). Sobrescrevível.
RMS_TF_SECRET_ID_RESOURCE="${RMS_TF_SECRET_ID_RESOURCE:-oci_vault_secret.rest_proxy_oauth_client_id[0]}"
RMS_TF_SECRET_SECRET_RESOURCE="${RMS_TF_SECRET_SECRET_RESOURCE:-oci_vault_secret.rest_proxy_oauth_client_secret[0]}"

# Repo root via git; TF dir p/ ler state/outputs.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/../../../.." && pwd))"
TF_DIR="${TF_DIR:-$REPO_ROOT/infra/environments/dev}"

# ------------------------------------------------------------------------------
# Cores / logging
# ------------------------------------------------------------------------------
if [[ -t 1 ]]; then
  C_RED=$'\033[0;31m'; C_GRN=$'\033[0;32m'; C_YLW=$'\033[0;33m'
  C_BLU=$'\033[0;34m'; C_BLD=$'\033[1m'; C_RST=$'\033[0m'
else C_RED=""; C_GRN=""; C_YLW=""; C_BLU=""; C_BLD=""; C_RST=""; fi

info() { printf '%s[i]%s %s\n' "$C_BLU" "$C_RST" "$*"; }
warn() { printf '%s[!]%s %s\n' "$C_YLW" "$C_RST" "$*" >&2; }
err()  { printf '%s[x]%s %s\n' "$C_RED" "$C_RST" "$*" >&2; }
hdr()  { printf '\n%s== %s ==%s\n' "$C_BLD" "$*" "$C_RST"; }

PASS_COUNT=0; FAIL_COUNT=0; WARN_COUNT=0
pass() { PASS_COUNT=$((PASS_COUNT+1)); printf '%s  PASS%s %s\n' "$C_GRN" "$C_RST" "$*"; }
fail() { FAIL_COUNT=$((FAIL_COUNT+1)); printf '%s  FAIL%s %s\n' "$C_RED" "$C_RST" "$*"; }
skip() { WARN_COUNT=$((WARN_COUNT+1)); printf '%s  WARN%s %s\n' "$C_YLW" "$C_RST" "$*"; }
summary() {
  printf '\n%s---------------------------------------------%s\n' "$C_BLD" "$C_RST"
  printf 'RESULTADO: %sPASS=%d%s %sFAIL=%d%s %sWARN=%d%s\n' \
    "$C_GRN" "$PASS_COUNT" "$C_RST" "$C_RED" "$FAIL_COUNT" "$C_RST" "$C_YLW" "$WARN_COUNT" "$C_RST"
  [[ "$FAIL_COUNT" -eq 0 ]]
}

require_tools() {
  local missing=0
  for t in curl jq; do command -v "$t" >/dev/null 2>&1 || { err "faltando: $t"; missing=1; }; done
  [[ $missing -eq 0 ]] || exit 1
}

oci_cli() { oci --profile "$OCI_PROFILE" --auth "$OCI_AUTH" --region "$OCI_REGION" "$@"; }

# ------------------------------------------------------------------------------
# Credenciais OAuth: env CLIENT_ID/CLIENT_SECRET, senão Vault (via terraform state).
# ------------------------------------------------------------------------------
_tf_secret_ocid() { # $1 = resource -> .id do state
  terraform -chdir="$TF_DIR" state show "$1" 2>/dev/null \
    | awk -F'"' '/^[[:space:]]*id[[:space:]]*=/{print $2; exit}'
}
_vault_secret() { # $1 = secret OCID -> conteúdo decodificado
  oci_cli secrets secret-bundle get --secret-id "$1" \
    --query 'data."secret-bundle-content".content' --raw-output 2>/dev/null | base64 -d
}

rms_resolve_credentials() {
  if [[ -n "${CLIENT_ID:-}" && -n "${CLIENT_SECRET:-}" ]]; then
    info "Credenciais OAuth via env."; return 0
  fi
  info "Buscando credenciais OAuth no Vault (terraform state + oci CLI)..."
  local id_ocid sec_ocid
  id_ocid="$(_tf_secret_ocid "$RMS_TF_SECRET_ID_RESOURCE")"
  sec_ocid="$(_tf_secret_ocid "$RMS_TF_SECRET_SECRET_RESOURCE")"
  [[ -n "$id_ocid" && -n "$sec_ocid" ]] || { err "OCIDs dos secrets não achados no state. Defina CLIENT_ID/CLIENT_SECRET."; exit 1; }
  CLIENT_ID="$(_vault_secret "$id_ocid")"
  CLIENT_SECRET="$(_vault_secret "$sec_ocid")"
  [[ -n "${CLIENT_ID:-}" && -n "${CLIENT_SECRET:-}" ]] || {
    err "Falha ao ler Vault (sessão OCI válida? oci session authenticate --profile $OCI_PROFILE)."; exit 1; }
  info "Credenciais carregadas do Vault."
}

# Imprime um access_token OAuth2 (nunca loga o token além do retorno).
rms_token() {
  rms_resolve_credentials
  local cred resp tok
  cred="$(printf '%s:%s' "$CLIENT_ID" "$CLIENT_SECRET" | base64 | tr -d '\n')"
  resp="$(curl -s --max-time 30 -X POST "$RMS_TOKEN_URL" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -H "Authorization: Basic $cred" \
    -d "grant_type=client_credentials&scope=${RMS_SCOPE}")"
  tok="$(printf '%s' "$resp" | jq -r '.access_token // empty' 2>/dev/null)"
  [[ -n "$tok" ]] || { err "Falha ao obter token. Resposta: $resp"; return 1; }
  printf '%s' "$tok"
}

# Monta URL foundation. rms_url <entity> [id]
#   com id  -> by-id path-param: {base}/services/foundation/<ent>/<id>
#   sem id  -> delta/publish:   {base}/services/foundation/<ent>
rms_url() {
  local ent="$1" id="${2:-}"
  ent="${ent#foundation/}"   # aceita "item" ou "foundation/item"
  if [[ -n "$id" ]]; then
    printf '%s/services/foundation/%s/%s' "$RMS_MERCH_BASE" "$ent" "$id"
  else
    printf '%s/services/foundation/%s' "$RMS_MERCH_BASE" "$ent"
  fi
}
