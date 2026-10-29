# Plano — Quarkus + AWS Lambda para construir um SaaS (com SDD e time de agentes)

## Em resumo

**O que você pede:** programar AWS Lambdas com Quarkus e usar os serviços AWS de um SaaS completo
(frontend com CDN, backend com autenticação/autorização, pagamentos com Stripe, IA com LangChain4j),
com um **time de agentes** que trabalha a partir de uma **especificação (SDD)** e passa o trabalho
de um agente para outro por um **handoff** padronizado.

**O que você recebe no final:**

1. **Mapa de conhecimento por ondas**: tudo o que é preciso saber, em ordem, com a skill que cobre cada parte (§2).
2. **13 skills de conhecimento versionadas novas** (U1–U13: Quarkus ↔ AWS, Stripe, LangChain4j, OpenSpec, clean code, observabilidade), além das skills de processo (orquestrador, handoff, estrutura, guarda-chuva de observabilidade, validação ao vivo). O resto já existe no repo e é reaproveitado.
3. **Um processo SDD completo e contínuo** (§3): entrevista → **spec de arquitetura técnica + ADRs** → **spec de funcionalidades** → design → tarefas → **ciclo de implementação em várias etapas** (testes, implementação, refinamento, clean code, refatoração, revisão) → deploy → sincronização código → spec → arquivamento. Cada passagem tem critérios de aceite explícitos.
4. **Um orquestrador** (`/building-quarkus-aws-saas`) que conduz esse processo e é o único que conversa com você.
5. **5 agentes novos no time** (integrador Quarkus, revisor de código, deployer, observabilidade, debugger) + o `spec-synchronizer` do handoff, trabalhando junto com 4 que já existem (§4).
6. **Handoff genérico** (pacote novo `handoff-core`, §5): skill + scripts determinísticos + agente `spec-synchronizer`. Os fluxos Quarkus/AWS **e** OCI passam a usá-lo.
7. **Observabilidade completa** (logs, métricas, traces X-Ray, alarmes, dashboards), no modelo do pacote OCI de observabilidade:
   - 4 skills de instrumentação no código Quarkus;
   - um pacote `aws-observability` com o agente `aws-observability`, o comando `/observe-aws-workload` e uma skill de **validação ao vivo** com scripts, como os `check-*.sh` do OCI.
8. **Pacotes em camadas, pensados para reuso** (§4.1, §6):
   - **`quarkus-core`**: base com ArC, REST, JUnit e clean code;
   - sobre ele, **Quarkus + Camel** (o atual) e **`quarkus-aws`** (o novo);
   - **`aws-lambda`** (deployer/debugger, qualquer runtime), **`aws-observability`** e **`handoff-core`** como pacotes independentes;
   - **`quarkus-aws-saas`** só como a composição deste SaaS.

Nada é construído antes da sua aprovação nos gates **G1** (escopo e nomes), **G2** (piloto), **G3** (commits). O push (**G4**) é sempre feito por você.

---

## 1. O que já existe e o que falta

| Área | Já existe no repo (reaproveitado) | Falta (novo) |
|---|---|---|
| Arquitetura AWS | `aws-skills`: 40 skills (CloudFront, S3, Cognito, API Gateway, Lambda, DynamoDB, SQS/SNS, WAF, X-Ray, SaaS multi-tenant…) + agente `aws-architect` | — |
| Infra (Terraform) | 26 skills `provisioning-aws-*-v6` + agente `aws-terraform-engineer` | — |
| Quarkus básico | `developing-quarkus-{arc,rest,junit}-v3-40`, hoje **dentro** de `camel-quarkus-skills` | movê-los para um pacote base `quarkus-core` + Quarkus **na Lambda** |
| Stripe | skills stripe-java 34 + `stripe-advisor` + `stripe-integrator` (Java puro) | Stripe **dentro do Quarkus/Lambda** |
| LangChain4j | 1.22.0 em Java puro (Quarkus fora do escopo) | extensão **quarkus-langchain4j** |
| Clean code | `refactoring-oci-java` + regra `java-functions-clean-code` (específicas de OCI) | versão para Quarkus/Lambda |
| Processo | `coordinating-oci-handoffs` (só para OCI) | SDD/OpenSpec + handoff **genérico** |

## 2. Mapa de conhecimento por ondas

Cada onda depende da anterior. A mesma ordem é usada para pesquisar e gerar as skills (P3/P4).

| Onda | Tema | Conhecimento | Skill |
|---|---|---|---|
| **0 · Processo** | Como trabalhar | SDD contínuo (§3), OpenSpec, handoff, clean code e refatoração | 🆕 U9 `specifying-changes-with-openspec-v<M>-<m>` · 🆕 U10 `refactoring-quarkus-java` · 🆕 orquestrador · 🆕 handoff |
| **1 · Base Lambda** | Rodar Quarkus na Lambda | `quarkus-amazon-lambda`, `function.zip`, JVM × nativo (`provided.al2023`), SnapStart, cold start, estrutura de projeto | 🆕 U1 `developing-quarkus-amazon-lambda-v3-40` · 🆕 `structuring-quarkus-lambda-projects` · ✅ `architecting-lambda-serverless-patterns` |
| | API HTTP | `quarkus-amazon-lambda-http`/`-rest` atrás do API Gateway | 🆕 U2 `developing-quarkus-amazon-lambda-http-v3-40` · ✅ `designing-aws-api-gateway-serverless` |
| | Testes | `quarkus-test-amazon-lambda`, mock event server, LocalStack Dev Services | 🆕 U6 `testing-quarkus-amazon-lambda-v3-40` · ✅ `developing-quarkus-junit-v3-40` |
| **2 · Identidade** | Login e permissões | Cognito, authorizer JWT, claims → `SecurityIdentity`, `@RolesAllowed`/`@PermissionsAllowed`, `cognito:groups`, tenant por usuário | 🆕 U3 `securing-quarkus-lambda-cognito-v3-40` · ✅ `securing-aws-cognito` |
| **3 · Dados e eventos** | Persistência | DynamoDB (+ enhanced client), S3 (URLs pré-assinadas) via Quarkiverse `quarkus-amazon-services` | 🆕 U4 `integrating-quarkus-amazon-data-v3-40` · ✅ `designing-dynamodb-nosql` |
| | Mensageria e config | SQS/SNS/EventBridge, Lambda acionada por SQS, SSM/Secrets Manager como fonte de config | 🆕 U5 `integrating-quarkus-amazon-messaging-v3-40` · ✅ `architecting-aws-sqs-messaging`, `securing-aws-secrets-certificates` |
| **4 · Frontend** | Distribuição | SPA no S3 + CloudFront (OAC), Route 53, ACM (us-east-1), WAF | ✅ `delivering-cloudfront-cdn`, `architecting-aws-s3-storage`, `configuring-aws-route53-dns`, `securing-aws-waf-web-acls` |
| **5 · Negócio** | Pagamentos | `StripeClient` como bean CDI, chave no Secrets Manager, webhook na Lambda (corpo bruto/base64 preservado para a assinatura), idempotência | 🆕 U7 `integrating-stripe-quarkus-v3-40` · ✅ skills stripe-java 34 |
| | IA | `@RegisterAiService`, OpenAI / Anthropic / **Bedrock** (role IAM, sem chave), timeouts × timeout da Lambda, limites de streaming | 🆕 U8 `integrating-quarkus-langchain4j-v<ext>` (indica qual versão do LangChain4j ela fixa em relação à 1.22.0) |
| **6 · Operação** | Infra e deploy | Terraform dos serviços, custo por tenant | ✅ `provisioning-aws-*-v6`, `architecting-aws-saas-multitenant`, `managing-aws-costs` |
| | Deploy e diagnóstico de Lambda | deploy do artefato, versões/aliases, rollback, smoke; diagnóstico por erro (502/503/504, timeout, AccessDenied, throttling, cold start) | 🆕 `deploying-aws-lambda` · 🆕 `debugging-aws-lambda` (modelo: `deploying-oci-functions`, `debugging-deployed-functions`) |
| **7 · Observabilidade** (modelo: pacote `oci-observability`) | Logs (código) | JSON logging no Quarkus, controles avançados de log da Lambda (formato JSON, nível), correlação por `requestId`/`tenantId` no MDC, sem PII, retenção | 🆕 U11 `logging-quarkus-lambda-v3-40` |
| | Traces (código) | X-Ray: `quarkus-amazon-lambda-xray` × `quarkus-opentelemetry` + ADOT, tracing dos clientes AWS SDK, sampling, efeito no nativo/SnapStart | 🆕 U12 `tracing-quarkus-lambda-v3-40` · ✅ `tracing-aws-xray` |
| | Métricas (código) | métricas de negócio e técnicas: Micrometer × CloudWatch EMF, dimensão por tenant sem explosão de cardinalidade; compatibilidade do Powertools Java com Quarkus | 🆕 U13 `monitoring-quarkus-lambda-v3-40` · ✅ `implementing-lambda-powertools-java` |
| | Os 3 pilares juntos (código) | skill guarda-chuva que compõe U11–U13 (como `observing-oci-java-functions`) | 🆕 `observing-quarkus-lambda` |
| | Infra de observabilidade | log groups, métricas e alarmes (CloudWatch), X-Ray (grupos, sampling rules), dashboards, Application Signals, SLOs, alarmes por tenant | ✅ `monitoring-cloudwatch-observability`, `provisioning-aws-cloudwatch-v6`, `provisioning-aws-xray-v6` (P2 confere se dashboards e SLOs estão cobertos e declara a lacuna, se houver) |
| | Validação ao vivo | provar que logs, métricas, traces, alarmes e dashboards funcionam de verdade, com AWS CLI, só leitura | 🆕 `validating-aws-observability` (scripts `check-logs`, `check-metrics`, `check-traces`, `check-alarms`, `check-dashboards`, como `validating-oci-observability`) |

