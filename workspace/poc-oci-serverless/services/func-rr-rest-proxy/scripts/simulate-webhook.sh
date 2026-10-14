#!/usr/bin/env bash
# ==============================================================================
# simulate-webhook.sh — simula a engine de webhook do RMS chamando a function.
#
# Faz POST de um envelope EVENT ou PAYLOAD (customizada) na rota
# /proxy/item/webhook do API Gateway, como o RMS faria. Serve para testar o
# fluxo ponta-a-ponta (parse -> enrich por id -> BrxServices) sem depender do
# RMS disparar de verdade.
#
# Uso:
#   ./simulate-webhook.sh [--mode EVENT|PAYLOAD] [--items id1,id2,...]
#                         [--uuid <id>] [--url <API_BASE_URL>]
#
# Exemplos:
#   ./simulate-webhook.sh                              # PAYLOAD, 3 itens default
#   ./simulate-webhook.sh --mode EVENT
#   ./simulate-webhook.sh --items 100010000,100010049
#   API_BASE_URL=https://gw/v1 ./simulate-webhook.sh
# ==============================================================================
set -uo pipefail

# --- defaults (sobrescrevíveis por env/arg) -----------------------------------
MODE="${MODE:-PAYLOAD}"
ITEMS="${ITEMS:-100010000,100010049,100010050}"
UUID="${UUID:-sim-webhook-0001}"
LISTENER_PATH="${LISTENER_PATH:-/proxy/item/webhook}"
SERVICE="${SERVICE:-foundation/item}"
# Timestamps fixos (evita depender de `date`); só rótulos no envelope.
TIMESTAMP="${TIMESTAMP:-2026-05-29T13:35:59.223Z}"
SINCE="${SINCE:-2026-05-29T02:27:59.838Z}"

# --- parse args ---------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode)  MODE="$2"; shift 2 ;;
    --items) ITEMS="$2"; shift 2 ;;
    --uuid)  UUID="$2"; shift 2 ;;
    --url)   API_BASE_URL="$2"; shift 2 ;;
    -h|--help)
      grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; exit 0 ;;
    *) echo "Argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done

MODE="$(printf '%s' "$MODE" | tr '[:lower:]' '[:upper:]')"

# --- cores / helpers ----------------------------------------------------------
if [[ -t 1 ]]; then
  C_RED=$'\033[0;31m'; C_GRN=$'\033[0;32m'; C_YLW=$'\033[0;33m'; C_BLD=$'\033[1m'; C_RST=$'\033[0m'
else C_RED=""; C_GRN=""; C_YLW=""; C_BLD=""; C_RST=""; fi
PASS=0; FAIL=0
info() { printf '[i] %s\n' "$*"; }
hdr()  { printf '\n%s== %s ==%s\n' "$C_BLD" "$*" "$C_RST"; }
pass() { PASS=$((PASS+1)); printf '%s  PASS%s %s\n' "$C_GRN" "$C_RST" "$*"; }
fail() { FAIL=$((FAIL+1)); printf '%s  FAIL%s %s\n' "$C_RED" "$C_RST" "$*"; }

# --- resolve base URL ---------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/../../.." && pwd))"
TF_DIR="${TF_DIR:-$REPO_ROOT/infra/environments/dev}"
if [[ -z "${API_BASE_URL:-}" ]]; then
  if command -v terraform >/dev/null 2>&1 && [[ -d "$TF_DIR" ]]; then
    API_BASE_URL="$(terraform -chdir="$TF_DIR" output -raw api_base_url 2>/dev/null || true)"
  fi
fi
if [[ -z "${API_BASE_URL:-}" ]]; then
  echo "${C_RED}ERRO${C_RST}: API_BASE_URL não resolvida (use --url ou env, ou 'terraform output api_base_url' em $TF_DIR)" >&2
  exit 1
fi
URL="${API_BASE_URL}${LISTENER_PATH}"

# --- monta envelope -----------------------------------------------------------
build_payload_items() {
  local out="" first=1 id
  IFS=',' read -ra arr <<< "$ITEMS"
  for id in "${arr[@]}"; do
    id="$(printf '%s' "$id" | tr -d '[:space:]')"
    [[ -z "$id" ]] && continue
    [[ $first -eq 0 ]] && out+=","
    out+="{\"action\":\"UPDATE\",\"item\":\"$id\",\"status\":\"A\",\"itemDescription\":\"sim $id\"}"
    first=0
  done
  printf '%s' "$out"
}

case "$MODE" in
  EVENT)
    BODY="{\"type\":\"EVENT\",\"timestamp\":\"$TIMESTAMP\",\"service\":\"$SERVICE\",\"uuid\":\"$UUID\",\"environment\":\"rgbu-rex-brxs-par1-mfcs\",\"since\":\"$SINCE\"}"
    ;;
  PAYLOAD)
    items_json="$(build_payload_items)"
    count="$(awk -F',' '{print NF}' <<< "$ITEMS")"
    BODY="{\"type\":\"PAYLOAD\",\"timestamp\":\"$TIMESTAMP\",\"service\":\"$SERVICE\",\"uuid\":\"$UUID\",\"environment\":\"rgbu-rex-brxs-par1-mfcs\",\"since\":\"$SINCE\",\"payload\":{\"items\":[$items_json],\"hasMore\":false,\"limit\":1000,\"count\":$count}}"
    ;;
  *) echo "MODE inválido: $MODE (use EVENT ou PAYLOAD)" >&2; exit 2 ;;
esac

# --- envia --------------------------------------------------------------------
hdr "SIMULATE WEBHOOK ($MODE) -> $URL"
info "uuid=$UUID  items=$ITEMS"
info "body: $BODY"

resp="$(curl -s -w '\n%{http_code}' --max-time 65 \
  -X POST -H 'Content-Type: application/json' --data "$BODY" "$URL")"
code="$(printf '%s' "$resp" | tail -n1)"
body="$(printf '%s' "$resp" | sed '$d')"

printf '%s-- resposta --%s\n%s\n' "$C_BLD" "$C_RST" "$body"
if [[ "$code" =~ ^(200|207)$ ]]; then
  pass "POST $LISTENER_PATH ($MODE) -> HTTP $code"
else
  fail "POST $LISTENER_PATH ($MODE) -> HTTP $code (esperado 200/207)"
fi

printf '\n%sRESULTADO:%s %sPASS=%d%s %sFAIL=%d%s\n' \
  "$C_BLD" "$C_RST" "$C_GRN" "$PASS" "$C_RST" "$C_RED" "$FAIL" "$C_RST"
info "Valide logs ENRICH/TRANSFORM/BRX_SEND via skill validating-oci-observability."
[[ "$FAIL" -eq 0 ]]
