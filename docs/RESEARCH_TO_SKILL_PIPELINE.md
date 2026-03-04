# Pipeline: Research → Skill Architecture

Este documento descreve como o novo skill **technical-framework-researcher** e o existente **skill-author-specialist** trabalham juntos para criar skills completos.

---

## 🔄 Pipeline End-to-End

```
┌─────────────────────────────────────────────────────────────────┐
│ USER: "Preciso de um skill para Terraform + AWS RDS"            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ SKILL #1: technical-framework-researcher                         │
│ ────────────────────────────────────────────────────────────────│
│ Input:                                                            │
│  - CLOUD_PROVIDER: "AWS"                                        │
│  - SERVICE_NAME: "RDS PostgreSQL"                               │
│  - TERRAFORM_VERSION: "1.7"                                     │
│  - PROVIDER_VERSION: "aws v5.x"                                 │
│  - INTEGRATION_PARTNERS_LIST: "VPC, Secrets Manager, IAM"       │
│                                                                  │
│ Executa:                                                         │
│  1. Validate inputs specificity                                 │
│  2. Map official documentation sources                          │
│  3. Extract patterns (✅ Mandatory, ⚠️ Conditional, 🚫 Forbidden)│
│  4. Create working code examples (version-tagged)               │
│  5. Document integrations + verification commands              │
│  6. Source bibliography (all dated)                             │
│                                                                  │
│ Output: research_AWS_RDS_PostgreSQL_v5.x.md                    │
│        (20-30 pages, highly detailed)                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ SKILL #2: skill-author-specialist                                │
│ ────────────────────────────────────────────────────────────────│
│ Input: research_AWS_RDS_PostgreSQL_v5.x.md                      │
│                                                                  │
│ Transforms:                                                      │
│  1. ✅ Mandatory → "✅ Always Do"                                │
│  2. ⚠️ Conditional → "⚠️ Ask First"                              │
│  3. 🚫 Forbidden → "🚫 Never Do"                                 │
│  4. Add Version Context section                                 │
│  5. Add Verification Loop section                               │
│  6. Add Integration Patterns section                            │
│                                                                  │
│ Output: .github/skills/terraform-aws-rds/SKILL.md              │
│        (5-10 pages, actionable)                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESULT: Copilot Can Now Execute                                 │
│ ────────────────────────────────────────────────────────────────│
│ User: "@github create RDS setup using terraform-aws-rds skill"  │
│                                                                  │
│ Copilot generates:                                              │
│  - main.tf (resources)                                          │
│  - variables.tf (inputs)                                        │
│  - outputs.tf (exports)                                         │
│  - terraform.tfvars (example values)                            │
│  - README.md (deployment guide)                                 │
│                                                                  │
│ All with:                                                        │
│  ✅ Mandatory patterns enforced                                  │
│  ⚠️ Architectural decisions validated                            │
│  🚫 Security anti-patterns prevented                             │
│  📋 Verification commands included                               │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📊 Comparação: Skills vs Roles

| Aspecto       | Researcher               | Author              | Resultado        |
|---------------|--------------------------|---------------------|------------------|
| **Input**     | Tech + Version           | Research doc        | User request     |
| **Foco**      | Validação + Conhecimento | Estrutura + Clarity | Execução         |
| **Tempo**     | 4-6 horas (meticuloso)   | 30 mins-1 hora      | Parallelizável   |
| **Output**    | 20-30 páginas            | 5-10 páginas        | Skill executável |
| **Qualidade** | Fonte-validada           | Formato-validado    | Trustworthy      |
| **Sequência** | 1º (upstream)            | 2º (downstream)     | Dependente       |

---

## 🔀 Quando Usar Cada Skill

### Cenário A: Novo Skill Completo
```
1. NÃO existe research document
2. Executar: Technical Framework Researcher
   → Gera: research_[TECH]_v[VERSION].md
3. Executar: Skill Author Specialist
   → Gera: .github/skills/[name]/SKILL.md
```

**Exemplo**:
```bash
# Semana 1: Pesquisa
@github research AWS RDS PostgreSQL v15 with Terraform v1.7
# Output: research_AWS_RDS_PostgreSQL_v15_terraform_v1.7.md

