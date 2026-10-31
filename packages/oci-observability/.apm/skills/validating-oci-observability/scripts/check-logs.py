#!/usr/bin/env python3
# ==============================================================================
# check-logs.py — valida que as Functions estão emitindo logs capturados pelo
# OCI Logging (service logs de invoke), consultando via logging-search.
#
# PASS: >=1 entrada de log no log group na janela recente.
# Extra: procura campos de log estruturado (opcRequestId/service) no payload.
# Somente leitura.
# ==============================================================================
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402


def _results(v):
    return L.jiter(L.jget(L.jget(v, "data"), "results"))


def _structured(v):
    """[.data.results[]?.data."logContent"?.data // .data.results[]?.data // empty] | tostring"""
    results = _results(v)
    first = []
    try:
        for r in results:
            d = L.jget(r, "data")
            try:
                lc = L.jget(d, "logContent")
            except L.JqError:
                continue
            x = L.jget(lc, "data")
            if L.jtruthy(x):
                first.append(x)
    except L.JqError:
        first = []
    if first:
        return L.compact(first)
    alt = [x for x in (L.jget(r, "data") for r in results) if L.jtruthy(x)]
    return L.compact(alt)


def main():
    L.init()
    L.require_tools()
    L.require_session()

    L.hdr(f"CHECK LOGS — OCI Logging (últimos {L.LOOKBACK_MIN}min)")

    if not L.LOG_GROUP_ID:
        L.fail(f"log_group_id não encontrado nos outputs do Terraform (rode em {L.TF_DIR}).")
        L.summary()
        return 1

    start = L.iso_minus_min(L.LOOKBACK_MIN)
    end = L.iso_now()
    L.info(f"Log group: {L.LOG_GROUP_ID}")
    L.info(f"Janela: {start} .. {end}")

    # Busca todas as entradas do log group na janela.
    query = f'search "{L.COMPARTMENT_OCID}/{L.LOG_GROUP_ID}"'
    _rc, raw = L.oci_cli("logging-search", "search-logs",
                         "--search-query", query,
                         "--time-start", start, "--time-end", end,
                         "--limit", "200")
    raw = raw.rstrip("\r\n")

    if not raw:
        L.fail("logging-search não retornou dados (verifique permissões / janela).")
        L.summary()
        return 1

    try:
        v = L.jload(raw)
        total = L.jlen(L.jget(L.jget(v, "data"), "results"))
    except (ValueError, L.JqError):
        v, total = L.NOINPUT, 0
    if L.to_int(total) > 0:
        L.pass_(f"Log group tem {total} entradas na janela.")
    else:
        L.fail("Nenhuma entrada de log na janela (invoque as functions antes: smoke-invoke.py).")

    # Estruturação: procura campos do Logback JSON no conteúdo dos logs.
    try:
        structured = _structured(v) if v is not L.NOINPUT else ""
    except L.JqError:
        structured = ""
    if re.search(r'opcRequestId|"service"|coldStart', structured):
        L.pass_("Logs contêm campos estruturados (opcRequestId/service/coldStart).")
    else:
        L.skip("Não confirmei campos estruturados no payload (pode ser latência de ingestão ou formato distinto).")

    # Presença por função (best-effort: procura o OCID da app no conteúdo dos logs).
    for label, app_id, _ns, _pref, _fn in L.FUNCTIONS_META:
        try:
            n = sum(1 for r in _results(v) if app_id in L.jtext(r)) if v is not L.NOINPUT else 0
        except L.JqError:
            n = 0
        if n > 0:
            L.pass_(f"Logs de '{label}': {n} entradas.")
        else:
            L.skip(f"Sem entradas atribuíveis a '{label}' (invoque a rota correspondente).")

    return L.summary()


if __name__ == "__main__":
    sys.exit(main())
