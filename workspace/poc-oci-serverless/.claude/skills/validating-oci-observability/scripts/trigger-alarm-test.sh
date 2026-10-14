#!/usr/bin/env bash
# ==============================================================================
# trigger-alarm-test.sh — dispara um cenário de erro controlado para validar
# ponta-a-ponta o caminho métrica -> alarme -> notificação.
#
# Estratégia: envia N requisições inválidas a uma rota ANÔNIMA que exercita
# caminho de erro (default /proxy/item/webhook) para gerar 5xx / FunctionError,
# depois faz polling do alarm-status até FIRING (janela do alarme = PT5M).
#
# Uso: ./trigger-alarm-test.sh [N_ERROS] [POLL_MAX_MIN]
#   N_EROS (default 15) | POLL_MAX_MIN (default 8)
#
# ATENÇÃO: gera erros reais nas métricas. Use só em dev. Os alarmes voltam a OK
# sozinhos após a janela sem novos erros.
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"
require_tools
require_session

N_ERR="${1:-15}"
POLL_MAX_MIN="${2:-8}"
TARGET_PATH="${TARGET_PATH:-/proxy/item/webhook}"
url="${API_BASE_URL}${TARGET_PATH}"

hdr "TRIGGER ALARM TEST — $N_ERR requisições inválidas em $TARGET_PATH"
warn "Isto injeta erros reais nas métricas de dev (para testar o alarme)."

# bash 3.2 (macOS default) não tem `declare -A` — acumula códigos num arquivo temp.
codes_file="$(mktemp)"
trap 'rm -f "$codes_file"' EXIT
for i in $(seq 1 "$N_ERR"); do
  c="$(curl -s -o /dev/null -w '%{http_code}' --max-time 65 \
        -X POST -H 'Content-Type: application/json' \
        --data '{"__invalid__":true,"trigger":"alarm-test","n":'"$i"'}' "$url")"
  printf '%s\n' "$c" >> "$codes_file"
  printf '.'
done
printf '\n'

info "Distribuição de códigos HTTP gerados:"
sort "$codes_file" | uniq -c | awk '{printf "   HTTP %s x%s\n", $2, $1}'

got5xx=0
grep -qE '^5' "$codes_file" && got5xx=1
if [[ "$got5xx" -eq 1 ]]; then
  pass "Gerou respostas 5xx — deve acionar alarm-apigw-5xx e/ou alarm-fn-errors."
else
  skip "App tratou todas as entradas sem 5xx. Para forçar FunctionError real, invoque"
  skip "diretamente com payload que estoure exceção, ou induza falha de downstream."
fi

# Polling do status dos alarmes-alvo até FIRING (ou timeout).
hdr "Aguardando alarme -> FIRING (janela PT5M; timeout ${POLL_MAX_MIN}min)"
deadline=$(( $(date -u +%s) + POLL_MAX_MIN*60 ))
fired=0
while [[ "$(date -u +%s)" -lt "$deadline" ]]; do
  status="$(oci_cli monitoring alarm-status list-alarms-status --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null)"
  hits="$(printf '%s' "$status" | jq -r \
    '[.data[]? | select(.status=="FIRING") | select((."display-name"|test("errors|5xx";"i")))] | .[]."display-name"' 2>/dev/null)"
  if [[ -n "$hits" ]]; then
    fired=1
    pass "Alarme(s) em FIRING:"
    printf '%s\n' "$hits" | sed 's/^/     - /'
    break
  fi
  printf '   %s aguardando...\n' "$(date -u +%H:%M:%S)"
  sleep 30
done

if [[ "$fired" -eq 1 ]]; then
  info "Se a subscription estiver ACTIVE, um email deve chegar em rodrigo.mendes@brxretail.com."
else
  fail "Nenhum alarme de erro/5xx entrou em FIRING dentro de ${POLL_MAX_MIN}min."
  info "Cheque: (a) métrica de erro casa com o resourceId do alarme (check-metrics.sh); (b) tráfego realmente 5xx."
fi

info "Os alarmes retornam a OK sozinhos após a janela sem novos erros."
summary
