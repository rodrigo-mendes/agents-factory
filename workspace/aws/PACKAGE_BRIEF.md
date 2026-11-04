# Package brief — aws (migrate skills + build agent)

Frente 2 do plano: migrar as 40 skills AWS já autoradas (hoje em `workspace/.claude/skills/`) para
um pacote APM + construir o agente consultivo. Pesquisa já atual (docs/, sdk_java/, terraform/).

```yaml
slug: aws
language: en
frameworks:
  - AWS (cloud architecture, 2026 editions / Well-Architected Nov-2024)
needs:
  - empacotar 40 skills de arquitetura AWS (migração, não reautoria)
  - agente consultivo de arquitetura AWS que roteia para as skills
legacy_source: workspace/.claude/skills (40 skills autoradas)
deliverables: [skills, agent, rules, readme]
agent_kind: advisory
out_of_scope:
  - reautorar/reescrever as skills (migração as-is)
  - pesquisa nova (research já atual, threshold 2027)
research_worker: (n/a — migração)
rounds: 3
```

## Decisões para o G1
1. **Estrutura:** pacote único `aws-skills` + `aws-architect`, ou split por domínio (como OCI)?
2. **Sobreposições:** famílias `applying-aws-*` e `applying-waf-*` cobrem os mesmos pilares; 3 skills
   de custo; 2 de CloudTrail. Migrar todas as 40 as-is, ou de-duplicar/mesclar na migração?
3. **Family facts/rules:** semear a partir dos "Version Context" + blueprints de padrões
   (always-do/never-do/policy), verificando os fatos-chave contra docs oficiais AWS.
