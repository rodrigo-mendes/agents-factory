# Claude Code para Infraestrutura: Terraform e AWS

**Perfil:** DevOps / SRE / Backend com infra própria  
**Stack coberto:** Terraform, AWS (Lambda, SQS, SNS, S3, DynamoDB, API Gateway, CloudWatch, IAM...)  
**Tempo estimado de leitura:** 10 min

---

## Base de conhecimento disponível

A Equipe de Governança BRX pesquisou e documentou os principais serviços AWS em `StoryBeat/AWS/`. Para Terraform, existe documentação em `StoryBeat/terraform/`. O subagente de infraestrutura (Terraform/AWS) e o subagente de arquitetura serverless usam essas bases para gerar infra que segue os padrões BRX.

**Sempre que possível, use o subagente de infraestrutura ou o de arquitetura serverless para tarefas de infra.** O chat livre para Terraform pode gerar código que não siga os padrões BRX.

> Nos exemplos deste guia usamos nomes ILUSTRATIVOS/hipotéticos: `agente-infra` (infraestrutura Terraform/AWS), `agente-arquitetura` (arquitetura serverless) e `agente-stack` (stack completa código + infra). Confirme os nomes reais do seu workspace digitando `/` no Claude Code ou listando `.claude/agents/`.

---

## Casos de uso frequentes

### 1. Provisionar um novo recurso AWS

**Modo recomendado:** o subagente de infraestrutura (ex.: `/agente-infra`)

```
/agente-infra crie um módulo Terraform para uma função Lambda:
- Runtime: Java 17
- Trigger: SQS queue (a queue é criada no mesmo módulo)
- Dead Letter Queue para mensagens com falha
- Alarme CloudWatch quando a DLQ passar de 5 mensagens
- Logs no CloudWatch com retenção de 30 dias
- IAM role com permissões mínimas
```

---

### 2. Desenhar uma arquitetura antes de implementá-la

**Modo recomendado:** o subagente de arquitetura serverless (ex.: `/agente-arquitetura`)

```
/agente-arquitetura desenhe o sistema de processamento de pedidos:
- Entrada: API REST de clientes (autenticada com Cognito)
- Processamento: validação, enriquecimento com dados de produto (DynamoDB)
- Notificação: e-mail ao cliente (SES) e evento interno (SNS)
- Volume: 200 req/min no horário de pico

Me dê diagrama de componentes, justificativa de cada serviço escolhido
e trade-offs da proposta.
```

---

### 3. Revisar ou atualizar Terraform existente

**Modo recomendado:** Modo de exploração para analisar → subagente de infraestrutura (ex.: `/agente-infra`) para mudanças

```
[Modo de exploração]
Analise @terraform/modules/api-gateway/main.tf.
Identifique:
1. Recursos sem tags BRX padrão
2. Roles IAM com permissões mais amplas do que o necessário
3. Configurações que poderiam melhorar a resiliência

Me dê a lista de problemas encontrados, sem fazer mudanças ainda.
```

Com a lista em mãos, use o subagente de infraestrutura (ex.: `/agente-infra`) para aplicar cada correção.

---

### 4. Entender o que faz um módulo Terraform existente

**Modo recomendado:** Modo de exploração / Plan Mode

```
Explique qual infraestrutura @terraform/modules/event-processing/ cria.
Quais recursos ela cria, quais são as dependências entre eles
e quais são os inputs obrigatórios?
```

---

### 5. Gerar documentação de um módulo

**Modo recomendado:** Modo de exploração / Modo agente

```
[Modo de exploração]
Leia @terraform/modules/lambda-sqs/ e gere a documentação README.md do módulo com:
- Descrição
- Tabela de inputs (nome, tipo, descrição, default, required)
- Tabela de outputs
- Exemplo de uso mínimo
```

---

### 6. Analisar custos de uma arquitetura

**Modo recomendado:** Modo de exploração (com as research docs como referência)

```
Com a arquitetura em @terraform/environments/prod/main.tf,
estime o custo mensal aproximado dos serviços Lambda, SQS e DynamoDB
assumindo 1M invocações Lambda/dia e 500GB de dados no DynamoDB.
Baseie a estimativa nas faixas de preço de 2024.
```

---

### 7. Revisar segurança de IAM

**Modo recomendado:** Modo de exploração / Plan Mode

```
Analise todos os arquivos IAM em @terraform/modules/:
- Identifique roles com `*` em actions ou resources
- Identifique policies que cruzam limites de serviço desnecessariamente
- Proponha o princípio de mínimo privilégio para cada caso

Formato: tabela com coluna Arquivo, Recurso, Problema, Fix proposto.
```

---

## Diferença entre os subagentes de infra

Nomes de comando ILUSTRATIVOS/hipotéticos — confirme os reais digitando `/` no Claude Code.

| Você precisa de | Subagente a usar |
|---|---|
| Desenho e proposta de arquitetura | Subagente de arquitetura serverless (ex.: `/agente-arquitetura`) |
| Módulos Terraform prontos para usar | Subagente de infraestrutura (ex.: `/agente-infra`) |
| Código Java + Terraform juntos | Subagente de stack completa (ex.: `/agente-stack`) |
| Analisar/revisar infra existente | Modo de exploração primeiro, depois o subagente de infraestrutura (ex.: `/agente-infra`) para mudanças |

---

## Erros comuns a evitar

| Erro | Consequência | Como evitar |
|---|---|---|
| Usar chat livre para Terraform sem contexto | Código sem tags BRX, IAM roles permissivos demais | Use o subagente de infraestrutura (ex.: `/agente-infra`) |
| Aceitar módulos sem revisar o IAM gerado | Permissões excessivas em produção | Revise sempre os roles e policies antes de aplicar |
| Implementar sem desenhar primeiro | Refatorações caras depois | Use o subagente de arquitetura serverless (ex.: `/agente-arquitetura`) antes do de infraestrutura (ex.: `/agente-infra`) |
| Não especificar o ambiente | O subagente pode gerar config de prod quando você queria dev | Sempre indique: `para o ambiente dev`, `para prod` |

---

## Próximos passos

- [3.3 — QA e Testing](03-qa-testing.md)
- [1.5 — Catálogo de agentes BRX](../modulo-1-agentes-customizados/05-catalogo-agentes-brx.md)
- [5.1 — O que não compartilhar com o Claude Code](../modulo-5-seguranca-governanca/01-o-que-nao-compartilhar.md) ← importante para infra
