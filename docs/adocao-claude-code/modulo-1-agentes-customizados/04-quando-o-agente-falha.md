# O que fazer quando o agente se desvia ou falha

**Perfil:** Dev  
**Tempo estimado de leitura:** 7 min

---

## Tipos de problemas

Os problemas com agentes customizados caem em quatro categorias:

1. **O agente não arranca** — erro ao invocar ou as fases P0/P1 falham
2. **O agente se desvia do objetivo** — começa bem mas gera algo diferente do que foi pedido
3. **O agente gera código incorreto** — a lógica ou a sintaxe tem erros
4. **O agente fica travado** — para de responder ou entra em loop

---

## 1. O agente não arranca

Nos exemplos deste guia usamos um agente de infraestrutura hipotético `agente-infra` (nome ILUSTRATIVO): substitua-o pelo nome real do seu workspace (descubra digitando `/` no Claude Code).

**Sintomas:**
- Mensagem de erro ao invocar o agente (ex.: `/agente-infra`) ou o subagente
- O agente diz que não encontra arquivos de instruções ou skills
- O subagente/comando não aparece na lista (`/` no chat)

**Causas e soluções:**

| Causa | Solução |
|---|---|
| O arquivo do agente (`.claude/agents/<nome>.md`) não está no projeto | Copie os artefatos do agents-factory para `.claude/agents/` do seu projeto ou abra o agents-factory no ambiente. Ver [guia 0.3](../modulo-0-fundamentos/03-setup-ambiente-dia-1.md) |
| Versão do Claude Code desatualizada | Atualize o Claude Code (`claude update`) ou reinstale a CLI/extensão do IDE |
| O nome do agente está incorreto | Digite `/` no chat e revise os nomes exatos na lista |
| O agente cita uma skill que não existe | Reporte à Equipe de Governança BRX (ver [Módulo 6.1](../modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md)) |

---

## 2. O agente se desvia do objetivo

**Sintomas:**
- Em P3, o plano proposto não é o que você pediu
- Em P4, o agente gera arquivos ou lógica que você não pediu
- O resultado final está longe da intenção original

**O que fazer:**

**Passo 1 — Interrompa o quanto antes**

Se você detecta isso em P3, muito melhor do que em P4. Escreva no chat: `Pare. Quero ajustar o plano.`

**Passo 2 — Reformule o objetivo com mais precisão**

O desvio costuma vir de uma instrução ambígua. Identifique qual parte do prompt foi ambígua e seja mais específico:

❌ Ambíguo:
```
/agente-infra cria infraestrutura para o serviço de notificações
```

✅ Preciso:
```
/agente-infra cria só a função Lambda e a queue SQS para o serviço de notificações. 
Não inclua API Gateway nem banco de dados. O nome da função deve ser `brx-notifications-processor`.
```

**Passo 3 — Forneça contexto que o agente não pode inferir**

Se o agente não tem acesso a certos arquivos do seu projeto, ele pode assumir coisas incorretas. Adicione referências explícitas com `@arquivo`:

```
/agente-infra cria o trigger SQS para a função Lambda em @src/lambda/NotificationProcessor.java
Use a queue definida em @terraform/modules/sqs/main.tf
```

**Passo 4 — Comece a conversa de novo se houver muito ruído acumulado**

Se já foram várias trocas e o agente continua sem entender o que você quer, comece uma conversa nova (`/clear`) com um prompt mais preciso. Uma conversa limpa dá melhores resultados do que tentar corrigir uma conversa que se torceu. (O Claude Code também compacta o contexto automaticamente quando ele fica longo.)

---

## 3. O agente gera código incorreto

**Sintomas:**
- O código não compila ou tem erros de sintaxe
- A lógica não faz o que descreve
- Os nomes de recursos, variáveis ou funções não seguem as convenções

**O que fazer:**

**Para erros de sintaxe ou compilação:**

Em P5, o agente deveria detectá-los e corrigi-los automaticamente. Se não fizer isso ou não conseguir em duas tentativas:

```
O código em [arquivo] tem este erro: [cole o erro exato]. 
Corrija só essa função sem tocar no resto.
```

**Para lógica incorreta:**

```
A função `processOrder` deveria fazer X mas faz Y. 
Aqui está o comportamento esperado: [descreva com precisão].
```

**Para nomes que não seguem as convenções:**

Primeiro verifique se a convenção está no arquivo de instruções do projeto (`CLAUDE.md`). Se não estiver, o agente não pode sabê-la:

```
Em BRX usamos o naming `brx-{env}-{servico}-{recurso}`. 
Atualize os nomes de recursos seguindo esse padrão.
```

Se a convenção deveria estar na skill mas não está, reporte à Equipe de Governança BRX.

---

## 4. O agente fica travado

**Sintomas:**
- O indicador de carregamento não some por mais de 2 minutos
- O agente fica em loop corrigindo o mesmo erro repetidamente
- Mensagens sem coerência ou incompletas

**O que fazer:**

1. **Pare o agente** (Esc no terminal ou o botão de stop)
2. **Avalie o que foi completado bem** — os arquivos já gerados podem continuar sendo válidos
3. **Comece uma conversa nova** (`/clear`) com um resumo do que já está feito:
   ```
   Já criei os módulos Terraform em `modules/lambda-sqs/`. 
   Agora preciso só atualizar `environments/dev/main.tf` para referenciá-los.
   ```
4. Se o travamento ocorre sempre no mesmo ponto, provavelmente há um bug no agente — reporte à Equipe de Governança BRX.

---

## Quando escalar para a Equipe de Governança BRX

Escale quando o problema é do agente em si, não do seu prompt:

- O agente cita uma skill que não existe ou está desatualizada
- O agente gera código que descumpre convenções BRX documentadas
- O agente trava sempre na mesma tarefa reproduzível
- Você quer solicitar uma nova funcionalidade ao agente

**Como escalar:** ver [Módulo 6.1 — Solicitar um novo agente ou skill](../modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md).

---

## Checklist rápido para diagnóstico

```
O agente arranca?
  └── Não → Verificar setup do projeto / .claude/agents/ (guia 0.3)

O plano em P3 faz sentido?
  └── Não → Interromper, reformular o prompt, executar de novo

O código gerado tem erros?
  └── Sim, sintaxe/compilação → Deixar P5 corrigir; se não conseguir, dar o erro exato
  └── Sim, lógica → Descrever o comportamento esperado com precisão
  └── Sim, naming → Dar a convenção explícita; se deveria estar na skill, reportar

O agente não avança?
  └── Começar conversa nova (/clear) com o estado atual do projeto
```

---

## Próximos passos

- [1.5 — Catálogo de agentes BRX](05-catalogo-agentes-brx.md)
- [6.1 — Como reportar ou solicitar melhorias em agentes](../modulo-6-contribuir-ecossistema/01-solicitar-agente-ou-skill.md)
