# Guia Agensi — do zero ao produto pago ou por assinatura

Passo a passo para publicar e manter os bundles no [Agensi](https://www.agensi.io/). Antes, faça a
[preparação comum](guia-publicacao.md) (passos 0 a 2).

Fontes oficiais, lidas em 2026-10-31:
[How to Sell Skills on Agensi](https://www.agensi.io/learn/how-to-sell-skills-on-agensi) (2026-03-30),
[Subscription Skills](https://www.agensi.io/learn/subscription-skills-launch) (2026-06-17),
[Sell](https://www.agensi.io/sell),
[How Agensi Payouts Work](https://www.agensi.io/learn/how-agensi-payouts-work-stripe-connect).
O que essas páginas não cobrem está marcado **não documentado — confirmar no painel ou com o suporte**.

## Visão geral

```
A conta ─▶ B recebimento ─▶ C zip ─▶ D teste grátis ─▶ E compra única ─┐
                                                       F assinatura ───┤
                                                                       ▼
                         J tirar do ar ◀─ I acompanhar ◀─ H atualizar ◀─ G bundle no perfil
```

## A. Criar a conta e ligar o modo criador

1. Crie a conta em https://www.agensi.io/.
2. **Dashboard → Settings → Creator Mode**: ligue.

## B. Configurar o recebimento

Necessário **antes** de qualquer produto pago ir ao ar; produto grátis não precisa.

1. **Creator Studio → Payouts**.
2. Escolha **Stripe Connect** ou, se o Stripe não atender o seu país, **Zoneless** (pagamento em USDC).
3. Faça o KYC: é obrigatório para receber.

**Quanto você recebe:** 70% de cada venda (nas assinaturas, 70% depois das taxas do Stripe).
Exemplo: venda de US$25 → **US$17,50** para você.

| Forma | Quando o dinheiro chega |
|---|---|
| Stripe Connect, venda por cartão | na hora da venda, na sua conta Stripe; o Stripe repassa ao banco no calendário dele |
| Stripe Connect, venda por créditos | quando o saldo a receber passa de US$3,50 |
| Zoneless (USDC) | 72 horas depois da venda, com saldo acima de US$3,50 |

## C. Preparar o zip

Use o zip gerado na preparação: `dist/<bundle>-claude.zip`.

O Agensi pede um zip com pelo menos um `SKILL.md` com `name` e `description` no frontmatter. Antes da
revisão manual, um scan automático faz 8 checagens; o nosso script de exportação já cobre a maioria:

| Checagem do Agensi | Coberta pelo `export-bundle.py`? |
|---|---|
| estrutura de arquivos | parcial: o formato "diretório compilado" é o risco que o teste grátis vai mostrar |
| tipos de arquivo | não (só copiamos o que o APM gera) |
| comandos perigosos | não: as skills que mandam rodar `aws`, `terraform`, `oci` dizem que é o usuário quem executa |
| segredos | sim (detector `key`) |
| coleta de variáveis de ambiente | não |
| acesso à rede | não |
| código ofuscado | não (não há) |
| prompt injection | não |

## D. Publicação de teste grátis

1. **Creator Dashboard → Submit a Skill**.
2. Envie `dist/stripe-for-java-claude.zip`.
3. Preço **grátis**, tags `java, stripe, payments`, descrição da listagem "TEST - do not buy".
4. Aguarde o scan e a revisão manual (24-48h, segundo o Agensi).
5. **Aprovado:** conecte um agente pelo conector do Agensi e veja o que ele recebe (só skills? agentes?
   rules?). Anote na [tabela de resultados](guia-publicacao.md#4-registrar-o-resultado-dos-testes-grátis).
6. **Reprovado:** copie o motivo exato para a tabela e pare aqui.

## E. Publicar pago — compra única

Mesmo fluxo da fase D, com preço. Regras que mudam a estratégia:

- **O comprador recebe todas as atualizações de graça**: o agente sempre carrega a versão mais nova.
  Por isso, cada versão maior é uma **listagem separada** (ex.: "AWS Terraform 6.x"); a 7.x será
  outra listagem.
- Preço sugerido pelo próprio Agensi: US$5-15 para skills simples, US$20-50 para as completas.
  Os nossos preços: [estrategia-bundles.md, seção 5](estrategia-bundles.md#5-modelo-de-preço-e-de-versão).

## F. Publicar por assinatura

1. No Creator Studio, escolha o modelo **assinatura** para o produto.
2. Preço mensal: **mínimo US$5**.
3. Desconto anual: de 0% a 50% (o padrão é 2 meses grátis, cerca de 17%).
4. A assinatura é entregue pelo servidor MCP do Agensi (`get_skill` / `install_skill`): **não há botão
   de download**, e o agente recebe a versão atual a cada chamada.

Cuidados:
- **O modelo de preço não muda depois de publicado.** Dá para migrar uma skill de compra única para
  assinatura, mas quem comprou antes fica com a versão de compra única.
- Toda atualização exige **release notes**; os assinantes recebem por e-mail.
- Quem cancela mantém o acesso até o fim do período pago.

Quais bundles vão para assinatura: [estrategia-bundles.md, seção 5](estrategia-bundles.md#5-modelo-de-preço-e-de-versão).

## G. Montar o bundle no perfil

O Agensi mostra bundles no perfil do criador ("Browse Skill Bundles").
**Não documentado:** como criar um bundle e como definir o preço dele. Procure a opção no Creator Studio;
se não achar, use a pergunta pronta no fim deste guia.

## H. Atualizar

1. Gere a versão nova: `python scripts/export-bundle.py <bundle> --apply`.
2. Envie o zip novo para o mesmo produto no Creator Studio.
3. A versão nova passa por revisão; a anterior continua no ar até a aprovação.
4. Escreva as release notes (obrigatórias na assinatura). Modelo:

```markdown
## <bundle> — <versão> — <AAAA-MM-DD>
### Added
- <skill nova ou exemplo novo>
### Changed
- <o que mudou e por quê; versão de ferramenta, se for o caso>
### Fixed
- <correção>
Applies to: <ferramenta> <versão> (e.g., hashicorp/aws 6.x)
```

O histórico de versões e aprovações fica no Creator Studio.

## I. Acompanhar

**Creator Studio → Earnings**: vendas, assinaturas e pagamentos.

## J. Tirar do ar

**Não documentado.** Procure a opção no Creator Studio; se não achar, pergunte ao suporte.

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---|---|---|
| Reprovado no scan de segredos | exemplo de chave em um "Nunca faça" | o filtro de exportação já barra esses padrões; rode `export-bundle.py` de novo e veja o `BLOCKED.txt` |
| Reprovado como "repackaged free skill" | skill de terceiros no pacote | confira que nada de `third-party/` entrou (o script remove a Vercel) |
| Produto pago não vai ao ar | recebimento não configurado | fase B (payout + KYC) |
| Revisão demora mais de 48h | fila de revisão | aguarde; a versão anterior (se houver) continua no ar |
| Agente do comprador não vê agentes/rules | entrega via MCP pode trazer só `SKILL.md` | anote no teste grátis e ajuste a descrição da listagem |

## Checklist por produto

- [ ] `export-bundle.py <bundle> --apply` com ✅
- [ ] modelo escolhido (compra única ou assinatura) — não muda depois
- [ ] preço, tags e descrição da listagem conferidos
- [ ] release notes escritas (se for atualização ou assinatura)
- [ ] registro (data, preço, versão, modelo) numa planilha sua

## Perguntas pendentes para o suporte (texto pronto)

> Hello Agensi team. Before publishing paid products I'd like to confirm: (1) how do I create a bundle on
> my creator profile and set its price? (2) does a skill delivered through the Agensi connector/MCP also
> deliver Claude Code subagents (`.claude/agents/`) and rules (`.claude/rules/`) included in the zip, or
> only `SKILL.md` content? (3) how do I unpublish a product? (4) is there a file size limit for the zip?
> Thank you.
