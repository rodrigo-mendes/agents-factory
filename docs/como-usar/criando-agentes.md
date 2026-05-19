# Guia: Criando Agentes

Como criar um projeto de agente completo usando o agent-bootstrap.

---

## Quando Usar

- Começar um domínio novo de automação
- Estruturar um agente que precisa de skills, instructions e prompts
- Garantir aderência ao Agent Router Pattern desde o início

## Passo a Passo

### 1. Execute o bootstrap

```
@workspace /agent-bootstrap
```

### 2. Responda às perguntas do wizard

| Pergunta | Exemplo de Resposta |
|----------|-------------------|
| Domínio do agente | "Provisionar infraestrutura OCI com Terraform" |
| Tipo de agente | Implementation / Advisory / Orchestrator |
| Skills necessárias | "networking, iam, functions, api-gateway" |
| Tecnologias | "Terraform 1.5+, OCI Provider 5.x" |

### 3. Escolha o tipo correto

| Tipo | Quando | Gera código? |
|------|--------|:---:|
| **Implementation** | Agente que vai gerar/modificar código | ✅ |
| **Advisory** | Agente que produz designs, ADRs, recomendações | ❌ |
| **Orchestrator** | Agente que coordena múltiplos domínios | ✅ |

### 4. Resultado gerado

```
.github/
├── agents/
│   └── {domain}.agent.md           ← Definição do agente (P0-P5)
├── instructions/
│   ├── {domain}-config.instructions.md     ← Setup do projeto
│   ├── {domain}-standards.instructions.md  ← Padrões de código
│   └── {domain}-skills.instructions.md     ← Routing table
├── prompts/
│   └── {domain}.prompt.md           ← Entry-point do usuário
└── skills/
    └── {domain}/
        └── SKILL.md                 ← Skill placeholder
```

### 5. Valide a estrutura

```
@workspace /agent-router-pattern-validator
```

### 6. (Opcional) Auditoria completa

```
@workspace /audit-architecture-consensus
```

---

## Após o Bootstrap

O bootstrap gera a **estrutura** mas as skills ficam como placeholders. Próximos passos:

1. **Pesquisar** cada skill necessária:
   ```
   @workspace /technical-framework-researcher
   ```

2. **Compilar** pesquisa em SKILL.md:
   ```
   @workspace /skill-creator
   ```

3. **Validar** cada skill:
   ```
   @workspace /skill-best-practices-validator
   ```

4. **Validar** o projeto completo:
   ```
   @workspace /project-analysis-validator
   ```

---

## Tipos de Agente em Detalhe

### Implementation Agent
- Segue P0-P5 completo
- Carrega skills → extrai padrões → gera código → valida
- Precisa de `tools: ['read', 'editFiles', 'createFile', 'runInTerminal', 'search']`

### Advisory Agent
- Segue P0-P5 mas P4 é "Deliver" (não "Implement")
- Produz: ADRs, diagramas, roadmaps, delegation plans
- **Delega** implementação para outros agentes (ex: "Use @oci-terraform para provisionar X")
- Precisa de `tools: ['read', 'search']` (sem edit/create)

### Orchestrator Agent
- Coordena múltiplos domínios (ex: Java + Terraform)
- Mantém ordem de dependência cross-domain
- Precisa de todos os tools

---

## Dicas

- **Comece pelo advisory**: Se não tem certeza do design, crie um advisory agent primeiro para definir a arquitetura, depois um implementation agent para executar.
- **Granularidade de skills**: Prefira skills focadas (1 serviço/conceito) vs mega-skills. Facilita composição.
- **Routing table**: A `{domain}-skills.instructions.md` é o "mapa" que diz ao agente qual skill carregar baseado em keywords do request.

## Armadilhas Comuns

| Armadilha | Solução |
|-----------|---------|
| Pular o bootstrap e criar manualmente | Use o bootstrap — garante estrutura completa |
| Agente sem skills (hardcoded knowledge) | Sempre externalizar conhecimento em skills |
| Skill genérica demais ("cloud-stuff") | Uma skill por serviço/conceito específico |
| Não validar após criar | Executar router-pattern-validator |

## Fluxo Completo

Ver: [Fluxo de Criação de Projeto](../fluxos/fluxo-criacao-projeto.md)
