# Scripts — `func-rr-rest-proxy`

Utilitários operacionais do webhook de item (RMS/Merchandising → function → BrxServices).

| Script | O que faz | Muda estado? |
|--------|-----------|--------------|
| [`simulate-webhook.sh`](simulate-webhook.sh) | Simula a engine RMS chamando a function (POST EVENT/PAYLOAD) | Não (só invoca a function) |
| [`register-webhook.sh`](register-webhook.sh) | Registra/gerencia o webhook no RMS apontando p/ a function | **Sim** (config no RMS) |
| [`../build-push.sh`](../build-push.sh) | Build + push da imagem Docker pro OCIR | Sim (push imagem) |

Contexto do fluxo: o RMS dispara o webhook → `POST /proxy/item/webhook` → a function parseia o envelope (`payload.items`), **enriquece cada item por id** em `foundation/item/{id}`, transforma p/ XML e envia ao BrxServices.

---

## Pré-requisitos

```bash
# Ferramentas
oci --version        # OCI CLI
terraform -version   # >= 1.5
jq --version
curl --version

# Sessão OCI (profile poc, região sa-saopaulo-1)
oci session authenticate --profile poc      # abre browser; token dura ~1h
oci session validate --profile poc          # confere validade

# Terraform dev inicializado (necessário p/ resolver outputs e state)
terraform -chdir=infra/environments/dev init
```

Variáveis de ambiente comuns (todas têm default; sobrescreva só se preciso):

| Env | Default | Usado por |
|-----|---------|-----------|
| `API_BASE_URL` | `terraform output api_base_url` | ambos |
| `OCI_PROFILE` | `poc` | register |
| `TF_DIR` | `<repo>/infra/environments/dev` | ambos |

> Os scripts resolvem o repo root via `git`, então rodam de qualquer diretório.

---

## 1. `simulate-webhook.sh` — testar a function como o RMS faria

Envia um envelope (EVENT ou PAYLOAD) pra rota `/proxy/item/webhook` (ANONYMOUS, sem auth). Serve pra validar o fluxo ponta-a-ponta sem depender do RMS disparar.

### Passo a passo

```bash
# 1. (1º hit pode dar cold start / HTTP 000 — rode de novo p/ aquecer)
./services/func-rr-rest-proxy/scripts/simulate-webhook.sh

# 2. PAYLOAD customizada com 3 itens default (100010000, 100010049, 100010050)
./simulate-webhook.sh --mode PAYLOAD

# 3. Itens específicos
./simulate-webhook.sh --items 100010000,100010049

# 4. Modo EVENT (só notifica; a function busca o delta)
./simulate-webhook.sh --mode EVENT

# 5. Apontando p/ outra base URL
API_BASE_URL=https://<gw-host>/v1 ./simulate-webhook.sh
```

### Argumentos

| Arg | Default | Descrição |
|-----|---------|-----------|
| `--mode` | `PAYLOAD` | `EVENT` ou `PAYLOAD` |
| `--items` | `100010000,100010049,100010050` | ids separados por vírgula (PAYLOAD) |
| `--uuid` | `sim-webhook-0001` | id de correlação do envelope |
| `--url` | (terraform) | override do `API_BASE_URL` |

### Saída esperada

```
== SIMULATE WEBHOOK (PAYLOAD) -> https://.../v1/proxy/item/webhook ==
[i] uuid=sim-webhook-0001  items=100010000,100010049,100010050
[i] body: {"type":"PAYLOAD",...}
-- resposta --
{"status":"sucesso",...,"total_processed":3,"success_count":3}
  PASS POST /proxy/item/webhook (PAYLOAD) -> HTTP 200
RESULTADO: PASS=1 FAIL=0
```

- **200** = todos itens OK. **207** = falha parcial (veja `errors` no body). **000** = cold start (repita).
- Depois, valide logs `ENRICH`/`TRANSFORM`/`BRX_SEND` (ver seção Observabilidade).

---

## 2. `register-webhook.sh` — registrar a function no webhook do RMS

Chama a API de administração do RMS (`.../MerchIntegrations/services/administration/operations/webhooks/manage`) autenticando via OAuth2 client-credentials. As credenciais vêm do **OCI Vault** (OCIDs lidos do `terraform state`).

> ⚠️ **`register` muda estado no RMS**: ele passa a chamar a function a cada `intervalSeconds`. Rode só quando quiser ativar. Prefira `list` primeiro.

### Passo a passo

```bash
# 0. Garanta sessão OCI válida (o script lê o Vault)
oci session validate --profile poc || oci session authenticate --profile poc

# 1. Ver config atual de webhooks (read-only, recomendado antes de tudo)
./services/func-rr-rest-proxy/scripts/register-webhook.sh --action list

# 2. Registrar/atualizar o webhook (aponta o RMS p/ nossa function)
./register-webhook.sh --action register

# 3. Desativar (mantém a config, enabled=N)
./register-webhook.sh --action disable
```

### Config enviada (PAYLOAD customizada)

```json
{ "collectionSize": 1, "items": [ {
  "service": "foundation/item",
  "credentialName": "APP_TESTE_BLUM",
  "listenerUrl": "<API_BASE_URL>/proxy/item/webhook",
  "includePayload": "Y",
  "enabled": "Y",
  "intervalSeconds": 10,
  "pageLimit": 1000,
  "queryParameter": "include=items.action,items.item,items.status,items.itemDescription",
  "heartbeatIntervalHours": 1
} ] }
```

### Overrides por env

