# Guia Completo: Custom GitHub Copilot Agents

Este documento apresenta os approaches, estruturas e melhores práticas para criar custom GitHub Copilot agents

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Estrutura de Arquivos Essencial](#estrutura-de-arquivos-essencial)
3. [Prompt First Approach](#prompt-first-approach)
4. [Three-Tier Safety Architecture](#three-tier-safety-architecture)
5. [Guidelines por Tipo de Arquivo](#guidelines-por-tipo-de-arquivo)
6. [Workflow Implementation](#workflow-implementation)
7. [Exemplos Práticos](#exemplos-práticos)
8. [Best Practices](#best-practices)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O projeto python-eci demonstra uma abordagem estruturada para criar GitHub Copilot agents especializados que:

- **Priorizam prompts especializados** sobre skills diretas (Prompt First)
- **Implementam arquitetura de segurança** em três níveis
- **Seguem padrões version-specific** para evitar erros
- **Fornecem verificação executável** para garantir qualidade

### Principais Conceitos

| Conceito | Descrição | Benefício |
|----------|-----------|-----------|
| **Prompt First** | Verifica prompts especializados antes de usar skills | Maior precisão e padronização |
| **Three-Tier Safety** | ✅ Always Do, ⚠️ Ask First, 🚫 Never Do | Prevenção de erros e vulnerabilidades |
| **Version Lock** | Skills específicos para versões exatas | Evita padrões obsoletos |
| **Executable Verification** | Comandos exatos para validação | Garantia de qualidade |

---

## 🏗️ Estrutura de Arquivos Essencial

### Diretório Base
```
project/
├── .github/
│   ├── agents/           # Definições principais dos agents
│   ├── instructions/     # Regras e integração de skills
│   ├── prompts/         # Prompts especializados por domínio
│   └── skills/          # Skills técnicos version-specific
└── frameworks-research/ # Documentação de tecnologias
```

### 1. Agent Definition (`.github/agents/`)

**Arquivo**: `[agent-name].agent.md`

**Propósito**: Definição principal do agent com metadados e comportamento

**Template**:
```yaml
---
name: python-eci
description: Custom GitHub Copilot agent for generating specification-compliant Python projects that follow ECI standards, skills, and best practices
tools: ['read', 'edit', 'search', 'execute']
metadata:
  version: "1.0.0"
  maintainer: "ECI Development Team"
  specialization: "Python Development"
  frameworks: ["FastAPI", "Pydantic", "Pytest", "JWT", "PostgreSQL", "Kafka"]
  compatibility: ["VSCode", "GitHub Copilot", "IntelliJ IDEA", "Eclipse"]
  last_updated: "2026-02-18"
---

You are a [Specialization] specialist focused on [main purpose].

## ⚠️ CRITICAL: Always Check for Prompts First!
**BEFORE doing anything else, check user request for these keywords:**

- **Domain1**: "keyword1", "keyword2" → Use `/agent-domain1`
- **Domain2**: "keyword3", "keyword4" → Use `/agent-domain2`

**If keywords match → Use corresponding prompt immediately. Show available options first.**
```

### 2. Instructions (`.github/instructions/`)

#### Skills Integration (`[agent-name]-skills.instructions.md`)
**Propósito**: Integração com skills e prompts especializados

**Estrutura**:
```markdown
---
name: [agent-name]-skills
description: Integrates ECI skills for modern development
applyTo: "**/*.py"
---

## ⚠️ IMPORTANT: Check Prompts First!
**BEFORE loading any skills or generating code, ALWAYS check for specialized prompts:**

1. **Domain1 keywords** → Use `/agent-domain1`
2. **Domain2 keywords** → Use `/agent-domain2`

**If ANY keywords match → IMMEDIATELY suggest the corresponding prompt.**
```

#### Standards (`[agent-name]-standards.instructions.md`)
**Propósito**: Garantia de qualidade e execução

**Estrutura**:
```markdown
---
name: [agent-name]-standards
description: Ensures projects follow execution readiness standards
applyTo: "**"
---

## Project Readiness Standards
Always verify these core requirements:
1. **Code Execution**: All code must execute successfully
2. **Dependencies**: All packages must be installable with exact versions
3. **Testing**: Tests must pass
4. **Environment**: Proper setup with .env.example
5. **Documentation**: Clear instructions for running the project
```

### 3. Prompts Especializados (`.github/prompts/`)

**Arquivo**: `[agent-name]-[domain].prompt.md`

**Propósito**: Prompts especializados por domínio técnico

**Template**:
```yaml
---
name: [agent-name]-[domain]
description: 'Create secure [domain] systems with patterns and integration for [applications].'
agent: [agent-name]
tools: ['read', 'edit', 'search', 'execute', 'github/*']
argument-hint: 'Choose [domain] pattern: [option1], [option2], or [option3]'
---

# [Domain] Prompt

## Role
You are a [Domain] Specialist. Your expertise is implementing [specific expertise].

---

## Skills Required

**MANDATORY**: Before generating any code, load:

### Primary Skill
- `.github/skills/[primary-skill]/SKILL.md` - [Primary skill description]

### Load Conditionally
- [Integration condition]? → Load `.github/skills/[integration-skill]/SKILL.md`

---

## Trigger Keywords

Use this prompt when user mentions:
- "keyword1"
- "keyword2"
- "keyword3"
```

### 4. Skills (`.github/skills/`)

**Estrutura**:
```
.github/skills/[skill-name]/
└── SKILL.md
```

**Regras de Nomenclatura**:
- Nome da pasta = campo `name` do YAML = `lowercase-kebab-case`
- Filename exatamente: `SKILL.md` (case-sensitive)
- Exemplos válidos:
  - ✅ `.github/skills/fastapi-web-framework/` → `name: fastapi-web-framework`
  - ✅ `.github/skills/psycopg-postgresql/` → `name: psycopg-postgresql`

---

## 🎯 Prompt First Approach

### Estratégia Principal

O **Prompt First Approach** é a principal estratégia do projeto:

1. **Keywords Detection**: Verifica palavras-chave na requisição do usuário
2. **Prompt Recommendation**: Sugere prompts especializados automaticamente
3. **Direct Usage**: Usa o prompt sugerido sem pedir permissão

### Keyword Mapping Example

```markdown
- **Authentication**: "auth", "JWT", "login", "token" → `/python-eci-auth`
- **Database**: "database", "PostgreSQL", "SQL", "query" → `/python-eci-database`
- **API**: "API", "endpoint", "REST", "FastAPI" → `/python-eci-web-api`
- **Testing**: "test", "pytest", "testing", "coverage" → `/python-eci-testing`
- **Events**: "Kafka", "event", "stream", "message" → `/python-eci-kafka`
```

### Prompt Recommendation Flow

```markdown
User: "I need JWT authentication for my API"

Agent: "I found specialized prompts that can help with JWT authentication:

**Available Prompts:**
- `/python-eci-auth` - JWT authentication systems with security patterns

**Recommended:** `/python-eci-auth stateless`
This provides structured JWT implementation with ECI security patterns and ensures compliance.

Using authentication prompt..."
```

### Decision Framework

1. **Identify keywords** que triggeram prompts especializados
2. **Check for compliance requirements** - se compliance estrita é necessária, usar prompts
3. **Evaluate complexity** - código complexo favorece prompts
4. **Consider repeatability** - padrões reutilizáveis devem usar prompts
5. **Default to semantic** para tarefas simples e únicas

---

## 🛡️ Three-Tier Safety Architecture

### ✅ Tier 1: Always Do (Mandatory Patterns)

Padrões não negociáveis que devem ser sempre seguidos:

**Estrutura**:
```markdown
### ✅ Always Do

**[Pattern Name]**: [Reason for being mandatory]

```python
# ✅ CORRECT: Comment explaining WHY each line is critical
# [Version-specific context]
[minimum functional code]
```
**Why it is mandatory**: [Reason from official documentation]
**Failure if omitted**: [Actual consequence]
**Source**: [Deep link to official docs]
```

**Exemplo Real**:
```markdown
### ✅ Always Do

**Async Context Manager**: Mandatory for correct connection management in FastAPI v0.100+

```python
# ✅ CORRECT: Ensures cleanup even with exceptions
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initializes connection pool
    await db.connect()
    yield
    # Shutdown: guaranteed cleanup
    await db.disconnect()

app = FastAPI(lifespan=lifespan)
```

**Why it's mandatory**: FastAPI v0.100 deprecated startup/shutdown events in favor of lifespan
**Fails if omitted**: Connections are not closed, causing resource leak
**Source**: https://fastapi.tiangolo.com/advanced/events/#lifespan
```

### ⚠️ Tier 2: Ask First (Architectural Crossroads)

Decisões que requerem input do usuário devido a tradeoffs:

**Estrutura**:
```markdown
### ⚠️ Ask First

**Decision Point**: [What needs user choice]

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| A | [benefit] | [cost] | [specific scenario] |
| B | [benefit] | [cost] | [specific scenario] |
| C | [benefit] | [cost] | [specific scenario] |

**Agent Behavior**: 
"Before implementing, ask the user:
'[Specific question with context necessary for informed decision]'"

**Decision Factors**:
- [Factor 1: e.g., expected request volume]
- [Factor 2: e.g., latency requirements]
- [Factor 3: e.g., budget/infrastructure cost]

**Source**: [Link]
```

### 🚫 Tier 3: Never Do (Anti-Patterns)

Padrões proibidos que devem ser evitados:

**Estrutura**:
```markdown
### 🚫 Never Do

**Anti-Pattern**: [What NOT to do]

```python
# 🚫 WRONG: [Specific explanation of the problem]
# [Context of the version where this fails]
[bad code]

# ✅ RIGHT: [Why this approach is safe]
# [Version where it was introduced/recommended]
[good code]
```

**Why it is prohibited**: [Reason for security/stability/performance]
**Actual impact**: [What breaks in production]
**Introduced in**: [Version where pattern was deprecated]
**Source**: [Link to official notice/CVE/changelog]
```

---

## 📋 Guidelines por Tipo de Arquivo

### Agent Files (`.agent.md`)

**Componentes Obrigatórios**:
- **Metadados YAML**: name, description, tools, metadata
- **Keyword Mapping**: Seção com triggers para prompts especializados
- **Prompt Hierarchy**: Regras para preferir prompts sobre skills diretas
- **Verification Checklist**: Checklist de qualidade

**Best Practices**:
```markdown
## ⚠️ CRITICAL: Always Check for Prompts First!
**BEFORE doing anything else, check user request for these keywords:**

- **Testing**: "test", "pytest", "testing", "coverage", "fixture", "mock" → Use `/python-eci-testing`
- **Authentication**: "auth", "JWT", "login", "token" → Use `/python-eci-auth`

**If keywords match → Use corresponding prompt immediately. Show available options first.**
```

### Instruction Files (`.instructions.md`)

#### Skills Integration
**Componentes**:
- **Prompt-first rules**: Regras explícitas para verificar prompts primeiro
- **Skill mapping**: Mapeamento de keywords para skills específicas
- **Cross-cutting rules**: Regras aplicáveis a todos os skills
- **Verification commands**: Comandos de verificação padronizados

#### Standards
**Componentes**:
- **Project readiness standards**: Requisitos obrigatórios
- **Dependency management rules**: Regras para gerenciamento de dependências
- **Testing requirements**: Requisitos de teste
- **Code quality standards**: Padrões de qualidade de código

### Prompt Files (`.prompt.md`)

**Componentes**:
- **Role definition**: Papel especializado do prompt
- **Required skills**: Skills obrigatórios e condicionais
- **Trigger keywords**: Palavras-chave que ativam o prompt
- **Workflow steps**: Passos estruturados de execução
- **Integration patterns**: Padrões de integração

### Skill Files (`SKILL.md`)

**Componentes Obrigatórios**:
- **Version Context**: Informações específicas da versão
- **Three-tier architecture**: ✅⚠️🚫 bem definidos
- **Verification loop**: Comandos exatos de verificação
- **Integration patterns**: Exemplos completos de integração

**Version Context Template**:
```markdown
## Version Context

**Technology**: [Official Name]
**Target Version**: v[X.Y.Z]
**Release Date**: [DD/MM/YYYY]
**Support Status**: [Active LTS / Maintenance / EOL on DATE]

**Breaking Changes in this version**:
- [Change 1 and impact]
- [Change 2 and impact]

⚠️ **CRITICAL - Agent Warning**: 
This skill is version-specific to v[X.Y.Z]. 
Reject ANY patterns from other versions.
```

---

## 🔧 Workflow Implementation

### 1. Research Phase

**Ferramenta**: `technical-framework-researcher.md`

**Processo**:
1. **Source Priority**: Official docs > Blog > GitHub > Community
2. **Version Absolutism**: Apenas versões específicas
3. **Safety First**: Priorizar anti-padrões de segurança
4. **Executable Truth**: Cada claim deve linkar para documentação

**Output**: `research_[tech]_v[version].md`

### 2. Skill Creation

**Ferramenta**: `skill-author-specialist.md`

**Processo**:
1. **Transform research** para manuais executáveis
2. **Apply three-tier safety architecture**
3. **Create version-specific patterns**
4. **Add verification loops**

**Output**: `.github/skills/[skill-name]/SKILL.md`

### 3. Agent Integration

**Processo**:
1. **Keyword mapping** no agent file
2. **Prompt creation** para cada domínio
3. **Instruction setup** para integração
4. **Testing e validation**

---

## 💡 Exemplos Práticos

### Exemplo 1: Criar Agent para Node.js

#### 1. Agent Definition
```yaml
---
name: nodejs-eci
description: Custom GitHub Copilot agent for Node.js projects following ECI standards
tools: ['read', 'edit', 'search', 'execute']
metadata:
  version: "1.0.0"
  maintainer: "Node.js Team"
  specialization: "Node.js Development"
  frameworks: ["Express", "Jest", "TypeScript", "JWT", "MongoDB"]
  compatibility: ["VSCode", "GitHub Copilot"]
  last_updated: "2026-02-18"
---
```

#### 2. Keyword Mapping
```markdown
- **Authentication**: "auth", "JWT", "login", "token" → Use `/nodejs-eci-auth`
- **Database**: "database", "MongoDB", "query" → Use `/nodejs-eci-database`
- **API**: "API", "endpoint", "REST", "Express" → Use `/nodejs-eci-web-api`
- **Testing**: "test", "Jest", "testing" → Use `/nodejs-eci-testing`
```

#### 3. Skill Creation
```
.github/skills/express-web-framework/SKILL.md
.github/skills/jest-testing-framework/SKILL.md
.github/skills/jsonwebtoken-auth/SKILL.md
```

### Exemplo 2: Prompt Especializado

```yaml
---
name: nodejs-eci-auth
description: 'Create secure JWT authentication systems for Node.js Express applications'
agent: nodejs-eci
tools: ['read', 'edit', 'search', 'execute', 'github/*']
argument-hint: 'Choose authentication pattern: stateless, refresh-tokens, or session-based'
---
```

---

## 🎯 Best Practices

### 1. Version Management
- **Sempre especifique versões exatas** nos skills
- **Use warnings críticos** para version-specific patterns
- **Mantenha changelog** de breaking changes

### 2. Security First
- **Prioritize anti-patterns de segurança** no Tier 3
- **Inclua verification commands** de segurança
- **Documente CVEs** e vulnerabilidades conhecidas

### 3. Quality Assurance
- **Forneça comandos exatos** para verificação
- **Inclua expected outputs** e exit codes
- **Crie troubleshooting sections**

### 4. Documentation
- **Use deep links** para documentação oficial
- **Inclua exemplos copy-paste funcionais**
- **Mantenha source bibliography** atualizada

### 5. Integration Patterns
- **Documente integrações completas** entre tecnologias
- **Inclua configuration examples**
- **Adicione common issues e solutions**

---

## 🔧 Troubleshooting

### Common Issues

| Problema                  | Causa                            | Solução                      |
|---------------------------|----------------------------------|------------------------------|
| **Skills não carregam**   | Nome da pasta diferente do YAML  | Verifique nomenclatura exata |
| **Prompts não triggeram** | Keywords mapeadas incorretamente | Revise keyword mapping       |
| **Verificação falha**     | Comandos incorretos ou faltando  | Teste comandos manualmente   |
| **Version conflicts**     | Múltiplas versões em conflito    | Use version lock explícito   |

### Debug Commands

```bash
# 1. Verificar estrutura de skills
find .github/skills -name "SKILL.md" -exec echo "=== {} ===" \; -exec head -n 10 {} \;

# 2. Validar YAML frontmatter
grep -l "^name:" .github/skills/*/SKILL.md

# 3. Testar keyword mapping
grep -r "keyword" .github/prompts/

# 4. Verificar links
grep -n "](http" .github/skills/*/SKILL.md
```

### Quality Checklist

- [ ] **Nomenclatura**: Folder = YAML name = kebab-case
- [ ] **Trigger**: Description começa com "Use this when..."
- [ ] **Three Levels**: ✅⚠️🚫 todos presentes
- [ ] **Version**: Mencionado 3+ vezes no documento
- [ ] **Code**: Mínimo 2 exemplos funcionais
- [ ] **Verification**: Comandos CLI presentes e testados
- [ ] **Links**: Todos testados, sem 404s
- [ ] **Paths**: Apenas relativos ou URLs, sem absolutos

---

## 📚 Referências

### Documentação Oficial
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/building-copilot-extensions/building-a-copilot-agent-for-your-copilot-extension/about-agent-skills)
- [GitHub Copilot Extensions](https://docs.github.com/en/copilot/building-copilot-extensions)

### Templates e Workflows
- [Technical Research Protocol](../../.windsurf/workflows/technical-framework-researcher.md)
- [Skill Author Specialist](../../.windsurf/skills/skill-author-specialist/SKILL.md)

---

## 🚀 Conclusão

Este guia demonstra como criar custom GitHub Copilot agents robustos e seguros usando:

1. **Prompt First Approach** para maior precisão
2. **Three-Tier Safety Architecture** para prevenir erros
3. **Version-Specific Patterns** para evitar obsolescência
4. **Executable Verification** para garantir qualidade
5. **Structured Integration** para padronização

Seguindo estas guidelines, você pode criar agents especializados que seguem padrões consistentes, previnem erros comuns e fornecem resultados de alta qualidade para domínios específicos de desenvolvimento.