# Semana 2: Skill
@github create skill from research_AWS_RDS_PostgreSQL_v15_terraform_v1.7.md
# Output: .github/skills/terraform-aws-rds/SKILL.md
```

### Cenário B: Skill Já Existe
```
⏭️ SKIP Technical Framework Researcher
✅ Usar: Skill Author Specialist (se updating format)
   OU Use skill diretamente (se já atual)
```

### Cenário C: Atualizar Skill Existente
```
1. Nova versão saiu (FastAPI v0.101)
2. Executar: Technical Framework Researcher (ONLY v0.101 diff)
   → Gera: research_FastAPI_v0.101_BREAKING_CHANGES.md
3. Update: skill-author-specialist ONLY migration section
   → Merge: Existing SKILL + new patterns
```

---

## 📋 Dados Fluem Entre Skills

### Research Document (Intermediário)
```markdown
research_AWS_RDS_PostgreSQL_v5.x.md

┌─ Metadata
│  ├─ Full_Name
│  ├─ Target_Version
│  └─ Support_Status
│
├─ Executive Summary
│
├─ Architectural Guardrails
│  ├─ ✅ Mandatory Patterns
│  │  ├─ Pattern 1 + Code + Why + Source
│  │  └─ Pattern 2 + Code + Why + Source
│  ├─ ⚠️ Conditional Patterns
│  │  ├─ Decision 1 + Options + Tradeoffs + Source
│  │  └─ Decision 2 + Options + Tradeoffs + Source
│  └─ 🚫 Forbidden Patterns
│     ├─ Anti-pattern 1 + Code DON'T/DO + Why + Source
│     └─ Anti-pattern 2 + Code DON'T/DO + Why + Source
│
├─ Implementation Blueprint
│  ├─ Lifecycle code
│  └─ Integration examples
│
├─ Quality Control
│  ├─ Verification Commands (with expected outputs)
│  └─ Testing/Mocking patterns
│
└─ Source Bibliography (all dated)
```

### Skill Document (Output)
```markdown
.github/skills/terraform-aws-rds/SKILL.md

┌─ Metadata (nested in YAML front matter)
│  ├─ name: terraform-aws-rds
│  └─ description: Use this when user needs to...
│
├─ Role & Version Context
│
├─ ✅ Always Do (from Mandatory Patterns)
├─ ⚠️ Ask First (from Conditional Patterns)
├─ 🚫 Never Do (from Forbidden Patterns)
│
├─ Integration Patterns
├─ Verification Loop
│
└─ External Resources
```

### Mapping Automático

```
Research → Skill (Direct Transformation)

research_[TECH]_v[VERSION].md
├─ Mandatory Patterns → ✅ Always Do
├─ Conditional Patterns → ⚠️ Ask First
├─ Forbidden Patterns → 🚫 Never Do
├─ Verification Commands → Verification Loop
├─ Metadata.Version → Version Context
├─ Integrations → Integration Patterns
└─ Bibliography → External Resources
```

---

## ⏱️ Cronograma Típico

### Opção 1: Sequencial (Mais Seguro)
```
Semana 1: Technical Framework Researcher
  Mon-Wed: Deep research (20+ hours)
  Thu: Review + validation (2 hours)
  Output: research_[TECH]_v[VERSION].md

Semana 2: Skill Author Specialist
  Mon: Transform research → skill (4 hours)
  Tue: Review + testing (2 hours)
  Output: .github/skills/[name]/SKILL.md

Total: 28+ hours, 2 semanas, altíssima qualidade
```

### Opção 2: Paralelizado (Mais Rápido)
```
Dia 1: Start Technical Framework Researcher (background)
Dia 2: While researcher works...
       Skill Author preps templates, examples

Dia 3-4: Researcher finaliza → Author transforma (same day)

Total: 18-20 hours, 4 dias, qualidade ainda alta
```

### Opção 3: Reuso (Mais Eficiente)
```
Skill já existe: terraform-aws-rds SKILL.md
Nova versão saiu: aws provider v5.50

Dia 1: Research ONLY breaking changes
       research_AWS_Provider_v5.50_DIFF.md (3-5 pages)

Dia 2: Author patches existing SKILL.md
       Merge new patterns, update version context

