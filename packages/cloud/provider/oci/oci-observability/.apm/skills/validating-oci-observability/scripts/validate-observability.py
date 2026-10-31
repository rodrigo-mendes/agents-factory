#!/usr/bin/env python3
# ==============================================================================
# validate-observability.py — orquestra a validação dos pilares de
# observabilidade em dev: gera tráfego, espera ingestão e valida
# logs, métricas, traces, alarmes e dashboards. Imprime tabela PASS/FAIL final.
#
# Uso: ./validate-observability.py [--no-smoke] [--wait SEG]
#   --no-smoke : não gerar tráfego (assume que já houve invocações)
#   --wait N   : segundos de espera pós-smoke p/ ingestão (default 120)
# Exit: nº de pilares em FAIL (0 = tudo OK); 2 = sessão OCI inválida.
# ==============================================================================
import os
import subprocess
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402


def main(argv):
    L.init()

    do_smoke = True
    wait_sec = "120"
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--no-smoke":
            do_smoke = False
            i += 1
        elif a == "--wait":
            if i + 1 >= len(argv):
                L.unbound(os.path.basename(__file__))
            wait_sec = argv[i + 1]
            i += 2
        else:
            i += 1

    L.require_tools()
    # Gate robusto p/ varredura longa: renova + prova a sessão ao vivo (a SecurityToken
    # do perfil poc expira ~1h e já quebrou runs longos com 401 no meio).
    L.require_fresh_session()

    results = {}

    def run_step(name, script, *args):
        L.hdr(f"PILAR: {name}")
        sys.stdout.flush()
        sys.stderr.flush()
        rc = subprocess.call([sys.executable, os.path.join(L.SCRIPT_DIR, script)] + list(args))
        results.setdefault(name, "PASS" if rc == 0 else "FAIL")

    # 1) Gera tráfego
    if do_smoke:
        run_step("smoke", "smoke-invoke.py", "3")
        L.info(f"Aguardando {wait_sec}s para ingestão de logs/métricas/traces...")
        L.sleep(wait_sec)
    else:
        L.info("--no-smoke: pulando geração de tráfego.")

    # 2) Valida os pilares (5 pilares: logs, métricas, traces, alarmes, dashboards)
    run_step("logs", "check-logs.py")
    run_step("metrics", "check-metrics.py")
    run_step("traces", "check-traces.py")
    run_step("alarms", "check-alarms.py")
    run_step("dashboards", "check-dashboards.py")

    # 3) Resumo consolidado
    L.hdr("RESUMO CONSOLIDADO — OBSERVABILIDADE (dev)")
    fails = 0
    for k in ("smoke", "logs", "metrics", "traces", "alarms", "dashboards"):
        v = results.get(k, "N/A")
        if v == "PASS":
            print(f"  {L.C_GRN}{k:<10} PASS{L.C_RST}")
        elif v == "FAIL":
            print(f"  {L.C_RED}{k:<10} FAIL{L.C_RST}")
            fails += 1
        else:
            print(f"  {k:<10} {v}")

    print("")
    if fails == 0:
        print(f"{L.C_GRN}{L.C_BLD}Observabilidade VALIDADA — todos os pilares OK.{L.C_RST}")
    else:
        print(f"{L.C_RED}{L.C_BLD}{fails} pilar(es) com falha — ver detalhes acima.{L.C_RST}")
        print("Dica: falhas em metrics/traces geralmente significam config das functions vazio")
        print("      (Problema #1 do plano) — rode o terraform apply e reexecute.")
    return fails


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
