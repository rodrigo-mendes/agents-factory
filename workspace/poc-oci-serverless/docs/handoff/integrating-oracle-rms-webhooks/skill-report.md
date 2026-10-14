---
kind: report
from: "@oci-functions-java"
to: "@oci-functions-java | @oci-serverless-stack | @oci-debugger"
refs: none
capability: integrating-oracle-rms-webhooks
outcome: success
createdAt: 2026-07-03T00:00:00Z
---

## What changed

Criado o skill reutilizável **`integrating-oracle-rms-webhooks`** (conhecimento + scripts), destilando a integração de webhook RMS/MFCS validada em vivo no `func-rr-rest-proxy`.

- `.claude/skills/integrating-oracle-rms-webhooks/SKILL.md` — Publish API, envelope EVENT/PAYLOAD, endpoints foundation (delta/by-id), OAuth2 IDCS, guardrails, marcação ✅ validado / ◻️ inferido.
- `blueprints/{always-do,ask-first,never-do,integration-patterns}.md`.
- `scripts/{lib-rms.sh,rms-token.sh,rms-get.sh,register-webhook.sh,simulate-webhook.sh,README.md}`.
- **Wiring** (descoberta por keyword no P0):
  - `.claude/rules/java-functions-skills.md` — linha na "Skill Directory Mapping".
  - `.claude/agents/oci-functions-java.md`, `oci-serverless-stack.md` — linha na "Skills Reference".
  - `.claude/agents/oci-debugger.md`, `oci-deployer.md` — bullet condicional em "Skills to Load".
  - `CLAUDE.md` (Agent Routing + Key Scripts) e `.claude/AGENTS.md` (seção Skills).

## Resources / OCIDs

- n/a (skill = documentação + tooling; não provisiona recursos).
- Impl de referência: `services/func-rr-rest-proxy/` (`client/RmsClient.java`, `RestProxyFunction.java`, `model/WebhookEnvelope.java`, `func.yaml:ITEM_ENRICH_PATH_TEMPLATE`).
- Endpoint dev do webhook: `<api_base_url>/proxy/item/webhook` (rota ANONYMOUS).
- Base RMS: `https://rex-npe.retail.sa-vinhedo-1.ocs.oraclecloud.com/rgbu-rex-brxs-par1-mfcs/MerchIntegrations`.

## Validation

- `bash -n` nos 5 scripts → ✅.
- `rms-token.sh` → JWT válido (OAuth2 client-credentials via Vault) → ✅.
- `simulate-webhook.sh --mode PAYLOAD` contra o gateway → HTTP 200 → ✅.
- Enrich by-id validado em vivo pela function: `item=100010000 → itemDescription "Camiseta..."`, `100010049 → Trusa`, `100010050 → Panty` → ✅.
- `rms-get.sh --entity item --id ...` de máquina local → **HTTP 302** (IDCS Cloud Gate; rede não allowlistada). A function alcança pelo egress OCI. Rodar de dentro da OCI/VPN.

## Validado vs inferido

- ✅ **Validado (foundation/item)**: base MerchIntegrations (irmã de RmsReSTServices), by-id path-param `/foundation/item/{id}` (NÃO `?item=`), envelope `payload.items`, OAuth2 IDCS, allowlist de rede.
- ◻️ **Inferido (swagger IDCS-gated)**: demais entidades foundation (locations, diff*, tax*, banners, channels, calendar) seguem o mesmo padrão Publish API; método exato do `webhooks/manage` (POST default, configurável).

## Acceptance status

- [ ] Skill auto-descoberto pelo harness → ✅
- [ ] Referenciado por keyword nos agents/rules (P0) → ✅
- [ ] Scripts executáveis + validados onde alcançáveis → ✅

## Next action

Nenhum handoff obrigatório — skill pronto. Agents carregam por keyword (rms/webhook/merchintegrations) no P0. Ao construir/depurar function que consome webhook RMS, seguir `integrating-oracle-rms-webhooks/SKILL.md` e usar os scripts.

## Open issues / blockers

- Método POST vs PUT do `webhooks/manage` e shape da resposta → confirmar de rede allowlistada (`register-webhook.sh --action list` imprime resposta crua).
- Bug pré-existente (fora do escopo do skill): `RmsClient.getItemsDelta` monta a base MerchIntegrations sob `/RmsReSTServices` → EVENT delta dá 404. Corrigir no `func-rr-rest-proxy` quando o modo EVENT for usado.
