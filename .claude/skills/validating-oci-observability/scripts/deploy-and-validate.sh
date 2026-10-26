#!/usr/bin/env bash
# ==============================================================================
# deploy-and-validate.sh — RUNBOOK ponta-a-ponta para corrigir e validar a
# observabilidade em dev. Executa, em ordem:
#   1) pré-checagens (sessão OCI, Docker)
#   2) build + push das 3 imagens (tags do func.yaml)
#   3) terraform apply (popula config das functions, novas imagens, subscription)
#   4) validação dos 4 pilares (validate-observability.sh)
#
# Requisitos:
#   - Docker rodando
#   - Sessão OCI ativa:  oci session authenticate --profile poc --region sa-saopaulo-1
#   - services/.env com credenciais OCIR
#
# Uso:
#   ./deploy-and-validate.sh            # executa tudo (pede confirmação no apply)
#   ./deploy-and-validate.sh --skip-build   # só apply + validação
#   ./deploy-and-validate.sh --plan-only    # para no terraform plan
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"

SKIP_BUILD=0
PLAN_ONLY=0
for a in "$@"; do
  case "$a" in
    --skip-build) SKIP_BUILD=1 ;;
    --plan-only)  PLAN_ONLY=1 ;;
  esac
done

require_tools
require_session

SERVICES_DIR="$REPO_ROOT/services"
OCIR_HOST="gru.ocir.io"
OCIR_NS="gr2o2hdgzoxw"
OCIR_REPO="serverless-app"
ALARM_EMAIL="${ALARM_EMAIL:-rodrigo.mendes@brxretail.com}"

# label|dir|tfvar_name
BUILDS=(
  "api-handler|api-handler|api_handler_image"
  "func-api-facade|func-api-facade|api_facade_image"
  "func-rr-rest-proxy|func-rr-rest-proxy|rest_proxy_image"
)

# ------------------------------------------------------------------------------
# 1) Build + push
# ------------------------------------------------------------------------------
declare -a TF_IMAGE_VARS=()
for b in "${BUILDS[@]}"; do
  IFS='|' read -r label dir tfvar <<< "$b"
  svc="$SERVICES_DIR/$dir"
  tag="$(grep '^version:' "$svc/func.yaml" | awk '{print $2}')"
  image="${OCIR_HOST}/${OCIR_NS}/${OCIR_REPO}/${label}:${tag}"
  TF_IMAGE_VARS+=("-var" "${tfvar}=${image}")

  if [[ "$SKIP_BUILD" -eq 0 ]]; then
    hdr "BUILD+PUSH $label -> $image"
    ( cd "$svc" && bash "$REPO_ROOT/scripts/preflight.sh" "$svc" ) || { err "preflight falhou em $label"; exit 1; }
    if [[ -x "$svc/build-push.sh" ]]; then
      ( cd "$svc" && ./build-push.sh "$tag" ) || { err "build-push falhou em $label"; exit 1; }
      pass "$label publicado: $image"
    else
      err "$svc/build-push.sh não encontrado/executável."; exit 1
    fi
  else
    info "SKIP build de $label; usarei imagem $image"
  fi
done

# ------------------------------------------------------------------------------
# 2) terraform plan/apply
# ------------------------------------------------------------------------------
hdr "TERRAFORM PLAN (dev)"
cd "$TF_DIR"
terraform plan -out=tfplan \
  "${TF_IMAGE_VARS[@]}" \
  -var "alarm_notification_email=${ALARM_EMAIL}" || { err "terraform plan falhou"; exit 1; }

if [[ "$PLAN_ONLY" -eq 1 ]]; then
  info "--plan-only: parando após o plan. Revise 'tfplan' e rode 'terraform apply tfplan'."
  exit 0
fi

printf '\n%sRevise o plan acima. Aplicar? (yes/no): %s' "$C_BLD" "$C_RST"
read -r answer
[[ "$answer" == "yes" ]] || { warn "Apply cancelado pelo usuário."; exit 0; }

hdr "TERRAFORM APPLY (dev)"
terraform apply tfplan || { err "terraform apply falhou"; exit 1; }
pass "Infra aplicada: config das functions populado, imagens atualizadas, subscription criada."
warn "CONFIRME o email de subscription enviado pela OCI para ${ALARM_EMAIL} (senão os alarmes não notificam)."

# ------------------------------------------------------------------------------
# 3) Validação
# ------------------------------------------------------------------------------
hdr "VALIDAÇÃO DE OBSERVABILIDADE"
info "Aguardando 60s para propagação das novas versões das functions..."
sleep 60
bash "$SCRIPT_DIR/validate-observability.sh" --wait 150
