#!/usr/bin/env python3
# ==============================================================================
# trigger-alarm-test.py — dispara um cenário de erro controlado para validar
# ponta-a-ponta o caminho métrica -> alarme -> notificação.
#
# Estratégia: envia N requisições inválidas a uma rota ANÔNIMA que exercita
# caminho de erro (default /proxy/item/webhook) para gerar 5xx / FunctionError,
# depois faz polling do alarm-status até FIRING (janela do alarme = PT5M).
#
# Uso: ./trigger-alarm-test.py --i-have-user-approval [N_ERROS] [POLL_MAX_MIN]
#   --i-have-user-approval  OBRIGATÓRIO: só com a aprovação explícita do usuário para ESTE teste
#                           (sem ele: exit 2, nenhuma requisição enviada)
#   N_ERROS (default 15) | POLL_MAX_MIN (default 8)
# Env: TARGET_PATH (default /proxy/item/webhook)
#
# ATENÇÃO: gera erros reais nas métricas. Use só em dev. Os alarmes voltam a OK
# sozinhos após a janela sem novos erros. (A OCI CLI só é usada para leitura.)
# ==============================================================================
import os
import re
import sys
import time
from collections import Counter
from datetime import datetime, timezone

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402


def _seq_count(s):
    try:
        n = float(s)
    except ValueError:
        L.err_raw(f"seq: invalid floating point argument: '{s}'")
        return 0
    return max(0, int(n // 1))


def _firing_names(text):
    """[.data[]? | select(.status=="FIRING") | select(."display-name"|test("errors|5xx";"i"))] | .[]."display-name" """
    try:
        v = L.jload(text)
        if v is L.NOINPUT:
            return []
        out = []
        for a in L.jiter(L.jget(v, "data")):
            if L.jget(a, "status") != "FIRING":
                continue
            name = L.jget(a, "display-name")
            if not isinstance(name, str):
                return []
            if re.search(r"errors|5xx", name, re.IGNORECASE):
                out.append(name)
        return out
    except (ValueError, L.JqError):
        return []


def main(argv):
    argv = list(argv)
    if "--i-have-user-approval" not in argv:
        sys.stderr.write("trigger-alarm-test.py: recusado — injeta erros reais e envia notificações; "
                         "rode só com a aprovação explícita do usuário (--i-have-user-approval).")
        sys.stderr.write(chr(10))
        return 2
    argv = [a for a in argv if a != "--i-have-user-approval"]
    L.init()
    L.require_tools()
    L.require_session()

    n_err = argv[0] if len(argv) > 0 and argv[0] != "" else "15"
    poll_max_min = argv[1] if len(argv) > 1 and argv[1] != "" else "8"
    target_path = os.environ.get("TARGET_PATH") or "/proxy/item/webhook"
    url = f"{L.API_BASE_URL}{target_path}"

    L.hdr(f"TRIGGER ALARM TEST — {n_err} requisições inválidas em {target_path}")
    L.warn("Isto injeta erros reais nas métricas de dev (para testar o alarme).")

    codes = []
    for i in range(1, _seq_count(n_err) + 1):
        c = L.http_code(url, method="POST",
                        data='{"__invalid__":true,"trigger":"alarm-test","n":' + str(i) + '}',
                        timeout=65)
        codes.append(c)
        sys.stdout.write(".")
        sys.stdout.flush()
    print("")

    L.info("Distribuição de códigos HTTP gerados:")
    for code, cnt in sorted(Counter(codes).items()):
        print(f"   HTTP {code} x{cnt}")

    if any(c.startswith("5") for c in codes):
        L.pass_("Gerou respostas 5xx — deve acionar alarm-apigw-5xx e/ou alarm-fn-errors.")
    else:
        L.skip("App tratou todas as entradas sem 5xx. Para forçar FunctionError real, invoque")
        L.skip("diretamente com payload que estoure exceção, ou induza falha de downstream.")

    # Polling do status dos alarmes-alvo até FIRING (ou timeout).
    L.hdr(f"Aguardando alarme -> FIRING (janela PT5M; timeout {poll_max_min}min)")
    try:
        poll_min = int(poll_max_min)
    except ValueError:
        poll_min = 0
    deadline = int(time.time()) + poll_min * 60
    fired = False
    while int(time.time()) < deadline:
        _rc, status = L.oci_cli("monitoring", "alarm-status", "list-alarms-status",
                                "--compartment-id", L.COMPARTMENT_OCID, "--all")
        hits = _firing_names(status)
        if hits:
            fired = True
            L.pass_("Alarme(s) em FIRING:")
            for h in hits:
                print(f"     - {h}")
            break
        print(f"   {datetime.now(timezone.utc).strftime('%H:%M:%S')} aguardando...")
        L.sleep(30)

    if fired:
        L.info("Se a subscription estiver ACTIVE, um email deve chegar em rodrigo.mendes@brxretail.com.")
    else:
        L.fail(f"Nenhum alarme de erro/5xx entrou em FIRING dentro de {poll_max_min}min.")
        L.info("Cheque: (a) métrica de erro casa com o resourceId do alarme (check-metrics.py); "
               "(b) tráfego realmente 5xx.")

    L.info("Os alarmes retornam a OK sozinhos após a janela sem novos erros.")
    return L.summary()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
