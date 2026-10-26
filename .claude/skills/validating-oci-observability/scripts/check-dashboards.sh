#!/usr/bin/env bash
# ==============================================================================
# check-dashboards.sh — 5º pilar: valida que os Management Dashboards RENDERIZAM.
#
# Import válido ≠ render válido: o `oci_management_dashboard_management_dashboards_import`
# aceita JSON estruturalmente correto que o Console não consegue desenhar. Este check
# valida os campos de render-readiness que faltavam nos pos-mortems P7/P8/P10:
#   - dashboard em estado ACTIVE
#   - cada saved-search tem widget-template + widget-vm (não vazios)
#   - data-config[].type ∈ {monitoringDataSource, tracesDataSource}
#   - metric widgets (monitoringDataSource) declaram o param `regionName`
#     (senão importa mas fica em branco — P10)
#   - cross-check: há datapoints por trás (custom namespace + oci_faas) => ingestão
#
# Uso: ./check-dashboards.sh [--name-filter "REST Proxy"]
# Env: OCI_PROFILE, OCI_AUTH, OCI_REGION, COMPARTMENT_OCID, LOOKBACK_MIN
# ==============================================================================
set -uo pipefail
source "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/lib-common.sh"

NAME_FILTER=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --name-filter) NAME_FILTER="$2"; shift 2 ;;
    -h|--help) grep '^#' "$0" | sed 's/^# \{0,1\}//' | sed '/^!/d'; exit 0 ;;
    *) err "Argumento desconhecido: $1"; exit 2 ;;
  esac
done

require_tools
require_session

hdr "Pilar 5 — Dashboards (render-readiness)"
info "Compartment: $COMPARTMENT_OCID"
[[ -n "$NAME_FILTER" ]] && info "Filtro de nome: '$NAME_FILTER'"

# --- 1. Dashboards ACTIVE ------------------------------------------------------
DASH_JSON="$(oci_cli management-dashboard dashboard list \
  --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null)" || DASH_JSON='{}'

# filtra não-OOB + name-filter (while-read p/ compat bash 3.2 — sem mapfile)
DASH_ROWS=()
while IFS= read -r line; do [[ -n "$line" ]] && DASH_ROWS+=("$line"); done < <(printf '%s' "$DASH_JSON" | jq -r --arg f "$NAME_FILTER" '
  .data.items[]? | select(."is-oob-dashboard" != true)
  | select($f == "" or (."display-name" | test($f)))
  | [."display-name", (."lifecycle-state" // "UNKNOWN")] | @tsv' 2>/dev/null)

if [[ "${#DASH_ROWS[@]}" -eq 0 ]]; then
  fail "Nenhum dashboard custom encontrado no compartment (esperado >=1)."
else
  for row in "${DASH_ROWS[@]}"; do
    name="${row%%$'\t'*}"; state="${row##*$'\t'}"
    if [[ "$state" == "ACTIVE" ]]; then pass "Dashboard ACTIVE: $name"
    else fail "Dashboard não-ACTIVE ($state): $name"; fi
  done
fi

# --- 2. Saved-searches: render fields -----------------------------------------
SS_JSON="$(oci_cli management-dashboard saved-search list \
  --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null)" || SS_JSON='{}'

# para cada saved-search custom: name | widget-template | data-config[0].type | tem_regionName
SS_ROWS=()
while IFS= read -r line; do [[ -n "$line" ]] && SS_ROWS+=("$line"); done < <(printf '%s' "$SS_JSON" | jq -r '
  .data.items[]? | select(."is-oob-saved-search" != true)
  | [ ."display-name",
      (."widget-template" // ""),
      (."data-config"[0].type // ""),
      ((."parameters-config" // []) | map(.name) | index("regionName") | if . == null then "no" else "yes" end)
    ] | @tsv' 2>/dev/null)

VALID_TYPES="monitoringDataSource tracesDataSource"
if [[ "${#SS_ROWS[@]}" -eq 0 ]]; then
  skip "Nenhuma saved-search custom (dashboards sem widgets?)."
else
  for row in "${SS_ROWS[@]}"; do
    IFS=$'\t' read -r ss_name wt dctype has_region <<<"$row"
    # widget-template presente
    if [[ -n "$wt" && "$wt" != "None" && "$wt" != "null" ]]; then
      pass "widget-template OK: $ss_name"
    else
      fail "widget-template AUSENTE (não renderiza): $ss_name"
    fi
    # data-config type válido
    if [[ " $VALID_TYPES " == *" $dctype "* ]]; then
      pass "dataSource '$dctype' OK: $ss_name"
    else
      fail "dataSource inválido/ausente ('$dctype'): $ss_name"
    fi
    # metric widget precisa de regionName param
    if [[ "$dctype" == "monitoringDataSource" ]]; then
      if [[ "$has_region" == "yes" ]]; then
        pass "regionName param OK (metric): $ss_name"
      else
        fail "regionName param AUSENTE (metric fica em branco — P10): $ss_name"
      fi
    fi
  done
fi

# --- 3. Cross-check ingestão (há dado por trás?) ------------------------------
ST="$(iso_minus_min "${LOOKBACK_MIN:-60}")"; ET="$(iso_now)"
metric_has_data() { # namespace query -> 0 se tem datapoints
  oci_cli monitoring metric-data summarize-metrics-data \
    --compartment-id "$COMPARTMENT_OCID" --namespace "$1" --query-text "$2" \
    --start-time "$ST" --end-time "$ET" 2>/dev/null \
    | jq -e '[.data[]?."aggregated-datapoints"[]?] | length > 0' >/dev/null 2>&1
}

for meta in "${FUNCTIONS_META[@]}"; do
  IFS='|' read -r label app_ocid ns prefix _fn <<<"$meta"
  if metric_has_data "oci_faas" "FunctionInvocationCount[1m]{applicationId=\"$app_ocid\"}.sum()"; then
    pass "ingestão oci_faas OK: $label"
  else
    skip "sem datapoints oci_faas p/ $label (gere tráfego: scripts/generate-dashboard-traffic.sh)"
  fi
  if metric_has_data "$ns" "${prefix}Invocation[1m].sum()"; then
    pass "ingestão custom ($ns) OK: $label"
  else
    skip "sem datapoints custom ($ns) p/ $label"
  fi
done

summary
