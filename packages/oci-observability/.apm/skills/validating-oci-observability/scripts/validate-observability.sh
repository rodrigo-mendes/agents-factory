#!/usr/bin/env bash
# ==============================================================================
# validate-observability.sh — orquestra a validação dos 4 pilares de
# observabilidade em dev: gera tráfego, espera ingestão e valida
# logs, métricas, traces e alarmes. Imprime tabela PASS/FAIL final.
#
# Uso: ./validate-observability.sh [--no-smoke] [--wait SEG]
#   --no-smoke : não gerar tráfego (assume que já houve invocações)
#   --wait N   : segundos de espera pós-smoke p/ ingestão (default 120)
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

DO_SMOKE=1
WAIT_SEC=120
while [[ $# -gt 0 ]]; do
  case "$1" in
    --no-smoke) DO_SMOKE=0; shift ;;
    --wait) WAIT_SEC="$2"; shift 2 ;;
    *) shift ;;
  esac
done

require_tools
# Gate robusto p/ varredura longa: renova + prova a sessão ao vivo (a SecurityToken
# do perfil poc expira ~1h e já quebrou runs longos com 401 no meio).
require_fresh_session

DIR="$SCRIPT_DIR"

# Resultado por pilar SEM associative array (macOS system bash é 3.2 — não tem
# `declare -A`). Mapa simples "nome=VALOR" numa lista indexada + helper de leitura.
RESULT_MAP=()
_set_result() { RESULT_MAP+=("$1=$2"); }
_get_result() {
  local k="$1" e
  for e in "${RESULT_MAP[@]}"; do
    [[ "$e" == "$k="* ]] && { printf '%s' "${e#*=}"; return 0; }
  done
  printf 'N/A'
}

run_step() {
  local name="$1"; shift
  hdr "PILAR: $name"
  if "$@"; then _set_result "$name" "PASS"; else _set_result "$name" "FAIL"; fi
}

# 1) Gera tráfego
if [[ "$DO_SMOKE" -eq 1 ]]; then
  run_step "smoke" bash "$DIR/smoke-invoke.sh" 3
  info "Aguardando ${WAIT_SEC}s para ingestão de logs/métricas/traces..."
  sleep "$WAIT_SEC"
else
  info "--no-smoke: pulando geração de tráfego."
fi

# 2) Valida os pilares (5 pilares: logs, métricas, traces, alarmes, dashboards)
run_step "logs"       bash "$DIR/check-logs.sh"
run_step "metrics"    bash "$DIR/check-metrics.sh"
run_step "traces"     bash "$DIR/check-traces.sh"
run_step "alarms"     bash "$DIR/check-alarms.sh"
run_step "dashboards" bash "$DIR/check-dashboards.sh"

# 3) Resumo consolidado
hdr "RESUMO CONSOLIDADO — OBSERVABILIDADE (dev)"
fails=0
order=("smoke" "logs" "metrics" "traces" "alarms" "dashboards")
for k in "${order[@]}"; do
  v="$(_get_result "$k")"
  case "$v" in
    PASS) printf '  %s%-10s PASS%s\n' "$C_GRN" "$k" "$C_RST" ;;
    FAIL) printf '  %s%-10s FAIL%s\n' "$C_RED" "$k" "$C_RST"; fails=$((fails+1)) ;;
    *)    printf '  %-10s %s\n' "$k" "$v" ;;
  esac
done

printf '\n'
if [[ "$fails" -eq 0 ]]; then
  printf '%sObservabilidade VALIDADA — todos os pilares OK.%s\n' "$C_GRN$C_BLD" "$C_RST"
else
  printf '%s%d pilar(es) com falha — ver detalhes acima.%s\n' "$C_RED$C_BLD" "$fails" "$C_RST"
  printf 'Dica: falhas em metrics/traces geralmente significam config das functions vazio\n'
  printf '      (Problema #1 do plano) — rode o terraform apply e reexecute.\n'
fi
exit "$fails"