✅ = já existe · 🆕 = nova. Nomes e versões finais são confirmados em G1, depois da verificação de versões (P1).
U10 fica em `quarkus-core` (vale para Camel e AWS) e parte da estrutura de `refactoring-oci-java` (Extract Method, decomposição por pacote, DRY, records), adaptada a Quarkus/CDI/Lambda.
**Fora do escopo:** Quarkus 4, SAM/CDK, Amplify, SDK de auth no browser, Camel na Lambda, ECS, RAG/vector stores.

---

## 3. O processo SDD, de ponta a ponta

### 3.1 Visão geral

```
 E1 Entrevista ──► E2 Spec de arquitetura técnica ──► E3 Spec de funcionalidades ──► E4 Design da change ──► E5 Tarefas
  (você)            + ADRs (uma por projeto, evolui)   (por capacidade, via changes)  (liga E2 a E3)            │
                                                                                                        ▼
 E9 Arquivamento ◄── E8 Sync código→spec ◄── E7 Deploy e validação ◄── E6 Ciclo de implementação (I0–I9, por tarefa)
       ▲                    ▲  (a qualquer momento: edição manual, correção do debugger, divergência de um agente)
       └── gate final ──────┘
```

Toda etapa termina num **critério de aceite** (§3.6). Ninguém avança enquanto ele não for cumprido.
Toda passagem entre agentes é um **registro de handoff** (§5).

### 3.2 E1 — Entrevista SDD (como funciona)

O orquestrador conduz a entrevista em **8 blocos**. Em cada rodada: no máximo 10 perguntas, opções
concretas sempre que possível, e um **resumo para você confirmar** no fim de cada bloco.

| Bloco | Pergunta central | Exemplos | Vai para |
|---|---|---|---|
| B1 Visão | Que problema o SaaS resolve e para quem? | proposta de valor, métrica de sucesso | `proposal.md` |
| B2 Atores | Quem usa e com que papel? | usuário, admin do tenant, admin da plataforma, sistema externo (Stripe) | E3 (atores), E2 (modelo de autorização) |
| B3 Funcionalidades | O que cada ator faz? | jornadas, casos de uso, prioridade (MoSCoW) | E3 |
| B4 Regras de negócio | O que é permitido ou proibido? | limites por plano, ciclo de vida da assinatura | E3 (requisitos + cenários negativos) |
| B5 Dados | Que dados existem e de quem são? | entidades, dono (tenant), retenção, dados pessoais (LGPD) | E2 (modelo de dados), E3 |
| B6 Requisitos não funcionais | Quão rápido, seguro, barato e disponível? | latência p95, RPO/RTO, custo por tenant, isolamento entre tenants | E2 (metas mensuráveis) |
| B7 Restrições técnicas | O que já está decidido? | região, conta AWS, domínio, provedores de IA, orçamento | E2 (ADRs) |
| B8 Aceite | Como saberemos que está pronto? | demo, cenários de aceite, fora de escopo | E3 (cenários), §3.6 |

Técnicas aplicadas: **perguntar só o que falta** (o mapa de ondas e a spec existente dizem o que já
se sabe); **devolver o entendido** ("entendi que… confirma?"); **perguntas abertas registradas** e
nunca supostas. Uma pergunta só pode ficar aberta se você marcar "não bloqueia". Na primeira change
do projeto, todos os blocos são cobertos. Nas seguintes, apenas os blocos que a change afeta.

### 3.3 E2 e E3 — Duas specs, com papéis diferentes

| | **Spec de arquitetura técnica + ADRs** (E2) | **Spec de funcionalidades** (E3) |
|---|---|---|
| Responde | *Como* o sistema é construído | *O que* o sistema faz |
| Escopo | o projeto inteiro; evolui com o tempo | uma capacidade (ex.: `items`, `billing`); muda via changes |
| Conteúdo | visão de componentes (frontend, API, Lambdas, dados, eventos), serviços AWS escolhidos, modelo de tenancy, modelo de segurança (authN, authZ, segredos), modelo de dados, integrações (Stripe, LLM), metas NFR mensuráveis, **observabilidade** (SLOs, campos obrigatórios de log, retenção, sampling de traces, lista de alarmes com limiar, dashboards; revisada pelo `aws-observability`), layout de IaC, convenções de código; **ADRs** (decisão, alternativas, consequência) | requisitos com ID (`R1`…) no formato "o sistema SHALL…", cada um com cenários QUANDO/ENTÃO (felizes e negativos), atores, regras de negócio |
| Quem escreve | orquestrador, a partir de B5–B7 | orquestrador, a partir de B2–B4 e B8 |
| Quem revisa | `aws-architect` (pilares WAF, lente SaaS) | você (e o `spec-synchronizer` na volta) |
| Onde (a confirmar em P1) | `openspec/specs/architecture/spec.md` + `openspec/specs/architecture/adr/NNN-*.md` | `openspec/specs/<capacidade>/spec.md`; deltas em `openspec/changes/<id>/specs/` |

O **design da change** (E4, `openspec/changes/<id>/design.md`) liga as duas: diz quais componentes
de E2 atendem cada requisito de E3. Se a change precisar mudar a arquitetura (um serviço novo, por
exemplo), ela inclui também um **delta da spec de arquitetura** + ADR, revisado pelo `aws-architect`.

**ADRs gerados em E2.** O orquestrador gera um ADR para cada decisão que custa caro mudar:
- cada restrição do bloco B7;
- cada escolha de serviço AWS (ex.: DynamoDB × Aurora, HTTP API × REST API);
- o modelo de tenancy (pool/silo/bridge) e o modelo de segurança;
- JVM × nativo × SnapStart;
- cada provedor externo (Stripe, OpenAI/Anthropic/Bedrock);
- cada trade-off entre metas NFR.

| Campo | Conteúdo |
|---|---|
| `NNN-titulo.md` | numeração sequencial, nunca reaproveitada |
| Status | `proposed → accepted`, depois `superseded by NNN` (um ADR aceito não é editado, é substituído) |
| Contexto | o problema e as forças (NFRs, restrições), com links para os requisitos `R*` afetados |
| Decisão | o que foi escolhido, em uma frase |
| Alternativas | ≥ 2, com o motivo da rejeição, citando a skill que sustenta o argumento (ex.: `designing-dynamodb-nosql`) |
| Consequências | positivas, negativas, e o que passa a ser proibido (vira checagem do revisor em I7) |
| Fontes | as skills/páginas oficiais usadas (regra de evidência; sem fonte → `(unverified)`) |

Os ADRs aceitos valem para todo o projeto. O revisor (I7) e o `spec-synchronizer` (E8) checam o código e os deltas contra eles.

### 3.4 E5 — Tarefas

Cada tarefa em `tasks.md` tem: ID, requisitos cobertos (`R1`, `R2`), componente de E2, agente
responsável, dependências, e as skills que o work-order vai mandar carregar. Uma tarefa é pequena
o bastante para um ciclo I0–I9 (regra prática: um endpoint ou um consumidor de evento).

### 3.5 E6 — Ciclo de implementação em várias etapas (por tarefa)