Total: 8-10 hours, 2 dias, manutenção apenas
```

---

## 🛡️ Quality Gates

### After Research (Before Authoring)
```
Checklist antes de passar para Skill Author:
- [ ] Todos os inputs foram específicos (não genéricos)?
- [ ] 3+ código examples totais?
- [ ] Cada claim tem source com data?
- [ ] Anti-patterns tem alternativas (DO version)?
- [ ] Versão mencionada 5+ vezes?
- [ ] CLI commands incluem output esperado?
- [ ] Nenhuma fonte >12 meses?
- [ ] 20+ páginas de conteúdo (não resumido)?

Se ✅ all: OK para Skill Author
Se ❌ qualquer um: Volta para Research refinar
```

### After Authoring (Before Publishing)
```
Checklist antes de publicar SKILL.md:
- [ ] Nome folder = YAML name = kebab-case?
- [ ] Description começa com "Use this when user needs..."?
- [ ] ✅ ⚠️ 🚫 todos presentes com conteúdo?
- [ ] Versão locked em 3+ places?
- [ ] Verification Loop CLI commands testados?
- [ ] Links testados (no 404s)?
- [ ] Paths relativos ou URLs (no absolutos)?
- [ ] 1+ exemplo copy-paste-run testado?

Se ✅ all: Publicar SKILL.md
Se ❌ qualquer um: Volta para Author refinar
```

---

## 📚 Exemplos de Skills Criados com Este Pipeline

### Exemplo 1: FastAPI Async
```
1️⃣ Research: research_FastAPI_v0.100.md (25 pages)
   - Lifespan context manager (new in 0.100)
   - Async/await patterns
   - WebSocket + SSE
   - Testing patterns
   
2️⃣ Skill: .github/skills/fastapi-async/SKILL.md (8 pages)
   - Always Do: lifespan context
   - Ask First: connection pooling strategy
   - Never Do: blocking sync in async
   - Verification: CLI commands
   
3️⃣ Copilot executes:
   @github build async FastAPI API with fastapi-async
   → Generates complete async API with lifespan, error handling
```

### Exemplo 2: Terraform AWS RDS
```
1️⃣ Research: research_AWS_RDS_PostgreSQL_v5.x.md (28 pages)
   - Terraform block + backends
   - RDS resource + module patterns
   - Security (encryption, IAM)
   - Integrations (VPC, Secrets Manager)
   
2️⃣ Skill: .github/skills/terraform-aws-rds/SKILL.md (7 pages)
   - Always Do: terraform block, encryption
   - Ask First: local vs S3 backend
   - Never Do: hardcoded credentials, public RDS
   - Verification: terraform validate, tfsec, plan
   
3️⃣ Copilot executes:
   @github provision RDS using terraform-aws-rds
   → Generates .tf files with all security patterns
```

---

## 🔗 Arquivos Relacionados

### Prompts
- [Technical Framework Researcher - Generic](../../agents-factory/prompts/technical-framework-researcher.prompt.md)
- [Technical Framework Researcher - Terraform](../../agents-factory/prompts/technical-framework-researcher-terraform.prompt.md)

### Skills
- [Technical Framework Researcher Skill](../skills/technical-framework-researcher/SKILL.md)
- [Skill Author Specialist](../../.github/skills/skill-author-specialist/SKILL.md)

### Templates
- [Skill Template](../../agents-factory/templates/skills/TEMPLATE.SKILL.md)
- [Research Template](../../agents-factory/templates/TEMPLATE.RESEARCH.md) - _não existe ainda_

### Documentação
- [Terraform Skill Creation Guide](../../agents-factory/docs/TERRAFORM_SKILL_CREATION_GUIDE.md)

---

## 📞 FAQ

**P: Preciso de ambos os skills?**
R: Sim. Researcher valida knowledge, Author estrutura para Copilot.

**P: Posso pular o Research?**
R: Não. Research garante hallucination-proof content. Author sem Research → skills incorretos.

**P: Qual é mais importante?**
R: Researcher (80% da qualidade). Author (20% da estrutura).

**P: Posso paralelizar?**
R: Parcialmente. Author pode começar templates enquanto Researcher trabalha, mas merging só após Research finalizar.

**P: Quanto tempo leva?**
R: Researcher: 4-6h. Author: 1-2h. Total: 5-8h por skill novo.

**P: E atualizações?**
R: Se versão changed: Research diffs (~2h) → Author patches (~30min).

---

**Próximo passo**: Use o **technical-framework-researcher SKILL** para iniciar pesquisa de nova tecnologia!
