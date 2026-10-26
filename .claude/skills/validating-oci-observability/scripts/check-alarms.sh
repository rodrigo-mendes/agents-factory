#!/usr/bin/env bash
# ==============================================================================
# check-alarms.sh — valida a configuração de alarmes e notificações:
#   - alarmes existem e estão habilitados
#   - status atual de cada alarme (OK / FIRING / SUSPENDED)
#   - tópico ONS tem subscription e se está CONFIRMADA (ACTIVE)
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-common.sh"
require_tools
require_session

hdr "CHECK ALARMS & NOTIFICATIONS"

# --- 1) Alarmes definidos ---
alarms="$(oci_cli monitoring alarm list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null)"
total="$(printf '%s' "$alarms" | jq -r '[.data[]?] | length' 2>/dev/null || echo 0)"
enabled="$(printf '%s' "$alarms" | jq -r '[.data[]? | select(."is-enabled"==true)] | length' 2>/dev/null || echo 0)"

if [[ "${total:-0}" -ge 1 ]]; then
  pass "Alarmes no compartment: $total (habilitados: $enabled)."
else
  fail "Nenhum alarme encontrado no compartment."
fi

# Esperados: fn-errors, fn-latency, fn-throttle (x3 apps) + apigw-5xx = 10
if [[ "${total:-0}" -ge 10 ]]; then
  pass "Contagem de alarmes >= 10 (cobertura esperada: 3 tipos x 3 apps + apigw-5xx)."
else
  skip "Esperava >=10 alarmes; encontrei $total. Confirme se todos foram aplicados."
fi

printf '%s' "$alarms" | jq -r '.data[]? | "  - \(."display-name") [\(.severity)] enabled=\(."is-enabled")"' 2>/dev/null

# --- 2) Status atual dos alarmes ---
hdr "Status atual dos alarmes"
status="$(oci_cli monitoring alarm-status list-alarms-status --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null)"
if [[ -n "$status" ]]; then
  firing="$(printf '%s' "$status" | jq -r '[.data[]? | select(.status=="FIRING")] | length' 2>/dev/null || echo 0)"
  printf '%s' "$status" | jq -r '.data[]? | "  - \(."display-name"): \(.status)"' 2>/dev/null | head -20
  if [[ "${firing:-0}" -gt 0 ]]; then
    info "$firing alarme(s) em FIRING no momento."
  else
    pass "Nenhum alarme em FIRING (sistema saudável)."
  fi
else
  skip "Não obtive alarm-status (verifique permissões de monitoring)."
fi

# --- 3) Subscription do tópico ONS ---
hdr "Subscription de notificação (ONS)"
if [[ -z "$NOTIFICATION_TOPIC_ID" ]]; then
  skip "notification_topic_id não encontrado nos outputs."
else
  subs="$(oci_cli ons subscription list --compartment-id "$COMPARTMENT_OCID" --all 2>/dev/null)"
  topic_subs="$(printf '%s' "$subs" | jq -r --arg t "$NOTIFICATION_TOPIC_ID" \
    '[.data[]? | select(."topic-id"==$t)]' 2>/dev/null)"
  n="$(printf '%s' "$topic_subs" | jq -r 'length' 2>/dev/null || echo 0)"
  if [[ "${n:-0}" -eq 0 ]]; then
    fail "Tópico de alertas SEM subscription -> alarmes disparam mas ninguém é notificado (aplique a subscription do plano)."
  else
    active="$(printf '%s' "$topic_subs" | jq -r '[.[] | select((.["lifecycle-state"]//.["lifecycleState"])=="ACTIVE")] | length' 2>/dev/null || echo 0)"
    printf '%s' "$topic_subs" | jq -r '.[] | "  - \(.protocol) \(.endpoint): \(.["lifecycle-state"]//.["lifecycleState"])"' 2>/dev/null
    if [[ "${active:-0}" -gt 0 ]]; then
      pass "$n subscription(s), $active ACTIVE (confirmada)."
    else
      skip "$n subscription(s) mas nenhuma ACTIVE — confirme o email enviado pela OCI (estado PENDING)."
    fi
  fi
fi

summary
