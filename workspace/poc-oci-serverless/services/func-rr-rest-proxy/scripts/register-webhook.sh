#!/usr/bin/env bash
# ==============================================================================
# register-webhook.sh — registra/gerencia o webhook do RMS apontando para a
# nossa function (listenerUrl = API Gateway /proxy/item/webhook).
#
# Chama a API de administração do RMS:
#   {MERCH_BASE}/services/administration/operations/webhooks/manage
# autenticando via OAuth2 client-credentials (mesmo fluxo do RmsClient.java).
# As credenciais OAuth são lidas do OCI Vault (OCIDs vêm do terraform state).
#
# Uso:
#   ./register-webhook.sh [--action register|list|disable] [--url <API_BASE_URL>]
#
# Ações:
#   register (default)  cria/atualiza o webhook (enabled=Y)
#   disable             mesma config com enabled=N
#   list                GET da config atual de webhooks (best-effort)
#
# Credenciais OAuth (ordem):
#   1) env CLIENT_ID + CLIENT_SECRET (se ambos setados)
#   2) OCI Vault: OCIDs via `terraform state show` + `oci secrets secret-bundle get`
#
# ATENÇÃO: registrar aponta o RMS para nossa function; ele passará a chamar de
# verdade a cada intervalSeconds. Rode apenas quando quiser ativar.
# ==============================================================================
set -uo pipefail

# --- defaults (sobrescrevíveis por env/arg) -----------------------------------
ACTION="${ACTION:-register}"
OCI_PROFILE="${OCI_PROFILE:-poc}"
OCI_AUTH="${OCI_AUTH:-security_token}"
OCI_REGION="${OCI_REGION:-sa-saopaulo-1}"

SERVICE="${SERVICE:-foundation/item}"
CREDENTIAL_NAME="${CREDENTIAL_NAME:-APP_TESTE_BLUM}"
LISTENER_PATH="${LISTENER_PATH:-/proxy/item/webhook}"
INCLUDE_PAYLOAD="${INCLUDE_PAYLOAD:-Y}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-10}"
PAGE_LIMIT="${PAGE_LIMIT:-1000}"
INCLUDE="${INCLUDE:-include=items.action,items.item,items.status,items.itemDescription}"
HEARTBEAT_HOURS="${HEARTBEAT_HOURS:-1}"
ENABLED="${ENABLED:-Y}"
WEBHOOK_HTTP_METHOD="${WEBHOOK_HTTP_METHOD:-POST}"

MERCH_BASE="${MERCH_BASE:-https://rex-npe.retail.sa-vinhedo-1.ocs.oraclecloud.com/rgbu-rex-brxs-par1-mfcs/MerchIntegrations}"
MANAGE_URL="${MANAGE_URL:-$MERCH_BASE/services/administration/operations/webhooks/manage}"

TOKEN_URL="${TOKEN_URL:-https://idcs-a23fd2fe5f18408c865bfc16a04cddb8.identity.oraclecloud.com/oauth2/v1/token}"
OAUTH_SCOPE="${OAUTH_SCOPE:-rgbu:merch:MFCS-PAR1}"

# --- parse args ---------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --action) ACTION="$2"; shift 2 ;;
    --url)    API_BASE_URL="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; exit 0 ;;
    *) echo "Argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done

# --- cores / helpers ----------------------------------------------------------
if [[ -t 1 ]]; then
  C_RED=$'\033[0;31m'; C_GRN=$'\033[0;32m'; C_YLW=$'\033[0;33m'; C_BLD=$'\033[1m'; C_RST=$'\033[0m'
else C_RED=""; C_GRN=""; C_YLW=""; C_BLD=""; C_RST=""; fi
info() { printf '[i] %s\n' "$*"; }
warn() { printf '%s[!]%s %s\n' "$C_YLW" "$C_RST" "$*" >&2; }
err()  { printf '%s[x]%s %s\n' "$C_RED" "$C_RST" "$*" >&2; }
hdr()  { printf '\n%s== %s ==%s\n' "$C_BLD" "$*" "$C_RST"; }
ok()   { printf '%s  OK%s %s\n' "$C_GRN" "$C_RST" "$*"; }

