#!/usr/bin/env python3
# ==============================================================================
# check-alarms.py — valida a configuração de alarmes e notificações:
#   - alarmes existem e estão habilitados
#   - status atual de cada alarme (OK / FIRING / SUSPENDED)
#   - tópico ONS tem subscription e se está CONFIRMADA (ACTIVE)
# Somente leitura.
# ==============================================================================
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402


def _count(text, pred=None):
    """`[.data[]? | select(pred)] | length` || echo 0  ('' sem input)."""
    try:
        v = L.jload(text)
        if v is L.NOINPUT:
            return ""
        items = L.jiter(L.jget(v, "data"))
        return str(sum(1 for i in items if pred is None or pred(i)))
    except (ValueError, L.JqError):
        return "0"


def _lines(items, fmt):
    """Emula `.[] | "<interpolação>"` (jq para no primeiro elemento inválido)."""
    for i in items:
        if i is not None and not isinstance(i, dict):
            break
        print(fmt(i or {}))


def _data_items(text):
    try:
        v = L.jload(text)
        return [] if v is L.NOINPUT else L.jiter(L.jget(v, "data"))
    except (ValueError, L.JqError):
        return []


def _state(s):
    a = s.get("lifecycle-state")
    return a if L.jtruthy(a) else s.get("lifecycleState")


def main():
    L.init()
    L.require_tools()
    L.require_session()

    L.hdr("CHECK ALARMS & NOTIFICATIONS")

    # --- 1) Alarmes definidos ---
    _rc, alarms = L.oci_cli("monitoring", "alarm", "list", "--compartment-id", L.COMPARTMENT_OCID, "--all")
    total = _count(alarms)
    enabled = _count(alarms, lambda a: isinstance(a, dict) and a.get("is-enabled") is True)

    if L.to_int(total) >= 1:
        L.pass_(f"Alarmes no compartment: {total} (habilitados: {enabled}).")
    else:
        L.fail("Nenhum alarme encontrado no compartment.")

    # Esperados: fn-errors, fn-latency, fn-throttle (x3 apps) + apigw-5xx = 10
    if L.to_int(total) >= 10:
        L.pass_("Contagem de alarmes >= 10 (cobertura esperada: 3 tipos x 3 apps + apigw-5xx).")
    else:
        L.skip(f"Esperava >=10 alarmes; encontrei {total}. Confirme se todos foram aplicados.")

    _lines(_data_items(alarms), lambda a: (
        f"  - {L.jtext(a.get('display-name'))} [{L.jtext(a.get('severity'))}] "
        f"enabled={L.jtext(a.get('is-enabled'))}"))

    # --- 2) Status atual dos alarmes ---
    L.hdr("Status atual dos alarmes")
    _rc, status = L.oci_cli("monitoring", "alarm-status", "list-alarms-status",
                            "--compartment-id", L.COMPARTMENT_OCID, "--all")
    status = status.rstrip("\r\n")
    if status:
        firing = _count(status, lambda s: isinstance(s, dict) and s.get("status") == "FIRING")
        _lines(_data_items(status)[:20], lambda s: f"  - {L.jtext(s.get('display-name'))}: {L.jtext(s.get('status'))}")
        if L.to_int(firing) > 0:
            L.info(f"{firing} alarme(s) em FIRING no momento.")
        else:
            L.pass_("Nenhum alarme em FIRING (sistema saudável).")
    else:
        L.skip("Não obtive alarm-status (verifique permissões de monitoring).")

    # --- 3) Subscription do tópico ONS ---
    L.hdr("Subscription de notificação (ONS)")
    if not L.NOTIFICATION_TOPIC_ID:
        L.skip("notification_topic_id não encontrado nos outputs.")
    else:
        _rc, subs = L.oci_cli("ons", "subscription", "list", "--compartment-id", L.COMPARTMENT_OCID, "--all")
        try:
            v = L.jload(subs)
            topic_subs = None if v is L.NOINPUT else [
                s for s in L.jiter(L.jget(v, "data"))
                if isinstance(s, dict) and s.get("topic-id") == L.NOTIFICATION_TOPIC_ID]
        except (ValueError, L.JqError):
            topic_subs = None
        n = len(topic_subs) if topic_subs is not None else 0
        if n == 0:
            L.fail("Tópico de alertas SEM subscription -> alarmes disparam mas ninguém é notificado "
                   "(aplique a subscription do plano).")
        else:
            active = sum(1 for s in topic_subs if _state(s) == "ACTIVE")
            for s in topic_subs:
                print(f"  - {L.jtext(s.get('protocol'))} {L.jtext(s.get('endpoint'))}: {L.jtext(_state(s))}")
            if active > 0:
                L.pass_(f"{n} subscription(s), {active} ACTIVE (confirmada).")
            else:
                L.skip(f"{n} subscription(s) mas nenhuma ACTIVE — confirme o email enviado pela OCI (estado PENDING).")

    return L.summary()


if __name__ == "__main__":
    sys.exit(main())
