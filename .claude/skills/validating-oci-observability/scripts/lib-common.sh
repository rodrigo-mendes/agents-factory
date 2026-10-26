#!/usr/bin/env bash
# ==============================================================================
# lib-common.sh — configuração e helpers compartilhados pelos scripts de
# validação de observabilidade.
#
# Uso: os demais scripts fazem `source "$(dirname "$0")/lib-common.sh"`.
# Todas as variáveis podem ser sobrescritas por ambiente antes de chamar.
# ==============================================================================

set -uo pipefail

# ------------------------------------------------------------------------------
# Configuração base (sobrescrevível por env var)
# ------------------------------------------------------------------------------
OCI_PROFILE="${OCI_PROFILE:-poc}"
OCI_AUTH="${OCI_AUTH:-security_token}"
OCI_REGION="${OCI_REGION:-sa-saopaulo-1}"

# Diretório do ambiente Terraform (para ler outputs).
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# Resolve o repo root via git (funciona de qualquer localização — repo scripts/ OU dentro do skill);
# fallback para o layout legado scripts/observability/ (2 níveis sob o root).
REPO_ROOT="$(git -C "$SCRIPT_DIR" rev-parse --show-toplevel 2>/dev/null || (cd "$SCRIPT_DIR/../.." && pwd))"
TF_DIR="${TF_DIR:-$REPO_ROOT/infra/environments/dev}"

# Janela de tempo padrão para queries (minutos).
LOOKBACK_MIN="${LOOKBACK_MIN:-15}"

# ------------------------------------------------------------------------------
# Cores / logging
# ------------------------------------------------------------------------------
if [[ -t 1 ]]; then
  C_RED=$'\033[0;31m'; C_GRN=$'\033[0;32m'; C_YLW=$'\033[0;33m'
  C_BLU=$'\033[0;34m'; C_BLD=$'\033[1m'; C_RST=$'\033[0m'
else
  C_RED=""; C_GRN=""; C_YLW=""; C_BLU=""; C_BLD=""; C_RST=""
fi

log()   { printf '%s\n' "$*"; }
info()  { printf '%s[i]%s %s\n' "$C_BLU" "$C_RST" "$*"; }
warn()  { printf '%s[!]%s %s\n' "$C_YLW" "$C_RST" "$*" >&2; }
err()   { printf '%s[x]%s %s\n' "$C_RED" "$C_RST" "$*" >&2; }
hdr()   { printf '\n%s== %s ==%s\n' "$C_BLD" "$*" "$C_RST"; }

# Contadores globais de asserção (usados pelos scripts individuais).
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

pass() { PASS_COUNT=$((PASS_COUNT+1)); printf '%s  PASS%s %s\n' "$C_GRN" "$C_RST" "$*"; }
fail() { FAIL_COUNT=$((FAIL_COUNT+1)); printf '%s  FAIL%s %s\n' "$C_RED" "$C_RST" "$*"; }
skip() { WARN_COUNT=$((WARN_COUNT+1)); printf '%s  WARN%s %s\n' "$C_YLW" "$C_RST" "$*"; }

# Resumo final; retorna 1 se houve qualquer FAIL.
summary() {
  printf '\n%s---------------------------------------------%s\n' "$C_BLD" "$C_RST"
  printf '%sRESULTADO:%s %sPASS=%d%s  %sFAIL=%d%s  %sWARN=%d%s\n' \
    "$C_BLD" "$C_RST" "$C_GRN" "$PASS_COUNT" "$C_RST" \
    "$C_RED" "$FAIL_COUNT" "$C_RST" "$C_YLW" "$WARN_COUNT" "$C_RST"
  [[ "$FAIL_COUNT" -eq 0 ]]
}

# ------------------------------------------------------------------------------
# Wrappers OCI CLI
# ------------------------------------------------------------------------------
oci_cli() {
  oci --profile "$OCI_PROFILE" --auth "$OCI_AUTH" --region "$OCI_REGION" "$@"
}