| Etapa | O que é feito | Evidência no report | Quem |
|---|---|---|---|
| **I0 Preparar** | lê o work-order, os requisitos, os cenários e as skills; escreve um plano curto (classes, pacotes, testes) | "Plano" | integrador |
| **I1 Testes primeiro** | cada cenário vira ≥ 1 teste, com nome rastreável (`R1_outroTenant_retorna403`); os testes falham | lista cenário → teste | integrador |
| **I2 Implementação mínima** | o menor código que faz os testes passarem | testes verdes | integrador |
| **I3 Refinamento** | casos de borda, validação de entrada, mapeamento de erros → HTTP, isolamento de tenant, timeouts × timeout da Lambda, idempotência; novos testes para cada um | lista de casos adicionados | integrador |
| **I4 Clean code** | aplica a regra de clean code: métodos pequenos, nomes que revelam a intenção, constantes no lugar de valores mágicos, responsabilidade única, sem duplicação; testes verdes a cada passo | checklist da regra | integrador (skill U10) |
| **I5 Refatoração para manutenção** | extrai colaboradores (`web/`, `service/`, `client/`, `obs/`), records para valores agrupados, remove acoplamento; **comportamento idêntico**, testes verdes após cada passo | antes/depois (classes, métodos > 40 linhas) | integrador (skill U10) |
| **I6 Verificação automática** | `mvn -q verify` (testes + cobertura JaCoCo das classes novas ≥ limite definido em G1), build do `function.zip`, nenhum aviso novo de compilação | saída dos comandos | integrador |
| **I7 Revisão independente** | revisão do diff contra a regra de clean code, os 🚫 das skills carregadas **e os ADRs vigentes** (ex.: o código usa o serviço, o modelo de tenancy e o padrão de segredos que os ADRs decidiram; uma violação de ADR é sempre HIGH, e para mudar a decisão é preciso um novo ADR em E2); achados HIGH/MEDIUM/LOW com arquivo:linha. Stripe → também `stripe-advisor`; mudança de design → também `aws-architect` | `review-NN.md` | `quarkus-code-reviewer` 🆕 (só leitura, não viu o raciocínio do autor) |
| **I8 Correção** | HIGH sempre corrigido; MEDIUM corrigido ou justificado; volta para I6. **No máximo 2 rodadas**; depois disso, a decisão sobe para você | achados resolvidos | integrador |
| **I9 Fechamento** | report final com o "Impacto na spec" (implementado / divergências / ambiguidades) | `report-NN-code.md` | integrador |

O orquestrador lança o integrador para I0–I6 (uma chamada), o revisor para I7 e o integrador de
novo para I8 quando há achados. Assim, quem revisa nunca é quem escreveu. Para Stripe, o
`stripe-integrator` faz I0–I9 com a skill U7, e o revisor + `stripe-advisor` fazem I7.

**Limite de tentativas e escalonamento para você.** Todo laço tem um máximo. Os contadores ficam no
`status.md` (são calculados pelo `board.py` a partir dos registros e não dependem da memória de um agente).

| Laço | Parâmetro | Padrão | Ao estourar |
|---|---|---|---|
| I1–I6: deixar testes e build verdes | `limits.build_attempts` | 3 por tarefa | escala para você |
| I7–I8: revisão → correção | `limits.review_rounds` | 2 | escala |
| E7: deploy → diagnóstico → correção | `limits.deploy_cycles` | 2 | escala (nenhum novo apply sem você) |
| E8: spec-delta refeito | `limits.delta_revisions` | 2 | escala |
| `check_records.py` falhando no mesmo registro | `limits.record_rejections` | 2 | escala |

**Os limites são parâmetros**, com 3 níveis de precedência (o mais específico vence):

1. **Padrão do perfil**: `handoff-profile.yaml` instalado (os valores acima).
2. **Projeto**: `openspec/handoff-profile.yaml`, só com o que muda:
   ```yaml
   limits:
     build_attempts: 5
     review_rounds: 3
   ```
3. **Execução**: argumentos do orquestrador, válidos só para aquela change:
   `/building-quarkus-aws-saas change=list-tenant-items limits.review_rounds=4 limits.deploy_cycles=1`

Os valores efetivos (e de onde veio cada um) ficam gravados no `status.md` da change, e o
`board.py` usa sempre esses valores. Validação feita pelo `check_records.py`: inteiro ≥ 1. O valor
`0` (escalar já na primeira falha) só é aceito com confirmação explícita sua, como o `rounds: 0` do
pipeline da fábrica. O mesmo mecanismo vale para os outros parâmetros do perfil (ex.: `coverage_min`).

Escalar significa: o agente devolve `outcome: needs-input`, e o orquestrador **para a tarefa** e te
mostra um registro `escalation-NN.md` com:
- o que foi tentado em cada tentativa;
- o erro ou achado que persiste, com evidência (saída do comando, arquivo:linha);
- a hipótese da causa;
- 2–4 opções concretas (ex.: relaxar o requisito, novo ADR, mudar a abordagem, aceitar o risco) com o impacto de cada uma.

Sua resposta é gravada literalmente e zera o contador daquela tarefa. As outras tarefas
independentes continuam enquanto isso.

### 3.6 Critérios de aceite (definição de "pronto" em cada passagem)

Regra: **quem produz nunca é quem verifica.** Cada etapa tem um verificador independente (outro
agente, um script ou você) e grava o resultado em `handoff/verify-<etapa>.md`.

| Passagem | Critérios (todos obrigatórios) | Autor | Verificador independente |
|---|---|---|---|
| **E1 → E2/E3** (entrevista pronta) | os 8 blocos respondidos (ou os blocos afetados, em changes seguintes); cada resumo confirmado por você; perguntas abertas só com "não bloqueia" | orquestrador | você + `spec-synchronizer` (modo revisão: lacunas e contradições) |
| **E2 aceita** (arquitetura + ADRs) | toda meta NFR mensurável (número + unidade); toda decisão relevante com ADR completo (≥ 2 alternativas, consequências, fontes); modelo de tenancy e de segurança definidos; nenhum HIGH em aberto; sua aprovação registrada | orquestrador | `aws-architect` + `check_records.py` (campos dos ADRs) + você |
| **E3 aceita** (funcionalidades) | todo requisito com ID e "SHALL"; ≥ 1 cenário feliz e ≥ 1 negativo por requisito; todo requisito ligado a um componente de E2 e sem conflito com os ADRs; nenhuma pergunta bloqueante | orquestrador | `spec-synchronizer` (modo revisão: testabilidade, conflito com ADR) + `check_records.py` (formato) + você |
| **E4 aceito** (design da change) | todo requisito da change mapeado a componentes de E2; mudanças de arquitetura com delta + ADR | orquestrador | `aws-architect` |
| **E5 pronta** (tarefas) | todo requisito coberto por ≥ 1 tarefa; toda tarefa com agente, skills e dependências; sem ciclos de dependência | orquestrador | `board.py` (cobertura requisito → tarefa, ciclos) |
| **Tarefa pronta** (fim de I9) | todo cenário dos requisitos ligados tem um teste verde; `mvn -q verify` verde; cobertura ≥ limite; build do `function.zip` OK; nenhum HIGH do revisor em aberto (inclusive violação de ADR); MEDIUMs resolvidos ou justificados; report válido com "Impacto na spec" | integrador | `quarkus-code-reviewer` + scripts (o orquestrador reexecuta `mvn -q verify`, não confia no report) |
| **Deploy pronto** (E7) | `terraform plan` sem destroy inesperado; apply aprovado por você; smoke test de cada cenário feliz OK; cold start dentro da meta NFR | deployer | `aws-lambda-debugger` (modo verificação pós-deploy) |
| **Observabilidade pronta** (E7) | os 5 pilares provados ao vivo depois do smoke test: logs JSON com `requestId`/`tenantId` e sem PII, métricas de negócio publicadas, trace X-Ray ponta a ponta (API GW → Lambda → DynamoDB), alarmes do E2 existentes e em estado válido, dashboard renderizando dados; teste de disparo de alarme só com sua aprovação | `aws-observability` (infra) + integrador (código) | `validating-aws-observability` (scripts) + `aws-lambda-debugger` |
| **E8 aceita** (spec-delta) | delta coerente com o diff; sem conflito com ADR (ou com ADR novo proposto); perguntas respondidas | `spec-synchronizer` | você + `check_records.py` |
| **Gate final: arquivar a change / fazer commit** (E9) | todas as passagens acima verdes (`verify-*.md`); **drift = 0**; nenhum spec-delta pendente; nenhuma pergunta aberta bloqueante; `check_records.py` com código de saída 0; aprovações registradas | orquestrador | `check_records.py` + `detect_drift.py` + `board.py` |

### 3.7 E8 — Sincronização código → spec (a volta)

O código nunca fica "à frente" da spec sem que alguém decida. Há três origens de mudança:

| Origem | Exemplo | Como é detectada |
|---|---|---|
| Um agente diverge na implementação | paginação adicionada em I3 | "Impacto na spec" do report (gatilho 1: a cada handoff) |
| Uma correção do debugger | timeout ajustado, novo erro 429 | report de correção + `detect_drift.py` (gatilho 1) |
| Você edita o código à mão | novo filtro `?status=active` | o hook `Stop` avisa (gatilho 4); você roda `/syncing-spec-from-code` (gatilho 3); se esquecer, o gate final bloqueia (gatilho 2) |

Passos, sempre os mesmos:

1. `detect_drift.py` lista os arquivos/endpoints alterados desde o último SHA sincronizado que nenhuma tarefa cobre.
2. O `spec-synchronizer` lê esse diff, as duas specs e os reports, e escreve um **spec-delta** (funcional e/ou de arquitetura):
   ```markdown
   ## MODIFIED Requirements
   ### Requirement: R1 Listar itens do próprio tenant
   #### Scenario: paginação
   - WHEN o usuário chama GET /tenants/A/items?limit=200
   - THEN recebe no máximo 50 itens e um cursor `next`
   ## Perguntas
   - O limite 50 é regra de negócio ou só técnica?
   ```
