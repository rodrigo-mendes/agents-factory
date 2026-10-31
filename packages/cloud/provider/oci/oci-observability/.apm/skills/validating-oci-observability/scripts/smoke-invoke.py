#!/usr/bin/env python3
# ==============================================================================
# smoke-invoke.py — invoca as rotas públicas do API Gateway para gerar tráfego
# (logs, métricas e traces). Valida os códigos HTTP retornados.
#
# Uso: ./smoke-invoke.py [N_REPEAT]
#   N_REPEAT: quantas vezes repetir cada rota (default 3, aquece cold start).
#
# Só faz GET de health/hello e um POST /hello (sem efeito persistente); não
# chama a OCI CLI. Timeout de 65s por requisição (como o `curl --max-time 65`).
# ==============================================================================
import os
import re
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_common as L  # noqa: E402

# rota|método|body|códigos_esperados(regex)
ROUTES = [
    '/health|GET||^(200|204)$',
    '/hello|GET||^200$',
    '/hello|POST|{"name":"smoke"}|^200$',
    '/handler/health|GET||^200$',
    '/facade/hello|GET||^200$',
    '/facade/health|GET||^200$',
    '/proxy/health|GET||^200$',
]


def _repeat_count(s):
    """`seq 1 N` -> nº de iterações (N inválido -> erro no stderr, 0 iterações)."""
    try:
        n = float(s)
    except ValueError:
        L.err_raw(f"seq: invalid floating point argument: '{s}'")
        return 0
    return max(0, int(n // 1))


def main(argv):
    L.init()

    repeat = argv[0] if argv and argv[0] != "" else "3"
    L.require_tools()

    L.hdr(f"SMOKE TEST — {L.API_BASE_URL} (x{repeat} por rota)")

    n = _repeat_count(repeat)
    for entry in ROUTES:
        path, method, body, expect = entry.split("|", 3)
        url = f"{L.API_BASE_URL}{path}"
        last_code = ""
        for _ in range(n):
            if method == "GET":
                last_code = L.http_code(url, timeout=65)
            else:
                # Paridade com o bash: "${body:-{}}" expandia para body + "}" quando body
                # não é vazio (o "}" final ficava literal) — mantido de propósito.
                data = (body + "}") if body else "{}"
                last_code = L.http_code(url, method=method, data=data, timeout=65)
        if re.search(expect, last_code):
            L.pass_(f"{method} {path} -> HTTP {last_code}")
        else:
            L.fail(f"{method} {path} -> HTTP {last_code} (esperado {expect})")

    L.info("Tráfego gerado. Aguarde ~1-3min para ingestão de logs/métricas antes de validar.")
    return L.summary()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
