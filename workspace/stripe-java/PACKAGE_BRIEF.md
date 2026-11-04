# Package brief — stripe-java (new build from research)

Frente 4: construir do zero a partir de `research_Stripe_Java_v33.md` (COMPLETA, 643 linhas,
Research_Date 2026-07-23, bibliografia presente). Versão canônica: **33.x** (estável atual 33.4.1;
pesquisa feita em 33.1.1 — drift de patch a anotar). v29 e v32.2.0 ficam superseded.

# UPDATE (2026-10-14): target switched to 34.x (current stable major; 34.0.0 shipped 2026-10-01).
# Per-unit research within phases (P3 pilot core -> G2 -> P4 fan-out). The 33.x research
# (research_Stripe_Java_v33.md) is retained as 33->34 migration reference, not the authoring base.
# Units renamed -v34: developing-stripe-java-core-v34, processing-stripe-payments-v34,
# handling-stripe-webhooks-v34, managing-stripe-subscriptions-v34. Pilot = core.

```yaml
slug: stripe-java
language: en
frameworks:
  - Stripe Java SDK (com.stripe:stripe-java) 34.x
needs:
  - skill(s) de conhecimento version-locked para a SDK Java da Stripe 33.x
  - agente para integrar/revisar pagamentos Stripe em Java (webhooks, idempotência, erros)
legacy_source: none
deliverables: [skills, agent, rules, readme]
agent_kind: executor
out_of_scope:
  - versões < 33 (disinformation por version-absolutism)
  - outras linguagens da SDK Stripe
research_worker: researching-technical-frameworks
rounds: 3
```

## Decisões para o G1
1. **Versão canônica:** 33.x (estável 33.4.1; pesquisa em 33.1.1). Confirmar nome version-locked
   (`developing-stripe-java-v33`, seguindo o padrão camel `-vMAJOR-MINOR`? ou `-v33`).
2. **Unidades:** a pesquisa é um doc coeso único. Opção A = **1 skill híbrida** `developing-stripe-java-v33`
   (todo o SDK). Opção B = **split por área** (payments, webhooks, billing, connect, error-handling) —
   exigiria recortar o blueprint em várias skills.
3. **Agente:** `stripe-integrator` (executor, estilo camel-quarkus-integrator) ou advisory.
