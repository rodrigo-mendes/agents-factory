#!/usr/bin/env python3
# ==============================================================================
# check-metrics.py — valida métricas de plataforma (oci_faas) e custom
# (namespaces por serviço) via Monitoring summarize-metrics-data.
#
# Também diagnostica se o filtro usado pelos ALARMES (applicationId = app OCID)
# realmente casa com a dimensão da métrica oci_faas. Se só o function OCID
# (resourceId) retornar dados, os alarmes não disparam.
# Somente leitura.
# ==============================================================================
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402


def main():
    L.init()
    L.require_tools()
    L.require_session()

    L.hdr(f"CHECK METRICS — OCI Monitoring (últimos {L.LOOKBACK_MIN}min)")

    start = L.iso_minus_min(L.LOOKBACK_MIN)
    end = L.iso_now()

    def summarize(ns, mql):
        """nº de datapoints (0 se nada)."""
        _rc, out = L.oci_cli("monitoring", "metric-data", "summarize-metrics-data",
                             "--compartment-id", L.COMPARTMENT_OCID,
                             "--namespace", ns,
                             "--query-text", mql,
                             "--start-time", start, "--end-time", end)
        try:
            return L.to_int(L.count_datapoints(out))
        except (ValueError, L.JqError):
            return 0

    # --- 1) Plataforma oci_faas (compartment-wide, sem filtro) ---
    L.info("Namespace de plataforma: oci_faas")
    dp = summarize("oci_faas", "FunctionInvocationCount[1m].sum()")
    if dp > 0:
        L.pass_(f"oci_faas/FunctionInvocationCount: {dp} datapoints (plataforma emitindo).")
    else:
        L.fail("oci_faas/FunctionInvocationCount sem datapoints (invoque as functions).")

    # --- 2) Diagnóstico do filtro dos alarmes (applicationId vs resourceId) ---
    L.hdr("Diagnóstico dimensão resourceId (validação dos alarmes)")
    for label, app_id, _ns, _pref, fn_id in L.FUNCTIONS_META:
        # Dimensão canônica confirmada ao vivo p/ oci_faas: applicationId (a que os alarmes usam).
        by_app = summarize("oci_faas", f'FunctionInvocationCount[5m]{{applicationId = "{app_id}"}}.sum()')
        by_fn = summarize("oci_faas", f'FunctionInvocationCount[5m]{{resourceId = "{fn_id}"}}.sum()')
        L.info(f"{label}: applicationId=app -> {by_app} dp | resourceId=function -> {by_fn} dp")
        if by_app > 0:
            L.pass_(f"{label}: filtro dos alarmes (applicationId) casa — alarmes recebem dados.")
        elif by_fn > 0:
            L.fail(f"{label}: métrica só casa por resourceId=FUNCTION, não applicationId. Revisar query dos alarmes.")
        else:
            L.skip(f"{label}: sem datapoints em nenhuma dimensão (gere tráfego e reexecute).")

    # --- 3) Custom metrics por serviço ---
    L.hdr("Custom metrics (namespaces por serviço)")
    for _label, _app_id, ns, pref, _fn_id in L.FUNCTIONS_META:
        dp = summarize(ns, f"{pref}Invocation[5m].sum()")
        if dp > 0:
            L.pass_(f"{ns}/{pref}Invocation: {dp} datapoints.")
        else:
            L.fail(f"{ns}/{pref}Invocation sem datapoints (config env vazia? veja Problema #1 do plano).")

    return L.summary()


if __name__ == "__main__":
    sys.exit(main())