# _with_timeout <segundos> <cmd...> — executa cmd com teto de tempo (wall-clock).
# Portável (usa gtimeout/timeout se existir, senão perl alarm — sempre presente no
# macOS/Linux). Retorna 124 se estourar o tempo (mesma convenção do coreutils).
# Necessário porque uma chamada OCI CLI contra token EXPIRADO pode TRAVAR (retry/
# backoff no endpoint de auth) em vez de retornar 401 rápido — sem teto, o gate
# "fail fast" viraria "hang forever".
_with_timeout() {
  local secs="$1"; shift
  if command -v gtimeout >/dev/null 2>&1; then
    gtimeout "$secs" "$@"
  elif command -v timeout >/dev/null 2>&1; then
    timeout "$secs" "$@"
  else
    # Fallback perl: fork o filho e mata-o no ALARM (NÃO usar exec — o handler
    # ALRM some após exec e o timer não teria efeito). Retorna 124 no timeout.
    perl -e '
      my $s = shift @ARGV;
      my $pid = fork();
      die "fork failed: $!" unless defined $pid;
      if ($pid == 0) { exec @ARGV or exit 127; }   # filho
      $SIG{ALRM} = sub { kill "TERM", $pid; kill "KILL", $pid; exit 124; };
      alarm $s;
      waitpid($pid, 0);
      exit($? >> 8);
    ' "$secs" "$@"
  fi
}

# Verifica pré-requisitos (oci, jq) e sessão válida. Sai 1 se faltar algo crítico.
require_tools() {
  local missing=0
  for t in oci jq; do
    command -v "$t" >/dev/null 2>&1 || { err "Ferramenta ausente: $t"; missing=1; }
  done
  [[ "$missing" -eq 0 ]] || exit 1
}

require_session() {
  if ! oci session validate --profile "$OCI_PROFILE" --auth "$OCI_AUTH" --local >/dev/null 2>&1; then
    err "Sessão OCI '$OCI_PROFILE' inválida/expirada."
    err "Renove com: oci session authenticate --profile $OCI_PROFILE --region $OCI_REGION"
    exit 2
  fi
}

# ------------------------------------------------------------------------------
# require_fresh_session — gate ROBUSTO para varreduras longas.
#
# A sessão SecurityToken do perfil `poc` expira em ~1h e já quebrou runs longos
# com 401 no meio (o token acaba antes do "valid until" que `--local` reporta —
# `--local` só checa o relógio, não o servidor). Este gate:
#   1) tenta `oci session refresh` (best-effort; estende sessões renováveis);
#   2) PROVA a sessão com uma chamada autenticada real (não `--local`), que é o
#      único teste que pega token rejeitado server-side.
# Falha rápido com exit 2 e mensagem clara ANTES de gastar minutos na varredura.
#
# Uso: chamar no início dos scripts que fazem sweeps longos (ex.:
# validate-observability.sh, check-dashboards.sh), no lugar de require_session.
# ------------------------------------------------------------------------------
require_fresh_session() {
  # Pré-cheque de relógio (barato); se nem o "valid until" bate, nem tenta refresh.
  if ! oci session validate --profile "$OCI_PROFILE" --auth "$OCI_AUTH" --local >/dev/null 2>&1; then
    err "Sessão OCI '$OCI_PROFILE' expirada (validação local falhou)."
    err "Reautentique (login interativo no browser): oci session authenticate --profile $OCI_PROFILE --region $OCI_REGION"
    exit 2
  fi

  # Tenta renovar a sessão (best-effort — não falha o gate se o refresh não puder).
  # Teto de 20s: contra token não-renovável o refresh pode demorar no endpoint de auth.
  # NB: `oci session refresh` sai 0 mesmo quando NÃO consegue renovar ("no longer
  # valid and cannot be refreshed") — por isso ele é só best-effort; quem decide é
  # a prova ao vivo abaixo.
  if _with_timeout 20 oci session refresh --profile "$OCI_PROFILE" >/dev/null 2>&1; then
    info "Sessão '$OCI_PROFILE': tentativa de refresh concluída (validação real abaixo é quem decide)."
  fi

  # Prova DEFINITIVA: chamada autenticada real, com timeouts curtos do próprio CLI
  # E teto wall-clock. É o que detecta token que o servidor já rejeita apesar do
  # "valid until" local ainda no futuro. Contra token expirado a chamada pode
  # TRAVAR (retry/backoff) — o teto garante o "fail fast".
  local probe_rc=0
  _with_timeout 20 oci --profile "$OCI_PROFILE" --auth "$OCI_AUTH" --region "$OCI_REGION" \
    --connection-timeout 5 --read-timeout 10 iam region list >/dev/null 2>&1 || probe_rc=$?
  if [[ "$probe_rc" -ne 0 ]]; then
    if [[ "$probe_rc" -eq 124 ]]; then
      err "Sessão OCI '$OCI_PROFILE': chamada autenticada TRAVOU (timeout) — token provavelmente expirado (o CLI fica em retry contra o endpoint de auth)."
    else
      err "Sessão OCI '$OCI_PROFILE' NÃO aceita pelo servidor (rc=$probe_rc) apesar do relógio local OK."
    fi
    err "O token SecurityToken provavelmente expirou (TTL ~1h). Reautentique ANTES da varredura:"
    err "  oci session authenticate --profile $OCI_PROFILE --region $OCI_REGION"
    err "(login interativo no browser — não pode ser feito headless)"
    exit 2
  fi
  info "Sessão '$OCI_PROFILE' validada ao vivo (chamada autenticada OK)."
}

