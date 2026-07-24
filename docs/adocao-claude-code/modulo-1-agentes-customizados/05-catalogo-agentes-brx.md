# Catálogo de agentes BRX

**Perfil:** Dev / Tech Lead  
**Mantido por:** Equipe de Governança BRX  
**Atualizado:** 2026-07

---

## Antes de tudo: este catálogo não é uma lista fixa

O conjunto de agentes disponíveis **muda com o tempo**. Novos agentes são publicados, outros são renomeados ou depreciados. Por isso este guia **não lista nomes de agentes como se fossem definitivos** — ele mostra como **descobrir os agentes reais do seu workspace** e descreve os **arquétipos** (categorias por capacidade) que você provavelmente encontrará.

Sempre que este guia usar um nome concreto de comando (como `agente-infra`), é um **nome ILUSTRATIVO/hipotético**, apresentado só como exemplo. O nome real que você vai digitar depende do que a Equipe de Governança BRX publicou.

---

## Como descobrir os agentes disponíveis no seu workspace

Há três formas de saber quais agentes existem de verdade:

1. **Digite `/` no Claude Code** (terminal ou painel do IDE). Aparecerá a lista de comandos e subagentes disponíveis no projeto atual, com os **nomes reais**.
2. **Liste os arquivos de definição** no repositório do projeto:
   - Subagentes: `.claude/agents/` (cada arquivo `.md` é um subagente)
   - Comandos slash customizados: `.claude/commands/`
3. **Pergunte à Equipe de Governança BRX** qual é o catálogo vigente e quais agentes cobrem o seu domínio.

> **Convenção de invocação:** os subagentes/comandos são invocados como `/<nome-do-agente>` (ou pedindo ao Claude Code para delegar a tarefa ao subagente correspondente). O `<nome-do-agente>` é o nome real que você descobre pelos passos acima.

---

## Como ler cada arquétipo

Para cada arquétipo você encontrará:
- **Quando usá-lo**: os casos de uso principais
- **O que precisa no contexto**: arquivos ou informações que um agente desse tipo espera encontrar no projeto
- **Que tipo de skills carrega**: as bases de conhecimento (em `.claude/skills/`) que um agente desse tipo costuma usar

No Claude Code, cada agente é definido em `.claude/agents/<nome>.md` (ou como comando em `.claude/commands/<nome>.md`) e é invocado por um comando slash `/<nome>` ou selecionando o subagente.

---

## Arquétipos de agentes

Os nomes de comando abaixo (`agente-infra`, `agente-arquitetura`, `agente-stack`) são **hipotéticos**, usados apenas para ilustrar a invocação. Confirme os nomes reais digitando `/` no Claude Code.

### Arquétipo: infraestrutura (Terraform/AWS)

Um subagente de infraestrutura provisiona e modifica recursos na AWS usando Terraform seguindo os padrões BRX.

**Quando usá-lo:**
- Criar novos módulos Terraform (Lambda, SQS, S3, API Gateway, DynamoDB...)
- Modificar recursos existentes de forma estruturada
- Refatorar módulos Terraform herdados para que sigam as convenções

**Como invocá-lo** (usando um agente de infraestrutura hipotético `agente-infra`):
```
/agente-infra <descrição do que você quer provisionar>
```

Exemplo:
```
/agente-infra cria um módulo para função Lambda com trigger SQS,
dead letter queue e alarme no CloudWatch quando o DLQ ultrapassar 10 mensagens
```

**O que precisa no contexto:**
- Estrutura de pastas Terraform existente (se você vai modificar)
- Arquivo `terraform.tfvars` ou variáveis de ambiente para inferir o contexto

**Que tipo de skills carrega** (em `.claude/skills/`)**:**
- Terraform patterns BRX
- AWS Lambda patterns
- AWS SQS patterns

---

### Arquétipo: arquitetura serverless

Um subagente de arquitetura serverless projeta e propõe arquiteturas serverless na AWS, sem chegar a gerar Terraform diretamente.

**Quando usá-lo:**
- Antes de implementar: obter uma proposta de arquitetura justificada
- Avaliar trade-offs entre opções de design serverless
- Revisar se uma arquitetura existente segue os padrões BRX

**Como invocá-lo** (usando um agente de arquitetura hipotético `agente-arquitetura`):
```
/agente-arquitetura <descrição do caso de uso ou problema>
```

Exemplo:
```
/agente-arquitetura preciso projetar o fluxo de processamento de pedidos:
receber eventos de compra, validá-los, notificar o usuário e persistir o resultado.
Volume estimado: 500 eventos/minuto em pico.
```

**O que precisa no contexto:**
- Nenhum pré-requisito técnico; funciona bem só com a descrição do problema

**Que tipo de skills carrega** (em `.claude/skills/`)**:**
- AWS Serverless patterns
- AWS arquitetura de referência

---

### Arquétipo: stack serverless completa (código + infra)

Um subagente de stack serverless completa implanta um serviço serverless completo coordenando código (por exemplo Java) e Terraform.

**Quando usá-lo:**
- Criar um serviço serverless completo do zero (código + infra juntos)
- Quando você precisa que o agente coordene a geração de código com os módulos Terraform correspondentes

