#!/usr/bin/env bash
# ==============================================================================
# simulate-webhook.sh — simula a engine de webhook do RMS fazendo POST de um
# envelope EVENT/PAYLOAD numa listenerUrl (a function consumidora). Testa o
# fluxo sem depender do RMS disparar.
#
# Uso:
#   ./simulate-webhook.sh --listener https://gw/v1/proxy/item/webhook
#   ./simulate-webhook.sh --listener <url> --mode EVENT
#   ./simulate-webhook.sh --listener <url> --service foundation/item --items 100010000,100010049
#
# Opções: --listener <url> (obrigatório) | --mode EVENT|PAYLOAD (default PAYLOAD)
#         --service <s> (default foundation/item) | --items csv | --uuid <id>
#         --expect <regex> (default ^(200|207)$)
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-rms.sh"
require_tools

LISTENER=""; MODE="PAYLOAD"; SERVICE="foundation/item"
ITEMS="${ITEMS:-100010000,100010049,100010050}"; UUID="${UUID:-sim-webhook-0001}"
EXPECT='^(200|207)$'
TIMESTAMP="${TIMESTAMP:-2026-05-29T13:35:59.223Z}"; SINCE="${SINCE:-2026-05-29T02:27:59.838Z}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --listener) LISTENER="$2"; shift 2 ;;
    --mode)     MODE="$2"; shift 2 ;;
    --service)  SERVICE="$2"; shift 2 ;;
    --items)    ITEMS="$2"; shift 2 ;;
    --uuid)     UUID="$2"; shift 2 ;;
    --expect)   EXPECT="$2"; shift 2 ;;
    -h|--help)  grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; exit 0 ;;
    *) err "arg desconhecido: $1"; exit 2 ;;
  esac
done
MODE="$(printf '%s' "$MODE" | tr '[:lower:]' '[:upper:]')"
[[ -n "$LISTENER" ]] || { err "--listener é obrigatório"; exit 2; }

build_items() {
  local out="" first=1 id
  IFS=',' read -ra arr <<< "$ITEMS"
  for id in "${arr[@]}"; do
    id="$(printf '%s' "$id" | tr -d '[:space:]')"; [[ -z "$id" ]] && continue
    [[ $first -eq 0 ]] && out+=","
    out+="{\"action\":\"UPDATE\",\"item\":\"$id\",\"status\":\"A\",\"itemDescription\":\"sim $id\"}"
    first=0
  done
  printf '%s' "$out"
}

case "$MODE" in
  EVENT)
    BODY="{\"type\":\"EVENT\",\"timestamp\":\"$TIMESTAMP\",\"service\":\"$SERVICE\",\"uuid\":\"$UUID\",\"environment\":\"rgbu-rex-brxs-par1-mfcs\",\"since\":\"$SINCE\"}" ;;
  PAYLOAD)
    items="$(build_items)"; count="$(awk -F',' '{print NF}' <<< "$ITEMS")"
    BODY="{\"type\":\"PAYLOAD\",\"timestamp\":\"$TIMESTAMP\",\"service\":\"$SERVICE\",\"uuid\":\"$UUID\",\"environment\":\"rgbu-rex-brxs-par1-mfcs\",\"since\":\"$SINCE\",\"payload\":{\"items\":[$items],\"hasMore\":false,\"limit\":1000,\"count\":$count}}" ;;
  *) err "MODE inválido: $MODE (EVENT|PAYLOAD)"; exit 2 ;;
esac

hdr "SIMULATE WEBHOOK ($MODE, $SERVICE) -> $LISTENER"
info "uuid=$UUID items=$ITEMS"
info "body: $BODY"
resp="$(curl -s -w $'\n%{http_code}' --max-time 65 -X POST -H 'Content-Type: application/json' --data "$BODY" "$LISTENER")"
code="$(printf '%s' "$resp" | tail -n1)"; body="$(printf '%s' "$resp" | sed '$d')"
printf '%s-- resposta (HTTP %s) --%s\n%s\n' "$C_BLD" "$code" "$C_RST" "$body"
if [[ "$code" =~ $EXPECT ]]; then pass "POST ($MODE) -> HTTP $code"
elif [[ "$code" == "000" ]]; then skip "HTTP 000 (cold start) — repita p/ aquecer"
else fail "POST ($MODE) -> HTTP $code (esperado $EXPECT)"; fi
summary
