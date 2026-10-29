# Scripts — `integrating-oracle-rms-webhooks`

Ferramentas CLI genéricas p/ interagir com as APIs do RMS/MFCS via webhook. Python 3 (só biblioteca padrão; Linux, macOS e Windows). Repo-agnósticas: resolvem o repo root via `git` e rodam de qualquer diretório. Todas fazem `import lib_rms` (mesmo diretório).

| Script | O que faz | Muda estado? |
|--------|-----------|--------------|
| `rms-token.py` | Imprime um access_token OAuth2 | Não |
| `rms-get.py` | GET foundation (by-id ou delta), qualquer entidade | Não |
| `register-webhook.py` | register/list/disable no `webhooks/manage` do RMS | **Sim** (register/disable) |
| `simulate-webhook.py` | POST de envelope EVENT/PAYLOAD numa listenerUrl | Não (invoca a function) |
| `lib_rms.py` | Config + helpers + `rms_token()`/`rms_url()` — importado | — |

## Pré-requisitos
```bash
python3 --version   # 3.8+ (no Windows: python ou py)
oci --version; terraform -version            # só p/ o caminho Vault (sem CLIENT_ID/CLIENT_SECRET)
oci session authenticate --profile poc      # token dura ~1h (necessário p/ ler Vault)
terraform -chdir=infra/environments/dev init # p/ ler OCIDs dos secrets no state
```
`curl` e `jq` não são mais necessários (HTTP via `urllib`, JSON via `json`).

## Config (env, todas com default em `lib_rms.py`)
| Env | Default |
|-----|---------|
| `RMS_MERCH_BASE` | `https://rex-npe.retail.sa-vinhedo-1.ocs.oraclecloud.com/rgbu-rex-brxs-par1-mfcs/MerchIntegrations` |
| `RMS_TOKEN_URL` | IDCS `/oauth2/v1/token` |
| `RMS_SCOPE` | `rgbu:merch:MFCS-PAR1` |
| `OCI_PROFILE` | `poc` |
| `CLIENT_ID` / `CLIENT_SECRET` | (fallback; senão lê do Vault via terraform state) |
| `TF_DIR` | `<repo>/infra/environments/dev` |
| `OCI_CMD` / `TERRAFORM_CMD` | `oci` / `terraform` (override p/ testes com fakes) |

Credenciais OAuth: usa `CLIENT_ID`/`CLIENT_SECRET` do env se setados; senão pega os OCIDs dos secrets no `terraform state` e lê do Vault (`oci secrets secret-bundle get` + base64 decode). Nunca loga o secret; `rms-get`/`register-webhook` nunca imprimem o token (só `rms-token.py` imprime, por design). Redirects (302 do IDCS Cloud Gate) não são seguidos — como o `curl` sem `-L`.

## Exemplos

```bash
S=.claude/skills/integrating-oracle-rms-webhooks/scripts

# token (debug) — a última linha é o token
python3 $S/rms-token.py
TOKEN=$(python3 $S/rms-token.py | tail -n1)

# by-id (path-param) — deve retornar o item CERTO
python3 $S/rms-get.py --entity item --id 100010000        # -> itemDescription "Camiseta..."

# delta (since/before)
python3 $S/rms-get.py --entity item \
  --since 2026-05-29T02:01:56Z --before 2026-05-29T02:06:57Z \
  --include "items.item,items.itemDescription"

# outras entidades (mesmo padrão)
python3 $S/rms-get.py --entity diffid  --id G_COLOR
python3 $S/rms-get.py --entity difftype --id C

# simular o webhook batendo na function
LISTENER=$(terraform -chdir=infra/environments/dev output -raw api_base_url)/proxy/item/webhook
python3 $S/simulate-webhook.py --listener "$LISTENER" --mode PAYLOAD
python3 $S/simulate-webhook.py --listener "$LISTENER" --mode EVENT

# registrar o webhook no RMS (⚠️ ativa o disparo real)
python3 $S/register-webhook.py --action list                                  # conferir 1º
python3 $S/register-webhook.py --service foundation/item --listener "$LISTENER"  # register
python3 $S/register-webhook.py --action disable --service foundation/item --listener "$LISTENER"
```

## Testes (offline)
`python3 ../tests/run_tests.py` — fake HTTP local (IDCS/RMS/listener) + fake `oci`/`terraform`; nunca chama RMS, IDCS ou OCI reais.

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
