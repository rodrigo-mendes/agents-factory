# Estratégia de venda: bundles de skills no Agensi e no SkillHQ

Documento de trabalho para publicar os pacotes deste repositório como produtos pagos.
Fatos sobre as plataformas vêm da documentação oficial de cada uma, lida em **2026-10-31**
(links na seção [Fontes](#11-fontes)). Onde a documentação não diz nada, o texto marca **não documentado**.
Confira os termos de novo antes de publicar: as duas plataformas mudam rápido.

## 1. Resumo

- **O que vender:** 19 bundles montados a partir dos pacotes existentes, cada um um meta-pacote em
  [`packages/bundles/`](../../packages/bundles/) (só `apm.yml`, sem conteúdo próprio; um deles tem também
  um `export.yml` que recorta o que vai para a venda).
- **Como empacotar:** `scripts/export-bundle.py` gera o diretório compilado do target (pasta para o
  SkillHQ, zip para o Agensi) já sem a Vercel e sem dados sensíveis (seção 9).
- **Passo a passo:** [preparação comum](guia-publicacao.md), [guia SkillHQ](guia-skillhq.md),
  [guia Agensi](guia-agensi.md).
- **Onde:** Agensi (compra única ou assinatura, 70% para o criador) e SkillHQ (compra única,
  85% menos taxa Stripe).
- **Como cobrar:** no Agensi, uma listagem por versão maior (compra única) e uma trilha "Latest" por
  assinatura para os bundles que mudam rápido. No SkillHQ, compra única com atualizações dentro da
  mesma versão maior.
- **Por onde começar:** 3 bundles e iscas grátis (seção 10).

## 2. Antes de vender (bloqueadores)

1. **Propriedade intelectual.** Confirme por escrito com o empregador (e com o cliente, se for o caso)
   que o conteúdo pode ser vendido por você. As duas plataformas exigem que o conteúdo seja seu ou
   licenciado; o Agensi diz que os criadores mantêm a propriedade e dão à plataforma licença para distribuir.
2. **Conteúdo de cliente e dados sensíveis.** Uma varredura com 8 detectores (nomes, e-mails, OCIDs,
   namespace do OCIR, hosts, contas AWS, chaves, caminhos pessoais) achou conteúdo de cliente e dados
   reais da tenancy nos pacotes OCI; foram trocados por placeholders em 2026-10-31. O mesmo detector
   roda em toda exportação e **barra** o bundle se achar algo (`scripts/export_detectors.py`).
   A skill `integrating-oracle-rms-webhooks` nunca é exportada: é a integração de um cliente, não um produto.
3. **Conteúdo de terceiros.** [`third-party/vercel-frontend`](../../packages/third-party/vercel-frontend/)
   só aponta para repositórios oficiais da Vercel. Essas 20 skills **nunca** entram num pacote pago: o
   Agensi rejeita "repackaged free skills". O bundle `saas-starter-team` puxa esse pacote por
   transitividade; a exportação precisa tirá-lo e o anúncio deve citar os repositórios da Vercel como
   pré-requisito gratuito.
4. **Qualidade.** Rode `/skill-best-practices-validator` e `/evaluating-skill-scenarios` em cada skill
   do bundle. O relatório serve de argumento de venda ("testado com cenários").
5. **Segurança.** O scan do Agensi procura comandos perigosos, segredos, coleta de variáveis de
   ambiente, acesso à rede, ofuscação e prompt injection. Skills que mandam rodar `aws`, `terraform` ou
   `oci` precisam deixar claro que os comandos são do usuário e que nada roda sem aprovação.

## 3. Comparativo das plataformas

| | Agensi | SkillHQ |
|---|---|---|
| Repasse | 70% por venda; assinatura 70% depois das taxas Stripe | 85% (comissão de 15%) + taxa Stripe à parte: 1,5% + €0,25 (UE), 3,25% + €0,25 (fora da UE) |
| Taxa para listar | não documentado | nenhuma |
| Preço | grátis; sugere US$5-15 (skill simples) e US$20-50 (completa) | mínimo €2,00; grátis €0,00; faixa citada "€2–$50" |
| Formato de envio | **zip** com `SKILL.md` (`name` + `description` no frontmatter) + scripts, referências e assets opcionais | **diretório** com `SKILL.md` + `README.md`, publicado pela CLI `skillhq` |
| Revisão | scan automático (8 checagens) + revisão manual de 24-48h | validação automática (estrutura, frontmatter, qualidade, duplicata) |
| Entrega ao comprador | o agente carrega a skill pelo conector/MCP do Agensi; nada é baixado | `skillhq install` grava em `~/.claude/skills/<nome>` (ou `./.claude/skills` com `--project`) |
| Atualizações | compra única recebe **atualizações grátis**; nova versão passa por revisão antes de valer | `skillhq publish --update --changelog`; o comprador roda `skillhq update` |
| Assinatura | sim: mínimo US$5/mês, desconto anual de 0 a 50% (padrão: 2 meses grátis), release notes obrigatórias | não documentado |
| Bundles | existem no perfil do criador; mecânica e preço não documentados | não documentado |
| Pagamento | Stripe Connect ou Zoneless (USDC); KYC obrigatório para receber | Stripe Connect; Starter publica sem Stripe, Pro (KYC) recebe direto no banco |
| Anti-pirataria | não documentado | fingerprint por download, SimHash, DMCA |
| Reembolso | não documentado | automático se nunca baixado; depois disso, não |
| Agentes atendidos | Claude, ChatGPT, Cursor, Codex, Gemini CLI e outros via conector | Claude Code (SKILL.md) e Custom GPTs |

**Consequência prática:** só os SKILL.md (com `blueprints/`, `assets/`, `scripts/`) são portáveis.
Subagentes (`.claude/agents/`), `/commands` com `context: fork` e rules (`.claude/rules/`) são do
Claude Code. A documentação do Agensi **não diz** se o MCP entrega algo além do SKILL.md. Antes de
publicar um bundle com agentes, publique uma skill de teste e confirme o que chega ao comprador.

## 4. Catálogo de bundles

Contagens de conteúdo próprio (sem as skills da Vercel), somando todos os pacotes que o bundle puxa.
Todo bundle inclui as 5 rules de `factory-core` (frontmatter e nomes); elas entram nas contagens.

### A. Para quem cria skills (o mesmo público dos marketplaces)

| Bundle | Pacotes diretos | Skills (commands) | Agentes | Rules | Público |
|---|---|---|---|---|---|
| [`skill-factory-pro`](../../packages/bundles/skill-factory-pro/apm.yml) | factory/agent-package-builder, artifact-authoring, researching-frameworks | 11 (9) | 4 | 5 | quem cria skills e agentes |
| [`harness-quality-kit`](../../packages/bundles/harness-quality-kit/apm.yml) | harness-quality/auditing, validating, evaluating | 14 (14) | 3 | 5 | quem mantém skills e agentes em produção |
| [`anti-hallucination-research`](../../packages/bundles/anti-hallucination-research/apm.yml) | factory/researching-frameworks, researching-platform | 20 (20) | 3 | 5 | arquitetos e times de plataforma |

### B. Cloud

| Bundle | Pacotes diretos | Skills (commands) | Agentes | Rules |
|---|---|---|---|---|
| [`aws-terraform-complete`](../../packages/bundles/aws-terraform-complete/apm.yml) | cloud/terraform/terraform | 39 (10) | 8 | 9 |
| [`aws-well-architected-reviewer`](../../packages/bundles/aws-well-architected-reviewer/apm.yml) | cloud/provider/aws/aws-architect | 44 (2) | 4 | 8 |
| [`oci-serverless-complete`](../../packages/bundles/oci-serverless-complete/apm.yml) | oci-functions-java, oci-observability, oci-architecture, oci-terraform | 56 (9) | 8 | 34 |
| [`multi-cloud-terraform`](../../packages/bundles/multi-cloud-terraform/apm.yml) | cloud/terraform/terraform, oci-terraform | 60 (12) | 9 | 17 |
| [`cloud-observability`](../../packages/bundles/cloud-observability/apm.yml) | aws-observability, oci-observability | 82 (3) | 4 | 11 |
| [`architecture-board`](../../packages/bundles/architecture-board/apm.yml) | solution-architecture, aws-architect, oci-architecture | 53 (4) | 8 | 10 |

### C. Java

| Bundle | Pacotes diretos | Skills (commands) | Agentes | Rules |
|---|---|---|---|---|
| [`serverless-java-aws`](../../packages/bundles/serverless-java-aws/apm.yml) | java/quarkus/quarkus-aws, cloud/provider/aws/aws-lambda | 88 (2) | 7 | 14 |
| [`camel-quarkus-integration`](../../packages/bundles/camel-quarkus-integration/apm.yml) | java/quarkus/camel-quarkus-integrator | 16 (0) | 1 | 9 |
| [`java-ai-langchain4j`](../../packages/bundles/java-ai-langchain4j/apm.yml) | java/libs/langchain4j, java/quarkus/quarkus-langchain4j | 62 (1) | 5 | 11 |
| [`stripe-for-java`](../../packages/bundles/stripe-for-java/apm.yml) | java/libs/stripe-java | 6 (2) | 2 | 6 |
| [`java-clean-code`](../../packages/bundles/java-clean-code/apm.yml) | java/clean-code/clean-code-quarkus, clean-code-oci | 2 (0) | 0 | 7 |

### D. Entrega e CI/CD

| Bundle | Pacotes diretos | Skills (commands) | Agentes | Rules |
|---|---|---|---|---|
| [`github-actions-secure-cicd`](../../packages/bundles/github-actions-secure-cicd/apm.yml) | delivery/github/github-actions-cicd | 12 (1) | 2 | 9 |
| [`spec-driven-delivery`](../../packages/bundles/spec-driven-delivery/apm.yml) | delivery/specs/openspec-github | 7 (2) | 2 | 7 |

### E. Fora de TI e carro-chefe

| Bundle | Pacotes diretos | Skills (commands) | Agentes | Rules |
|---|---|---|---|---|
| [`technical-book-author`](../../packages/bundles/technical-book-author/apm.yml) | content-generation/book-writing | 10 (10) | 13 | 5 |
| [`saas-starter-team`](../../packages/bundles/saas-starter-team/apm.yml) | saas/aws-saas-serverless-quarkus-react-nextjs | 123 (16) + 20 Vercel | 29 | 23 |

Bundles grandes por transitividade: `cloud-observability` (82 skills) e `serverless-java-aws` (88)
trazem as 40 `aws-skills` e as 26 `aws-terraform` porque os agentes dependem delas. Isso é valor
para o comprador, mas confira se o preço reflete o tamanho.

### F. Recortado na exportação

| Bundle | Pacotes diretos | O que vai para a venda |
|---|---|---|
| [`ai-code-review-squad`](../../packages/bundles/ai-code-review-squad/apm.yml) | quarkus-langchain4j, terraform, github-actions-cicd, stripe-java | REVIEW_SQUAD_COUNTS |

Os revisores estão em pacotes diferentes, então o `apm.yml` instala os pacotes inteiros e o
[`export.yml`](../../packages/bundles/ai-code-review-squad/export.yml) recorta: entram só os 5
revisores read-only (`quarkus-code-reviewer`, `langchain4j-reviewer`, `terraform-code-reviewer`,
`cicd-pipeline-reviewer`, `stripe-advisor`) e as skills e rules que eles citam. `nextjs-code-reviewer` e
`ui-design-reviewer` ficam fora porque dependem das skills da Vercel.

## 5. Modelo de preço e de versão

### Regra de versão

O repositório segue "1 skill = 1 versão" (skills com sufixo `-v6`, `-v3-40`, `-v1-22`). Isso continua
valendo na venda: **o produto pode não ter versão, o conteúdo sempre tem**.

- **Agensi, compra única:** como o comprador recebe atualizações grátis, cada versão maior vira uma
  **listagem separada** ("AWS Terraform 6.x"). Correções dentro da 6.x saem como atualização; a
  versão 7 vira outra listagem. Quem comprou a 6.x não é empurrado para a 7.
- **Agensi, assinatura "Latest":** a trilha sempre aponta para a versão estável atual. Ao trocar de
  versão maior, a release note (obrigatória) diz qual versão passou a valer. O modelo de preço é fixo
  por skill depois de publicado; dá para migrar uma skill de compra única para assinatura, e quem
  comprou antes mantém a versão única.
- **SkillHQ:** só compra única (assinatura não documentada). Mesma regra: uma listagem por versão
  maior, `--update` só dentro dela.

### Quem vai para assinatura e quem fica em compra única

| Assinatura "Latest" no Agensi (muda rápido) | Compra única (estável) |
|---|---|
| `skill-factory-pro` (muda com o Claude Code e o formato SKILL.md) | `camel-quarkus-integration` (Quarkus 3.40 LTS) |
| `aws-terraform-complete` (provider da AWS lança versões com frequência) | `stripe-for-java` (stripe-java 34.x) |
| `github-actions-secure-cicd` (incidentes de supply chain) | `oci-serverless-complete` |
| `harness-quality-kit` | `technical-book-author` |
| `serverless-java-aws`, `java-ai-langchain4j` (quarkus-langchain4j está em CR) | `spec-driven-delivery`, `architecture-board` |

### Tabela de preços sugerida

A compra única deve custar cerca de 3 a 4 meses de assinatura, para uma não canibalizar a outra.

| Nível | Exemplos | Compra única | Assinatura (Agensi) |
|---|---|---|---|
| Isca grátis | 1 skill de cada bundle | €0 | — |
| Avulso | uma skill ou um agente | €3-9 | US$5/mês (mínimo) |
| Bundle de domínio | stripe, camel, spec-driven, github-actions, book | €15-25 | US$5-7/mês |
| Bundle profissional | skill-factory-pro, aws-terraform-complete, multi-cloud, serverless-java-aws | €29-39 | US$9-12/mês |
| Carro-chefe | saas-starter-team | €49 (perto do teto citado pelo SkillHQ) | US$15/mês |

Sugestões de isca grátis (uma por bundle, para atrair quem depois compra o pacote):
`composing-github-actions-pipelines`, `applying-aws-well-architected`, `rules-compiler`,
`specifying-changes-with-openspec-v1-15`, `developing-quarkus-arc-v3-40`.

## 6. O que é enviado: o diretório compilado do target

O pacote vendido é o que o APM gera para o target (hoje `claude`), já filtrado:

```
dist/<bundle>/claude/            ← pasta (SkillHQ)
├── README.md                    ← gerado: descrição, versão, data, conteúdo, instalação
└── .claude/
    ├── skills/<nome>/SKILL.md (+ blueprints/, assets/, scripts/)
    ├── agents/<nome>.md
    └── rules/<nome>.md
dist/<bundle>-claude.zip         ← o mesmo conteúdo (Agensi)
```

O comprador copia a pasta `.claude/` para a raiz do projeto. Skills funcionam em outros agentes que
leem `SKILL.md`; agentes, `/commands` e rules são do Claude Code.

**Risco a testar antes de vender:** as duas plataformas documentam um `SKILL.md` na raiz do pacote
enviado; o diretório compilado tem os `SKILL.md` dentro de `.claude/skills/<nome>/`. Publique um
bundle pequeno como grátis em cada plataforma e veja se a validação aceita
([tabela de resultados](guia-publicacao.md#4-registrar-o-resultado-dos-testes-grátis)).

## 7. Agensi — resumo

Conta e Creator Mode → recebimento (Stripe Connect ou USDC, com KYC) → envio do zip pelo
**Submit a Skill** → scan automático + revisão de 24-48h → compra única (atualizações grátis para quem
comprou) ou assinatura (mínimo US$5/mês, release notes obrigatórias, modelo fixo depois de publicado).
Passo a passo completo: [guia-agensi.md](guia-agensi.md).

## 8. SkillHQ — resumo

Conta → CLI (`npm install -g @skill-hq/cli`, `skillhq auth login`) → `skillhq validate` →
`skillhq publish --price --category` → plano Pro (KYC Stripe) para receber → atualizações com
`--update --changelog`. Passo a passo completo: [guia-skillhq.md](guia-skillhq.md).

## 9. Como gerar os pacotes no repositório

Cada bundle é um meta-pacote em `packages/bundles/<nome>/apm.yml`: lista só os pacotes de topo, o resto
vem por transitividade. Os bundles **não** entram no `apm.yml` raiz (seria um segundo caminho para
pacotes já instalados).

```bash
python scripts/export-bundle.py stripe-for-java              # simulação: mostra o que entraria
python scripts/export-bundle.py stripe-for-java --apply      # grava a pasta e o zip em dist/
python scripts/export-bundle.py --all --apply                # todos os bundles
```

Por bundle, o script:

1. instala só o bundle numa pasta temporária nova a cada tentativa, de caminho curto
   (`C:\tmp\ax\<6 letras>`): com nomes longos, os caminhos dentro de `apm_modules/` passam do limite
   de 260 caracteres do Windows e a instalação falha sempre. Até 5 tentativas (os bloqueios de arquivo
   do Windows são intermitentes);
2. roda os 2 scripts de pós-instalação nessa pasta (`--root`);
3. lê no `apm.lock.yaml` dessa pasta cada arquivo gerado e o pacote dono dele;
4. tira os arquivos que não vêm de um pacote local ou que vêm de `third-party/` (Vercel), tira
   `integrating-oracle-rms-webhooks` e aplica o `export.yml`, se houver;
5. roda os 8 detectores de dado sensível: se acharem algo, o bundle é **barrado** e a lista vai para
   `dist/<bundle>/BLOCKED.txt`;
6. grava a pasta e o zip (zip reproduzível: mesma entrada, mesmo sha256).

**`export.yml` (opcional, ao lado do `apm.yml`; o APM ignora):**

| Campo | Valores | Padrão |
|---|---|---|
| `agents` | lista de nomes, ou `all` | `all` |
| `skills` | lista de nomes, `cited` ou `all` | `all` |
| `rules` | lista de nomes, `cited` ou `all` (as 5 rules base de frontmatter e nomes sempre vão) | `all` |
| `include` / `exclude` | caminhos relativos ao target (`skills/x`, `agents/y.md`, `rules/z.md`); aceitam `*` | — |

`cited` = nomes escritos entre crases no texto dos agentes selecionados.

Os detectores têm testes próprios: `python scripts/tests/test_export_detectors.py`. Para varrer uma
pasta inteira: `python scripts/export_detectors.py packages --skip third-party`.

## 10. Lançamento em fases

1. **Bloqueadores (seção 2):** IP, conteúdo de cliente, Vercel, validação e scan.
2. **Teste de entrega:** publique um bundle pequeno como grátis em cada plataforma e confirme o que
   chega ao comprador (só SKILL.md ou também agentes e rules) — fase D dos guias.
3. **Primeira leva:** `github-actions-secure-cicd` (público mais amplo), `skill-factory-pro` (mesmo
   público dos marketplaces) e `aws-terraform-complete`, cada um com uma isca grátis.
4. **Medir por 4 semanas:** downloads das iscas, conversão para pago, reembolsos e assinaturas
   canceladas.
5. **Expandir:** bundles de nicho (OCI, Camel, Stripe), depois o carro-chefe `saas-starter-team`.
6. **Manutenção:** o pipeline do repositório produz as atualizações e as release notes
   (`/researching-technical-frameworks` → `/skill-creator` → `/skill-best-practices-validator` →
   `/evaluating-skill-scenarios`). Reserve tempo por mês para cada bundle em assinatura.

## 11. Fontes

Todas lidas em 2026-10-31.

- Agensi, *How to Sell Skills on Agensi* (2026-03-30): https://www.agensi.io/learn/how-to-sell-skills-on-agensi
- Agensi, *Subscription Skills on Agensi* (2026-06-17): https://www.agensi.io/learn/subscription-skills-launch
- Agensi, *Sell*: https://www.agensi.io/sell
- Agensi, *How Agensi Payouts Work*: https://www.agensi.io/learn/how-agensi-payouts-work-stripe-connect
- SkillHQ, página inicial (preços, taxas, anti-pirataria, reembolso): https://skillhq.dev/
- SkillHQ, *CLI docs*: https://skillhq.dev/docs/cli
- SkillHQ, *Become a seller*: https://skillhq.dev/become-seller
- SkillHQ, termos e contrato do vendedor (não lidos, ler antes de publicar):
  https://skillhq.dev/legal/terms, https://skillhq.dev/legal/seller-agreement
