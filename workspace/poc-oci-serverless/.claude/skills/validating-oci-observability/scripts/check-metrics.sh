#!/usr/bin/env bash
# ==============================================================================
# check-metrics.sh — valida métricas de plataforma (oci_faas) e custom
# (namespaces por serviço) via Monitoring summarize-metrics-data.
#
# Também diagnostica se o filtro resourceId usado pelos ALARMES (app OCID)
# realmente casa com a dimensão da métrica oci_faas (que costuma ser function
# OCID). Se só o function OCID retornar dados, os alarmes não disparam.
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"
require_tools
require_session

hdr "CHECK METRICS — OCI Monitoring (últimos ${LOOKBACK_MIN}min)"

start="$(iso_minus_min "$LOOKBACK_MIN")"
end="$(iso_now)"

# summarize <namespace> <mql> -> imprime nº de datapoints (0 se nada)
summarize() {
  local ns="$1" mql="$2" out
  out="$(oci_cli monitoring metric-data summarize-metrics-data \
    --compartment-id "$COMPARTMENT_OCID" \
    --namespace "$ns" \
    --query-text "$mql" \
    --start-time "$start" --end-time "$end" 2>/dev/null)"
  printf '%s' "$out" | jq -r \
    '[.data[]?."aggregated-datapoints"[]?] | length' 2>/dev/null || echo 0
}

# --- 1) Plataforma oci_faas (compartment-wide, sem filtro) ---
info "Namespace de plataforma: oci_faas"
dp="$(summarize oci_faas 'FunctionInvocationCount[1m].sum()')"
if [[ "${dp:-0}" -gt 0 ]]; then
  pass "oci_faas/FunctionInvocationCount: $dp datapoints (plataforma emitindo)."
else
  fail "oci_faas/FunctionInvocationCount sem datapoints (invoque as functions)."
fi

# --- 2) Diagnóstico do filtro resourceId dos alarmes (app vs function) ---
hdr "Diagnóstico dimensão resourceId (validação dos alarmes)"
for meta in "${FUNCTIONS_META[@]}"; do
  IFS='|' read -r label app_id ns pref fn_id <<< "$meta"
  # Dimensão canônica confirmada ao vivo p/ oci_faas: applicationId (a que os alarmes usam).
  by_app="$(summarize oci_faas "FunctionInvocationCount[5m]{applicationId = \"$app_id\"}.sum()")"
  by_fn="$(summarize oci_faas "FunctionInvocationCount[5m]{resourceId = \"$fn_id\"}.sum()")"
  info "$label: applicationId=app -> ${by_app:-0} dp | resourceId=function -> ${by_fn:-0} dp"
  if [[ "${by_app:-0}" -gt 0 ]]; then
    pass "$label: filtro dos alarmes (applicationId) casa — alarmes recebem dados."
  elif [[ "${by_fn:-0}" -gt 0 ]]; then
    fail "$label: métrica só casa por resourceId=FUNCTION, não applicationId. Revisar query dos alarmes."
  else
    skip "$label: sem datapoints em nenhuma dimensão (gere tráfego e reexecute)."
  fi
done

# --- 3) Custom metrics por serviço ---
hdr "Custom metrics (namespaces por serviço)"
for meta in "${FUNCTIONS_META[@]}"; do
  IFS='|' read -r label app_id ns pref fn_id <<< "$meta"
  dp="$(summarize "$ns" "${pref}Invocation[5m].sum()")"
  if [[ "${dp:-0}" -gt 0 ]]; then
    pass "$ns/${pref}Invocation: $dp datapoints."
  else
    fail "$ns/${pref}Invocation sem datapoints (config env vazia? veja Problema #1 do plano)."
  fi
done

summary
