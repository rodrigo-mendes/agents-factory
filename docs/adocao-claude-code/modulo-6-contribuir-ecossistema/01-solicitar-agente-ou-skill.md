# Como solicitar um novo subagente ou skill

**Perfil:** Dev / Tech Lead  
**Tempo estimado de leitura:** 6 min

---

## Quando faz sentido solicitar um novo artefato

### Solicite uma nova **skill** quando:

- Sua equipe usa uma tecnologia com frequência e o Claude Code gera código que não segue os padrões BRX para essa tecnologia
- Existe um conjunto de "sempre fazer / nunca fazer" bem definido para uma ferramenta (framework, biblioteca, serviço cloud)
- O mesmo contexto técnico se repete nos prompts de vários desenvolvedores da equipe

Exemplos: skill de Spring Boot na BRX, skill de testes com Testcontainers, skill de tratamento de erros em Lambda.

### Solicite um novo **subagente** quando:

- Há uma tarefa complexa e repetitiva que segue sempre os mesmos passos
- A tarefa exige combinar múltiplos arquivos ou recursos de forma orquestrada
- O valor da automação justifica o tempo de construção (tarefa feita pelo menos 2-3 vezes por semana na equipe)

Exemplos: subagente para criar microsserviços Java com estrutura completa, subagente para gerar módulos Terraform de nova região, subagente para onboarding de novos serviços.

---

## Processo de solicitação

### Passo 1: Documentar o caso de uso

Antes de abrir uma solicitação, documente brevemente:

```markdown
## Solicitação: [Nome descritivo do subagente/skill]

### Tipo
[ ] Skill  [ ] Subagente

### Problema ou tarefa que resolve
[Descrição do problema atual: qual tarefa é, por que é repetitiva, o que dá errado sem o artefato]

### Frequência de uso estimada
[Quantas vezes por semana/mês seria usado e por quantos desenvolvedores]

### Tecnologias/domínio envolvido
[Stack, framework, serviços cloud...]

### Exemplo de prompt típico atual (sem o artefato)
[Como você descreve a tarefa hoje no modo livre, com todo o contexto que precisa explicar]

### Resultado esperado com o artefato
[Como seria invocar o subagente/skill e o que ele deveria produzir]

### Equipe solicitante
[Nome da equipe e Tech Lead de contato]
```

---

### Passo 2: Abrir a solicitação

Abra um issue no repositório `agents-factory` com:
- Título: `[REQUEST] Skill: nome-da-skill` ou `[REQUEST] Subagente: nome-do-subagente`
- Etiqueta: `solicitud-skill` ou `solicitud-agente`
- Conteúdo: o template do Passo 1

---

### Passo 3: Processo de avaliação (Equipe de Governança BRX)

A Equipe de Governança avalia:

1. **Impacto**: quantas equipes/desenvolvedores se beneficiariam?
2. **Viabilidade técnica**: existe base de conhecimento suficiente para criar o artefato com qualidade?
3. **Priorização**: como se encaixa no roadmap do programa?

O resultado pode ser:
- **Aprovado**: a equipe de governança o inclui no backlog com prioridade
- **Aprovado com contribuição**: a equipe solicitante participa da pesquisa/criação sob supervisão da governança
- **Pendente**: a solicitação é válida, mas há pré-requisitos (research, versões estáveis do framework)
- **Rejeitado com alternativa**: a solicitação não se aplica como artefato global, mas se sugere uma alternativa (instruções de contexto do projeto, por exemplo)

---

### Passo 4: Se você puder contribuir com a criação

Se a equipe de governança aprovar e a equipe solicitante quiser participar da criação:

1. Leia os guias técnicos do agents-factory: `docs/como-usar/criando-skills.md` e `docs/como-usar/criando-agentes.md`
2. Use os prompts de pesquisa do agents-factory para gerar a base de conhecimento
3. Trabalhe com a equipe de governança na revisão e validação do artefato

---

## O que não solicitar como artefato global

| Solicitação | Por que não se aplica | Alternativa |
|---|---|---|
| "Um subagente para o meu projeto específico" | Os subagentes globais são para padrões compartilhados | `CLAUDE.md` do projeto (Módulo 4) |
| "Uma skill que faça X de forma diferente de como a skill Y já faz" | Criaria fragmentação | Revisar/atualizar a skill existente |
| "Um subagente que saiba como funciona o nosso domínio de negócio" | O domínio de negócio não é conhecimento global | Instruções de contexto (`CLAUDE.md`) ou documentação da equipe |

---

## Próximos passos

- [6.2 — Ciclo de vida de uma skill](02-ciclo-vida-skill.md)
- [6.3 — Post-mortem de subagente](03-post-mortem-agente.md)
