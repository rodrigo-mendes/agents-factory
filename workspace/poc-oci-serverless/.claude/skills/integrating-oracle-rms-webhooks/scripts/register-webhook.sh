#!/usr/bin/env bash
# ==============================================================================
# register-webhook.sh — registra/gerencia um webhook no RMS/MFCS apontando para
# uma listenerUrl (nossa function). Chama:
#   {RMS_MERCH_BASE}/services/administration/operations/webhooks/manage
# com OAuth2 Bearer (client-credentials; creds via env ou Vault).
#
# Uso:
#   ./register-webhook.sh --service foundation/item --listener https://gw/v1/proxy/item/webhook
#   ./register-webhook.sh --action list
#   ./register-webhook.sh --action disable --service foundation/item --listener <url>
#
# Opções:
#   --action register|list|disable   (default register)
#   --service <s>                     (default foundation/item)
#   --listener <url>                  (obrigatório p/ register/disable)
# Env overrides: CREDENTIAL_NAME(APP_TESTE_BLUM) INCLUDE_PAYLOAD(Y) INTERVAL_SECONDS(10)
#   PAGE_LIMIT(1000) INCLUDE(include=items.action,items.item,items.status,items.itemDescription)
#   HEARTBEAT_HOURS(1) WEBHOOK_HTTP_METHOD(POST) MANAGE_URL
#
# ATENÇÃO: register/disable MUDAM estado no RMS (ele passa a chamar a listenerUrl).
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-rms.sh"
require_tools

ACTION="register"; SERVICE="${SERVICE:-foundation/item}"; LISTENER="${LISTENER:-}"
while [[ $# -gt 0 ]]; do
  case "$1" in
    --action)   ACTION="$2"; shift 2 ;;
    --service)  SERVICE="$2"; shift 2 ;;
    --listener) LISTENER="$2"; shift 2 ;;
    -h|--help)  grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; exit 0 ;;
    *) err "arg desconhecido: $1"; exit 2 ;;
  esac
done

CREDENTIAL_NAME="${CREDENTIAL_NAME:-APP_TESTE_BLUM}"
INCLUDE_PAYLOAD="${INCLUDE_PAYLOAD:-Y}"
INTERVAL_SECONDS="${INTERVAL_SECONDS:-10}"
PAGE_LIMIT="${PAGE_LIMIT:-1000}"
INCLUDE="${INCLUDE:-include=items.action,items.item,items.status,items.itemDescription}"
HEARTBEAT_HOURS="${HEARTBEAT_HOURS:-1}"
WEBHOOK_HTTP_METHOD="${WEBHOOK_HTTP_METHOD:-POST}"
MANAGE_URL="${MANAGE_URL:-$RMS_MERCH_BASE/services/administration/operations/webhooks/manage}"

build_body() { # $1 = enabled
  jq -n --arg service "$SERVICE" --arg cred "$CREDENTIAL_NAME" --arg listener "$LISTENER" \
        --arg incp "$INCLUDE_PAYLOAD" --arg enabled "$1" --argjson interval "$INTERVAL_SECONDS" \
        --argjson pagelimit "$PAGE_LIMIT" --arg query "$INCLUDE" --argjson heartbeat "$HEARTBEAT_HOURS" \
    '{collectionSize:1, items:[{service:$service, credentialName:$cred, listenerUrl:$listener,
        includePayload:$incp, enabled:$enabled, intervalSeconds:$interval, pageLimit:$pagelimit,
        queryParameter:$query, heartbeatIntervalHours:$heartbeat}]}'
}

send() { # $1 método, $2 body
  local a=(-s -w $'\n%{http_code}' --max-time 60 -X "$1"
    -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json')
  [[ -n "${2:-}" ]] && a+=(-H 'Content-Type: application/json' --data "$2")
  curl "${a[@]}" "$MANAGE_URL"
}

TOKEN="$(rms_token)" || exit 1

case "$ACTION" in
  register|disable)
    [[ -n "$LISTENER" ]] || { err "--listener é obrigatório p/ $ACTION"; exit 2; }
    local_enabled="Y"; [[ "$ACTION" == "disable" ]] && local_enabled="N"
    hdr "WEBHOOK $ACTION -> $MANAGE_URL"
    info "service=$SERVICE credentialName=$CREDENTIAL_NAME enabled=$local_enabled"
    info "listenerUrl=$LISTENER"
    BODY="$(build_body "$local_enabled")"
    info "body: $BODY"
    resp="$(send "$WEBHOOK_HTTP_METHOD" "$BODY")"
    ;;
  list)
    hdr "WEBHOOK list -> $MANAGE_URL"
    resp="$(send GET "")"
    ;;
  *) err "ação inválida: $ACTION"; exit 2 ;;
esac

code="$(printf '%s' "$resp" | tail -n1)"
body="$(printf '%s' "$resp" | sed '$d')"
printf '%s-- HTTP %s --%s\n' "$C_BLD" "$code" "$C_RST"
printf '%s\n' "$body" | (jq . 2>/dev/null || cat)
case "$code" in
  2*) pass "$ACTION -> HTTP $code" ;;
  30*) fail "$ACTION -> HTTP $code (redirect IDCS Cloud Gate: RMS só aceita de rede allowlistada — rode de dentro da OCI/VPN)" ;;
  401|403) fail "$ACTION -> HTTP $code (auth: credentialName/scope/token)" ;;
  *) fail "$ACTION -> HTTP $code (405/404? ajuste WEBHOOK_HTTP_METHOD/MANAGE_URL)" ;;
esac
summary
