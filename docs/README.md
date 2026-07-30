# Documentação — Agents Factory

## Por Jornada

### 🆕 Sou novo aqui
1. [Visão Geral](visao-geral.md) — Entenda o modelo mental do framework
2. [Como Usar → Onboarding](como-usar/README.md) — Setup e primeiro uso
3. [Início Rápido (5 minutos)](como-usar/inicio-rapido.md) — Pipeline completo numa única leitura
4. [Glossário](referencia/glossario.md) — Termos do framework

### 🔨 Quero criar algo
1. [Catálogo de Capacidades](capacidades/README.md) — Encontre a ferramenta certa
2. [Manual de Uso dos Agentes](manual/README.md) — Referência completa com exemplos de chamadas
3. [Fluxos Combinados](fluxos/README.md) — Pipelines de ponta-a-ponta
4. Guias específicos:
   - [Pesquisando tecnologias](como-usar/pesquisando-tecnologias.md)
   - [Criando skills](como-usar/criando-skills.md)
   - [Criando agentes](como-usar/criando-agentes.md)

### ✅ Quero validar qualidade
1. [Validando artefatos](como-usar/validando-artefatos.md)
2. [Fluxo de Qualidade](fluxos/fluxo-qualidade.md)

### 📚 Referência
1. [Convenções](referencia/convencoes.md) — P0-P5, Three-Tier, naming, YAML
2. [Glossário](referencia/glossario.md) — Todos os termos
3. [Mapeamento .github/ ↔ .claude/](referencia/mapeamento-github-claude.md) — Equivalência Copilot vs Claude Code

---

## Mapa Completo

```
docs/
├── visao-geral.md                 ← Arquitetura + diagramas
├── manual/
│   ├── README.md                  ← Índice + cheat sheet de 24 comandos
│   ├── framework-researcher.md    ← 7 comandos de pesquisa
│   ├── skill-author.md            ← 4 comandos de geração
│   ├── architecture-auditor.md    ← 8 comandos de auditoria
│   └── quality-validator.md       ← 5 comandos de validação
├── capacidades/
│   ├── README.md                  ← Catálogo completo
│   ├── skills.md                  ← 2 meta-skills
│   ├── templates.md               ← 14 templates + rastreabilidade
│   ├── prompts-pesquisa.md        ← 7 prompts de pesquisa
│   ├── prompts-compilacao.md      ← 4 prompts de compilação
│   ├── prompts-validacao.md       ← 4 prompts de validação
│   ├── prompts-arquitetura.md     ← 8 prompts de auditoria (4 Copilot + 4 Claude Code)
│   └── prompts-framework.md       ← 1 prompt de ciclo de vida
├── como-usar/
│   ├── README.md                  ← Onboarding rápido
│   ├── inicio-rapido.md           ← Pipeline completo em 3 passos (5 minutos)
│   ├── pesquisando-tecnologias.md
│   ├── criando-skills.md
│   ├── criando-agentes.md
│   └── validando-artefatos.md
├── fluxos/
│   ├── README.md                  ← Mapa geral de fluxos
│   ├── fluxo-criacao-projeto.md
│   ├── fluxo-base-conhecimento.md
│   ├── fluxo-qualidade.md
│   └── fluxo-implementacao.md
└── referencia/
    ├── convencoes.md
    ├── glossario.md
    └── mapeamento-github-claude.md
```
