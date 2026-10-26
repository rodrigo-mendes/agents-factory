#!/usr/bin/env bash
# ==============================================================================
# generate-dashboard-traffic.sh — generates load to populate the 3 dashboards
# of func-rr-rest-proxy (Operations Overview, Upstream Dependencies, Route Analytics).
#
# Fires real traffic on the ANONYMOUS routes of the API Gateway, spread over time
# so time-series widgets have multiple data points:
#   - GET  /proxy/health          -> volume, /health GET (D1, D3)
#   - POST /proxy/item/webhook    -> spans RMS/BrxServices, custom metrics (D1, D2, D3)
#       * PAYLOAD valid items      -> 200
#       * PAYLOAD empty item id    -> 207 (RestProxyError{207})
#       * Invalid JSON             -> 400 (RestProxyError{400})
#       * EVENT mode               -> span RMS.ItemsDelta
#
# Store routes (/proxy/store/*) are AUTHENTICATION_ONLY (JWT disabled) -> not
# callable; store widgets remain empty (expected). Throttle likewise.
#
# All configurable values are exposed as environment variables or CLI flags.
# No OCIDs, tenancy IDs, profile names, or namespaces are hardcoded.
#
# Usage (all parameters are optional — env vars or flags):
#   ./generate-dashboard-traffic.sh [--rounds N] [--sleep SEC] [--url API_BASE_URL]
#
# Environment variables (can replace any flag):
#   ROUNDS          Number of traffic rounds          (default: 4)
#   SLEEP           Seconds to sleep between waves    (default: 40)
#   API_BASE_URL    API Gateway base URL              (resolved via terraform output if not set)
#   TF_DIR          Terraform environment directory   (default: <repo-root>/infra/environments/dev)
#
# Examples:
#   ./generate-dashboard-traffic.sh
#   ./generate-dashboard-traffic.sh --rounds 2 --sleep 20
#   ./generate-dashboard-traffic.sh --url https://abc123.apigateway.sa-saopaulo-1.oci.customer-oci.com
#   ROUNDS=6 SLEEP=30 ./generate-dashboard-traffic.sh
#   API_BASE_URL=https://abc123... ./generate-dashboard-traffic.sh --rounds 2
#
# Source: workspace/poc-oci-serverless/scripts/generate-dashboard-traffic.sh
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
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/../../../../../.." && pwd))"
TF_DIR="${TF_DIR:-$REPO_ROOT/infra/environments/dev}"
SIM="${SIM:-$REPO_ROOT/services/func-rr-rest-proxy/scripts/simulate-webhook.sh}"

# --- resolve base URL ---------------------------------------------------------
if [[ -z "${API_BASE_URL:-}" ]]; then
  if command -v terraform >/dev/null 2>&1 && [[ -d "$TF_DIR" ]]; then
    API_BASE_URL="$(terraform -chdir="$TF_DIR" output -raw api_base_url 2>/dev/null || true)"
  fi
fi
if [[ -z "${API_BASE_URL:-}" ]]; then
  echo "ERROR: API_BASE_URL not resolved." >&2
  echo "  Options:" >&2
  echo "    --url <url>                       pass via flag" >&2
  echo "    API_BASE_URL=<url> ./script.sh    pass via env var" >&2
  echo "    terraform output api_base_url     from $TF_DIR (requires active Terraform state)" >&2
  exit 1
fi
export API_BASE_URL

# item ids per round (arbitrary test identifiers — not infrastructure OCIDs)
ITEM_SET_1="${ITEM_SET_1:-100010000}"
ITEM_SET_2="${ITEM_SET_2:-100010000,100010049}"
ITEM_SET_3="${ITEM_SET_3:-100010000,100010049,100010050}"
ITEM_SET_4="${ITEM_SET_4:-100010000,100010049,100010050,100010051}"
ITEMSETS=("$ITEM_SET_1" "$ITEM_SET_2" "$ITEM_SET_3" "$ITEM_SET_4")

hdr() { printf '\n=== %s ===\n' "$*"; }
hit() { # method path [data] -> log status code
  local m="$1" p="$2" d="${3:-}"
  local code
  if [[ "$m" == GET ]]; then
    code=$(curl -s -o /dev/null -w '%{http_code}' "$API_BASE_URL$p")
  else
    code=$(curl -s -o /dev/null -w '%{http_code}' -X "$m" -H 'Content-Type: application/json' -d "$d" "$API_BASE_URL$p")
  fi
  printf '  %-4s %-24s -> %s\n' "$m" "$p" "$code"
}

echo "Target: $API_BASE_URL | rounds=$ROUNDS sleep=${SLEEP}s | simulate-webhook: $([[ -x "$SIM" ]] && echo ok || echo absent)"

for r in $(seq 1 "$ROUNDS"); do
  hdr "Round $r/$ROUNDS"

  # Wave 1: health (volume, /health GET)
  for i in 1 2 3; do hit GET /proxy/health; done

  # Wave 2: webhook OK (valid PAYLOAD) — uses simulate-webhook.sh if present
  if [[ -x "$SIM" ]]; then
    idx=$(( (r-1) % ${#ITEMSETS[@]} ))
    "$SIM" --mode PAYLOAD --items "${ITEMSETS[$idx]}" --uuid "mass-r${r}-ok" 2>&1 \
      | grep -iE 'HTTP|status|PASS|FAIL' | head -3 || true
  else
    hit POST /proxy/item/webhook \
      '{"type":"PAYLOAD","service":"foundation/item","uuid":"mass-r'"$r"'-ok","payload":{"items":[{"action":"UPDATE","item":"100010000","status":"A","itemDescription":"sim"}],"count":1}}'
  fi

  sleep "$SLEEP"

  # Wave 3: webhook 207 (one empty item id -> partial failure)
  hit POST /proxy/item/webhook \
    '{"type":"PAYLOAD","service":"foundation/item","uuid":"mass-r'"$r"'-207","payload":{"items":[{"action":"UPDATE","item":"100010000","status":"A","itemDescription":"ok"},{"action":"UPDATE","item":"","status":"A","itemDescription":"invalid"}],"count":2}}'

  # Wave 4: webhook 400 (malformed JSON -> parse error)
  hit POST /proxy/item/webhook '{"type":"PAYLOAD","payload":{"items":[ BROKEN JSON'

  sleep "$SLEEP"

  # Wave 5: webhook EVENT (triggers span RMS.ItemsDelta in APM)
  if [[ -x "$SIM" ]]; then
    "$SIM" --mode EVENT --uuid "mass-r${r}-event" 2>&1 \
      | grep -iE 'HTTP|status|PASS|FAIL' | head -3 || true
  else
    hit POST /proxy/item/webhook \
      '{"type":"EVENT","service":"foundation/item","uuid":"mass-r'"$r"'-event","since":"2026-05-29T02:27:59.838Z"}'
  fi

  [[ "$r" -lt "$ROUNDS" ]] && sleep "$SLEEP"
done

hdr "Traffic generation complete"
echo "Wait ~3 min (metric ingestion latency) / a few min (APM trace ingestion), then validate dashboards."
echo "  check-dashboards.sh                        # render-readiness (5th pillar)"
echo "  check-dashboards.sh --name-filter '<name>' # single dashboard"
