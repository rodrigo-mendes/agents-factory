# Skills globais vs instruções de projeto

**Perfil:** Tech Lead  
**Tempo estimado de leitura:** 5 min

---

## Em que se diferenciam

| | Instruções de projeto | Skills globais BRX |
|---|---|---|
| **Quem cria** | Tech Lead da equipe | Equipe de Governança BRX |
| **Onde vivem** | `CLAUDE.md` do repositório | `.claude/skills/` no agents-factory |
| **Alcance** | Um projeto concreto | Toda a organização BRX |
| **Profundidade** | Convenções operacionais (curto, prático) | Padrões técnicos profundos (✅⚠️🚫 com exemplos de código) |
| **Quem as ativa** | O Claude Code carrega automaticamente ao abrir o projeto | Os agentes as carregam; os devs podem referenciá-las |
| **O que cobrem** | Naming, estrutura do projeto, quais bibliotecas usar | Como usar uma tecnologia corretamente segundo os padrões BRX |

---

## A regra para evitar duplicação

> **Instruções de projeto:** o *o quê* do seu projeto (quais versões, quais bibliotecas, qual naming).  
> **Skills globais:** o *como* de uma tecnologia (como se usa Lambda na BRX, como se estrutura Terraform na BRX).

Se uma convenção se aplica a toda a organização e é tecnicamente profunda → deve ser uma skill global.  
Se uma convenção se aplica apenas ao seu projeto e é operacional → vai no `CLAUDE.md` do projeto.

---

## Exemplos concretos

### O que vai nas instruções de projeto (`CLAUDE.md`)

```markdown
## Stack
- Java 17, Spring Boot 3.2
- DynamoDB com AWS SDK v2

## Estrutura de pacotes
com.brx.orders.{layer}

## Naming
- Serviços: sufixo `Service`
- Repositórios: `DynamoDb{Nome}Repository` para implementações
```

Isso é específico do projeto `orders-service`.

---

### O que vai em uma skill global

Uma skill de `java-spring-lambda-brx` (hipotética) conteria:

```
✅ Always Do:
- Use Spring Cloud Function para o handler Lambda
- Defina a função como @Bean do tipo Function<Input, Output>
- Use SLF4J com contexto de correlação (MDC) em todas as chamadas

🚫 Never Do:
- Não use @SpringBootTest em testes de Lambda (ciclo de vida diferente)
- Não capture exceções no handler sem relançar — o SQS precisa da falha para o retry
```

Isso se aplica a todas as equipes da BRX que usam Java com Lambda.

---

## O que acontece se você duplica

Se você colocar nas instruções de projeto algo que já está em uma skill global:

1. **Inconsistências**: se a skill for atualizada, suas instruções de projeto ficam desatualizadas
2. **Conflitos**: se as duas dizem coisas diferentes, o Claude Code dá prioridade variável e o resultado é imprevisível
3. **Manutenção dupla**: mudanças precisam ser feitas em dois lugares

**Regra prática:** se algo já está em uma skill global BRX, no `CLAUDE.md` do projeto escreva apenas `Ver skill java-spring-lambda-brx` ou simplesmente não mencione. O agente já sabe disso.

---

## Quando falar com a Equipe de Governança BRX

Se você detectar que uma convenção que usa no seu projeto deveria ser um padrão de toda a organização, contate a Equipe de Governança BRX para que a elevem a skill global. Ver [Módulo 6.1 — Como solicitar um novo agente ou skill](../modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md).

---

## Próximos passos

- [Módulo 6 — Contribuir ao ecossistema BRX](../modulo-6-contribuir-ecossistema/README.md)
- [Módulo 5 — Segurança e Governança](../modulo-5-seguranca-governanca/README.md)