3. O orquestrador mostra o delta. Você **aceita** (a spec é atualizada), **rejeita** (vira um work-order para reverter o código) ou **responde às perguntas** (o delta é refeito).
4. `board.py` grava o novo SHA sincronizado. O drift volta a zero e o gate libera.

### 3.8 Exemplo condensado

*"O usuário logado vê os itens do tenant dele."* E1 (blocos B3, B4 e B8, porque a arquitetura já
existe) → E3: `R1` com os cenários "tenant A vê os itens de A" e "tenant A pedindo B → 403" → E4:
Lambda HTTP + authorizer Cognito + DynamoDB `PK=TENANT#id` → E5: T1 código, T2 Terraform → E6 T1:
dois testes (I1), resource + repositório (I2), paginação por causa do limite de 1 MB da Query (I3:
**divergência**), métodos extraídos (I4), `ItemsService` separado do resource (I5), `mvn verify`
verde (I6), revisor aponta 1 MEDIUM (I7), corrigido (I8), report (I9) → E7: plan, seu OK, apply,
smoke → E8: o delta de paginação é proposto e você aceita → E9: gate verde, change arquivada.

---

## 4. O time de agentes

```
                         você
                          │
            /building-quarkus-aws-saas  (orquestrador inline: conduz E1–E9, único que fala com você)
                          │  work-orders ──► agentes ──► reports;  scripts entre cada passo
 ┌──────────┬──────────┬──┴───────┬───────────┬────────────┬───────────┬───────────┬──────────────┬──────────────┐
 ▼          ▼          ▼          ▼           ▼            ▼           ▼           ▼              ▼
aws-      quarkus-   quarkus-   stripe-     aws-terraform aws-lambda- aws-        aws-lambda-    spec-
architect lambda-    code-      integrator  -engineer     deployer 🆕 observa-    debugger 🆕    synchronizer 🆕
(E2/E4)   integrator reviewer🆕 + advisor   (infra)       (E7)        bility 🆕   (falhas,       (E1/E3 revisão,
          🆕 (E6)    (I7)       (Stripe)                              (logs,      pós-deploy)    E8 delta)
                                                                      métricas,
                                                                      X-Ray,
                                                                      alarmes)
```

**Divisão da observabilidade (igual ao OCI):** a instrumentação **no código** (logs JSON, spans,
métricas) é do `quarkus-lambda-integrator`, com U11–U13. A **infra** (log groups, retenção, alarmes,
dashboards, X-Ray) e a **validação ao vivo** são do `aws-observability`. A infra que não é de
observabilidade continua com o `aws-terraform-engineer`.

| Agente | Tipo | Etapa | Lê | Escreve |
|---|---|---|---|---|
| `building-quarkus-aws-saas` (skill) | orquestrador inline | E1–E9 | tudo | specs, tasks, work-orders, aplica deltas aprovados |
| `aws-architect` ✅ | consultivo | E2, E4 | work-order + specs | `report-architecture.md` |
| `quarkus-lambda-integrator` 🆕 | executor | I0–I6, I8–I9 | work-order, review, diagnosis | código + `report-NN-code.md` |
| `quarkus-code-reviewer` 🆕 | revisor (só leitura) | I7 | diff + regra de clean code + skills | `review-NN.md` |
| `stripe-integrator` ✅ | executor (gera o código Stripe) | I0–I9 de tarefas Stripe | work-order (com U7) | código + `report-NN-stripe.md` |
| `stripe-advisor` ✅ | revisor Stripe | I7 | diff Stripe | notas de revisão |
| `aws-terraform-engineer` ✅ | executor | tarefas de infra | work-order | HCL + `report-NN-terraform.md` |
| `aws-lambda-deployer` 🆕 | executor | E7 | reports de código e infra | `deploy-report.md` |
| `aws-observability` 🆕 | executor de observabilidade (no modelo de `oci-observability`) | E2 (seção de observabilidade), tarefas de observabilidade, E7 (validação ao vivo) | work-order, specs, deploy-report | Terraform de log groups/alarmes/dashboards/X-Ray + `report-NN-observability.md` + `verify-E7-observability.md` |
| `aws-lambda-debugger` 🆕 | diagnóstico (só leitura); também verificação pós-deploy | E7 (verificação) e quando E7 falha | deploy-report, logs, métricas | `verify-E7.md` / `diagnosis-report.md` |
| `spec-synchronizer` 🆕 | sincronização; também revisão de spec | E1/E3 (revisão), E8 (delta) | drift + specs + ADRs + reports | `verify-E1.md`, `verify-E3.md`, `spec-delta-NN.md` |

Regras do time: só o orquestrador lança agentes (sem aninhamento); nenhum agente pede aprovação a
você diretamente; `terraform apply` só roda com a sua aprovação repassada pelo orquestrador.
**Stripe no Quarkus:** o `stripe-integrator` passa a carregar também as skills listadas no work-order
(por exemplo, U7). A mudança é mínima e fica para decisão em G1.

### 4.1 Em que pacote e pasta fica cada agente

Na fábrica, todo artefato é escrito em `packages/<pacote>/.apm/` (nunca em `.claude/`, que é gerado).
No projeto SaaS, o `apm install` coloca todos os agentes juntos em `.claude/agents/`.

| Agente / skill de orquestração | Pacote | Caminho de origem na fábrica | Instalado no projeto em | Situação |
|---|---|---|---|---|
| `building-quarkus-aws-saas` (orquestrador) | `quarkus-aws-saas` | `packages/quarkus-aws-saas/.apm/skills/building-quarkus-aws-saas/SKILL.md` | `.claude/skills/building-quarkus-aws-saas/` | 🆕 |
| `quarkus-lambda-integrator` | `quarkus-aws` | `packages/quarkus-aws/.apm/agents/quarkus-lambda-integrator.agent.md` | `.claude/agents/quarkus-lambda-integrator.md` | 🆕 |
| `quarkus-code-reviewer` | `quarkus-aws` | `packages/quarkus-aws/.apm/agents/quarkus-code-reviewer.agent.md` | `.claude/agents/quarkus-code-reviewer.md` | 🆕 |
| `aws-lambda-deployer` | `aws-lambda` | `packages/aws-lambda/.apm/agents/aws-lambda-deployer.agent.md` | `.claude/agents/aws-lambda-deployer.md` | 🆕 |
| `aws-lambda-debugger` | `aws-lambda` | `packages/aws-lambda/.apm/agents/aws-lambda-debugger.agent.md` | `.claude/agents/aws-lambda-debugger.md` | 🆕 |
| `aws-observability` | `aws-observability` | `packages/aws-observability/.apm/agents/aws-observability.agent.md` | `.claude/agents/aws-observability.md` | 🆕 |
| `spec-synchronizer` | `handoff-core` | `packages/handoff-core/.apm/agents/spec-synchronizer.agent.md` | `.claude/agents/spec-synchronizer.md` | 🆕 |
| `aws-architect` | `aws-architect` | `packages/aws-architect/.apm/agents/aws-architect.agent.md` | `.claude/agents/aws-architect.md` | ✅ sem mudança |
| `aws-terraform-engineer` | `terraform` | `packages/terraform/.apm/agents/aws-terraform-engineer.agent.md` | `.claude/agents/aws-terraform-engineer.md` | ✅ sem mudança |
| `stripe-integrator` | `stripe-java` | `packages/stripe-java/.apm/agents/stripe-integrator.agent.md` | `.claude/agents/stripe-integrator.md` | ♻️ 1 linha (G1): carregar as skills do work-order |
| `stripe-advisor` | `stripe-java` | `packages/stripe-java/.apm/agents/stripe-advisor.agent.md` | `.claude/agents/stripe-advisor.md` | ✅ sem mudança |

> P0 confere com `ls` os caminhos dos agentes existentes (✅/♻️) antes de qualquer brief.

**Por que essa divisão (reuso):** cada pacote serve a outros projetos além deste SaaS.

| Pacote | Reusável por | Fica nele |
|---|---|---|
| `quarkus-core` | qualquer app Quarkus 3.40 | ArC, REST, JUnit, clean code (U10) |
| `quarkus-aws` | qualquer Quarkus na AWS (não só SaaS) | U1–U6, U11–U13, guarda-chuva de observabilidade, estrutura de projeto, integrador e revisor, regras de Lambda Quarkus |
| `aws-lambda` | qualquer Lambda, de qualquer runtime | deployer e debugger. São **agnósticos de runtime**: recebem o artefato (`function.zip`) já construído pelo integrador e o caminho do Terraform pelo handoff. Quando o runtime é Quarkus, o debugger carrega U1/U11–U13 por indicação do work-order |
| `aws-observability` | qualquer workload AWS | agente, comando e validação ao vivo |
| `handoff-core` | qualquer família de agentes (inclusive OCI) | protocolo, scripts, `spec-synchronizer`, OpenSpec (U9) |
| `quarkus-aws-saas` | este SaaS (composição) | orquestrador, perfil de handoff, Stripe no Quarkus (U7), LangChain4j no Quarkus (U8) |

