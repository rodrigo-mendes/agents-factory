# Post-mortem de subagente: quando revisar e atualizar

**Perfil:** Tech Lead / Equipe de Governança BRX  
**Tempo estimado de leitura:** 7 min

---

## Para que serve um post-mortem de subagente

Um post-mortem de subagente não é uma análise de falha — é uma **revisão periódica de efetividade**. O objetivo é responder: o subagente continua fazendo bem o seu trabalho? Há partes que podem ser melhoradas com o que aprendemos usando-o?

Diferencia-se de reportar um bug pontual por ser uma revisão holística programada, não reativa.

---

## Quando fazer uma revisão de subagente

### Revisões programadas

| Frequência | Gatilho |
|---|---|
| **Trimestral** | Para subagentes de uso frequente (> 50 invocações/mês) |
| **Semestral** | Para subagentes de uso moderado |
| **Diante de atualização de framework** | A versão do framework que o subagente usa tem uma nova major release |
| **Diante de mudança de convenções BRX** | As convenções do domínio do subagente mudaram |

### Revisões reativas

Faça uma revisão imediata quando:
- 3 ou mais desenvolvedores reportam o mesmo problema com o subagente em menos de um mês
- O subagente passa a ser usado em um caso de uso diferente do original
- Uma skill que o subagente usa foi atualizada ou depreciada

---

## Processo de revisão

### 1. Coletar evidências

Antes de revisar o subagente, colete:

- Feedback de desenvolvedores: quais partes do subagente eles corrigem com frequência?
- Prompts que funcionam bem vs prompts que geram resultados ruins (casos documentados)
- Casos de uso atuais: o subagente está sendo usado para aquilo que foi projetado?
- Versões atuais dos frameworks que ele usa vs versões do research doc

---

### 2. Revisar o subagente contra uma checklist

```markdown
## Checklist de revisão de subagente — [Nome do subagente] — [Data]

### Precisão técnica
[ ] As skills que ele usa estão atualizadas (< 12 meses ou validadas como vigentes)
[ ] Os padrões de código gerados continuam corretos para as versões atuais
[ ] Não há anti-padrões documentados que o subagente faça de forma incorreta

### Usabilidade
[ ] O workflow P0-P5 se completa sem bloqueios nos casos de uso principais
[ ] A proposta em P3 é clara e não ambígua para o usuário
[ ] As mensagens de erro ou de solicitação de contexto são compreensíveis

### Cobertura
[ ] Os casos de uso documentados no catálogo continuam sendo os que os devs usam
[ ] Não há casos de uso frequentes que o subagente não cubra e deveria cobrir
[ ] As ferramentas que o subagente usa estão disponíveis no ambiente padrão da BRX

### Qualidade do output
[ ] O código gerado em 80% dos casos não requer correções de convenções
[ ] Os testes gerados (se aplicável) são testes reais que falham se o código falhar
[ ] A infra gerada (se aplicável) segue o princípio de mínimo privilégio
```

---

### 3. Classificar os achados

| Severidade | Critério | Ação |
|---|---|---|
| **Crítico** | O subagente gera código inseguro ou com erros sistemáticos | Patch imediato; notificar as equipes |
| **Alto** | Padrões desatualizados que produzem código incorreto com frequência | Atualização no próximo sprint |
| **Médio** | Casos de uso não cobertos que poderiam ser cobertos | Adicionar ao backlog com prioridade |
| **Baixo** | Melhorias de UX ou mensagens mais claras | Melhorar quando for conveniente |

---

### 4. Documentar e comunicar

Use o template em `.github/templates/reports/POST_MORTEM_TEMPLATE.md` para documentar a revisão.

Compartilhe o resultado com:
- Os Tech Leads das equipes que usam o subagente
- A equipe de governança, para atualizar o estado no catálogo

---

## Como reportar um problema com um subagente (sem fazer uma revisão completa)

Se você encontrar um problema pontual com um subagente, não é necessário fazer uma revisão completa. Abra um issue no `agents-factory` com:

- **Título:** `[BUG] Subagente <nome>: descrição do problema`
- **Descrição do problema:** o que você pediu, o que o subagente gerou, o que deveria ter gerado
- **Reprodutibilidade:** sempre acontece, ou foi uma vez?
- **Impacto:** o código gerado estava errado? Você detectou antes ou depois de aplicá-lo?

---

## Sinais de que um subagente precisa de revisão urgente

- Um desenvolvedor leva para produção código gerado pelo subagente que produz um incidente
- A equipe de Terraform/backend diz "paramos de usar o subagente porque ele sempre gera X errado"
- Uma skill que o subagente usa foi marcada como depreciada e o subagente não foi atualizado
- O subagente gera código que usa uma biblioteca que foi retirada do stack BRX

---

## Próximos passos

- [6.1 — Solicitar um novo subagente ou skill](01-solicitar-agente-ou-skill.md)
- [6.2 — Ciclo de vida de uma skill](02-ciclo-vida-skill.md)
- [Template de post-mortem](../../../.github/templates/reports/POST_MORTEM_TEMPLATE.md)
