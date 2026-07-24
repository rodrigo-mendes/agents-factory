# Setup do ambiente: dia 1 com o Claude Code

**Perfil:** Dev  
**Tempo estimado:** 20-30 min

---

## Pré-requisitos

Antes de começar, verifique que você tem:

- [ ] Node.js instalado (recomendado versão LTS atual) — necessário para instalar o CLI via npm
- [ ] Conta Anthropic com **plano corporativo (Team/Enterprise)** atribuído pela BRX, ou acesso ao Anthropic Console
- [ ] (Opcional) VS Code ≥ 1.85 ou uma IDE JetBrains, se quiser usar a extensão
- [ ] Acesso ao repositório `agents-factory` na organização BRX

Se você não tem o plano/licença atribuído, contate o responsável da sua equipe ou a Equipe de Governança BRX.

---

## Passo 1: Instalar o Claude Code

A forma principal de usar o Claude Code é o **CLI no terminal**. Instale globalmente com npm:

```bash
npm install -g @anthropic-ai/claude-code
```

> Alternativamente, existe um instalador nativo para o seu sistema operacional. Consulte a documentação oficial do Claude Code se preferir não usar o npm.

**Extensão de IDE (opcional):** se você trabalha no **VS Code** ou em uma **IDE JetBrains**, instale a extensão do Claude Code pela loja de extensões da sua IDE (`Ctrl+Shift+X` / `Cmd+Shift+X` no VS Code, buscar por **"Claude Code"**). A extensão integra o painel do Claude Code ao editor, mas o CLI continua sendo o coração da ferramenta.

---

## Passo 2: Autenticar com sua conta Anthropic

1. No terminal, dentro de qualquer pasta, rode:

   ```bash
   claude
   ```

2. Na primeira execução, o Claude Code guia você pelo fluxo de login. Abrirá o navegador para você autenticar com sua conta Anthropic / plano corporativo da BRX.
3. Complete o fluxo de autorização e volte ao terminal.

**Verificação:** após o login, você deve ver o prompt interativo do Claude Code no terminal, sem mensagens de erro de autenticação. Se aparecer um aviso de plano/licença, ela ainda não foi atribuída à sua conta.

---

## Passo 3: Verificar que o Claude Code funciona

1. Abra um terminal em uma pasta de projeto qualquer.
2. Rode `claude`.
3. Escreva: `Olá, o que você pode fazer?`
4. Você deve receber uma resposta descrevendo as capacidades da ferramenta.

Para um teste rápido de edição, peça algo simples como: `Crie um arquivo teste.java com uma classe que soma dois números.` O Claude vai propor o arquivo e mostrar o diff para você aprovar.

Se o comando `claude` não for encontrado, verifique se a instalação global do npm está no seu `PATH` (reabra o terminal ou revise a variável `PATH`).

---

## Passo 4: Abrir o seu projeto

O Claude Code trabalha no contexto da pasta onde você o executa. Para trabalhar no seu projeto:

```bash
cd /caminho/para/seu-projeto
claude
```

A partir daí, o Claude enxerga os arquivos do projeto, carrega o `CLAUDE.md` (se existir) e usa esse contexto nas respostas. Se estiver usando a extensão de IDE, abra a pasta do projeto na IDE e o painel do Claude Code já opera nesse diretório; o arquivo aberto no editor é enviado como contexto.

---

## Passo 5: Acessar os agentes e skills da BRX (opcional, para devs avançados)

Os subagentes e skills customizados da BRX vivem no repositório `agents-factory`, nas pastas `.claude/agents/` e `.claude/skills/`. Para usá-los no seu projeto:

**Opção A — Clonar o agents-factory como referência**

```bash
git clone <url-do-repo-agents-factory>
cd agents-factory
claude
```

Ao rodar o Claude Code dentro do agents-factory, os subagentes em `.claude/agents/` e as skills em `.claude/skills/` ficam disponíveis.

**Opção B — Copiar os artefatos necessários para o seu projeto**

Copie os arquivos de `.claude/agents/` e as skills de `.claude/skills/` que a sua equipe precisa para as pastas correspondentes (`.claude/agents/` e `.claude/skills/`) do seu próprio repositório. Consulte o seu Tech Lead sobre quais subagentes são relevantes para o seu projeto.

**Opção C — Configuração de usuário (global)**

Você também pode colocar subagentes e skills que usa em todos os projetos em `~/.claude/agents/` e `~/.claude/skills/`, na configuração de usuário. Assim ficam disponíveis em qualquer repositório sem copiar por projeto.

---

## Passo 6: Configurar permissões básicas

O Claude Code usa **permissões** para controlar quais ferramentas e comandos ele pode executar sem pedir aprovação a cada passo. A configuração fica em `.claude/settings.json` (por projeto) ou `~/.claude/settings.json` (por usuário).

Crie/edite `.claude/settings.json` na raiz do seu projeto com uma **allowlist** de permissões recomendadas:

```json
{
  "permissions": {
    "allow": [
      "Bash(npm run test:*)",
      "Bash(git status)",
      "Bash(git diff:*)",
      "Read(./**)",
      "Edit(./src/**)"
    ]
  }
}
```

> A allowlist em `permissions.allow` pré-aprova ações seguras e repetitivas, para que os subagentes BRX concluam tarefas mais longas sem parar a cada comando. Mantenha a lista mínima: só inclua o que você realmente confia. Ações fora da allowlist continuam pedindo sua aprovação explícita.

Você também pode usar os **modos de permissão** do Claude Code durante uma sessão para ajustar, na hora, o quanto o agente pode agir sozinho.

---

## Verificação final

Antes de dar o setup por concluído, cheque:

- [ ] O comando `claude` abre o Claude Code no terminal, sem erro de autenticação
- [ ] O Claude responde às suas perguntas dentro do projeto
- [ ] Você consegue referenciar um arquivo na conversa com `@nome-do-arquivo`
- [ ] O Plan Mode ativa com `Shift+Tab` (modo read-only para explorar)
- [ ] (Opcional) Os subagentes e skills da BRX estão disponíveis no projeto

---

## Problemas comuns

| Problema | Causa provável | Solução |
|---|---|---|
| Erro de autenticação/plano ao rodar `claude` | Plano/licença não atribuído | Contatar o responsável de equipe ou a Governança BRX |
| Comando `claude` não encontrado | Instalação global do npm fora do `PATH` | Reabrir o terminal; revisar `PATH`; reinstalar com `npm install -g @anthropic-ai/claude-code` |
| O Claude não responde | Sem conexão ou VPN bloqueando | Verificar conexão; revisar a política de VPN com o TI |
| Subagentes/skills da BRX não aparecem | agents-factory não está no projeto | Clonar o repo, ou copiar `.claude/agents` e `.claude/skills` para o seu projeto (ou para `~/.claude/`) |
| O Claude pede aprovação a cada comando | Sem allowlist configurada | Adicionar permissões em `.claude/settings.json` (`permissions.allow`) |

---

## Próximos passos

- [Módulo 0.1 — Modos, capacidades e limites](01-claude-code-na-brx-modos-capacidades-limites.md)
- [Módulo 0.2 — Mapa do ecossistema BRX](02-mapa-ecossistema-claude-code-brx.md)
- [Módulo 1.1 — O que é um agente customizado](../modulo-1-agentes-customizados/01-o-que-e-um-agente-customizado.md)
