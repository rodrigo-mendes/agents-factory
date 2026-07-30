# Guia: Criando Skills

Como criar uma SKILL.md que segue todos os padrões do framework.

---

## Quando Usar

- Após pesquisar uma tecnologia (output do researcher)
- Para encapsular conhecimento de domínio específico
- Para fornecer guardrails a agentes

## Passo a Passo

### 1. Tenha a pesquisa pronta

Uma skill precisa de conteúdo validado. Se ainda não tem:
```
/technical-framework-researcher
```
Ver: [Pesquisando Tecnologias](pesquisando-tecnologias.md)

### 2. Execute o skill-creator

```
/skill-creator
```

Forneça o caminho para o documento de pesquisa quando solicitado.

### 3. O que o skill-creator faz internamente

1. Carrega o padrão `authoring-agent-skills/SKILL.md`
2. Lê seu documento de pesquisa
3. Estrutura em three-tier:
   - **✅ Always Do**: Padrões obrigatórios com código completo
   - **⚠️ Ask First**: Decisões arquiteturais (apresenta trade-offs)
   - **🚫 Never Do**: Anti-padrões com alternativa e impacto
4. Gera YAML frontmatter correto
5. Cria blueprints auxiliares

### 4. Resultado esperado

```
skill-name/
├── SKILL.md              ← Skill principal
└── blueprints/
    ├── always-do-patterns.md   ← Padrões com código
    └── never-do-patterns.md    ← Anti-padrões com alternativas
```

### 5. Valide a skill

```
/skill-best-practices-validator
```

### 6. Checklist de qualidade

Antes de considerar pronta, verifique:

- [ ] YAML frontmatter com `name` (≤64 chars, kebab-case)
- [ ] YAML `description` com "Use when..." (≤1024 chars)
- [ ] Seção ✅ Always Do com código de exemplo em TODOS os padrões
- [ ] Seção ⚠️ Ask First com trade-off matrix
- [ ] Seção 🚫 Never Do com alternativa E impacto
- [ ] `blueprints/` com always-do e never-do
- [ ] Versão específica declarada (version absolutism)
- [ ] Nenhuma informação de versão diferente misturada

---

## Compilers Alternativos

Se sua pesquisa é de um domínio específico, use o compiler especializado:

| Domínio da pesquisa | Usar |
|---------------------|------|
| Genérico | `skill-creator` |
| Serviço cloud + Terraform (`technical-framework-researcher-terraform`) | `skill-creator` |
| Arquitetura (C4, DDD, TOGAF) | `architecture-approaches-skill-generator` |
| Metodologias (Scrum, SAFe) | `methodologies-skill-generator` |
| Práticas Terraform (`terraform-engineering-best-practices-researcher`) | `terraform-instructions-compiler` (gera .instructions.md, não SKILL.md) |

---

## Dicas

- **Código obrigatório nos ✅**: Cada "Always Do" DEVE ter um bloco de código funcional. Sem código = skill incompleta.
- **Alternativas nos 🚫**: Cada "Never Do" deve dizer O QUE fazer ao invés. "Não faça X" sem alternativa não ajuda.
- **Progressive disclosure**: Informação básica primeiro, detalhes avançados depois. Não frontload tudo.

## Armadilhas Comuns

| Armadilha | Solução |
|-----------|---------|
| Criar skill sem pesquisa prévia | Sempre pesquisar primeiro — evita alucinações |
| Misturar versões na mesma skill | Uma skill = uma versão. Separar. |
| ✅ sem código | Adicionar bloco de código funcional |
| 🚫 sem alternativa | Sempre incluir "Ao invés, faça Y" |
| Nome genérico ("utils", "helpers") | Usar gerund-form descritivo (ex: `provisioning-oci-functions`) |

## Fluxo Completo

Ver: [Fluxo de Base de Conhecimento](../fluxos/fluxo-base-conhecimento.md)