U9 (OpenSpec) vai para `handoff-core`, porque o formato de spec/delta é usado pelo `spec-synchronizer`
e não depende de Quarkus nem de AWS.

### 4.2 Árvore completa dos pacotes novos e alterados

```
packages/
├── quarkus-core/                                  🆕 base Quarkus 3.40
│   ├── apm.yml                                    deps: factory-core
│   ├── README.md
│   └── .apm/
│       ├── skills/
│       │   ├── developing-quarkus-arc-v3-40/      ← movida de camel-quarkus-skills
│       │   ├── developing-quarkus-rest-v3-40/     ← movida
│       │   ├── developing-quarkus-junit-v3-40/    ← movida
│       │   └── refactoring-quarkus-java/          🆕 U10 (SKILL.md + blueprints/)
│       └── instructions/
│           └── quarkus-clean-code.instructions.md 🆕
│
├── camel-quarkus-skills/                          ♻️ Quarkus + Camel
│   ├── apm.yml                                    deps: factory-core, quarkus-core
│   └── .apm/skills/developing-camel-quarkus-*-v3-40/   (10 skills, só os links são corrigidos)
│
├── handoff-core/                                  🆕 handoff genérico
│   ├── apm.yml                                    deps: factory-core
│   ├── README.md
│   └── .apm/
│       ├── skills/
│       │   ├── coordinating-agent-handoffs/
│       │   │   ├── SKILL.md
│       │   │   ├── blueprints/                    protocol.md, record-kinds.md, profile-format.md, evaluation-scenarios.md
│       │   │   ├── assets/                        templates genéricos (work-order, report, review, deploy, diagnosis, spec-delta, escalation)
│       │   │   └── scripts/                       check_records.py, board.py, detect_drift.py, tests/ (+ fixtures/)
│       │   ├── syncing-spec-from-code/SKILL.md    comando (context: fork → spec-synchronizer)
│       │   └── specifying-changes-with-openspec-v<M>-<m>/   U9
│       ├── agents/spec-synchronizer.agent.md
│       ├── instructions/sdd-openspec-workflow.instructions.md   (paths: openspec/**)
│       └── hooks (no apm.yml, `hooks:`)           Stop → detect_drift.py (só avisa)
│
├── aws-observability/                             🆕 modelo: oci-observability
│   ├── apm.yml                                    deps: factory-core, handoff-core, aws-skills, aws-terraform
│   ├── README.md
│   └── .apm/
│       ├── agents/aws-observability.agent.md
│       ├── skills/
│       │   ├── observe-aws-workload/SKILL.md      comando (context: fork → aws-observability)
│       │   └── validating-aws-observability/      SKILL.md + scripts/ (check-logs.sh, check-metrics.sh, check-traces.sh,
│       │                                          check-alarms.sh, check-dashboards.sh, validate-observability.sh, lib-common.sh, tests/)
│       └── instructions/aws-observability-skills.instructions.md
│
├── quarkus-aws/                                   🆕 Quarkus + AWS (reusável)
│   ├── apm.yml                                    deps: factory-core, quarkus-core, handoff-core, aws-skills
│   ├── README.md
│   └── .apm/
│       ├── agents/
│       │   ├── quarkus-lambda-integrator.agent.md
│       │   └── quarkus-code-reviewer.agent.md
│       ├── skills/
│       │   ├── structuring-quarkus-lambda-projects/
│       │   ├── observing-quarkus-lambda/          guarda-chuva U11–U13
│       │   ├── developing-quarkus-amazon-lambda-v3-40/        U1
│       │   ├── developing-quarkus-amazon-lambda-http-v3-40/   U2
│       │   ├── securing-quarkus-lambda-cognito-v3-40/         U3
│       │   ├── integrating-quarkus-amazon-data-v3-40/         U4
│       │   ├── integrating-quarkus-amazon-messaging-v3-40/    U5
│       │   ├── testing-quarkus-amazon-lambda-v3-40/           U6
│       │   ├── logging-quarkus-lambda-v3-40/                  U11
│       │   ├── tracing-quarkus-lambda-v3-40/                  U12
│       │   └── monitoring-quarkus-lambda-v3-40/               U13
│       └── instructions/
│           ├── quarkus-lambda-code-standards.instructions.md
│           └── quarkus-lambda-project-config.instructions.md
│
├── aws-lambda/                                    🆕 operação de Lambda (reusável, qualquer runtime)
│   ├── apm.yml                                    deps: factory-core, handoff-core, aws-skills, aws-terraform, aws-observability
│   ├── README.md
│   └── .apm/
│       ├── agents/
│       │   ├── aws-lambda-deployer.agent.md       artefato pronto → terraform plan → apply (com seu OK) → smoke
│       │   └── aws-lambda-debugger.agent.md       diagnóstico por status HTTP/erro, como oci-debugger; verificação pós-deploy
│       ├── skills/
│       │   ├── deploying-aws-lambda/              procedimento de deploy, rollback (alias/versão), smoke test
│       │   └── debugging-aws-lambda/              árvore de diagnóstico (502/503/504, timeout, IAM AccessDenied, cold start, throttling)
│       └── instructions/aws-lambda-deployment-preflight.instructions.md   (como deployment-preflight-checks do OCI)
│
├── quarkus-aws-saas/                              🆕 composição do SaaS
│   ├── apm.yml                                    deps: factory-core, quarkus-aws, aws-lambda, aws-observability, handoff-core,
│   │                                              aws-architect, terraform, stripe-java
│   ├── README.md
│   └── .apm/
│       └── skills/
│           ├── building-quarkus-aws-saas/         orquestrador inline (SKILL.md, blueprints/ por etapa E1–E9, assets/ templates SDD/ADR)
│           ├── coordinating-quarkus-aws-handoffs/ perfil (§5.5)
│           ├── integrating-stripe-quarkus-v3-40/              U7
│           └── integrating-quarkus-langchain4j-v<ext>/        U8
│
├── oci-core/                                      ♻️ deps: + handoff-core
│   └── .apm/skills/coordinating-oci-handoffs/     vira perfil OCI; nome e os 4 templates mantidos
│
└── stripe-java/                                   ♻️ (opcional, G1) 1 linha em agents/stripe-integrator.agent.md
```

Toda skill versionada segue o formato híbrido (`SKILL.md` enxuto + `blueprints/`, com
`evaluation-scenarios.md`). A pesquisa que dá origem a cada uma fica em
`workspace/quarkus-aws-saas/research_*_v3.40.md` (um único workspace para toda a construção, mesmo com vários pacotes).

`deploying-aws-lambda` e `debugging-aws-lambda` são as skills de procedimento que faltavam para os
dois agentes, no modelo de `deploying-oci-functions` e `debugging-deployed-functions` do OCI. Entram
no mapa de ondas na onda 6 e são pesquisadas em P4.

---

## 5. Handoff genérico — como funciona (novo pacote `handoff-core`)

Design escolhido: **"Skill + scripts + sync agent"**. Os scripts fazem tudo o que é mecânico e o
único agente faz só o que exige julgamento. A parte genérica sai do protocolo OCI atual
(`packages/oci-core/.apm/skills/coordinating-oci-handoffs/blueprints/handoff-protocol.md`, 352 linhas, usado por 6 agentes OCI).

### 5.1 Peças

| Peça | O que é |
|---|---|
| `coordinating-agent-handoffs` (skill) | o protocolo: tipos de registro, frontmatter, ciclo de vida, handshake, modos, templates |
| `handoff-profile.yaml` (um por família) | papéis e agentes, nomes de arquivo, pasta raiz, modo, regras de "próximo passo", integração com spec (`openspec` ou `none`) |
| `scripts/check_records.py` | valida os registros contra o protocolo e o perfil |
| `scripts/board.py` | gera `status.md` e calcula o próximo passo |
| `scripts/detect_drift.py` | compara o código com o que a spec e as tarefas cobrem |
| `spec-synchronizer` (agente) + `/syncing-spec-from-code` (comando) | escreve spec-deltas (§3.7) |
| hook `Stop` (no `hooks:` do pacote) | roda `detect_drift.py` e só avisa; antes de ativar num projeto, confirmo com você |
| `coordinating-quarkus-aws-handoffs` | perfil Quarkus/AWS (modo orquestrado, OpenSpec), detalhado em §5.5 |
| `coordinating-oci-handoffs` ♻️ | vira o perfil OCI (modo mediado pelo usuário, sem OpenSpec). **Nome e caminhos dos 4 templates mantidos**, então os 6 agentes OCI continuam funcionando sem edição |

### 5.2 Registros e ciclo de vida

Pasta: `openspec/changes/<id>/handoff/` (Quarkus) ou `docs/handoff/<capability>/` (OCI, como hoje).

