#!/usr/bin/env python3
# ==============================================================================
# check-traces.py — validação (best-effort) de traces no APM Domain.
#
# A consulta de traces via OCI CLI é limitada; este script usa as métricas
# oci_apm (IngestedBytes / PayloadRejections) como prova de ingestão.
# Pré-condição real p/ traces: functions com APM_DOMAIN_URL + APM_DATA_KEY no
# config (ver Problema #1 do plano). Sem isso, o exportador OTel não inicializa.
# Somente leitura.
# ==============================================================================
import os
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402


def _config_keys(out):
    """.data.config // {} | keys | join(",")  ('' em erro)."""
    try:
        v = L.jload(out)
        if v is L.NOINPUT:
            return ""
        cfg = L.jget(L.jget(v, "data"), "config")
        if not L.jtruthy(cfg):
            cfg = {}
        if not isinstance(cfg, dict):
            return ""
        return ",".join(sorted(cfg.keys()))
    except (ValueError, L.JqError):
        return ""


def _sum_values(out):
    """[.data[]?."aggregated-datapoints"[]?.value] | add // 0  -> float, or None (no output)."""
    try:
        v = L.jload(out)
        if v is L.NOINPUT:
            return None
        vals = [L.jget(p, "value") for e in L.jiter(L.jget(v, "data"))
                for p in L.jiter(L.jget(e, "aggregated-datapoints"))]
        nums = [x for x in vals if x is not None]
        if any(isinstance(x, (str, bool, list, dict)) for x in nums):
            return None
        total = sum(nums) if nums else None
        return total if L.jtruthy(total) else 0
    except (ValueError, L.JqError):
        return None


def main():
    L.init()
    L.require_tools()
    L.require_session()

    L.hdr(f"CHECK TRACES — OCI APM (últimos {L.LOOKBACK_MIN}min)")

    if not L.APM_DOMAIN_ID:
        L.skip("apm_domain_id não encontrado nos outputs; pulei validação de traces.")
        L.summary()
        return 0
    L.info(f"APM Domain: {L.APM_DOMAIN_ID}")

    # 1) Confirma que o config das functions carrega APM (pré-requisito de traces).
    L.hdr("Pré-requisito: APM_DOMAIN_URL/APM_DATA_KEY no config das functions")
    missing = 0
    for label, app_id, _ns, _pref, _fn in L.FUNCTIONS_META:
        _rc, out = L.oci_cli("fn", "application", "get", "--application-id", app_id)
        cfg = _config_keys(out)
        if "APM_DATA_KEY" in cfg and "APM_DOMAIN_URL" in cfg:
            L.pass_(f"{label}: APM_DOMAIN_URL + APM_DATA_KEY presentes no config.")
        else:
            L.fail(f"{label}: config sem APM_* (keys atuais: {cfg or '<vazio>'}) -> traces NÃO fluem.")
            missing = 1

    # 2) Ingestão de traces via métricas oci_apm (confiável; a query TQL via CLI é instável).
    #    IngestedBytes > 0 e PayloadRejections == 0 provam que os spans OTLP são aceitos.
    L.hdr("Ingestão de traces (namespace oci_apm)")
    mstart = L.iso_minus_min(L.LOOKBACK_MIN)
    mend = L.iso_now()

    def apm_dp(mql):
        _rc, out = L.oci_cli("monitoring", "metric-data", "summarize-metrics-data",
                             "--compartment-id", L.COMPARTMENT_OCID, "--namespace", "oci_apm",
                             "--query-text", mql, "--start-time", mstart, "--end-time", mend)
        return _sum_values(out)

    ingested = apm_dp("IngestedBytes[1m].sum()")
    rejections = apm_dp("PayloadRejections[1m].sum()")
    ing_s = L.jnum(ingested) if ingested is not None else "0"
    rej_s = L.jnum(rejections) if rejections is not None else "0"
    L.info(f"IngestedBytes={ing_s} | PayloadRejections={rej_s} (janela {L.LOOKBACK_MIN}min)")

    if (ingested or 0) > 0:
        L.pass_(f"APM ingerindo traces (IngestedBytes={ing_s}).")
    else:
        L.skip("IngestedBytes=0 (ingestão tem latência de minutos; gere tráfego e reexecute).")
    if (rejections or 0) > 0:
        L.fail(f"PayloadRejections={rej_s} > 0 — spans OTLP sendo REJEITADOS (endpoint/formato errado). "
               "Ver dim RejectionCause.")
    else:
        L.pass_("PayloadRejections=0 — nenhum payload OTLP rejeitado.")

    if missing != 0:
        L.warn("Traces não vão aparecer enquanto o config APM estiver ausente (rode terraform apply).")
    return L.summary()


if __name__ == "__main__":
    sys.exit(main())
