# Guia: Criando Agentes

Como criar um projeto de agente completo no Claude Code.

> **Nota**: O artefato `agent-bootstrap` foi cancelado e nunca foi implementado. Para criar um
> novo projeto de agente, comece com `/skill-creator` para criar as skills individuais e organize-as
> sob `.claude/`. A estrutura do projeto segue as convenções do Agent Router Pattern descrito abaixo.

---

## Quando Usar

- Começar um domínio novo de automação
- Estruturar um agente que precisa de skills, rules e comandos
- Garantir aderência ao Agent Router Pattern desde o início

## Passo a Passo

### 1. Pesquise as tecnologias do domínio

Antes de criar qualquer artefato, pesquise as tecnologias que o agente precisará conhecer:

```
/technical-framework-researcher
```

### 2. Crie cada skill com o skill-creator

Para cada área de conhecimento do domínio, execute:

```
/skill-creator
```

As skills são criadas em `.claude/skills/{nome-da-skill}/SKILL.md` seguindo o padrão three-tier.

### 3. Escolha o tipo correto de agente

| Tipo | Quando | Gera código? |
|------|--------|:---:|
| **Implementation** | Agente que vai gerar/modificar código | ✅ |
| **Advisory** | Agente que produz designs, ADRs, recomendações | ❌ |
| **Orchestrator** | Agente que coordena múltiplos domínios | ✅ |

### 4. Estrutura esperada do projeto

Organize os artefatos gerados sob `.claude/`:

```
.claude/
├── agents/
│   └── {domain}.md                  ← Definição do agente (P0-P5)
├── rules/
│   ├── {domain}-config.md           ← Setup do projeto
│   ├── {domain}-standards.md        ← Padrões de código
│   └── {domain}-skills.md           ← Routing table
├── skills/
│   └── {domain}/
│       └── SKILL.md                 ← Skill principal + blueprints/
```

### 5. Valide a estrutura de routing

```
/agent-router-pattern-validator
```

### 6. (Opcional) Auditoria completa

```
/audit-architecture-consensus
```

---

## Após Criar as Skills

As skills geradas pelo `/skill-creator` ficam como ponto de partida. Próximos passos:

1. **Validar** cada skill:
   ```
   /skill-best-practices-validator
   ```

2. **Validar** o projeto completo:
   ```
   /project-analysis-validator .claude/
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
- **Delega** implementação para outros agentes
- Precisa de `tools: ['read', 'search']` (sem edit/create)

### Orchestrator Agent
- Coordena múltiplos domínios (ex: Java + Terraform)
- Mantém ordem de dependência cross-domain
- Precisa de todos os tools

---

## Dicas

- **Comece pelo advisory**: Se não tem certeza do design, crie um advisory agent primeiro para definir a arquitetura, depois um implementation agent para executar.
- **Granularidade de skills**: Prefira skills focadas (1 serviço/conceito) vs mega-skills. Facilita composição.
- **Routing table**: O arquivo `{domain}-skills.md` em `.claude/rules/` é o "mapa" que diz ao agente qual skill carregar baseado em keywords do request.

## Armadilhas Comuns

| Armadilha | Solução |
|-----------|---------|
| Criar skills sem pesquisa prévia | Pesquise primeiro com `/technical-framework-researcher` — evita alucinações |
| Agente sem skills (hardcoded knowledge) | Sempre externalizar conhecimento em skills |
| Skill genérica demais ("cloud-stuff") | Uma skill por serviço/conceito específico |
| Não validar após criar | Executar `/agent-router-pattern-validator` e `/project-analysis-validator .claude/` |

## Fluxo Completo

Ver: [Fluxo de Criação de Projeto](../fluxos/fluxo-criacao-projeto.md)
