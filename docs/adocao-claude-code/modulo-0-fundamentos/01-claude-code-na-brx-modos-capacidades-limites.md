# Claude Code na BRX: modos, capacidades e limites

**Perfil:** Todos  
**Tempo estimado de leitura:** 8 min

---

## O que é o Claude Code

O Claude Code é um agente de IA que roda no terminal (CLI) e ajuda a escrever, entender e modificar código. Ele também oferece extensões para **VS Code** e **JetBrains** e uma versão web em **claude.ai/code**. Na BRX ele opera sob um **plano/licença corporativo (Anthropic Console ou plano Team/Enterprise)**, o que habilita administração centralizada e a garantia de que, sob o plano corporativo, os dados **não são usados para treinar modelos**.

Por baixo, o Claude Code usa os modelos Claude: **Opus 4.8** (o mais capaz), **Sonnet 4.6**, **Haiku 4.5** e **Fable 5**. A recomendação na BRX é usar os modelos mais capazes e recentes para tarefas de código.

O Claude Code **não é**:
- Um motor de busca de documentação (embora possa resumi-la se você der o contexto)
- Um substituto do code review humano
- Um sistema que "lembra" conversas anteriores entre sessões automaticamente (o contexto do projeto vem do `CLAUDE.md`, não da memória de sessões passadas)
- Um sistema que executa código em produção sozinho — ele propõe e executa comandos localmente sob seu controle e suas permissões

---

## Os três modos principais

### Modo de exploração / perguntas (Plan Mode)

> Use para: explorar, perguntar, entender, planejar.

O ponto de partida mais comum. Você roda `claude` no terminal (ou abre o painel do Claude Code na extensão do IDE) e escreve sua pergunta. O Claude responde em linguagem natural e pode incluir código como parte da resposta.

Para explorar com segurança, ative o **Plan Mode** com `Shift+Tab`: nesse modo o Claude fica **read-only** — ele lê, analisa e propõe um plano, mas **não modifica arquivos** até você aprovar. É ideal para entender o projeto antes de agir.

Exemplos de quando usar:
- "O que este método `processOrder()` faz?"
- "Qual seria a melhor estrutura para este serviço?"
- "Explique as diferenças entre `SQS` e `SNS`."

**Dica:** Você pode referenciar arquivos com `@nome-do-arquivo` (menção de arquivo) para dar contexto sem precisar colar o código manualmente. Você também pode deixar o Claude explorar o projeto sozinho — ele busca os arquivos relevantes por conta própria.

---

### Edições diretas (edição de arquivos com diff)

> Use para: mudanças cirúrgicas em um ou vários arquivos.

Diferente de outras ferramentas, o Claude Code **edita arquivos nativamente**: ele mostra o **diff** da mudança e você aprova ou rejeita antes de aplicar. Não há um atalho separado para "entrar em modo de edição" — as edições fazem parte do loop natural do agente. Basta pedir a mudança em linguagem natural.

Exemplos de quando usar:
- Refatorar um método específico
- Adicionar tratamento de erros a uma função existente
- Renomear variáveis em um bloco de código
- Gerar um teste unitário para uma função

**Dica:** Quanto mais delimitado o contexto (mencione o arquivo com `@`, ou tenha o arquivo aberto no IDE, que é enviado como contexto), mais preciso o resultado. Sempre revise o diff antes de aprovar.

---

### Modo agente (agente autônomo)

> Use para: tarefas complexas que envolvem múltiplos passos, ferramentas ou arquivos.

O modo agente é o **modo padrão** do Claude Code: ele planeja e executa uma sequência de ações — ler arquivos, executar comandos no terminal, escrever código, validar resultados — de forma autônoma. Entre um passo e outro, **o agente toma decisões por conta própria**, sempre respeitando suas permissões.

Na BRX, o modo agente é a base sobre a qual funcionam os **subagentes customizados** (ver Módulo 1).

Exemplos de quando usar:
- Implementar uma funcionalidade completa do zero
- Rodar e corrigir uma suíte de testes em loop até que passem
- Analisar uma arquitetura e propor mudanças com justificativa

