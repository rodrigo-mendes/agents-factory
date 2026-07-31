# Documentation — Agents Factory

## By Journey

### 🆕 I'm new here
1. [Overview](visao-geral.md) — Understand the framework's mental model
2. [How to Use → Onboarding](como-usar/README.md) — Setup and first use
3. [Quick Start (5 minutes)](como-usar/inicio-rapido.md) — Complete pipeline in a single read
4. [Glossary](referencia/glossario.md) — Framework terms

### 🔨 I want to create something
1. [Capabilities Catalog](capacidades/README.md) — Find the right tool
2. [Agent Usage Manual](manual/README.md) — Complete reference with invocation examples
3. [Combined Flows](fluxos/README.md) — End-to-end pipelines
4. Specific guides:
   - [Researching technologies](como-usar/pesquisando-tecnologias.md)
   - [Creating skills](como-usar/criando-skills.md)
   - [Creating agents](como-usar/criando-agentes.md)

### ✅ I want to validate quality
1. [Validating artifacts](como-usar/validando-artefatos.md)
2. [Quality Flow](fluxos/fluxo-qualidade.md)

### 📚 Reference
1. [Conventions](referencia/convencoes.md) — P0-P5, Three-Tier, naming, YAML
2. [Glossary](referencia/glossario.md) — All terms
3. [Mapping .github/ ↔ .claude/](referencia/mapeamento-github-claude.md) — Copilot vs Claude Code equivalency

---

## Full Map

```
docs/
├── visao-geral.md                 ← Architecture + diagrams
├── manual/
│   ├── README.md                  ← Index + cheat sheet of 24 commands
│   ├── framework-researcher.md    ← 7 research commands
│   ├── skill-author.md            ← 4 generation commands
│   ├── architecture-auditor.md    ← 8 audit commands
│   └── quality-validator.md       ← 5 validation commands
├── capacidades/
│   ├── README.md                  ← Complete catalog
│   ├── skills.md                  ← 2 meta-skills
│   ├── templates.md               ← 14 templates + traceability
│   ├── prompts-pesquisa.md        ← 7 research prompts
│   ├── prompts-compilacao.md      ← 4 compilation prompts
│   ├── prompts-validacao.md       ← 4 validation prompts
│   ├── prompts-arquitetura.md     ← 8 audit prompts (4 Copilot + 4 Claude Code)
│   └── prompts-framework.md       ← 1 lifecycle prompt
├── como-usar/
│   ├── README.md                  ← Quick onboarding
│   ├── inicio-rapido.md           ← Complete pipeline in 3 steps (5 minutes)
│   ├── pesquisando-tecnologias.md
│   ├── criando-skills.md
│   ├── criando-agentes.md
│   └── validando-artefatos.md
├── fluxos/
│   ├── README.md                  ← General flow map
│   ├── fluxo-criacao-projeto.md
│   ├── fluxo-base-conhecimento.md
│   ├── fluxo-qualidade.md
│   └── fluxo-implementacao.md
└── referencia/
    ├── convencoes.md
    ├── glossario.md
    └── mapeamento-github-claude.md
```
