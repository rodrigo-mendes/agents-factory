#!/usr/bin/env bash
# ==============================================================================
# check-traces.sh — validação (best-effort) de traces no APM Domain.
#
# A consulta de traces via OCI CLI é limitada; este script tenta as APIs
# disponíveis e, se não houver, orienta a validação manual no console APM.
# Pré-condição real p/ traces: functions com APM_DOMAIN_URL + APM_DATA_KEY no
# config (ver Problema #1 do plano). Sem isso, o exportador OTel não inicializa.
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"
require_tools
require_session

hdr "CHECK TRACES — OCI APM (últimos ${LOOKBACK_MIN}min)"

if [[ -z "$APM_DOMAIN_ID" ]]; then
  skip "apm_domain_id não encontrado nos outputs; pulei validação de traces."
  summary; exit 0
fi
info "APM Domain: $APM_DOMAIN_ID"

start="$(iso_minus_min "$LOOKBACK_MIN")"
end="$(iso_now)"

# 1) Confirma que o config das functions carrega APM (pré-requisito de traces).
hdr "Pré-requisito: APM_DOMAIN_URL/APM_DATA_KEY no config das functions"
missing=0
for meta in "${FUNCTIONS_META[@]}"; do
  IFS='|' read -r label app_id _ns _pref _fn <<< "$meta"
  cfg="$(oci_cli fn application get --application-id "$app_id" 2>/dev/null \
        | jq -r '.data.config // {} | keys | join(",")' 2>/dev/null)"
  if printf '%s' "$cfg" | grep -q 'APM_DATA_KEY' && printf '%s' "$cfg" | grep -q 'APM_DOMAIN_URL'; then
    pass "$label: APM_DOMAIN_URL + APM_DATA_KEY presentes no config."
  else
    fail "$label: config sem APM_* (keys atuais: ${cfg:-<vazio>}) -> traces NÃO fluem."
    missing=1
  fi
done

# 2) Ingestão de traces via métricas oci_apm (confiável; a query TQL via CLI é instável).
#    IngestedBytes > 0 e PayloadRejections == 0 provam que os spans OTLP são aceitos.
hdr "Ingestão de traces (namespace oci_apm)"
mstart="$(iso_minus_min "$LOOKBACK_MIN")"
mend="$(iso_now)"
apm_dp() {
  oci_cli monitoring metric-data summarize-metrics-data \
    --compartment-id "$COMPARTMENT_OCID" --namespace oci_apm \
    --query-text "$1" --start-time "$mstart" --end-time "$mend" 2>/dev/null \
    | jq -r '[.data[]?."aggregated-datapoints"[]?.value] | add // 0'
}
ingested="$(apm_dp 'IngestedBytes[1m].sum()')"
rejections="$(apm_dp 'PayloadRejections[1m].sum()')"
info "IngestedBytes=${ingested:-0} | PayloadRejections=${rejections:-0} (janela ${LOOKBACK_MIN}min)"

if awk "BEGIN{exit !(${ingested:-0} > 0)}"; then
  pass "APM ingerindo traces (IngestedBytes=${ingested})."
else
  skip "IngestedBytes=0 (ingestão tem latência de minutos; gere tráfego e reexecute)."
fi
if awk "BEGIN{exit !(${rejections:-0} > 0)}"; then
  fail "PayloadRejections=${rejections} > 0 — spans OTLP sendo REJEITADOS (endpoint/formato errado). Ver dim RejectionCause."
else
  pass "PayloadRejections=0 — nenhum payload OTLP rejeitado."
fi

[[ "$missing" -eq 0 ]] || warn "Traces não vão aparecer enquanto o config APM estiver ausente (rode terraform apply)."
summary
