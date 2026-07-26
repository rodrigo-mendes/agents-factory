# Modo agente: tarefas complexas multi-passo com ferramentas

**Perfil:** Dev / Tech Lead  
**Tempo estimado de leitura:** 7 min

---

## Para que serve o modo agente

O modo agente é o **modo padrão do Claude Code**: ele planeja e executa uma sequência de ações de forma autônoma — lê arquivos, escreve código, roda comandos no terminal, valida resultados, corrige erros e repete até concluir a tarefa.

Diferente de apenas perguntar (que só responde) ou de uma edição pontual (que altera um trecho), **o modo agente atua de forma encadeada** com ferramentas.

---

## Dois tipos de agentes no Claude Code

### Agente base do Claude Code (sem customização)

É o Claude Code rodando com seu comportamento padrão no terminal ou no IDE. Ele já tem acesso às ferramentas de ler/escrever arquivos, rodar comandos, buscar no codebase e navegar pelo projeto.

**Quando usá-lo:** tarefas multi-passo que não exigem conhecer as convenções específicas de BRX.

### Subagentes customizados BRX

Versões pré-instruídas com as convenções e o stack de BRX, definidas em `.claude/agents/*.md` e acionadas via o subagente (ferramenta Task/Agent) ou por comandos slash customizados em `.claude/commands/*.md`, invocados como `/<nome-do-agente>`. O conjunto real depende do que a Equipe de Governança BRX publicou; descubra os nomes digitando `/` no Claude Code.

**Quando usá-los:** qualquer tarefa de domínio onde o stack BRX importa (infraestrutura, serviços Java, etc.). Veja o [catálogo de agentes](../modulo-1-agentes-customizados/05-catalogo-agentes-brx.md).

---

## Ferramentas que um agente pode usar

O Claude Code tem acesso a estas ferramentas por padrão:

| Ferramenta | O que faz |
|---|---|
| `Read` | Ler o conteúdo de qualquer arquivo do projeto |
| `Glob` | Listar arquivos por padrão de caminho (ex.: `**/*.java`) |
| `Grep` | Buscar texto/expressão regular no codebase |
| `Write` | Criar um arquivo novo |
| `Edit` | Modificar um arquivo existente (mostrando o diff) |
| `Bash` | Executar um comando no terminal |
| `Task` / `Agent` | Delegar uma subtarefa a um subagente (ex.: Explore) |

Cada vez que o agente usa uma ferramenta que altera o estado (editar, escrever, rodar comando), o Claude Code pede sua **permissão** — a menos que essa ação já esteja pré-aprovada na allowlist (veja abaixo). Ferramentas apenas de leitura, como `Read`, `Grep` e `Glob`, costumam ser seguras de liberar.

---

## Supervisionar a execução

Diferente da exploração ou de uma edição pontual, no modo agente o Claude **toma decisões de forma autônoma** entre os passos. Seu papel é:

1. **Dar o objetivo claro** no início
2. **Confirmar o plano** quando o agente propuser (fase P3 nos agentes BRX) — o Plan Mode ajuda aqui
3. **Supervisionar** os passos enquanto são executados
4. **Interromper se algo der errado** — não espere o fim

O Claude mostra quais ferramentas está usando e o que encontra. Acompanhar isso enquanto ele trabalha ajuda a detectar desvios cedo.

---

## Padrões de uso frequentes na BRX

### Implementar uma funcionalidade completa de ponta a ponta

```
Implemente o endpoint POST /api/v1/orders:
- Valide o body contra OrderRequest (já existe em @dto/OrderRequest.java)
- Persista na tabela DynamoDB orders usando o repositório de @OrderRepository.java
- Publique um evento SQS OrderCreated com o OrderId gerado
- Retorne 201 com o OrderId
- Testes de integração com LocalStack
```

### Executar e corrigir testes em loop

```
Execute os testes de @OrderServiceTest.java.
Se falharem, analise os erros e corrija.
Repita até que todos passem.
```

### Analisar e refatorar um módulo

```
Analise o módulo @src/services/payment/.
Identifique: dependências circulares, métodos com mais de 50 linhas,
código duplicado com o módulo @src/services/order/.
Proponha e aplique refatorações para cada problema encontrado, uma a uma.
```

### Gerar documentação

```
Leia todos os endpoints públicos em @src/controllers/
e gere a especificação OpenAPI 3.0 em docs/api/openapi.yaml.
```

---

## Quando usar o agente base vs um subagente customizado BRX

Os nomes de comando abaixo (`agente-infra`, `agente-arquitetura`) são ILUSTRATIVOS/hipotéticos — confirme os nomes reais digitando `/` no Claude Code.

| Tarefa | Agente base | Subagente customizado BRX |
|---|---|---|
| Gerar testes para código Java genérico | ✅ | ✅ (melhor se houver skill Java) |
| Provisionar infra na AWS com Terraform | ❌ | ✅ subagente de infraestrutura (ex.: `/agente-infra`) |
| Refatorar código sem convenções específicas | ✅ | — |
| Criar um serviço Java seguindo padrões BRX | ❌ | ✅ (quando existir agente backend) |
| Depurar um teste que falha | ✅ | — |
| Projetar uma arquitetura serverless BRX | ❌ | ✅ subagente de arquitetura serverless (ex.: `/agente-arquitetura`) |

---

## Boas práticas no modo agente

**Seja específico com o objetivo, não com os passos:**

✅ Melhor: `Implemente o serviço de notificações completo com seus testes`  
❌ Pior: `Primeiro crie o arquivo, depois escreva a classe, depois o método send(), depois o teste...`

O agente é melhor decidindo os passos internamente do que seguindo uma sequência ditada passo a passo.

**Forneça contexto do que já existe:**

```
Já existem @NotificationRepository.java e a tabela DynamoDB `notifications` no ambiente.
Não os recrie. Apenas implemente o serviço que os utiliza.
```

**Defina os limites explicitamente:**

```
Modifique apenas arquivos em src/services/notifications/.
Não toque nos controladores nem na camada de repositório.
```

---

## Permissões e aprovação de ferramentas

Quando o agente tenta pela primeira vez executar uma ação que altera o estado (rodar um comando com `Bash`, editar ou criar um arquivo), o Claude Code pede sua confirmação. Você pode:

- **Permitir uma vez:** aprova só esta execução
- **Permitir sempre (adicionar à allowlist):** o Claude Code passa a aprovar automaticamente esse tipo de ação nas próximas vezes, gravando a regra em `.claude/settings.json`
- **Recusar:** o agente não usa aquela ferramenta

Para agentes de confiança, você pode pré-aprovar ferramentas apenas de leitura na allowlist de permissões, no campo `permissions.allow` do `.claude/settings.json`:

```json
{
  "permissions": {
    "allow": ["Read", "Grep", "Glob"]
  }
}
```

**Nunca pré-aprove `Bash` irrestrito** para agentes desconhecidos. Se precisar liberar comandos, restrinja o escopo por padrão (por exemplo, `Bash(mvn test:*)` em vez de `Bash`). Os subagentes BRX já têm as ferramentas e os comandos que podem executar limitados na sua própria definição em `.claude/agents/`.

---

## Próximos passos

- [1.1 — O que é um subagente customizado BRX](../modulo-1-agentes-customizados/01-o-que-e-um-agente-customizado.md)
- [1.3 — Entender o workflow P0-P5](../modulo-1-agentes-customizados/03-entender-resposta-workflow-p0-p5.md)
- [Módulo 3 — Guias por papel com exemplos específicos](../modulo-3-guias-por-papel/README.md)
