# Glossário

Termos do framework Agents Factory.

---

## Termos Gerais

| Termo | Definição |
|-------|-----------|
| **Agent / Agente** | Artefato (`.agent.md` no Copilot, `.claude/agents/*.md` no CC) que define um orquestrador com workflow P0-P5. Carrega skills e gera/revisa código. |
| **Agent Router Pattern** | Padrão de separação: entry-point → agent (orchestration) → skills (knowledge) → rules/instructions (config). Ver [Convenções](convencoes.md#agent-router-pattern). |
| **Advisory Agent** | Tipo de agent que produz designs, ADRs e planos de delegação mas NÃO gera código. P4 = "Deliver", não "Implement". |
| **Always Do (✅)** | Tier 1 do three-tier: padrão obrigatório que o agente executa automaticamente sem perguntar. Deve ter código funcional. |
| **Ask First (⚠️)** | Tier 2 do three-tier: decisão arquitetural que requer aprovação do usuário antes de prosseguir. Requer tabela de trade-offs. |
| **Blueprint** | Arquivo auxiliar em `blueprints/` que expande padrões da skill com código completo. Permite SKILL.md < 500 linhas. |
| **Compiler** | Prompt/skill que transforma documento de pesquisa em artefato operacional (SKILL.md ou .instructions.md). |
| **Consensus Audit** | Auditoria que corre 3 lentes em paralelo (scope + flow + engine) e prioriza findings por concordância: 3/3 🔴, 2/3 🟡, 1/3 🟢. |
| **Cross-domain** | Implementação que envolve múltiplos domínios técnicos (ex: Java + Terraform) com dependências mútuas. Requer Orchestrator Agent. |
| **Dead-end** | Componente que é referenciado mas não existe, ou cadeia de invocação incompleta (ex: `agent: x` mas `.claude/agents/x.md` não existe). |
| **Delegation** | Quando um advisory agent instrui o usuário a usar outro agent para implementação. |
| **Entry-point** | `.prompt.md` (Copilot) ou skill command `context: fork` (CC) — ponto de entrada do utilizador para um fluxo. |
| **Fan-out depth** | Número de níveis de subagentes aninhados. O padrão deste projecto é 1: comando → subagente → output. |
| **Generator** | Sinônimo de Compiler. Skill que gera artefatos a partir de pesquisa. |
| **G0→G4** | Hierarquia de responsabilidades de projecto Claude Code: G0 CLAUDE.md → G1 agents → G2 rules → G3 skills-fork → G4 meta-skills. Equivalente CC do L0→L4 Copilot. |
| **Implementation Agent** | Tipo de agent que segue P0-P5 completo e gera/modifica código. |
| **Instruction** | Artefato `.instructions.md` (Copilot) com configuração project-wide (setup, padrões, routing). Equivalente CC: `.claude/rules/*.md`. |
| **L0→L4** | Hierarquia de responsabilidades de projecto GitHub Copilot: L0 settings → L1 instructions → L2 skills → L3 agents → L4 prompts. |
| **Meta-skill** | Skill auto-invocável (sem `context: fork` e sem `disable-model-invocation`) que define padrões base do framework. Carregada pelo subagente em P0. Ex: `researching-technical-frameworks`. |
| **Never Do (🚫)** | Tier 3 do three-tier: anti-padrão que o agente bloqueia automaticamente, oferecendo alternativa inline e impacto. |
| **Orchestrator Agent** | Tipo de agent que coordena implementação em múltiplos domínios com ordem de dependência. |
| **Orphan** | Componente que existe no projeto mas não é referenciado por nenhum outro componente. |
| **P0-P5** | Workflow obrigatório de 6 fases: P0 Verify Docs → P1 Analyze → P2 Consult → P3 Propose → P4 Implement → P5 Validate. |
| **Progressive Disclosure** | Princípio de apresentar informação básica primeiro, detalhes avançados depois. SKILL.md ≤ 500 linhas; overflow para `blueprints/`. |
| **Prompt** | Artefato `.prompt.md` (Copilot) que serve como entry-point do utilizador. Equivalente CC: skill command com `context: fork`. |
| **Reachability** | Propriedade de um componente ser alcançável através da cadeia de invocação a partir de algum entry-point. |
| **Researcher** | Skill/prompt que pesquisa tecnologia/metodologia seguindo `researching-technical-frameworks`. Produz `research_<Tech>_v<Version>.md`. |
| **Rule** | Artefato `.claude/rules/*.md` com campo `paths:` que é injectado automaticamente quando os ficheiros correspondentes estão em contexto. Equivalente CC de `.instructions.md`. |
| **Routing Table** | Ficheiro `{domain}-skills.md` em `.claude/rules/` (CC) ou `.skills.instructions.md` (Copilot) — mapeia keywords → skills a carregar. |
| **Scaffolding** | Geração de estrutura de ficheiros a partir de templates (ex: `skill-creator` gera SKILL.md + blueprints a partir de pesquisa). |
| **Skill** | Artefato `SKILL.md` com base de conhecimento versionada e padrões three-tier (✅⚠️🚫). |
| **Source Hierarchy** | Hierarquia de fontes aceites: oficial/registry > blog oficial > exemplos oficiais > comunidade <12 meses > rejeitar o resto. |
| **Subagente** | Agente definido em `.claude/agents/` que recebe fork de uma skill command via `context: fork`. Roda em contexto isolado. |
| **Template** | Arquivo `TEMPLATE.*.md` em `.claude/templates/` ou `.github/templates/` — modelo para criar novos artefatos. |
| **Three-Tier** | Arquitectura de guardrails em 3 camadas: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do. Obrigatória em toda SKILL.md. |
| **Validator** | Skill que verifica qualidade de artefatos contra padrões definidos. Nunca modifica ficheiros por omissão. |
| **Version Absolutism** | Princípio: uma skill = uma versão específica. Versões antigas = desinformação. Pesquisas separadas por versão. |

---

## Termos YAML — Claude Code

| Campo YAML | Contexto | Descrição |
|-----------|----------|-----------|
| `context: fork` | Skills command (G3) | Instrui o CC engine a spawnar um subagente isolado quando esta skill é invocada |
| `disable-model-invocation: true` | Skills command (G3) | Impede auto-listagem da skill no budget de contexto. Obrigatório em todos os 24 comandos operacionais |
| `allowed-tools:` | Skills (`.claude/skills/`) | Lista de ferramentas disponíveis para a skill. Nunca usar `tools:` numa skill |
| `tools:` | Subagentes (`.claude/agents/`) | Lista de ferramentas disponíveis para o subagente. Nunca usar `allowed-tools:` num agente |
| `paths:` | Rules (`.claude/rules/`) | Glob de ficheiros que activa a rule automaticamente quando estão em contexto |
| `agent:` | Skills command (G3) | Nome do subagente a invocar no fork (ex: `agent: framework-researcher`) |
| `argument-hint:` | Skills command (G3) | Sugestão de input exibida ao utilizador quando invoca o comando |
