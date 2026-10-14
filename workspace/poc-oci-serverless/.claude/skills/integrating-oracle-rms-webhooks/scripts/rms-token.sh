#!/usr/bin/env bash
# ==============================================================================
# rms-token.sh — obtém e imprime um access_token OAuth2 (client-credentials) do
# RMS/IDCS. Debug/uso ad-hoc. Credenciais via env CLIENT_ID/CLIENT_SECRET ou Vault.
#
# Uso:  ./rms-token.sh            # imprime só o token (bom p/ $(...) )
#       ./rms-token.sh --verbose  # imprime também scope/URL
# ==============================================================================
source "$(dirname "${BASH_SOURCE[0]}")/lib-rms.sh"
require_tools

VERBOSE=0
[[ "${1:-}" == "--verbose" || "${1:-}" == "-v" ]] && VERBOSE=1

if [[ $VERBOSE -eq 1 ]]; then
  info "token_url=$RMS_TOKEN_URL"
  info "scope=$RMS_SCOPE"
fi

TOKEN="$(rms_token)" || exit 1
printf '%s\n' "$TOKEN"