| Tipo (`kind`) | Exemplo de arquivo | Estados / resultado |
|---|---|---|
| `work-order` | `wo-03-code.md` | `pending → in-progress → done` ou `blocked`, `cancelled` |
| `report` | `report-03-code.md` | `outcome: success \| partial \| failed \| needs-input` |
| `review` | `review-03.md` | `outcome: approved \| changes-requested` + achados |
| `deploy-report` / `diagnosis-report` | `deploy-report.md` | `success \| failed` |
| `spec-delta` | `spec-delta-02.md` | `proposed → accepted \| rejected \| revise` |
| `status` | `status.md` (gerado) | quadro + aprovações + último SHA sincronizado |

Frontmatter comum (validado por `check_records.py`):

```yaml
kind: report
id: report-03-code
from: quarkus-lambda-integrator
to: building-quarkus-aws-saas
change: list-tenant-items        # ou capability: no perfil OCI
refs: [wo-03-code]
requirements: [R1]
outcome: success
createdAt: 2026-11-04T10:15:00Z
```

Seções obrigatórias por tipo, conforme o template: o work-order tem Escopo, Skills, Requisitos,
Restrições e Critérios de aceite; o report tem Feito, Evidências, **Impacto na spec** e Próximo passo sugerido.

### 5.3 Handshake (o que todo passo faz)

1. O orquestrador escreve o work-order e roda `check_records.py`.
2. O agente lê o work-order, os `refs` e as skills indicadas. Não lê o histórico da conversa.
3. O agente trabalha e escreve **um** registro de saída a partir do template.
4. O orquestrador roda `check_records.py` (código de saída ≠ 0 → devolve ao agente com a lista de erros), depois `detect_drift.py` e `board.py`.
5. `board.py` aplica as regras do perfil e diz o próximo passo. Exemplos de regras do perfil Quarkus:
   - `report code success` → `quarkus-code-reviewer`
   - `review changes-requested` (rodada < 2) → integrador; rodada = 2 → você
   - todas as tarefas de código e infra `done` → `aws-lambda-deployer`
   - `deploy failed` → `aws-lambda-debugger`; `diagnosis` → work-order de correção para o dono
   - drift > 0 ou "Impacto na spec" com divergência → `spec-synchronizer`
   - tudo `done` e drift = 0 → gate final (§3.6)
6. No modo **orquestrado** (Quarkus), o orquestrador segue o próximo passo. No modo **mediado pelo usuário** (OCI, como hoje), o agente diz a você qual comando rodar.

### 5.4 Scripts (contrato)

| Script | Entrada | Saída | Código de saída |
|---|---|---|---|
| `check_records.py <dir> --profile <yaml>` | pasta de handoff | lista de erros (frontmatter, refs quebradas, seções faltando, estado inválido) | 0 ok · 1 erros |
| `board.py <dir> --profile <yaml> [--sync-sha <sha>]` | registros + `tasks.md` | `status.md` + próximo passo no stdout | 0 · 1 se o perfil é inválido |
| `detect_drift.py <repo> --change <dir>` | `git diff <sha_sincronizado>..HEAD` + arquivos citados nos reports | arquivos/endpoints sem tarefa ou requisito | 0 sem drift · 2 drift |

Todos são Python sem dependências externas, como os scripts de `building-agent-packages`, e têm testes unitários com registros de exemplo do OCI e do Quarkus.

### 5.5 O perfil Quarkus/AWS (`coordinating-quarkus-aws-handoffs`)

Uma skill de conhecimento fina. **Não repete o protocolo**: aponta para `coordinating-agent-handoffs`
e acrescenta só o que é próprio desta família.

```
coordinating-quarkus-aws-handoffs/
├── SKILL.md                     # quando usar, papéis, tabela "quem lê / quem escreve", link ao genérico
├── assets/
│   ├── handoff-profile.yaml     # o perfil lido pelos scripts (exemplo abaixo)
│   ├── wo-code.template.md      # work-order de código: requisitos, cenários, ADRs aplicáveis, skills U1–U13, etapas I0–I9
│   ├── wo-terraform.template.md # work-order de infra: módulos, skills provisioning-aws-*-v6, critérios de plan
│   ├── report-code.template.md  # evidência por etapa I0–I9 + "Impacto na spec"
│   ├── review.template.md       # achados HIGH/MEDIUM/LOW, checagem contra ADRs e regra de clean code
│   ├── deploy-report.template.md / diagnosis-report.template.md
│   ├── spec-delta.template.md   # no formato de delta do OpenSpec (ADDED/MODIFIED/REMOVED) + Perguntas
│   ├── adr.template.md          # campos do §3.3
│   └── escalation.template.md   # tentativas, evidência, hipótese, opções
└── blueprints/
    ├── roles-and-skills.md      # que skills cada work-order manda carregar, por tipo de tarefa
    ├── openspec-integration.md  # onde fica cada arquivo dentro de openspec/; como o arquivamento aplica os deltas
    └── evaluation-scenarios.md  # cenários para o skill-evaluator
```

Exemplo de `handoff-profile.yaml` (resumido; o formato final é definido em P5 e validado pelos scripts):

```yaml
profile: quarkus-aws
protocol: coordinating-agent-handoffs     # o genérico
mode: orchestrated                        # oci: user-mediated
root: openspec/changes/{change}/handoff   # oci: docs/handoff/{capability}
spec:
  kind: openspec                          # oci: none
  functional: openspec/specs/{capability}/spec.md
  architecture: openspec/specs/architecture/spec.md
  adr_dir: openspec/specs/architecture/adr
roles:                                    # papel → agente (lista completa no §4)
  orchestrator: building-quarkus-aws-saas
  architect: aws-architect
  code: quarkus-lambda-integrator
  stripe: stripe-integrator
  reviewer: [quarkus-code-reviewer, stripe-advisor]
  infra: aws-terraform-engineer
  deploy: aws-lambda-deployer
  observability: aws-observability
  debug: aws-lambda-debugger
  sync: spec-synchronizer
records:
  work-order: "wo-{nn}-{role}.md"
  report: "report-{nn}-{role}.md"
  review: "review-{nn}.md"
  spec-delta: "spec-delta-{nn}.md"
  escalation: "escalation-{nn}.md"
required_sections:
  report: [Feito, Evidências, Impacto na spec, Próximo passo sugerido]
  review: [Achados, Checagem de ADRs]
limits:                                   # §3.5: padrões; sobrescrevíveis por projeto e por execução
  build_attempts: 3
  review_rounds: 2
  deploy_cycles: 2
  delta_revisions: 2
  record_rejections: 2
quality:
  coverage_min: 80                        # % JaCoCo das classes novas (valor final decidido em G1)
next:                                     # regras avaliadas em ordem; a primeira que casar vence
  - when: {limit_reached: any}            # sempre primeiro: estourou um limite → você
    then: escalate
  - when: {kind: report, role: code, outcome: success}
    then: reviewer
  - when: {kind: review, outcome: changes-requested}
    then: code
  - when: {drift: true}
    then: sync
  - when: {all_tasks: done, kinds_done: [code, infra]}
    then: deploy
  - when: {kind: deploy-report, outcome: failed}
    then: debug
  - when: {kind: deploy-report, outcome: success}
    then: observability                   # validação ao vivo dos 5 pilares
  - when: {all_tasks: done, drift: false, pending_deltas: 0}
    then: final-gate
```

O perfil OCI (`coordinating-oci-handoffs`) usa o mesmo formato, com `mode: user-mediated`,
`spec.kind: none`, os papéis OCI atuais e os nomes de arquivo que ele já usa (`stream-a-java.md`,
`report-java.md`…). É isso que permite reaproveitar os scripts sem quebrar os 6 agentes OCI.

**Sim, os `roles` são os agentes do time** (§4). Cada papel aponta para um agente:

| Papel | Agente | Novo? | Também cobre |
|---|---|---|---|
| orchestrator | `building-quarkus-aws-saas` (skill inline) | 🆕 | E1–E9 |
| architect | `aws-architect` | ✅ | E2, E4 |
| code | `quarkus-lambda-integrator` | 🆕 | todo o código Quarkus, **inclusive o de LangChain4j** (com U8) |
| stripe | `stripe-integrator` | ✅ | código Stripe (com U7) |
| reviewer | `quarkus-code-reviewer` + `stripe-advisor` | 🆕 + ✅ | I7 |
| infra | `aws-terraform-engineer` | ✅ | Terraform |
| deploy | `aws-lambda-deployer` | 🆕 | E7 |
| observability | `aws-observability` | 🆕 | infra de observabilidade + validação ao vivo |
| debug | `aws-lambda-debugger` | 🆕 | diagnóstico + verificação pós-deploy |
| sync | `spec-synchronizer` (de `handoff-core`) | 🆕 | E1/E3 (revisão), E8 |

### 5.6 Onde cada coisa fica

São dois lugares diferentes: **este repositório (a fábrica)**, onde as skills e os agentes são
escritos, e **o seu projeto SaaS**, onde eles são instalados e onde o trabalho acontece.

