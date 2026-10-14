#!/usr/bin/env bash
# ==============================================================================
# smoke-invoke.sh — invoca as rotas públicas do API Gateway para gerar tráfego
# (logs, métricas e traces). Valida os códigos HTTP retornados.
#
# Uso: ./smoke-invoke.sh [N_REPEAT]
#   N_REPEAT: quantas vezes repetir cada rota (default 3, aquece cold start).
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

REPEAT="${1:-3}"
require_tools

hdr "SMOKE TEST — $API_BASE_URL (x$REPEAT por rota)"

# rota|método|body|códigos_esperados(regex)
ROUTES=(
  "/health|GET||^(200|204)$"
  "/hello|GET||^200$"
  "/hello|POST|{\"name\":\"smoke\"}|^200$"
  "/handler/health|GET||^200$"
  "/facade/hello|GET||^200$"
  "/facade/health|GET||^200$"
  "/proxy/health|GET||^200$"
)

for entry in "${ROUTES[@]}"; do
  IFS='|' read -r path method body expect <<< "$entry"
  url="${API_BASE_URL}${path}"
  last_code=""
  for _ in $(seq 1 "$REPEAT"); do
    if [[ "$method" == "GET" ]]; then
      last_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 65 "$url")"
    else
      last_code="$(curl -s -o /dev/null -w '%{http_code}' --max-time 65 \
        -X "$method" -H 'Content-Type: application/json' \
        --data "${body:-{}}" "$url")"
    fi
  done
  if [[ "$last_code" =~ $expect ]]; then
    pass "$method $path -> HTTP $last_code"
  else
    fail "$method $path -> HTTP $last_code (esperado $expect)"
  fi
done

info "Tráfego gerado. Aguarde ~1-3min para ingestão de logs/métricas antes de validar."
summary
