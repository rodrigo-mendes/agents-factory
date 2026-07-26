# Claude Code para Code Review

**Perfil:** Dev / Tech Lead  
**Tempo estimado de leitura:** 8 min

---

## Por que a revisão assistida pelo Claude Code é útil e por que tem limites

O Claude Code pode ajudar você a identificar bugs, problemas de segurança e dívida técnica em um código que você não escreveu, ou no seu próprio antes de mandar para revisão. No entanto:

- **Não conhece o contexto de negócio** do seu produto nem as decisões de design passadas
- **Não pode aprovar nem rejeitar** um PR — essa é a sua responsabilidade
- **Pode dar falsos negativos** (não encontrar algo que está de fato errado) ou falsos positivos

Use o Claude Code como um **primeiro filtro** que ajuda você a não deixar passar o óbvio, não como um revisor substituto.

---

## Casos de uso frequentes

### 1. Revisão delimitada antes de abrir o PR (auto-review)

**Modo recomendado:** Modo de exploração / Plan Mode

```
Revise @OrderService.java com foco em:
1. Bugs potenciais (null pointers, condições de corrida, off-by-one)
2. Vulnerabilidades de segurança (injeção, exposição de dados, autorização)
3. Regressões em relação à interface pública (mudanças de assinatura, comportamento)

NÃO comente:
- Estilo ou formatação
- Naming de variáveis que já segue a convenção
- Melhorias "nice-to-have"

Formato: tabela com coluna Problema, Linha aproximada, Severidade (Alta/Média/Baixa), Fix sugerido.
```

---

### 2. Revisar lógica de negócio específica

**Modo recomendado:** Modo de exploração com contexto

```
Revise a lógica de cálculo de descontos em @DiscountCalculator.java.
O requisito é: desconto de 10% para pedidos > 100€,
20% para pedidos > 500€, sem acumulação com descontos de campanha.

A implementação atual reflete corretamente esse requisito?
Identifique discrepâncias ou casos de borda não tratados.
```

---

### 3. Revisar mudanças de um PR

**Modo recomendado:** Modo de exploração com o diff

```
Tenho este diff de um PR que modifica o serviço de autenticação:
[cole o diff ou use @arquivo]

Revise com foco em:
1. Há regressões no tratamento de tokens?
2. A expiração é validada corretamente?
3. Há dados sensíveis que poderiam ser logados acidentalmente?

Me dê apenas os problemas concretos que você encontrar.
```

---

### 4. Revisar migrações de banco de dados

**Modo recomendado:** Modo de exploração / Plan Mode

```
Revise a migração em @V23__add_order_audit_table.sql:
1. Ela pode ser executada sem bloquear tabelas em produção (a tabela orders tem 50M registros)?
2. Há algum rollback implícito se falhar no meio?
3. Os índices definidos são suficientes para os queries mais frequentes?
```

---

### 5. Revisar contratos de API

**Modo recomendado:** Modo de exploração / Plan Mode

```
Compare @api/v1/openapi.yaml (versão atual) com @api/v2/openapi.yaml (nova versão).
Há breaking changes? Liste cada um com:
- Endpoint afetado
- Tipo de mudança (campo removido, tipo alterado, comportamento alterado)
- Impacto para clientes que usam a v1
```

---

### 6. Gerar um checklist de revisão para a sua equipe

**Modo recomendado:** Modo de exploração

```
Analise os últimos PRs neste repositório (arquivos em @src/) e gere
um checklist de revisão específico para este projeto.
Deve incluir os pontos mais relevantes para o nosso stack Java + AWS Lambda.
No máximo 15 pontos, ordenados por importância.
```

---

## Como pedir uma revisão realmente útil

A qualidade de uma revisão do Claude Code depende quase completamente do que você pede para revisar.

### Defina o foco

❌ Genérico (resposta longa, pouco acionável):
```
Revise este código.
```

✅ Delimitado (resposta curta, acionável):
```
Revise apenas a segurança do tratamento de tokens JWT em @AuthService.java.
Me dê no máximo 5 problemas ordenados por severidade.
```

### Forneça o contexto de negócio que o Claude Code não tem

```
Este endpoint é público (sem autenticação), então a validação de entrada é crítica.
Revise @PublicOrderController.java com esse foco.
```

### Separe as revisões por área

Uma revisão que pede "bugs + segurança + desempenho + estilo + arquitetura" produz respostas longas e genéricas. Faça uma revisão por área:

1. `Revise bugs e lógica incorreta.`
2. (Se a anterior não encontrou nada crítico) `Revise implicações de segurança.`
3. (Só se necessário) `Revise desempenho nos paths críticos.`

---

## Comandos slash nativos de revisão

Além dos prompts manuais acima, o Claude Code traz comandos slash nativos que já estruturam a revisão para você:

- **`/review`** — revisa um Pull Request do GitHub (útil ao revisar o PR de outra pessoa)
- **`/code-review`** — revisa o diff local (suas mudanças ainda não commitadas ou o branch atual), ideal para o auto-review antes de abrir o PR
- **`/security-review`** — faz uma revisão de segurança focada das mudanças pendentes, procurando vulnerabilidades comuns

Esses comandos são um bom ponto de partida; para focos específicos (uma regra de negócio, um contrato de API), continue usando os prompts delimitados das seções acima.

---

## O que não delegar ao Claude Code em uma revisão

| Não delegar | Por quê |
|---|---|
| Decisões de design arquitetônico | O Claude não conhece as restrições do negócio |
| Aprovação final do PR | A responsabilidade é sua |
| Revisar se um feature "faz sentido" para o produto | Requer contexto de negócio que o Claude não tem |
| Revisar conformidade com requisitos legais ou de compliance | Crítico demais para depender de IA |

---

## Integração com o fluxo de revisão da equipe

Se a sua equipe usa GitHub Pull Requests, você pode combinar o Claude Code com o processo de revisão existente:

1. **Antes de publicar o PR** — auto-review com `/code-review` (ou um prompt delimitado) para pegar o óbvio; use `/security-review` quando as mudanças mexem em áreas sensíveis
2. **Ao revisar o PR de outra pessoa** — use `/review` para revisar o PR do GitHub, ou cole o diff no chat para um segundo par de olhos
3. **Depois da revisão humana** — se há um comentário de revisão que você não entende, explique-o ao Claude para entender o raciocínio

Veja também [Módulo 5.2 — Responsabilidade humana no código gerado](../modulo-5-seguranca-governanca/02-responsabilidade-revisao-codigo.md).

---

## Próximos passos

- [5.2 — Responsabilidade humana: revisar sempre o código gerado](../modulo-5-seguranca-governanca/02-responsabilidade-revisao-codigo.md)
- [3.1 — Backend Java/Spring](01-backend-java-kotlin-spring.md)
- [3.3 — QA e Testing](03-qa-testing.md)