```
agents-factory/  (a fábrica: fonte, versionada aqui)
└── packages/
    ├── handoff-core/.apm/
    │   ├── skills/coordinating-agent-handoffs/   ← protocolo genérico + scripts/ + templates genéricos
    │   ├── skills/syncing-spec-from-code/        ← comando
    │   └── agents/spec-synchronizer.agent.md
    ├── quarkus-aws/ , aws-lambda/ , aws-observability/   ← skills e agentes reusáveis (§4.2)
    └── quarkus-aws-saas/.apm/
        ├── skills/coordinating-quarkus-aws-handoffs/   ← o PERFIL (§5.5): handoff-profile.yaml + templates
        ├── skills/building-quarkus-aws-saas/            ← orquestrador
        └── skills/<U7, U8>/

        │  apm install   (no projeto SaaS, uma vez; de novo para atualizar)
        ▼

meu-saas/  (o seu projeto: tudo abaixo é versionado no git DELE)
├── .claude/                                   ← INSTALADO pelo apm (não editar à mão)
│   ├── skills/coordinating-quarkus-aws-handoffs/assets/handoff-profile.yaml   ← perfil padrão
│   ├── skills/…  agents/…  rules/…
├── openspec/
│   ├── handoff-profile.yaml                   ← OPCIONAL: sobrescreve o perfil padrão (ex.: limites, cobertura)
│   ├── specs/
│   │   ├── architecture/spec.md + adr/NNN-*.md   ← spec de arquitetura + ADRs (vivas)
│   │   └── <capacidade>/spec.md                  ← specs de funcionalidades (vivas)
│   └── changes/
│       ├── list-tenant-items/                 ← uma change EM ANDAMENTO
│       │   ├── proposal.md, design.md, tasks.md, specs/ (deltas)
│       │   └── handoff/                       ← OS REGISTROS: wo-*, report-*, review-*, spec-delta-*,
│       │                                         escalation-*, verify-*, status.md
│       └── archive/2026-11-04-list-tenant-items/   ← change ARQUIVADA, com o handoff/ junto (histórico)
├── src/ …, pom.xml, infra/ (Terraform)
```

- **Registros de handoff:** ficam no projeto SaaS, em `openspec/changes/<id>/handoff/`, e são
  commitados junto com o código. Quando a change é arquivada, a pasta inteira vai para
  `openspec/changes/archive/<data>-<id>/` com o `handoff/` dentro. Assim, todo requisito tem a
  trilha completa (work-order → report → review → deploy → delta) no git. O nome exato da pasta de arquivo segue o OpenSpec e é confirmado em P1.
- **Perfil:** a fonte fica na fábrica (`packages/quarkus-aws-saas/.apm/skills/coordinating-quarkus-aws-handoffs/`).
  No projeto, os scripts leem a cópia instalada em `.claude/skills/…/handoff-profile.yaml`, a menos que exista
  `openspec/handoff-profile.yaml` (sobrescrita opcional por projeto, só com os campos que mudam).
  Ajustar limites ou cobertura num projeto não exige mexer na fábrica.
- **Nada do seu projeto volta para a fábrica.** A fábrica guarda apenas os exemplos de teste dos
  scripts (`handoff-core/.apm/skills/coordinating-agent-handoffs/scripts/tests/fixtures/`) e o ensaio
  ponta a ponta do §8, que roda numa pasta temporária.
- **OCI:** igual ao modelo atual. Os registros ficam em `docs/handoff/<capability>/` do projeto OCI e
  o perfil em `.claude/skills/coordinating-oci-handoffs/`.

---

## 6. Pacotes

### 6.1 Pacotes em camadas

```
                    factory-core
                         │
                    quarkus-core  🆕  (base: ArC, REST, JUnit, clean code — Quarkus 3.40 LTS)
                    ┌────┴─────────────────────────┐
     Quarkus + Camel                          Quarkus + AWS 🆕
     camel-quarkus-skills ♻️ (10 skills Camel)  quarkus-aws (U1–U6, U11–U13, integrador, revisor, regras)
     camel-quarkus-integrator (agente, regras)          │
                                                        │      aws-lambda 🆕 (deployer, debugger)
                                                        │      aws-observability 🆕 (agente, validação)
                                                        │      handoff-core 🆕 (protocolo, scripts, sync, U9)
                                                        ▼          │
                                              quarkus-aws-saas 🆕 ◄─┘  composição: orquestrador, perfil, U7, U8
                                              (+ aws-architect, terraform, stripe-java)
```

| Pacote | Conteúdo | Depende de |
|---|---|---|
| **`quarkus-core`** 🆕 | **move** (`git mv`, sem reescrever) `developing-quarkus-arc-v3-40`, `developing-quarkus-rest-v3-40`, `developing-quarkus-junit-v3-40` de `camel-quarkus-skills`; **novo** U10 `refactoring-quarkus-java` + regra `quarkus-clean-code`; `_family_facts` só com os fatos de Quarkus | `factory-core` |
| **`camel-quarkus-skills`** ♻️ (Quarkus + Camel) | ficam as 10 skills `developing-camel-quarkus-*`; descrição do `apm.yml` corrigida (hoje ainda diz "Pilot stage") | `factory-core`, `quarkus-core` |
| `camel-quarkus-integrator` | sem mudança de conteúdo; só links de blueprint que apontam para as 3 skills movidas | `factory-core`, `camel-quarkus-skills` (recebe `quarkus-core` transitivamente) |
| **`quarkus-aws`** 🆕 (Quarkus + AWS, reusável) | U1–U6, U11–U13, `observing-quarkus-lambda`, `structuring-quarkus-lambda-projects`, agentes `quarkus-lambda-integrator` e `quarkus-code-reviewer`, regras de Lambda Quarkus | `factory-core`, `quarkus-core`, `handoff-core`, `aws-skills` |
| **`aws-lambda`** 🆕 (qualquer runtime) | agentes `aws-lambda-deployer` e `aws-lambda-debugger`, skills `deploying-aws-lambda` e `debugging-aws-lambda`, regra de preflight | `factory-core`, `handoff-core`, `aws-skills`, `aws-terraform`, `aws-observability` |
| **`quarkus-aws-saas`** 🆕 (composição) | orquestrador, perfil de handoff, U7, U8 | `factory-core`, `quarkus-aws`, `aws-lambda`, `aws-observability`, `handoff-core`, `aws-architect`, `terraform`, `stripe-java` |
| **`aws-observability`** 🆕 (no modelo de `oci-observability`; não depende de Quarkus, serve a qualquer workload AWS) | agente `aws-observability`, comando `/observe-aws-workload`, skill `validating-aws-observability` (scripts `check-logs.sh`, `check-metrics.sh`, `check-traces.sh`, `check-alarms.sh`, `check-dashboards.sh`, `validate-observability.sh`, `lib-common.sh`), regra `aws-observability-skills` (tabela de roteamento, como `observability-skills.md` do OCI) | `factory-core`, `handoff-core`, `aws-skills`, `aws-terraform` |

**Por que a mudança é segura:** os **nomes das skills não mudam**, e o `apm install` as instala nas
mesmas pastas de `.claude/skills/`. Para quem usa, nada muda. O que muda é o pacote de origem e os
links relativos dentro de `packages/` (28 arquivos citam as 3 skills, inclusive o agente e as regras
de `camel-quarkus-integrator`). Esses links são corrigidos pelo `scripts/fix-cross-package-links.py`
do repo e conferidos pelo `verify_package.py`.

**Decisão para G1:** `developing-quarkus-arc-v3-40` tem um blueprint `camel-integration.md`
(conteúdo de Camel dentro da skill base). A recomendação é movê-lo para `developing-camel-quarkus-bean-v3-40`,
para que `quarkus-core` não fale de Camel. A alternativa é deixá-lo onde está, para não mudar
nada nesta etapa.

**Ordem:** a reorganização é feita **primeiro** e vai num commit próprio. Ela é verificada sozinha
antes de qualquer skill AWS (critério: depois do `apm install --target claude`, o conteúdo de
`.claude/skills/developing-quarkus-*` e `developing-camel-quarkus-*` fica idêntico ao de antes,
exceto pelos links corrigidos, e as evaluation-scenarios de `integrating-camel-quarkus` continuam passando).

### 6.2 Demais pacotes e itens

