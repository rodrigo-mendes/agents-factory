# Mapa do ecossistema Claude Code BRX

**Perfil:** Todos  
**Tempo estimado de leitura:** 6 min

---

## A camada de personalização BRX

O Claude Code funciona de fábrica para tarefas gerais de programação. Para torná-lo útil com o stack, as convenções e os processos próprios da BRX, a **Equipe de Governança BRX** mantém uma camada de personalização construída sobre o repositório **agents-factory**.

Essa camada adiciona três tipos de artefatos:

```
Claude Code base
    └── + Instruções de contexto (CLAUDE.md)
            → o Claude entende as convenções do projeto
    └── + Skills (.claude/skills/<nome>/SKILL.md)
            → o Claude segue padrões específicos da BRX (Java, Terraform, AWS...)
    └── + Subagentes (.claude/agents/*.md)
            → o Claude executa fluxos de trabalho completos pré-desenhados
```

---

## Componentes do ecossistema

### Instruções de contexto

Arquivos de texto que dizem ao Claude como se comportar em um projeto específico: convenções de nomenclatura, frameworks usados, o que evitar. São carregados automaticamente quando você abre esse projeto e roda o Claude Code nele.

**Quem mantém:** cada equipe, para o próprio repositório  
**Onde vivem:** `CLAUDE.md` na raiz do projeto (e `CLAUDE.md` aninhados por subpasta)  
**Como criá-los:** ver [Módulo 4](../modulo-4-instrucoes-contexto/README.md)

---

### Skills

Uma skill é uma base de conhecimento estruturada sobre uma tecnologia ou prática específica. Contém padrões que o Claude deve sempre seguir (✅), decisões que deve consultar antes de tomar (⚠️) e anti-padrões que nunca deve usar (🚫). É um conceito nativo do Claude Code.

**Quem mantém:** Equipe de Governança BRX  
**Onde vivem:** `.claude/skills/<nome>/SKILL.md` no agents-factory  
**Como usá-las:** os agentes as carregam automaticamente; ver [Módulo 1.3](../modulo-1-agentes-customizados/03-entender-resposta-workflow-p0-p5.md)

Skills e comandos slash disponíveis atualmente:

**Meta-skills (auto-invocáveis):**

| Skill | Descrição | Estado |
|---|---|---|
| `authoring-agent-skills` | Meta: como criar skills | Estável |
| `researching-technical-frameworks` | Meta: pesquisa técnica | Estável |

**Comandos de pesquisa → `framework-researcher`:**

| Comando | Descrição |
|---|---|
| `technical-framework-researcher` | Pesquisa tecnologias e frameworks |
| `technical-framework-researcher-terraform` | Pesquisa específica de Terraform |
| `cloud-architecture-researcher` | Pesquisa arquitetura de nuvem |
| `business-domain-researcher` | Pesquisa de domínio de negócio |
| `requirements-methodology-researcher` | Pesquisa metodologias de requisitos |
| `architecture-methodology-researcher` | Pesquisa metodologias de arquitetura |
| `terraform-engineering-best-practices-researcher` | Melhores práticas de engenharia Terraform |

**Comandos de autoria → `skill-author`:**

| Comando | Descrição |
|---|---|
| `skill-creator` | Cria novos SKILL.md |
| `methodologies-skill-generator` | Gera skills de metodologias |
| `architecture-approaches-skill-generator` | Gera skills de abordagens de arquitetura |
| `terraform-instructions-compiler` | Compila instruções Terraform |

**Comandos de auditoria — alvo Copilot → `architecture-auditor`:**

| Comando | Descrição |
|---|---|
| `audit-architecture-scope` | Audita escopo de arquitetura |
| `audit-architecture-flow` | Audita fluxo de arquitetura |
| `audit-architecture-engine` | Motor de auditoria de arquitetura |
| `audit-architecture-consensus` | Auditoria por consenso (3 lentes) |

**Comandos de auditoria — alvo Claude Code → `architecture-auditor`:**

| Comando | Descrição |
|---|---|
| `audit-cc-architecture-scope` | Audita escopo de arquitetura (Claude Code) |
| `audit-cc-architecture-flow` | Audita fluxo de arquitetura (Claude Code) |
| `audit-cc-architecture-engine` | Motor de auditoria de arquitetura (Claude Code) |
| `audit-cc-architecture-consensus` | Auditoria por consenso — Claude Code (3 lentes) |

**Comandos de validação → `quality-validator`:**

| Comando | Descrição |
|---|---|
| `skill-best-practices-validator` | Valida aderência de skills às boas práticas |
| `instructions-best-practices-validator` | Valida aderência de instruções/rules |
| `agent-router-pattern-validator` | Valida padrão de roteamento de agentes |
| `copilot-compatibility-review` | Revisa compatibilidade com GitHub Copilot |
| `project-analysis-validator` | Valida análise de projeto |

> Para solicitar uma nova skill: ver [Módulo 6.1](../modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md)

---

### Subagentes customizados

Um subagente customizado é um fluxo de trabalho pré-desenhado que combina instruções, skills e ferramentas para realizar uma tarefa complexa de forma estruturada. Quando você invoca um subagente (via o comando/ferramenta de subagente ou por menção, ou por um comando slash customizado `/<nome-do-agente>`), ele segue um processo em fases (P0-P5) que garante que as convenções BRX sejam verificadas antes de escrever código. O conjunto de subagentes disponíveis depende do que a Equipe de Governança BRX publicou; descubra os nomes reais digitando `/` no Claude Code ou listando `.claude/agents/` (e `.claude/skills/`).

**Quem mantém:** Equipe de Governança BRX  
**Onde vivem:** `.claude/agents/*.md` no agents-factory (e distribuídos aos projetos que os usam); comandos slash customizados ficam em `.claude/skills/<nome>/SKILL.md` (com `context: fork` no frontmatter)  
**Como usá-los:** ver [Módulo 1](../modulo-1-agentes-customizados/README.md)

---

### Prompts operacionais

Prompts especializados para tarefas específicas do ciclo de vida de desenvolvimento: pesquisar tecnologias, gerar documentação de arquitetura, auditar código, compilar skills. São o "motor" interno do agents-factory.

**Quem usa:** principalmente a Equipe de Governança BRX e Tech Leads avançados  
**Onde vivem:** nos prompts/comandos internos do agents-factory

---

## Como o conhecimento flui

```
Equipe de Governança BRX
    │
    ├── Pesquisa tecnologias (prompts researcher/)
    │       └── gera → Research docs (StoryBeat/)
    │
    ├── Compila em skills (prompts compiler/)
    │       └── gera → SKILL.md em .claude/skills/
    │
    ├── Cria subagentes que usam essas skills
    │       └── gera → .claude/agents/*.md
    │
    └── Distribui para as equipes
            └── As equipes usam os subagentes → melhor código, sem reinventar convenções
```

---

## Quem faz o quê

| Ator | Responsabilidades |
|---|---|
| **Dev** | Usar subagentes e o chat. Dar feedback do que falha ou falta. |
| **Tech Lead** | Configurar as instruções de contexto (`CLAUDE.md`) do projeto. Solicitar novos subagentes/skills. |
| **Governança BRX** | Criar e manter skills e subagentes globais. Gerir o programa e as métricas. |

---

## Próximos passos

- [Módulo 0.3 — Setup do ambiente: dia 1](03-setup-ambiente-dia-1.md)
- [Módulo 1.5 — Catálogo de agentes BRX](../modulo-1-agentes-customizados/05-catalogo-agentes-brx.md)
- [Módulo 4 — Instruções de contexto](../modulo-4-instrucoes-contexto/README.md)
