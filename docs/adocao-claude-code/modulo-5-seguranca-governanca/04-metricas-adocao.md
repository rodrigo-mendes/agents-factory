# Métricas de adoção: como medir e reportar

**Perfil:** Equipe de Governança BRX / Tech Lead  
**Tempo estimado de leitura:** 8 min

---

## Por que medir a adoção

As métricas de adoção servem para três coisas:
1. **Justificar o investimento** do programa perante a direção
2. **Identificar oportunidades** de melhoria nos guias e agentes
3. **Detectar equipes** que precisam de mais suporte

Sem métricas, é impossível saber se o programa está funcionando ou o que mudar.

---

## Fontes de dados disponíveis

### Anthropic Console (uso da organização)

O Anthropic Console fornece uma visão de administração com o uso agregado por organização e por usuário. Acessível pelos administradores da organização Anthropic da BRX.

Métricas disponíveis diretamente:

| Métrica | Descrição |
|---|---|
| Usuários ativos | Usuários que usaram o Claude Code ao menos uma vez no período |
| Tokens consumidos | Total de tokens de entrada/saída no período (por organização/usuário) |
| Custo | Gasto associado ao consumo de tokens no período |
| Sessões | Número de sessões/conversas iniciadas |
| Uso por modelo | Distribuição do consumo entre Opus / Sonnet / Haiku / Fable |

> O Console permite exportar esses dados (por exemplo, em CSV) para análise em Excel/Sheets. Não há uma métrica de "acceptance rate de sugestões inline" como em ferramentas de autocompletar: no Claude Code, o sinal equivalente é a **aceitação de edições/diffs propostos** pelo agente, medida através de pesquisas ou instrumentação própria do programa.

---

## KPIs recomendados para o programa BRX

### KPIs de adoção (uso do programa)

| KPI | Descrição | Periodicidade |
|---|---|---|
| **Taxa de ativação** | % de licenças atribuídas com ao menos 1 uso ativo nos últimos 30 dias | Mensal |
| **Adoção por equipe** | Nº de equipes com taxa de ativação > 70% | Mensal |
| **Retenção de uso** | % de usuários ativos no mês passado que seguem ativos este mês | Mensal |

### KPIs de qualidade de uso

| KPI | Descrição | Periodicidade |
|---|---|---|
| **Aceitação de edições/diffs** | % de diffs propostos pelo Claude que são aceitos (via pesquisa ou instrumentação própria) | Semanal |
| **Uso de subagentes/skills** | Nº de invocações de subagentes (`/<nome-do-agente>`) e skills por semana | Semanal |
| **Sessões e tokens por período** | Nº de sessões e tokens consumidos por equipe/usuário (do Console) | Mensal |

### KPIs de impacto (mais difíceis, mas mais valiosos)

Estes não vêm automaticamente do Console e exigem pesquisas ou proxies:

| KPI | Como medir |
|---|---|
| **Tempo economizado percebido** | Pesquisa mensal (escala 1-5: "O Claude Code me economiza tempo no meu trabalho diário") |
| **Satisfação com os subagentes** | Pesquisa trimestral por domínio (backend, infra, QA) |
| **Qualidade do código gerado** | % de PRs em que o revisor reporta "código gerado por IA sem revisão suficiente" |

---

## Como acessar os dados do Console

**Para administradores da organização:**

1. Acesse o **Anthropic Console** com uma conta de administrador da organização da BRX
2. Vá à seção de **Uso / Usage** (uso por organização e por usuário, tokens e custo)
3. Filtre pelo período desejado (e por membro/equipe, quando disponível)
4. **Exporte em CSV** para análise em Excel/Sheets

**Automação:**

O Console/organização Anthropic expõe o uso e permite exportação, o que possibilita alimentar dashboards internos com os dados de consumo (usuários ativos, tokens, custo). Combine esses dados com métricas próprias do programa (uso de subagentes/skills, pesquisas de satisfação) para ter a visão completa. Consulte a documentação vigente do Console para os detalhes de exportação/integração disponíveis.

---

## Cadência de reporte recomendada

| Frequência | Audiência | Conteúdo |
|---|---|---|
| **Semanal** | Equipe de Governança BRX interna | Aceitação de edições, uso de subagentes/skills, anomalias |
| **Mensal** | Tech Leads das equipes | Métricas da equipe, comparativo com o mês anterior |
| **Trimestral** | Direção | Resumo de adoção, ROI estimado, roadmap |

---

## Como interpretar as métricas de uso

Como o Claude Code é um agente (e não um autocompletar), evite reduzir o sucesso a um único número como "% de sugestões aceitas". Interprete os sinais em conjunto:

| Sinal | Interpretação |
|---|---|
| Poucas sessões / poucos tokens | Baixo uso. Pode indicar: falta de onboarding, atrito no setup, ou desconhecimento dos casos de uso. |
| Uso constante, mas sem subagentes/skills | Uso básico. Oportunidade de treinar a equipe nos agentes e skills do ecossistema BRX. |
| Uso de subagentes/skills crescente | Adoção madura. A equipe incorporou o ecossistema ao fluxo de trabalho. |

**Importante:** um volume de tokens alto não é, por si só, sinal de sucesso — assim como um volume baixo não é necessariamente ruim. Uma equipe que usa o Claude Code de forma pontual e certeira pode ter alto impacto real com consumo moderado. Cruze sempre os números de uso com a satisfação percebida e a qualidade do código.

---

## Modelo de relatório mensal

```markdown
# Relatório de Adoção do Claude Code — [Mês] [Ano]

## Resumo executivo
- Usuários ativos: X de Y licenças (Z%)
- Equipes com adoção > 70%: N
- Aceitação de edições (média): X%
- Invocações de subagentes/skills BRX: N
- Tokens consumidos no período: N (custo estimado: R$ X)

## Por equipe
[tabela: Equipe | Usuários ativos | Aceitação de edições | Uso de subagentes/skills | Tokens]

## Destaques
[2-3 conquistas ou casos de sucesso do mês]

## Áreas de melhoria
[2-3 equipes ou áreas com adoção baixa e plano de ação]

## Próximos passos do programa
[ações do próximo mês]
```

---

## Próximos passos

- [Módulo 6 — Contribuir para o ecossistema](../modulo-6-contribuir-ecossistema/README.md)
- [5.1 — O que não compartilhar com o Claude Code](01-o-que-nao-compartilhar.md)
