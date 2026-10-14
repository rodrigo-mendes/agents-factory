#!/usr/bin/env bash
# ==============================================================================
# rms-get.sh — GET em endpoints foundation do RMS/MFCS (by-id ou delta).
#
#   by-id : GET {base}/services/foundation/<ent>/<id>        (path-param)
#   delta : GET {base}/services/foundation/<ent>?since=&before=&limit=&include=
#
# Uso:
#   ./rms-get.sh --entity item --id 100010000
#   ./rms-get.sh --entity item --since 2026-05-29T02:01:56Z --before 2026-05-29T02:06:57Z
#   ./rms-get.sh --entity item --since ... --include "items.item,items.itemDescription"
#   ./rms-get.sh --entity diffid --id G_COLOR
#
# Opções: --entity <e> (default item) | --id <id> | --since <ts> | --before <ts>
#         --limit <n> (default 1000) | --include <csv> | --raw (só body)
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-rms.sh"
require_tools

ENTITY="item"; ID=""; SINCE=""; BEFORE=""; LIMIT="1000"; INCLUDE=""; RAW=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --entity)  ENTITY="$2"; shift 2 ;;
    --id)      ID="$2"; shift 2 ;;
    --since)   SINCE="$2"; shift 2 ;;
    --before)  BEFORE="$2"; shift 2 ;;
    --limit)   LIMIT="$2"; shift 2 ;;
    --include) INCLUDE="$2"; shift 2 ;;
    --raw)     RAW=1; shift ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; exit 0 ;;
    *) err "arg desconhecido: $1"; exit 2 ;;
  esac
done

# urlencode simples (via jq)
enc() { printf '%s' "$1" | jq -sRr @uri; }

URL="$(rms_url "$ENTITY" "$ID")"
if [[ -z "$ID" ]]; then
  sep="?"
  [[ -n "$LIMIT" ]]   && { URL+="${sep}limit=$LIMIT"; sep="&"; }
  [[ -n "$SINCE" ]]   && { URL+="${sep}since=$(enc "$SINCE")"; sep="&"; }
  [[ -n "$BEFORE" ]]  && { URL+="${sep}before=$(enc "$BEFORE")"; sep="&"; }
  [[ -n "$INCLUDE" ]] && { URL+="${sep}include=$(enc "$INCLUDE")"; sep="&"; }
fi

TOKEN="$(rms_token)" || exit 1

[[ $RAW -eq 0 ]] && { hdr "RMS GET ${ENTITY}${ID:+/$ID}"; info "$URL"; }

resp="$(curl -s -w $'\n%{http_code}' --max-time 60 \
  -H "Authorization: Bearer $TOKEN" -H 'Accept: application/json' "$URL")"
code="$(printf '%s' "$resp" | tail -n1)"
body="$(printf '%s' "$resp" | sed '$d')"

if [[ $RAW -eq 1 ]]; then printf '%s\n' "$body"; else
  printf '%s-- HTTP %s --%s\n' "$C_BLD" "$code" "$C_RST"
  printf '%s\n' "$body" | (jq . 2>/dev/null || cat)
fi
case "$code" in
  2*) ;;
  30*) err "HTTP $code → redirect IDCS Cloud Gate. RMS só aceita de rede allowlistada (egress OCI/VPN); local recebe 302. Rode de dentro da OCI ou via VPN."; exit 1 ;;
  404) err "HTTP 404 — id inexistente OU path errado (base MerchIntegrations? /foundation/<ent>/{id}?)"; exit 1 ;;
  401|403) err "HTTP $code — token/scope não aceitos"; exit 1 ;;
  *) err "HTTP $code"; exit 1 ;;
esac
