# Prompts de Compilação

4 prompts que transformam documentos de pesquisa em artefatos operacionais (SKILL.md ou .instructions.md).

Todos seguem o padrão do `TEMPLATE.GENERATOR.prompt.md`.

---

## Visão Geral

| Prompt | Input | Output | Domínio |
|--------|-------|--------|---------|
| `skill-creator` | Qualquer pesquisa | SKILL.md | Genérico |
| `terraform-instructions-compiler` | Pesquisa Terraform | .instructions.md (múltiplos) | Terraform |
| `archtecture-approches-skill-generator` | Pesquisa de arquitetura | SKILL.md | Arquitetura |
| `methodologies-skill-generator` | Pesquisa de metodologia | SKILL.md | Metodologias |

---

## 1. skill-creator

> **Arquivo**: `.github/prompts/skill-creator.prompt.md`

### Descrição
Orquestra a geração de uma SKILL.md a partir de qualquer documento de pesquisa, aplicando o padrão `authoring-agent-skills`.

### Invocação
```
@workspace /skill-creator
```

### Workflow Interno
1. Carrega padrão `authoring-agent-skills/SKILL.md`
2. Lê documento de pesquisa fornecido
3. Aplica three-tier architecture (✅⚠️🚫)
4. Gera SKILL.md com YAML frontmatter correto
5. Cria `blueprints/` com always-do e never-do patterns

### Input Esperado
- Caminho para documento de pesquisa (output de qualquer researcher)

### Output Produzido
```
skill-name/
├── SKILL.md
└── blueprints/
    ├── always-do-patterns.md
    └── never-do-patterns.md
```

### Dependências
- Skill: `authoring-agent-skills` (padrão de estrutura)
- Template: `TEMPLATE.SKILL.md` (referência implícita)

### Complementa
- Todos os 7 prompts de pesquisa (recebe output deles)
- `skill-best-practices-validator` (valida o output)

---

## 2. terraform-instructions-compiler

> **Arquivo**: `.github/prompts/terraform-instructions-compiler.prompt.md`

### Descrição
Compilador interativo que extrai best practices de pesquisa Terraform e gera múltiplos arquivos .instructions.md categorizados.

### Invocação
```
@workspace /terraform-instructions-compiler
```

### Workflow Interno
1. **Fase 1.1**: Lê documento de pesquisa Terraform
2. **Fase 1.2**: Carrega templates de referência:
   - `TEMPLATE.STANDARDS.instructions.md` (L54)
   - `TEMPLATE.CONFIG.instructions.md` (L55)
   - `TEMPLATE.SKILLS.instructions.md` (L56)
3. **Fase 2**: Entrevista interativa (quais aspectos incluir)
4. **Fase 3**: Planejamento (quais arquivos gerar)
5. **Fase 4**: Geração dos .instructions.md

### Input Esperado
- Documento de pesquisa de `terraform-engineering-best-practices-researcher` ou `technical-framework-researcher-terraform`

### Output Produzido
```
.github/instructions/
├── terraform-config.instructions.md      ← Setup, backend, providers
├── terraform-standards.instructions.md   ← Naming, modules, structure
└── terraform-skills.instructions.md      ← Keyword → skill routing table
```

### Dependências
- Templates: `TEMPLATE.CONFIG.instructions.md`, `TEMPLATE.STANDARDS.instructions.md`, `TEMPLATE.SKILLS.instructions.md` (**referência explícita**)

### Complementa
- `terraform-engineering-best-practices-researcher` (input principal)
- `technical-framework-researcher-terraform` (input alternativo)
- `instructions-best-practices-validator` (valida output)

---

## 3. archtecture-approches-skill-generator

> **Arquivo**: `.github/prompts/archtecture-approches-skill-generator.prompt.md`

### Descrição
Gera SKILL.md a partir de pesquisa de metodologia de arquitetura, aplicando o padrão three-tier com foco em decisões arquiteturais.

### Invocação
```
@workspace /archtecture-approches-skill-generator
```

### Workflow Interno
1. Carrega padrão `authoring-agent-skills/SKILL.md`
2. Lê pesquisa de metodologia de arquitetura
3. Identifica decisões arquiteturais → mapeia para ⚠️ Ask First
4. Identifica padrões obrigatórios → mapeia para ✅ Always Do
5. Identifica anti-padrões → mapeia para 🚫 Never Do
6. Gera SKILL.md versionada

### Input Esperado
- Documento de pesquisa de `architecture-methodology-researcher`

### Output Produzido
- `SKILL.md` com decisões arquiteturais estruturadas em three-tier

### Dependências
- Skill: `authoring-agent-skills` (padrão de estrutura)

### Complementa
- `architecture-methodology-researcher` (input)
- `skill-best-practices-validator` (valida output)

---

## 4. methodologies-skill-generator

> **Arquivo**: `.github/prompts/methodologies-skill-generator.prompt.md`

### Descrição
Gera SKILL.md a partir de pesquisa de metodologia de engenharia/requisitos, estruturando práticas em three-tier.

### Invocação
```
@workspace /methodologies-skill-generator
```

### Workflow Interno
1. Carrega padrão `authoring-agent-skills/SKILL.md`
2. Lê pesquisa de metodologia
3. Estrutura práticas obrigatórias, opcionais e proibidas
4. Gera SKILL.md com exemplos de aplicação

### Input Esperado
- Documento de pesquisa de `requirements-methodology-researcher`

### Output Produzido
- `SKILL.md` com práticas de metodologia em three-tier

### Dependências
- Skill: `authoring-agent-skills` (padrão de estrutura)

### Complementa
- `requirements-methodology-researcher` (input)
- `skill-best-practices-validator` (valida output)

---

## Matriz de Compatibilidade: Researcher → Compiler

| Researcher | Compiler Recomendado |
|-----------|---------------------|
| `technical-framework-researcher` | `skill-creator` |
| `technical-framework-researcher-terraform` | `terraform-instructions-compiler` |
| `terraform-engineering-best-practices-researcher` | `terraform-instructions-compiler` |
| `architecture-methodology-researcher` | `archtecture-approches-skill-generator` |
| `cloud-architecture-researcher` | `skill-creator` |
| `business-domain-researcher` | `skill-creator` |
| `requirements-methodology-researcher` | `methodologies-skill-generator` |