| Env | Default |
|-----|---------|
| `CREDENTIAL_NAME` | `APP_TESTE_BLUM` |
| `INTERVAL_SECONDS` | `10` |
| `PAGE_LIMIT` | `1000` |
| `INCLUDE` | `include=items.action,items.item,items.status,items.itemDescription` |
| `HEARTBEAT_HOURS` | `1` |
| `SERVICE` | `foundation/item` |
| `LISTENER_PATH` | `/proxy/item/webhook` |
| `WEBHOOK_HTTP_METHOD` | `POST` |
| `MANAGE_URL` | `<MERCH_BASE>/services/administration/operations/webhooks/manage` |
| `TOKEN_URL` / `OAUTH_SCOPE` | IDCS token / `rgbu:merch:MFCS-PAR1` |
| `CLIENT_ID` / `CLIENT_SECRET` | (fallback se Vault indisponível) |

### Credenciais OAuth (ordem)

1. `CLIENT_ID` + `CLIENT_SECRET` do ambiente, se ambos setados; senão
2. **Vault**: OCIDs via `terraform state show oci_vault_secret.rest_proxy_oauth_client_id[0]` → `oci secrets secret-bundle get` → `base64 -d`.

O script **nunca** imprime token/secret.

### Saída esperada

```
== WEBHOOK register -> https://.../webhooks/manage ==
[i] service=foundation/item  credentialName=APP_TESTE_BLUM  enabled=Y
[i] listenerUrl=https://.../v1/proxy/item/webhook
  OK Credenciais OAuth carregadas do Vault.
  OK Token OAuth obtido.
-- resposta (HTTP 200) --
{ ... }
  OK register -> HTTP 200
```

---

## 3. `../build-push.sh` — build + push da imagem

```bash
# Requer services/.env (copie de services/.env.example, preencha OCIR_*)
cd services/func-rr-rest-proxy
./build-push.sh 0.0.22          # tag explícita (senão usa version do func.yaml)
```

Roda preflight, `docker login` OCIR, build `linux/amd64`, push. Imprime a URI final. Depois, faça `terraform apply` com `-var rest_proxy_image=<uri>` (o `terraform.tfvars` é permission-blocked — use `-var`).

---

## Fluxo end-to-end (deploy → testar → ativar)

```bash
export JAVA_HOME=$(/usr/libexec/java_home -v 21)   # nunca Java 25/26 (Mockito quebra)

# 1. build + testes
cd services/func-rr-rest-proxy && mvn -B test && cd -

# 2. build + push imagem
services/func-rr-rest-proxy/build-push.sh 0.0.22

# 3. deploy dev (override das 3 imagens nos valores VIVOS p/ não fazer downgrade)
terraform -chdir=infra/environments/dev apply \
  -var rest_proxy_image=gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-rr-rest-proxy:0.0.22 \
  -var api_handler_image=gru.ocir.io/gr2o2hdgzoxw/serverless-app/api-handler:0.0.10 \
  -var api_facade_image=gru.ocir.io/gr2o2hdgzoxw/serverless-app/func-api-facade:0.0.8

# 4. testar (simula o RMS) — rode 2x p/ aquecer cold start
services/func-rr-rest-proxy/scripts/simulate-webhook.sh --mode PAYLOAD

# 5. validar observabilidade (logs/métricas/traces/alarmes)
.claude/skills/validating-oci-observability/scripts/validate-observability.sh

# 6. ativar o webhook real no RMS (quando pronto)
services/func-rr-rest-proxy/scripts/register-webhook.sh --action list      # conferir
services/func-rr-rest-proxy/scripts/register-webhook.sh --action register  # ativar
```

> Verificar imagem viva de uma função:
> `oci fn function get --function-id $(terraform -chdir=infra/environments/dev output -raw rest_proxy_function_id) --profile poc --query 'data.image' --raw-output`

---

## Observabilidade (validar após simular)

Logs estruturados JSON (source `app-rest-proxy-dev`) trazem, por invocação de webhook:

- `WEBHOOK type=.. uuid=.. service=.. count=..` — entrada (uuid = correlação)
- `ENRICH item=<id> elapsed=<ms>ms full=<json>` — item completo pós-fetch
- `TRANSFORM item=<id> xml=<xml>` — pós-transformação
- `BRX_SEND item=<id> method=<PUT|POST|DELETE> elapsed=<ms>ms` — envio ao BrxServices

Traces APM: spans `RMS.OAuthToken`, `RMS.ItemFetch`, `BrxServices.PostItem` (com duração). Métrica: `RestProxyWebhookItems` (dims route/mode/result).

Use o skill `validating-oci-observability` (`.claude/skills/validating-oci-observability/scripts/`).

---

## Troubleshooting

| Sintoma | Causa provável | Ação |
|---------|----------------|------|
| `HTTP 000` | Cold start (function escalou a zero) | Repita a chamada (aquece) |
| `HTTP 207` no webhook | Falha parcial por item | Veja `errors[]` no body / logs `Item <id> failed` |
| `HTTP 500` + `404` no EVENT | Delta usa base MerchIntegrations errada (bug conhecido) | Use `--mode PAYLOAD`; correção do delta pendente |
| register `HTTP 401/403` | Token/scope/credentialName | Cheque OAuth scope e `oci session` |
| register `HTTP 404/405` | Método/URL do `manage` diferente | Ajuste `WEBHOOK_HTTP_METHOD` / `MANAGE_URL` |
| `Falha ao ler secrets do Vault` | Sessão OCI expirada | `oci session authenticate --profile poc` |
| `enrich` retorna item errado | `?item=` não filtra | Já corrigido: usa path `/foundation/item/{id}` |
| Mockito "cannot mock" nos testes | Java 25/26 | `export JAVA_HOME=$(/usr/libexec/java_home -v 21)` |