- **`packages/handoff-core/`** (novo): skill genérica + scripts, agente `spec-synchronizer`, comando `/syncing-spec-from-code`, hook de drift. Depende de `factory-core`. `oci-core` passa a depender dele.
- **Regras** (com `paths:`): em `quarkus-core`, `quarkus-clean-code` (usada em I4 e I7, vale para Camel e AWS); em `quarkus-aws`, `quarkus-lambda-code-standards` e `quarkus-lambda-project-config` (`pom.xml`, `application.properties`); em `handoff-core`, `sdd-openspec-workflow` (`openspec/**`); em `aws-lambda`, `aws-lambda-deployment-preflight`; em `aws-observability`, `aws-observability-skills`. Os globs Java podem cruzar com as regras OCI `java-functions-*` e com as do `camel-quarkus-integrator`: estreitar ou documentar.
- **`apm.yml` raiz:** adiciona só `quarkus-aws-saas`. `quarkus-aws`, `aws-lambda`, `aws-observability`, `handoff-core` e `quarkus-core` **não** entram direto, porque vêm de forma transitiva (P8 confere com `apm audit --ci` qual entrada cada um precisa); listá-lo duas vezes dá `ambiguous resolved_by` no `apm audit --ci`. O comentário do `apm.yml` raiz sobre a resolução transitiva é atualizado.
- **`CLAUDE.md` e docs:** o parágrafo de Camel Quarkus ("13 version-locked knowledge skills") passa a descrever `quarkus-core` + 10 skills Camel; contagens só via `check_counts.py`.
- **Workspace:** `workspace/quarkus-aws-saas/` (brief, estado, `_family_facts_v3.40.md` herdado dos fatos Quarkus 3.40 existentes + versões Quarkiverse, runtimes Java da Lambda, SnapStart, OpenSpec; `research_*`; `validation/round-<k>/`).
- **OpenSpec:** em P1 verificamos versão, maturidade, licença, estrutura de pastas e integração com Claude Code. Se não atender à regra de evidência, U9 vira templates SDD próprios no `assets/` do orquestrador, com a mesma estrutura. Você decide em G1.

## 7. Como vamos executar (pipeline `/building-agent-packages`, modo `new`)

| Passo | O que acontece | Você decide? |
|---|---|---|
| P0 | preflight, workspace, brief e estado; registro das suas respostas literais | |
| P1 | verificação das versões nas páginas oficiais (Quarkus 3.40 LTS, Quarkiverse amazon-services e langchain4j, runtimes Lambda, SnapStart, OpenSpec) | |
| P2 | tabela go/no-go, design, fatos e regras da família | **G1**: escopo, nomes, OpenSpec × próprio, limite de cobertura, mudança no stripe-integrator, refatoração OCI, destino do `camel-integration.md` |
| P2.5 | **reorganização Quarkus**: cria `quarkus-core`, `git mv` das 3 skills, deps, links, `apm install`, verificação de equivalência (§6.1); commit próprio no plano de G3 | |
| P3 | piloto: U1 completo (pesquisa → skill → validação), com custo medido | **G2** |
| P4 | demais unidades em ondas (lotes de até 4), na ordem do mapa: ondas 0–5, depois a onda 7 (U11–U13, guarda-chuva, `validating-aws-observability`) | |
| P5 | `handoff-core` (skill, scripts + testes, agente, comando, hook), orquestrador, perfis, agentes, regras, READMEs, `apm.yml`; refatoração do perfil OCI | |
| P6 | ciclo de qualidade (3 rodadas): validator, evaluator, auditor; todo HIGH é conferido no arquivo | |
| P7–P8 | varredura de fatos; `apm install`, scripts de correção, contagens, `CLAUDE.md` e docs | |
| P9 | commits por grupos de caminhos explícitos (fora os arquivos já modificados no branch que não fazem parte disto) | **G3**, depois **G4** (push feito por você) |

Respostas já registradas (2026-10-28): Quarkus **3.40 LTS**, IaC **Terraform**, frontend **mapear skills existentes**, entregáveis **skills + mapa + agente + regras**, LLM **OpenAI + Anthropic + Bedrock**, agentes **orquestrador + integrador + deployer + debugger, com entrevista SDD/OpenSpec e skill de handoff**; handoff **"Skill + scripts + sync agent"**; gatilhos de sync **"At every handoff step, Before archive/commit (gate), On demand command, Claude Code hook"**; e os comentários deste plano: ondas, handoff genérico com agente próprio também usado pelo OCI, stripe-integrator gerando o código, apresentação mais clara, SDD contínuo nos dois sentidos, entrevista detalhada, specs de arquitetura técnica e funcional separadas, critérios de aceite, ciclo de implementação em várias etapas com clean code e refatoração, até 10 perguntas por rodada, E2 gera ADRs, revisão também contra os ADRs, verificação independente em cada fase, detalhe do perfil Quarkus com exemplo de `handoff-profile.yaml`, limite de tentativas com escalonamento para você, Quarkus em camadas (`quarkus-core` como base de Quarkus + Camel e Quarkus + AWS), limites por parâmetro, observabilidade completa com o agente `aws-observability` no modelo do OCI, integrador e revisor em `quarkus-aws` (reuso), e deployer e debugger em `aws-lambda`.

## 8. Como vamos verificar

### 8.1 Verificação independente em cada fase da construção

Mesma regra do §3.6: **quem produz não verifica.** Cada fase grava sua evidência em
`workspace/quarkus-aws-saas/validation/<fase>/` e o estado só avança com a verificação verde.

| Fase | Produz | Verificador independente | O que é checado |
|---|---|---|---|
| P0 | workspace, brief, estado (eu) | `scripts/inspect_workspace.py` | estrutura, slug sem colisão, workers presentes |
| P1 | tabela de versões (eu) | um `framework-researcher` diferente refaz a busca às cegas (só os nomes, sem minhas respostas) | versão, data, EOL e URL batem; divergência → `(unverified)` + você decide |
| P2 | go/no-go, design, `_family_facts` (eu) | `quality-validator` | nomes vs `skill-frontmatter.md`, sobreposição com skills existentes, todo fato com fonte oficial |
| P2.5 | reorganização Quarkus (eu) | `verify_package.py` nos 3 pacotes Quarkus + diff de `.claude/skills/` antes/depois (só links podem mudar) + `skill-evaluator` em `integrating-camel-quarkus` | nenhuma skill perdida, links válidos, comportamento do Camel inalterado |
| P3/P4 | research (researcher) → skill (author) | `quality-validator` + `verify_skill.py` + `skill-evaluator` (cenários) | regra de evidência, formato híbrido, links, tags, comportamento |
| P5 | agentes, regras, orquestrador, handoff (author) | `architecture-auditor` (`audit-cc-*`, 3 lentes) + `verify_package.py` + testes unitários dos scripts | escopo, fluxo, mecânica; roteamento; os scripts com os exemplos OCI e Quarkus |
| P6 | correções (author) | outra instância de `quality-validator`/`skill-evaluator`, que não viu a rodada anterior | todo HIGH reconferido no arquivo antes e depois da correção |
| P7 | varredura de fatos (author) | `grep` por script (o fato antigo não aparece em nenhum lugar) + `quality-validator` | consistência entre skills |
| P8 | `apm install`, contagens, docs (eu) | `check_counts.py`, `apm install --frozen` + `git diff --exit-code`, `apm audit --ci` | sem drift entre `packages/` e `.claude/`, contagens reais |
| P9 | commits (eu) | `git status` + `git show --stat` por grupo, conferidos com o plano de commits aprovado em G3 | só os caminhos aprovados entraram |

### 8.2 Verificações finais

- `verify_skill.py` em cada skill; `verify_package.py` em `quarkus-core`, `camel-quarkus-skills`, `quarkus-aws`, `aws-lambda`, `aws-observability`, `handoff-core`, `quarkus-aws-saas` e `oci-core`.
- `apm install --frozen` + `git diff --exit-code` limpos; `apm audit --ci` limpo; `check_counts.py` igual ao `CLAUDE.md`.
- Evaluation-scenarios passando em cada skill, incluindo: o orquestrador se recusa a delegar antes de E2/E3 serem aceitas; o revisor nunca é o mesmo agente que escreveu o código; o gate final bloqueia com drift > 0.
- Testes unitários dos 3 scripts com registros de exemplo do OCI e do Quarkus.
- **Scripts de validação ao vivo** (`validating-aws-observability`): testados com saídas gravadas do AWS CLI (fixtures) para o caso verde e para cada falha (sem logs, log sem `tenantId`, trace quebrado, alarme ausente ou em `INSUFFICIENT_DATA`, dashboard vazio). Só fazem leitura, exceto o teste de disparo de alarme, que exige confirmação. Não chamam a AWS na fábrica.
- **Cobertura de observabilidade:** P2 compara o que U11–U13 + as skills AWS existentes cobrem com os 5 pilares e declara as lacunas (ex.: SLOs/Application Signals, se não estiverem cobertos) na tabela go/no-go de G1.
- **Regressão OCI:** links e os 4 templates de `coordinating-oci-handoffs` intactos; `check_records.py` passando nos exemplos OCI; cenários de `design-oci-architecture` passando.
- **Ensaio ponta a ponta** em pasta temporária, com o exemplo do §3.8 + um webhook de checkout Stripe: E1–E9 completos, I0–I9 com evidência em cada etapa, `mvn -q verify` verde, `function.zip` gerado, `terraform validate` OK, `status.md` gerado por `board.py`. Nenhum `apply`.
- **Ensaio da volta:** editar à mão um endpoint → o hook `Stop` avisa → `/syncing-spec-from-code` produz um delta coerente → o gate bloqueia até o delta ser aceito → o drift volta a zero.