command -v jq >/dev/null 2>&1 || { err "jq é obrigatório"; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/../../.." && pwd))"
TF_DIR="${TF_DIR:-$REPO_ROOT/infra/environments/dev}"

oci_cli() { oci --profile "$OCI_PROFILE" --auth "$OCI_AUTH" --region "$OCI_REGION" "$@"; }

# --- resolve API base URL / listenerUrl ---------------------------------------
if [[ -z "${API_BASE_URL:-}" ]]; then
  if command -v terraform >/dev/null 2>&1 && [[ -d "$TF_DIR" ]]; then
    API_BASE_URL="$(terraform -chdir="$TF_DIR" output -raw api_base_url 2>/dev/null || true)"
  fi
fi
[[ -z "${API_BASE_URL:-}" ]] && { err "API_BASE_URL não resolvida (use --url/env)"; exit 1; }
LISTENER_URL="${API_BASE_URL}${LISTENER_PATH}"

# --- credenciais OAuth --------------------------------------------------------
tf_secret_ocid() { # $1 = resource name -> imprime o .id do state
  terraform -chdir="$TF_DIR" state show "$1" 2>/dev/null \
    | awk -F'"' '/^[[:space:]]*id[[:space:]]*=/{print $2; exit}'
}
vault_secret() { # $1 = secret OCID -> conteúdo decodificado
  oci_cli secrets secret-bundle get --secret-id "$1" \
    --query 'data."secret-bundle-content".content' --raw-output 2>/dev/null | base64 -d
}

resolve_credentials() {
  if [[ -n "${CLIENT_ID:-}" && -n "${CLIENT_SECRET:-}" ]]; then
    info "Usando CLIENT_ID/CLIENT_SECRET do ambiente."
    return 0
  fi
  info "Buscando credenciais OAuth no Vault (via terraform state + oci CLI)..."
  local id_ocid sec_ocid
  id_ocid="$(tf_secret_ocid 'oci_vault_secret.rest_proxy_oauth_client_id[0]')"
  sec_ocid="$(tf_secret_ocid 'oci_vault_secret.rest_proxy_oauth_client_secret[0]')"
  if [[ -z "$id_ocid" || -z "$sec_ocid" ]]; then
    err "OCIDs dos secrets não encontrados no terraform state. Defina CLIENT_ID/CLIENT_SECRET via env."
    exit 1
  fi
  CLIENT_ID="$(vault_secret "$id_ocid")"
  CLIENT_SECRET="$(vault_secret "$sec_ocid")"
  if [[ -z "${CLIENT_ID:-}" || -z "${CLIENT_SECRET:-}" ]]; then
    err "Falha ao ler secrets do Vault (sessão OCI válida? re-auth: oci session authenticate --profile $OCI_PROFILE)."
    exit 1
  fi
  ok "Credenciais OAuth carregadas do Vault."
}

get_token() {
  resolve_credentials
  local cred resp
  cred="$(printf '%s:%s' "$CLIENT_ID" "$CLIENT_SECRET" | base64 | tr -d '\n')"
  resp="$(curl -s --max-time 30 -X POST "$TOKEN_URL" \
    -H 'Content-Type: application/x-www-form-urlencoded' \
    -H "Authorization: Basic $cred" \
    -d "grant_type=client_credentials&scope=${OAUTH_SCOPE}")"
  ACCESS_TOKEN="$(printf '%s' "$resp" | jq -r '.access_token // empty' 2>/dev/null)"
  if [[ -z "$ACCESS_TOKEN" ]]; then
    err "Falha ao obter token OAuth. Resposta: $resp"
    exit 1
  fi
  ok "Token OAuth obtido."
}

# --- body do webhook ----------------------------------------------------------
build_body() { # $1 = enabled flag
  local enabled="$1"
  jq -n \
    --arg service "$SERVICE" \
    --arg cred "$CREDENTIAL_NAME" \
    --arg listener "$LISTENER_URL" \
    --arg incp "$INCLUDE_PAYLOAD" \
    --arg enabled "$enabled" \
    --argjson interval "$INTERVAL_SECONDS" \
    --argjson pagelimit "$PAGE_LIMIT" \
    --arg query "$INCLUDE" \
    --argjson heartbeat "$HEARTBEAT_HOURS" \
    '{collectionSize:1, items:[{
        service:$service, credentialName:$cred, listenerUrl:$listener,
        includePayload:$incp, enabled:$enabled, intervalSeconds:$interval,
        pageLimit:$pagelimit, queryParameter:$query, heartbeatIntervalHours:$heartbeat
      }]}'
}

send() { # $1 = método, $2 = body(json ou vazio)
  local method="$1" body="${2:-}"
  local args=(-s -w $'\n%{http_code}' --max-time 60 -X "$method"
    -H "Authorization: Bearer $ACCESS_TOKEN" -H 'Accept: application/json')
  [[ -n "$body" ]] && args+=(-H 'Content-Type: application/json' --data "$body")
  curl "${args[@]}" "$MANAGE_URL"
}

# --- ações --------------------------------------------------------------------
case "$ACTION" in
  register|disable)
    [[ "$ACTION" == "disable" ]] && ENABLED="N"
    hdr "WEBHOOK $ACTION -> $MANAGE_URL"
    info "service=$SERVICE  credentialName=$CREDENTIAL_NAME  enabled=$ENABLED"
    info "listenerUrl=$LISTENER_URL"
    get_token
    BODY="$(build_body "$ENABLED")"
    info "body: $BODY"
    resp="$(send "$WEBHOOK_HTTP_METHOD" "$BODY")"
    ;;
  list)
    hdr "WEBHOOK list -> $MANAGE_URL"
    get_token
    resp="$(send GET "")"
    ;;
  *) err "ação inválida: $ACTION (use register|disable|list)"; exit 2 ;;
esac

code="$(printf '%s' "$resp" | tail -n1)"
body="$(printf '%s' "$resp" | sed '$d')"
printf '%s-- resposta (HTTP %s) --%s\n' "$C_BLD" "$code" "$C_RST"
printf '%s\n' "$body" | (jq . 2>/dev/null || cat)

case "$code" in
  200|201|202|204) ok "$ACTION -> HTTP $code"; exit 0 ;;
  401|403) err "$ACTION -> HTTP $code (auth: cheque credentialName/scope/token)"; exit 1 ;;
  *) err "$ACTION -> HTTP $code (se 405/404, ajuste WEBHOOK_HTTP_METHOD/MANAGE_URL)"; exit 1 ;;
esac