**Como invocá-lo** (usando um agente de stack hipotético `agente-stack`):
```
/agente-stack <descrição do serviço completo>
```

Exemplo:
```
/agente-stack cria o serviço de processamento de notificações:
Lambda em Java 17 com Spring Cloud Function, queue SQS de entrada, 
DLQ, e tabela DynamoDB para auditoria de eventos processados
```

**O que precisa no contexto:**
- Estrutura base do projeto de código (por exemplo Maven `pom.xml` ou similar)
- Estrutura base de Terraform (se já existir)

**Que tipo de skills carrega** (em `.claude/skills/`)**:**
- Java Lambda patterns BRX
- Terraform patterns BRX
- AWS patterns relevantes

---

### Arquétipo: backend (geração de serviços)

Um subagente de backend gera serviços seguindo as convenções de API e camadas da BRX (controllers, serviços, repositórios, DTOs).

**Quando usá-lo:**
- Implementar um endpoint completo (multi-arquivo) seguindo os padrões do projeto
- Criar um serviço backend do zero com a estrutura de camadas esperada

**O que precisa no contexto:**
- Estrutura de projeto backend existente (para inferir camadas e convenções)
- Referências a DTOs, repositórios ou tabelas já existentes (via `@arquivo`)

**Que tipo de skills carrega** (em `.claude/skills/`)**:**
- Padrões de API/backend BRX
- Padrões da linguagem/framework (por exemplo Java/Spring)

---

### Arquétipo: testing

Um subagente de testing gera testes unitários e de integração que exercitam de fato o comportamento do código.

**Quando usá-lo:**
- Gerar testes para um serviço ou classe existente
- Cobrir casos de borda de um comportamento já implementado

**O que precisa no contexto:**
- O código a ser testado (via `@arquivo`)
- Convenções de teste do projeto (framework, mocks, fixtures)

**Que tipo de skills carrega** (em `.claude/skills/`)**:**
- Padrões de testing BRX (unitário e de integração)

---

### Arquétipo: code review

Um subagente de code review analisa mudanças (diffs, PRs) buscando bugs, riscos e desvios de convenções — sem gerar código de produção.

**Quando usá-lo:**
- Revisar um PR antes de aprová-lo
- Obter uma segunda opinião sobre riscos de uma mudança

**O que precisa no contexto:**
- O diff ou os arquivos alterados
- As convenções contra as quais revisar (via `CLAUDE.md` ou skills)

**Que tipo de skills carrega** (em `.claude/skills/`)**:**
- Convenções e anti-padrões BRX do domínio revisado

---

## Meta-agentes: para quem cria e mantém agentes e skills

Além dos agentes de uso diário, o ecossistema costuma incluir agentes voltados à **Equipe de Governança BRX** e a Tech Leads que criam ou mantêm agentes e skills. Descritos por papel (os nomes de comando reais, se existirem, você descobre digitando `/` ou consultando a Governança):

| Papel do meta-agente | Propósito | Público |
|---|---|---|
| Um subagente para criar novos agentes | Gerar a estrutura de um novo agente | Governança BRX |
| Um subagente para compilar skills | Compilar uma research em um `SKILL.md` | Governança BRX |
| Um subagente de pesquisa técnica de frameworks | Investigar uma tecnologia para criar knowledge base | Governança BRX / Tech Lead |
| Um subagente de auditoria de arquitetura | Auditar se uma arquitetura segue os padrões documentados | Tech Lead / Governança |

Para mais detalhes sobre a toolchain de criação, ver os docs do agents-factory em `docs/como-usar/`.

---

## Agentes planejados (em desenvolvimento)

O roadmap de novos arquétipos evolui. Em geral inclui domínios ainda não cobertos por agentes estáveis:

| Domínio | Estado | ETA estimado |
|---|---|---|
| Backend (geração de serviços) | Em design | Q3 2026 |
| Testing (geração de testes unitários e de integração) | Em investigação | Q4 2026 |
| Code Review (análise de PRs) | Proposto | A definir |

Para solicitar a priorização de um agente, ver [Módulo 6.1](../modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md).

---

## Como saber se um agente está atualizado

Os agentes de BRX usam skills versionadas. Se uma skill tem mais de 12 meses sem atualizar, pode ser que seus padrões estejam desatualizados. Se você encontrar um agente que segue padrões obsoletos:

1. Verifique a data no arquivo do agente (`.claude/agents/<nome>.md`)
2. Revise o campo `version` nos `SKILL.md` (em `.claude/skills/`) que ele usa
3. Se estiverem desatualizados, reporte à Equipe de Governança BRX

> O repositório pode conter exemplos de referência de agentes (por exemplo, sob `.github/templates/examples/`). Use-os como modelo, mas confirme sempre o catálogo vigente com a Governança antes de assumir que um agente existe com um nome específico.

---

## Próximos passos

- [1.1 — Como invocar um agente](01-o-que-e-um-agente-customizado.md)
- [1.4 — O que fazer quando o agente falha](04-quando-o-agente-falha.md)
- [6.1 — Solicitar um novo agente](../modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md)
