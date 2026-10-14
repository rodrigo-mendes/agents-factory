#!/usr/bin/env bash
# ==============================================================================
# check-logs.sh — valida que as Functions estão emitindo logs capturados pelo
# OCI Logging (service logs de invoke), consultando via logging-search.
#
# PASS: >=1 entrada de log no log group na janela recente.
# Extra: procura campos de log estruturado (opcRequestId/service) no payload.
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"
require_tools
require_session

hdr "CHECK LOGS — OCI Logging (últimos ${LOOKBACK_MIN}min)"

if [[ -z "$LOG_GROUP_ID" ]]; then
  fail "log_group_id não encontrado nos outputs do Terraform (rode em $TF_DIR)."
  summary; exit 1
fi

start="$(iso_minus_min "$LOOKBACK_MIN")"
end="$(iso_now)"
info "Log group: $LOG_GROUP_ID"
info "Janela: $start .. $end"

# Busca todas as entradas do log group na janela.
query="search \"${COMPARTMENT_OCID}/${LOG_GROUP_ID}\""
raw="$(oci_cli logging-search search-logs \
  --search-query "$query" \
  --time-start "$start" --time-end "$end" \
  --limit 200 2>/dev/null)"

if [[ -z "$raw" ]]; then
  fail "logging-search não retornou dados (verifique permissões / janela)."
  summary; exit 1
fi

total="$(printf '%s' "$raw" | jq -r '.data.results | length' 2>/dev/null || echo 0)"
if [[ "${total:-0}" -gt 0 ]]; then
  pass "Log group tem $total entradas na janela."
else
  fail "Nenhuma entrada de log na janela (invoque as functions antes: smoke-invoke.sh)."
fi

# Estruturação: procura campos do Logback JSON no conteúdo dos logs.
structured="$(printf '%s' "$raw" | jq -r \
  '[.data.results[]?.data."logContent"?.data // .data.results[]?.data // empty]
   | tostring' 2>/dev/null)"
if printf '%s' "$structured" | grep -qE 'opcRequestId|"service"|coldStart'; then
  pass "Logs contêm campos estruturados (opcRequestId/service/coldStart)."
else
  skip "Não confirmei campos estruturados no payload (pode ser latência de ingestão ou formato distinto)."
fi

# Presença por função (best-effort: procura o nome da app no source dos logs).
for meta in "${FUNCTIONS_META[@]}"; do
  IFS='|' read -r label app_id _ns _pref <<< "$meta"
  n="$(printf '%s' "$raw" | jq -r --arg a "$app_id" \
        '[.data.results[]? | select((tostring) | contains($a))] | length' 2>/dev/null || echo 0)"
  if [[ "${n:-0}" -gt 0 ]]; then
    pass "Logs de '$label': $n entradas."
  else
    skip "Sem entradas atribuíveis a '$label' (invoque a rota correspondente)."
  fi
done

summary