# ------------------------------------------------------------------------------
# Terraform outputs (cacheados em memória)
# ------------------------------------------------------------------------------
_TF_JSON=""
_TF_PRIMED=0
tf_outputs() {
  if [[ -z "$_TF_JSON" ]]; then
    _TF_JSON="$(cd "$TF_DIR" && terraform output -json 2>/dev/null)" || _TF_JSON="{}"
  fi
  printf '%s' "$_TF_JSON"
}

# tf_prime — popula o cache _TF_JSON UMA vez no shell atual (não em subshell).
# CRÍTICO: tf_out chama tf_outputs dentro de "$(...)" (subshell), então o cache
# setado lá se PERDE ao sair do subshell — sem esta prime, CADA tf_out re-executa
# `terraform output -json` (dezenas de vezes = varredura trava minutos). Chamar
# tf_prime no escopo pai faz o assignment persistir para todos os tf_out seguintes.
tf_prime() {
  [[ "$_TF_PRIMED" -eq 1 ]] && return 0
  _TF_JSON="$(cd "$TF_DIR" && terraform output -json 2>/dev/null)" || _TF_JSON="{}"
  _TF_PRIMED=1
}

# tf_out <output_name> [fallback]
tf_out() {
  local name="$1" fallback="${2:-}"
  local v
  v="$(tf_outputs | jq -r --arg k "$name" '.[$k].value // empty' 2>/dev/null)"
  if [[ -z "$v" || "$v" == "null" ]]; then printf '%s' "$fallback"; else printf '%s' "$v"; fi
}

# ------------------------------------------------------------------------------
# Constantes derivadas (com fallback para OCIDs conhecidos do state — dev)
# ------------------------------------------------------------------------------
# Popula o cache de outputs UMA vez (ver tf_prime) — evita reexecutar
# `terraform output -json` a cada tf_out (senão a construção do FUNCTIONS_META
# dispararia dezenas de chamadas e a varredura travaria por minutos).
tf_prime
COMPARTMENT_OCID="$(tf_out compartment_ocid 'ocid1.compartment.oc1..aaaaaaaat3d6o3oron7jqrztl572jjrsdobf6bimutf57jirbzetc4magzja')"
API_BASE_URL="$(tf_out api_base_url 'https://lopiafgboojvw37sqyoxptl7t4.apigateway.sa-saopaulo-1.oci.customer-oci.com/v1')"
LOG_GROUP_ID="$(tf_out log_group_id '')"
APM_DOMAIN_ID="$(tf_out apm_domain_id '')"
NOTIFICATION_TOPIC_ID="$(tf_out notification_topic_id '')"