**Dica:** para tarefas maiores, planeje antes de executar — use o **Plan Mode** (`Shift+Tab`) para o agente propor um plano que você revisa e aprova, e só então o deixe implementar. Acompanhe os passos à medida que o agente avança; você pode interromper e corrigir se ele estiver indo em uma direção equivocada.

---

## Resumo dos modos

| Modo | Como usar | Modifica arquivos | Melhor para |
|---|---|---|---|
| Exploração / Plan Mode | `claude` no terminal; `Shift+Tab` para Plan Mode read-only | Não (read-only no Plan Mode) | Explorar, perguntar, entender, planejar |
| Edições diretas | Pedir a mudança em linguagem natural; aprovar o diff | Sim (com diff para aprovar) | Mudanças pontuais em código |
| Agente | Modo padrão do Claude Code | Sim (autônomo, sob permissões) | Tarefas multi-passo complexas |

---

## A regra de ouro: planeje antes de executar

> Para qualquer tarefa que não seja trivial: **planeje → revise o plano → execute.**

1. **Planeje** — entre no **Plan Mode** (`Shift+Tab`), read-only, para o Claude entender o que já existe e propor um plano sem tocar em nada.
2. **Revise o plano** — corrija ou ajuste antes de qualquer alteração. Corrigir um plano é muito mais barato do que desfazer código já escrito.
3. **Execute** — aprovado o plano, saia do Plan Mode e deixe o Claude implementar (edição direta ou modo agente), supervisionando o diff.

Esse fluxo é aprofundado no [Módulo 2](../modulo-2-modos-claude-code/README.md) e, nos subagentes BRX, corresponde ao ponto de confirmação do workflow P0-P5 ([Módulo 1.3](../modulo-1-agentes-customizados/03-entender-resposta-workflow-p0-p5.md)).

---

## Capacidades-chave na BRX

| Capacidade | Disponível | Notas |
|---|---|---|
| Agente no terminal (CLI) | ✅ | Rodando `claude`; é a forma principal de uso |
| Extensões de IDE (VS Code/JetBrains) | ✅ | Painel do Claude Code integrado ao editor |
| Versão web (claude.ai/code) | ✅ | Segundo o plano |
| Subagentes customizados BRX | ✅ | Ver catálogo no Módulo 1 |
| Skills e comandos slash customizados | ✅ | `.claude/skills/<nome>/SKILL.md` (comandos slash usam `context: fork` no frontmatter) |
| Memória de projeto (`CLAUDE.md`) | ✅ | Instruções e contexto do projeto, carregados automaticamente |
| MCP servers (ferramentas externas) | ✅ | Para conectar sistemas externos, segundo configuração |
| Execução de código em produção | ❌ | Só propõe e executa localmente sob suas permissões |

---

## Limites importantes

### Janela de contexto

Cada conversa tem um limite de tokens (unidades de texto que o Claude consegue processar de uma vez). Quando a conversa fica muito longa:
- As respostas podem ficar mais genéricas
- O Claude pode "perder" instruções dadas no início
- A qualidade das sugestões cai

**O que fazer:** O Claude Code **compacta** o contexto automaticamente quando ele fica longo, preservando o essencial. Ainda assim, para trocar de tarefa ou "zerar" a conversa, use `/clear` para começar uma conversa nova com um resumo do estado atual. Ver guias de gestão de sessão no Confluence.

### Confiabilidade das respostas

O Claude pode gerar código plausível, porém incorreto, especialmente em:
- APIs pouco comuns ou muito recentes
- Lógica de negócio específica da BRX que não está no contexto
- Interações entre sistemas complexos

**O que fazer:** Revise sempre o código gerado. Use os subagentes customizados BRX para tarefas em que a precisão sobre o nosso stack é crítica.

### Dados sensíveis

Nunca inclua na conversa: senhas, tokens, chaves de API, dados de clientes ou informação interna classificada. Ver Módulo 5.

---

## Próximos passos

- [Módulo 0.2 — Mapa do ecossistema Claude Code BRX](02-mapa-ecossistema-claude-code-brx.md)
- [Módulo 0.3 — Setup do ambiente: dia 1](03-setup-ambiente-dia-1.md)
- [Módulo 2 — Modos do Claude Code em detalhe](../modulo-2-modos-claude-code/README.md)
