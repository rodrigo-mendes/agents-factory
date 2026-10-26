# Scripts — `integrating-oracle-rms-webhooks`

Ferramentas CLI genéricas p/ interagir com as APIs do RMS/MFCS via webhook. Repo-agnósticas: resolvem o repo root via `git` e rodam de qualquer diretório. Todas fazem `source lib-rms.sh`.

| Script | O que faz | Muda estado? |
|--------|-----------|--------------|
| `rms-token.sh` | Imprime um access_token OAuth2 | Não |
| `rms-get.sh` | GET foundation (by-id ou delta), qualquer entidade | Não |
| `register-webhook.sh` | register/list/disable no `webhooks/manage` do RMS | **Sim** (register/disable) |
| `simulate-webhook.sh` | POST de envelope EVENT/PAYLOAD numa listenerUrl | Não (invoca a function) |
| `lib-rms.sh` | Config + helpers + `rms_token()`/`rms_url()` — sourced | — |

## Pré-requisitos
```bash
oci --version; terraform -version; jq --version; curl --version
oci session authenticate --profile poc      # token dura ~1h (necessário p/ ler Vault)
terraform -chdir=infra/environments/dev init # p/ ler OCIDs dos secrets no state
```

## Config (env, todas com default em `lib-rms.sh`)
| Env | Default |
|-----|---------|
| `RMS_MERCH_BASE` | `https://rex-npe.retail.sa-vinhedo-1.ocs.oraclecloud.com/rgbu-rex-brxs-par1-mfcs/MerchIntegrations` |
| `RMS_TOKEN_URL` | IDCS `/oauth2/v1/token` |
| `RMS_SCOPE` | `rgbu:merch:MFCS-PAR1` |
| `OCI_PROFILE` | `poc` |
| `CLIENT_ID` / `CLIENT_SECRET` | (fallback; senão lê do Vault via terraform state) |
| `TF_DIR` | `<repo>/infra/environments/dev` |

Credenciais OAuth: usa `CLIENT_ID`/`CLIENT_SECRET` do env se setados; senão pega os OCIDs dos secrets no `terraform state` e lê do Vault (`oci secrets secret-bundle get | base64 -d`). Nunca loga token/secret.

## Exemplos

```bash
S=.claude/skills/integrating-oracle-rms-webhooks/scripts

# token (debug)
$S/rms-token.sh
TOKEN=$($S/rms-token.sh)

# by-id (path-param) — deve retornar o item CERTO
$S/rms-get.sh --entity item --id 100010000        # -> itemDescription "Camiseta..."

# delta (since/before)
$S/rms-get.sh --entity item \
  --since 2026-05-29T02:01:56Z --before 2026-05-29T02:06:57Z \
  --include "items.item,items.itemDescription"

# outras entidades (mesmo padrão)
$S/rms-get.sh --entity diffid  --id G_COLOR
$S/rms-get.sh --entity difftype --id C

# simular o webhook batendo na function
LISTENER=$(terraform -chdir=infra/environments/dev output -raw api_base_url)/proxy/item/webhook
$S/simulate-webhook.sh --listener "$LISTENER" --mode PAYLOAD
$S/simulate-webhook.sh --listener "$LISTENER" --mode EVENT

# registrar o webhook no RMS (⚠️ ativa o disparo real)
$S/register-webhook.sh --action list                                  # conferir 1º
$S/register-webhook.sh --service foundation/item --listener "$LISTENER"  # register
$S/register-webhook.sh --action disable --service foundation/item --listener "$LISTENER"
```

## Troubleshooting
| Sintoma | Causa | Ação |
|---------|-------|------|
| `rms-get`/`register` → **302** | RMS atrás do IDCS Cloud Gate com allowlist de rede; local não permitido | Rodar de **dentro da OCI** (egress da VCN) ou via **VPN allowlistada**. A function funciona pq sai pelo egress OCI. |
| `rms-get` by-id → 404 | id inexistente OU base/path errado | Confirmar `RMS_MERCH_BASE` (irmã de RmsReSTServices) e `/foundation/<ent>/{id}` |
| by-id retorna item errado | usou `?item=` (não path) | Este script usa path-param — não force query |
| token vazio / Vault falha | sessão OCI expirada | `oci session authenticate --profile poc` |
| register 401/403 | scope/credentialName/token | Cheque `RMS_SCOPE` e a credencial |
| register 404/405 | método/URL do manage | Ajuste `WEBHOOK_HTTP_METHOD` / `MANAGE_URL` |
| simulate HTTP 000 | cold start da function | Repita p/ aquecer |

Ver `../SKILL.md` e `../blueprints/` p/ padrões e armadilhas.
