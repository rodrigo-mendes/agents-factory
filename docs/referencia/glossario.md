# Glossário

Termos do framework Agents Factory.

---

| Termo | Definição |
|-------|-----------|
| **Agent** | Artefato `.agent.md` que define um orquestrador com workflow P0-P5. Carrega skills e gera/revisa código. |
| **Agent Router Pattern** | Padrão de separação: Prompt (entry) → Agent (orchestration) → Skills (knowledge) → Instructions (config). |
| **Advisory Agent** | Tipo de agent que produz designs, ADRs e planos de delegação mas NÃO gera código. |
| **Always Do (✅)** | Tier 1 do three-tier: padrão obrigatório que o agente executa automaticamente sem perguntar. |
| **Ask First (⚠️)** | Tier 2 do three-tier: decisão arquitetural que requer aprovação do usuário antes de prosseguir. |
| **Blueprint** | Arquivo auxiliar em `blueprints/` que expande padrões da skill com código completo. |
| **Compiler** | Prompt que transforma documento de pesquisa em artefato operacional (SKILL.md ou .instructions.md). |
| **Cross-domain** | Implementação que envolve múltiplos domínios técnicos (ex: Java + Terraform) com dependências mútuas. |
| **Dead-end** | Componente que é referenciado mas não existe, ou cadeia de invocação incompleta. |
| **Delegation** | Quando um advisory agent instrui o usuário a usar outro agent para implementação. |
| **Entry-point** | Prompt que serve como ponto de entrada do usuário para um fluxo. |
| **Generator** | Sinônimo de Compiler. Prompt que gera artefatos a partir de pesquisa. |
| **Implementation Agent** | Tipo de agent que segue P0-P5 completo e gera/modifica código. |
| **Instruction** | Artefato `.instructions.md` com configuração project-wide (setup, padrões, routing). |
| **Never Do (🚫)** | Tier 3 do three-tier: anti-padrão que o agente bloqueia automaticamente, oferecendo alternativa. |
| **Orchestrator Agent** | Tipo de agent que coordena implementação em múltiplos domínios com ordem de dependência. |
| **Orphan** | Componente que existe no projeto mas não é referenciado por nenhum outro componente. |
| **P0-P5** | Workflow obrigatório de 6 fases: Verify → Analyze → Consult → Propose → Implement → Validate. |
| **Progressive Disclosure** | Princípio de apresentar informação básica primeiro, detalhes avançados depois. |
| **Prompt** | Artefato `.prompt.md` que serve como entry-point do usuário no Copilot Chat. |
| **Reachability** | Propriedade de um componente ser alcançável através da cadeia de invocação a partir de algum prompt. |
| **Researcher** | Prompt que pesquisa tecnologia/metodologia seguindo a skill `researching-technical-frameworks`. |
| **Routing Table** | Arquivo `.skills.instructions.md` que mapeia keywords do request para skills a carregar. |
| **Scaffolding** | Geração de estrutura de arquivos a partir de templates (ex: agent-bootstrap). |
| **Skill** | Artefato `SKILL.md` com base de conhecimento versionada e padrões three-tier (✅⚠️🚫). |
| **Template** | Arquivo `TEMPLATE.*.md` que serve como modelo para criar novos artefatos. |
| **Three-Tier** | Arquitetura de guardrails em 3 camadas: ✅ Always Do, ⚠️ Ask First, 🚫 Never Do. |
| **Validator** | Prompt que verifica qualidade de artefatos contra padrões definidos. |
| **Version Absolutism** | Princípio: uma skill = uma versão específica. Nunca misturar versões. |
