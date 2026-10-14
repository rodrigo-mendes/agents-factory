#!/usr/bin/env bash
# ==============================================================================
# generate-dashboard-traffic.sh — gera massa de dados p/ popular os 3 dashboards
# do func-rr-rest-proxy (Operations Overview, Upstream Dependencies, Route Analytics).
#
# Dispara tráfego real nas rotas ANÔNIMAS do API Gateway, espalhado no tempo p/ as
# séries temporais terem vários pontos:
#   - GET  /proxy/health          -> volume, /health GET (D1, D3)
#   - POST /proxy/item/webhook    -> spans RMS/BrxServices, custom metrics (D1, D2, D3)
#       * PAYLOAD itens válidos    -> 200
#       * PAYLOAD item id vazio    -> 207 (RestProxyError{207})
#       * JSON inválido            -> 400 (RestProxyError{400})
#       * EVENT mode               -> span RMS.ItemsDelta
#
# Store routes (/proxy/store/*) são AUTHENTICATION_ONLY com JWT desabilitado -> não
# chamáveis; widgets de store ficam vazios (esperado). Throttle idem (concorrência 0).
#
# Uso:
#   ./generate-dashboard-traffic.sh [--rounds N] [--sleep SEG] [--url API_BASE_URL]
# Env equivalentes: ROUNDS, SLEEP, API_BASE_URL
#
# Exemplos:
#   ./generate-dashboard-traffic.sh                 # 4 rodadas, sleep 40s (~6-8 min)
#   ROUNDS=2 SLEEP=20 ./generate-dashboard-traffic.sh
# ==============================================================================
set -uo pipefail

ROUNDS="${ROUNDS:-4}"
SLEEP="${SLEEP:-40}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --rounds) ROUNDS="$2"; shift 2 ;;
    --sleep)  SLEEP="$2";  shift 2 ;;
    --url)    API_BASE_URL="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; exit 0 ;;
    *) echo "Argumento desconhecido: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/.." && pwd))"
TF_DIR="${TF_DIR:-$REPO_ROOT/infra/environments/dev}"
SIM="$REPO_ROOT/services/func-rr-rest-proxy/scripts/simulate-webhook.sh"

# --- resolve base URL ---------------------------------------------------------
if [[ -z "${API_BASE_URL:-}" ]]; then
  if command -v terraform >/dev/null 2>&1 && [[ -d "$TF_DIR" ]]; then
    API_BASE_URL="$(terraform -chdir="$TF_DIR" output -raw api_base_url 2>/dev/null || true)"
  fi
fi
if [[ -z "${API_BASE_URL:-}" ]]; then
  echo "ERRO: API_BASE_URL não resolvida (use --url, env, ou 'terraform output api_base_url' em $TF_DIR)" >&2
  exit 1
fi
export API_BASE_URL

hdr() { printf '\n=== %s ===\n' "$*"; }
hit() { # method path [data] -> loga status
  local m="$1" p="$2" d="${3:-}"
  local code
  if [[ "$m" == GET ]]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE_URL$p")
  else
    code=$(curl -s -o /dev/null -w '%{http_code}' -X "$m" -H 'Content-Type: application/json' -d "$d" "$API_BASE_URL$p")
  fi
  printf '  %-4s %-24s -> %s\n' "$m" "$p" "$code"
}

# item ids p/ variar por rodada (existem no RMS de teste)
ITEMSETS=("100010000" "100010000,100010049" "100010000,100010049,100010050" "100010000,100010049,100010050,100010051")

echo "Alvo: $API_BASE_URL | rodadas=$ROUNDS sleep=${SLEEP}s | simulate-webhook: $([[ -x "$SIM" ]] && echo ok || echo AUSENTE)"

for r in $(seq 1 "$ROUNDS"); do
  hdr "Rodada $r/$ROUNDS"

  # Wave 1: health (volume, /health GET)
  for i in 1 2 3; do hit GET /proxy/health; done

  # Wave 2: webhook OK (PAYLOAD itens válidos) — usa simulate-webhook.sh
  if [[ -x "$SIM" ]]; then
    idx=$(( (r-1) % ${#ITEMSETS[@]} ))
    "$SIM" --mode PAYLOAD --items "${ITEMSETS[$idx]}" --uuid "mass-r${r}-ok" 2>&1 | grep -iE 'HTTP|status|PASS|FAIL' | head -3 || true
  else
    hit POST /proxy/item/webhook '{"type":"PAYLOAD","service":"foundation/item","uuid":"mass-r'"$r"'-ok","payload":{"items":[{"action":"UPDATE","item":"100010000","status":"A","itemDescription":"sim"}],"count":1}}'
  fi

  sleep "$SLEEP"

  # Wave 3: webhook 207 (1 item id vazio -> partial failure)
  hit POST /proxy/item/webhook '{"type":"PAYLOAD","service":"foundation/item","uuid":"mass-r'"$r"'-207","payload":{"items":[{"action":"UPDATE","item":"100010000","status":"A","itemDescription":"ok"},{"action":"UPDATE","item":"","status":"A","itemDescription":"invalido"}],"count":2}}'

  # Wave 4: webhook 400 (JSON inválido)
  hit POST /proxy/item/webhook '{"type":"PAYLOAD","payload":{"items":[ BROKEN JSON'

  sleep "$SLEEP"

  # Wave 5: webhook EVENT (span RMS.ItemsDelta)
  if [[ -x "$SIM" ]]; then
    "$SIM" --mode EVENT --uuid "mass-r${r}-event" 2>&1 | grep -iE 'HTTP|status|PASS|FAIL' | head -3 || true
  else
    hit POST /proxy/item/webhook '{"type":"EVENT","service":"foundation/item","uuid":"mass-r'"$r"'-event","since":"2026-05-29T02:27:59.838Z"}'
  fi

  [[ "$r" -lt "$ROUNDS" ]] && sleep "$SLEEP"
done

hdr "Massa concluída"
echo "Espere ~3 min (ingest de métrica) / alguns min (traces APM), depois valide os dashboards."
