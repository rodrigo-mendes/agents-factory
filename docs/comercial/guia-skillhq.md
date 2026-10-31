# Guia SkillHQ — do zero ao produto pago

Passo a passo para publicar e manter os bundles no [SkillHQ](https://skillhq.dev/). Antes, faça a
[preparação comum](guia-publicacao.md) (passos 0 a 2).

Fontes oficiais, lidas em 2026-10-31: [página inicial](https://skillhq.dev/) (preços, taxas,
anti-pirataria, reembolso), [CLI docs](https://skillhq.dev/docs/cli),
[Become a seller](https://skillhq.dev/become-seller). O que essas páginas não cobrem está marcado
**não documentado — confirmar com o suporte** (`support@skillhq.dev`).

## Visão geral

```
A conta ─▶ B CLI ─▶ C validar ─▶ D teste grátis ─▶ E Pro (receber) ─▶ F publicar pago
                                                                           │
                         J tirar do ar ◀─ I proteger ◀─ H acompanhar ◀─ G atualizar
```

## A. Criar a conta

1. Acesse https://skillhq.dev/ e crie a conta com GitHub, Google ou e-mail.
2. Você começa no plano **Starter**: já publica, mas ainda não recebe no banco (fase E).

## B. Instalar e autenticar a CLI

```bash
npm install -g @skill-hq/cli
skillhq auth login          # abre o navegador para o login (OAuth)
skillhq auth status         # deve mostrar a sua conta
```

Para desinstalar depois: `npm uninstall -g @skill-hq/cli`. Para sair da conta: `skillhq auth logout`.

## C. Validar sem publicar

```bash
skillhq validate dist/stripe-for-java/claude
```

A validação confere estrutura, frontmatter, qualidade do conteúdo e duplicatas.

| Resultado | O que fazer |
|---|---|
| Passou | Siga para a fase D. Anote "validou" na [tabela de resultados](guia-publicacao.md#4-registrar-o-resultado-dos-testes-grátis). |
| Reclamou de `SKILL.md` na raiz | É o risco conhecido: exportamos o diretório compilado (`.claude/...`). Copie a mensagem exata para a tabela e pare aqui: o script de exportação precisa de outro formato (por exemplo, uma pasta por skill). |
| Reclamou de duplicata | O SkillHQ compara com o que já existe (SimHash). Confira se a skill não foi publicada antes, por você ou por outra pessoa. |

## D. Publicação de teste grátis

```bash
skillhq publish dist/stripe-for-java/claude \
  --price 0 --category development \
  --tags java,stripe,payments \
  --short-description "TEST - do not buy"
```

Depois, **instale como comprador** numa pasta vazia para ver o que chega:

```bash
mkdir -p /c/tmp/skillhq-buyer && cd /c/tmp/skillhq-buyer
skillhq install <nome-do-produto> --project     # instala em ./.claude/skills/<nome>
find .claude -maxdepth 3
```

Anote na tabela de resultados se chegaram **skills**, **agentes** e **rules**. A documentação só fala em
`.claude/skills/`; agentes (`.claude/agents/`) e rules (`.claude/rules/`) podem não ser copiados.

## E. Habilitar o recebimento (plano Pro)

1. No painel, faça o upgrade para **Pro**.
2. Faça o KYC no Stripe (cerca de 5 minutos): nome, endereço e foto de um documento oficial.
3. Conecte a conta bancária. Os pagamentos seguem o calendário padrão do Stripe.

**Quanto você recebe:** a página diz que o vendedor fica com 85%; a comissão é 15% e a taxa do Stripe
é 1,5% + €0,25 (UE) ou 3,25% + €0,25 (fora da UE). O exemplo oficial (venda de €10 → €8,50 para o
vendedor, €1,10 para a plataforma, €0,40 de Stripe) indica que a taxa do Stripe sai da parte da
plataforma. Por esse exemplo, uma venda de **€29 rende €24,65**. Confirme no primeiro extrato.

## F. Publicar pago

Um comando por bundle. Preço em euros (mínimo €2,00) e uma das 4 categorias:
`development`, `productivity`, `security` ou `devops`.

```bash
skillhq publish dist/aws-terraform-complete/claude \
  --price 29 --category devops \
  --tags terraform,aws,iac \
  --short-description "26 hashicorp/aws 6.x skills + Terraform engineer and reviewer agents"
```

| Bundle | Categoria sugerida |
|---|---|
| Terraform, CI/CD, observabilidade, cloud | `devops` |
| Java, Quarkus, Stripe, LangChain4j, clean code | `development` |
| revisores, harness quality | `security` (revisão) ou `development` |
| pesquisa, livro técnico, skill factory | `productivity` |

Preços sugeridos: [estrategia-bundles.md, seção 5](estrategia-bundles.md#5-modelo-de-preço-e-de-versão).

Se o `publish` pedir Stripe Connect: faça a fase E primeiro.

## G. Atualizar

Dentro da **mesma versão maior** (correções, exemplos novos):

```bash
python scripts/export-bundle.py aws-terraform-complete --apply
skillhq publish dist/aws-terraform-complete/claude --update --changelog "Fix S3 lifecycle example"
```

O comprador recebe ao rodar `skillhq update` (`skillhq outdated` mostra o que tem atualização).

Versão maior nova (ex.: provider AWS 7.x) = **produto novo**, com outro nome. Quem comprou a 6.x não é
empurrado para a 7.x ([regra de versão](estrategia-bundles.md#5-modelo-de-preço-e-de-versão)).

## H. Acompanhar vendas e reembolsos

- Vendas e pagamentos: painel do vendedor.
- Reembolso automático **só se o comprador nunca baixou**. Depois do download, não há reembolso; skills
  quebradas passam por análise manual.

## I. Proteger contra cópia

- Cada download recebe uma marca (fingerprint) e cópias parafraseadas são detectadas por SimHash.
- Para pedir a remoção de uma cópia: processo DMCA descrito nos
  [termos de serviço](https://skillhq.dev/legal/terms) e no
  [contrato do vendedor](https://skillhq.dev/legal/seller-agreement) (leia os dois antes de publicar pago).

## J. Tirar do ar

**Não documentado** na CLI (não há `unpublish`). Faça pelo painel do vendedor ou peça ao suporte.

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| `publish` pede Stripe Connect | plano Starter | fase E (upgrade para Pro) |
| validação reprovada por estrutura | formato "diretório compilado" | anotar a mensagem e parar (fase C) |
| `--category` inválida | só existem 4 categorias | `development`, `productivity`, `security`, `devops` |
| `--short-description` cortada | limite de 200 caracteres | encurtar |
| comprador não recebeu agentes/rules | a CLI instala em `.claude/skills/` | anotar e incluir instruções de cópia no `README.md` |

## Checklist por bundle publicado

- [ ] `export-bundle.py <bundle> --apply` com ✅ (sem `BLOCKED.txt`)
- [ ] `skillhq validate` passou
- [ ] preço, categoria, tags e descrição curta conferidos
- [ ] `README.md` do pacote com versão e data
- [ ] registro da publicação (data, preço, versão) numa planilha sua

## Perguntas pendentes para o suporte (texto pronto)

> Hello SkillHQ team. Before publishing paid products I'd like to confirm three points that the docs
> don't cover: (1) is there a native way to sell a bundle of several skills as one product, or should a
> single directory contain several skills? (2) does `skillhq install` also copy Claude Code subagents
> (`.claude/agents/`) and rules (`.claude/rules/`) shipped in the package, or only `.claude/skills/`?
> (3) how can a seller unpublish a product? Thank you.
