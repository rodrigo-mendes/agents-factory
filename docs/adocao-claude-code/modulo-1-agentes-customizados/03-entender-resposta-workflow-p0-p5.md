# Entender a resposta de um agente: o workflow P0-P5

**Perfil:** Dev  
**Tempo estimado de leitura:** 8 min

---

## Por que os agentes BRX não respondem de uma vez

Diferentemente do chat livre, os agentes de BRX seguem um processo em seis fases antes de escrever uma única linha de código. Esse processo garante que o agente:

1. Usa os padrões corretos do stack BRX
2. Entende o contexto atual do seu projeto
3. Mostra a você um plano antes de agir

Conhecer essas fases permite que você saiba **o que o agente está fazendo em cada momento** e quando intervir.

O workflow P0-P5 é uma convenção dos agentes BRX (definida nas instruções do subagente), não um recurso genérico do Claude Code.

---

## As seis fases da sua perspectiva

### P0 — Carregando instruções

**O que você verá:** o agente informa que está carregando skills e instruções, ou o Claude Code mostra as ferramentas de leitura sendo usadas.

**O que faz internamente:** o agente carrega as skills relevantes (bases de conhecimento com padrões BRX), as instruções do projeto (`CLAUDE.md`) e sua própria configuração.

**O que você faz:** nada. Espere. Esta fase é automática e costuma durar segundos.

**Sinal de problema:** se o agente disser que não encontra um arquivo de skill ou instrução, pode ser que os artefatos não estejam bem configurados no seu projeto. Ver [guia 1.4](04-quando-o-agente-falha.md).

---

### P1 — Analisando o projeto

**O que você verá:** o agente lê arquivos do seu projeto: estrutura de pastas, arquivos de configuração, código existente.

**O que faz internamente:** entende o estado atual antes de propor mudanças, para não gerar código que colida com o que já existe.

**O que você faz:** nada, mas pode observar quais arquivos ele está lendo. Se você vê que ele está lendo arquivos irrelevantes para a sua tarefa, pode interromper e ser mais específico no prompt.

---

### P2 — Consultando padrões

**O que você verá:** o agente pode mostrar fragmentos das regras que aplica (✅ sempre fazer, ⚠️ perguntar primeiro, 🚫 nunca fazer).

**O que faz internamente:** confronta sua tarefa contra os padrões da skill para garantir que a implementação vai seguir as convenções BRX.

**O que você faz:** nada. Se o agente detecta um ponto que exige uma decisão de design (marcado com ⚠️), ele pode fazer uma pergunta antes de continuar. Responda-a.

**Exemplo de pergunta em P2:**
```
⚠️ A skill indica que a criptografia em repouso é configurável.
Você quer ativar criptografia com KMS para este bucket S3, ou usar a criptografia padrão do S3?
```

---

### P3 — Proposta + sua confirmação ← ponto de maior interação

**O que você verá:** o agente apresenta um plano estruturado do que vai fazer, geralmente em forma de lista de ações ou arquivos que vai criar/modificar. No Claude Code, isso mapeia diretamente para a aprovação de plano/ações — você aprova ou rejeita antes de o agente prosseguir.

**O que faz internamente:** nada ainda. Está esperando a sua aprovação antes de escrever código.

**O que você faz:** **revise o plano e responda.** Opções:
- `"Adiante"` / `"Confirmo"` → o agente implementa o plano como está
- `"Adiante, mas sem o passo 3"` → você aprova parcialmente
- `"Troque X por Y e depois prossiga"` → você corrige antes de implementar
- `"Pare"` / `"Cancele"` → você aborta

**Esta é a fase mais importante.** Se o plano não faz sentido, é mais fácil corrigi-lo aqui do que depois de o agente ter gerado código.

**Exemplo de proposta P3:**
```
Plano de implementação:
1. Criar módulo Terraform `modules/lambda-sqs/`
   - main.tf: função Lambda + queue SQS + trigger event source mapping
   - variables.tf: nome de função, memória, timeout
   - outputs.tf: ARN da função e URL da queue
2. Atualizar `environments/dev/main.tf` para referenciar o novo módulo
3. Adicionar tags padrão BRX a todos os recursos

Confirma ou quer ajustar algo?
```

---

### P4 — Implementação

**O que você verá:** o agente gera arquivos, escreve código, possivelmente executa comandos (como `terraform validate`).

**O que faz internamente:** implementa exatamente o que foi aprovado em P3.

**O que você faz:** supervisione. Você pode ver os arquivos que ele vai criando. Se algo não vai bem (gera um arquivo no caminho errado, escreve algo incorreto), você pode interromper.

---

### P5 — Validação

**O que você verá:** o agente executa comandos de verificação (`terraform validate`, `maven test`, etc.) e reporta o resultado.

**O que faz internamente:** verifica que o que gerou é sintaticamente correto e consistente.

**O que você faz:** revisar o resultado da validação. Se houver erros, o agente pode tentar corrigi-los automaticamente. Se a correção não funcionar em duas tentativas, interrompa e revise manualmente.

---

## Resumo das fases

| Fase | Nome | Precisa agir | Duração típica |
|---|---|---|---|
| P0 | Carregando instruções | Não | Segundos |
| P1 | Analisando o projeto | Não | 10-30 s |
| P2 | Consultando padrões | Às vezes (se houver ⚠️) | Segundos |
| **P3** | **Proposta** | **Sim — confirmar plano** | Até você responder |
| P4 | Implementação | Supervisionar | 30 s – vários minutos |
| P5 | Validação | Revisar resultado | 10-60 s |

---

## Quando interromper

Você pode interromper o agente a qualquer momento (Esc no terminal, o botão de stop, ou escrevendo uma mensagem). Os bons momentos para fazer isso:

- **Em P1** se você vê que ele está lendo arquivos completamente fora de contexto
- **Em P3** se o plano não é o que você queria (melhor corrigir aqui)
- **Em P4** se você vê que ele está gerando algo incorreto
- **Nunca** em P0 ou P2 sem motivo, já que essas fases são automáticas e necessárias

---

## Próximos passos

- [1.4 — O que fazer quando o agente se desvia ou falha](04-quando-o-agente-falha.md)
- [1.2 — Quando usar agente vs chat livre](02-quando-usar-agente-vs-chat-livre.md)