# ------------------------------------------------------------------------------
# FUNCTIONS_META — mapa "label|app_ocid|custom_namespace|prefixo_metrica|function_ocid"
#
# Cada linha da spec abaixo declara:
#   label | tf_output_base | custom_namespace | prefixo_metrica | fallback_app_ocid | fallback_fn_ocid
#
# tf_output_base resolve DOIS outputs do terraform: "<base>_application_id" e
# "<base>_function_id". Preferimos SEMPRE o valor vivo do `terraform output`; os
# OCIDs hardcoded servem apenas de fallback quando o output ainda não existe no
# state (ex.: outputs recém-adicionados que ainda não passaram por `apply`).
#
# Os 3 apps pub/sub (Pattern 02) compartilham o namespace custom
# `event_pubsub_analytics`. O prefixo de métrica reflete o nome real emitido por
# cada serviço (EventProduced / NotifyEventProcessed / AuditEventProcessed); como
# o probe genérico de custom metric usa "${pref}Invocation", ele é best-effort
# para esses apps — as partes decisivas (diagnóstico applicationId x resourceId e
# checagem de config APM) independem do prefixo.
#
# Fallbacks confirmados ao vivo (oci fn ... list, 2026-07-22, região sa-saopaulo-1).
# ------------------------------------------------------------------------------
# shellcheck disable=SC2034
_FUNCTIONS_META_SPEC=(
  # label|tf_base|namespace|prefix|fallback_app|fallback_fn
  "api-handler|api_handler|api_handler_analytics|ApiHandler|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyadf7booxbvvg6ernldcdbwrxahtw7w2jer3sfhp7ujjyq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyawaxod6lh5w37le6yfyinnsibpwpq6grvprgua2amij5q"
  "func-api-facade|api_facade|serverless_facade|ApiFacade|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyaetxnny6q7rr3trylculrbucuim3mti7tsa4i2zkzuoyq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyaqlmzdfkvbe7rwtys7zsukahfmhu6t5ikqqm3mfkq6zdq"
  "func-rr-rest-proxy|rest_proxy|rest_proxy_analytics|RestProxy|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyased4pvcjmegljcx4uw47bypu53bbwkfsb2bajtoxv75a|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyaizt447zllj2362ztaibza5dcsxw2cfcj3ocoeazuty4a"
  # --- Event-Driven Pub/Sub (Pattern 02) ---
  "func-event-producer|event_producer|event_pubsub_analytics|EventProduced|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyaocnsg26tu2cwf4mqdmhcn7guqtofqisgkyrpop2hxdkq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyasqb6jm3f5hadyrhlc6y4zqrldu3gm5restrrdip4u3va"
  "func-evt-consumer-notify|evt_consumer_notify|event_pubsub_analytics|NotifyEventProcessed|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nyao6cktchg6zm4z3vtqytqkqvps2jlx7tqzfahc3jolmfq|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nyaqxui43bkqdhs6gcctenbjs54ozsbnhy2oyal5dshw44a"
  "func-evt-consumer-audit|evt_consumer_audit|event_pubsub_analytics|AuditEventProcessed|ocid1.fnapp.oc1.sa-saopaulo-1.amaaaaaa543c4nya4afwc7uhswdby5cwm4zzv3xzot5nvoyomj4t4lcmieha|ocid1.fnfunc.oc1.sa-saopaulo-1.amaaaaaa543c4nya4gsk4nyx7a23dqfeszxcljr7hgf2jyxlkgjx2r5vtnbq"
)

# Popula FUNCTIONS_META dinamicamente: para cada linha da spec, resolve
# <base>_application_id / <base>_function_id via terraform output (preferido),
# caindo para o OCID hardcoded quando o output não existe no state.
FUNCTIONS_META=()
for _spec in "${_FUNCTIONS_META_SPEC[@]}"; do
  IFS='|' read -r _label _base _ns _pref _fb_app _fb_fn <<< "$_spec"
  _app="$(tf_out "${_base}_application_id" "$_fb_app")"
  _fn="$(tf_out "${_base}_function_id" "$_fb_fn")"
  FUNCTIONS_META+=("${_label}|${_app}|${_ns}|${_pref}|${_fn}")
done
unset _spec _label _base _ns _pref _fb_app _fb_fn _app _fn

# ------------------------------------------------------------------------------
# Tempo (ISO-8601 UTC). macOS (BSD date) e Linux (GNU date).
# ------------------------------------------------------------------------------
iso_now()      { date -u +%Y-%m-%dT%H:%M:%SZ; }
iso_minus_min() {
  local m="$1"
  if date -u -v-1M +%s >/dev/null 2>&1; then
    date -u -v-"${m}"M +%Y-%m-%dT%H:%M:%SZ   # BSD/macOS
  else
    date -u -d "-${m} minutes" +%Y-%m-%dT%H:%M:%SZ  # GNU/Linux
  fi
}
