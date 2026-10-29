#!/usr/bin/env python3
# ==============================================================================
# rms-token.py — obtém e imprime um access_token OAuth2 (client-credentials) do
# RMS/IDCS. Debug/uso ad-hoc. Credenciais via env CLIENT_ID/CLIENT_SECRET ou Vault.
#
# Uso:  python3 rms-token.py            # imprime o token (as linhas [i] de credencial vêm antes)
#       python3 rms-token.py --verbose  # imprime também scope/URL
# ==============================================================================
"""Port of rms-token.sh (standard library only)."""

import os
import sys

sys.dont_write_bytecode = True  # keep the skill folder free of __pycache__
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import lib_rms as L  # noqa: E402


def main(argv):
    verbose = bool(argv) and argv[0] in ("--verbose", "-v")
    if verbose:
        L.info("token_url=%s" % L.RMS_TOKEN_URL)
        L.info("scope=%s" % L.RMS_SCOPE)

    # Credential log lines were part of the captured $(rms_token) in the bash version:
    # they are printed together with the token, and only on success.
    lines = []
    token = L.rms_token(log=lambda msg: lines.append("%s[i]%s %s\n" % (L.C_BLU, L.C_RST, msg)))
    if token is None:
        return 1
    L.out("".join(lines) + token + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
