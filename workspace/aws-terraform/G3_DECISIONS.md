# G3 — decisões pendentes (aws-terraform + terraform-engineer)

Escrito pelo orquestrador em 2026-10-23, antes do P6. Escopo: pacote `aws-terraform` (26 skills + 3 instructions) e o agente `terraform-engineer` + roteador em `packages/terraform`.

## A. Decisões de família (afetam as 26 skills)

| # | Tema | Situação | Opções | Recomendação |
|---|---|---|---|---|
| A1 | Confiança de páginas da branch `main` do provider | A regra de evidência limita páginas "latest/main" a confiança média; as 26 skills as tratam como alta (as páginas do registry não renderizam; o `main` é o upstream) | (a) manter alta e registrar a convenção; (b) limitar a média: mover as regras 🚫 apoiadas só em `main` para "perguntar primeiro" | (a) |
| A2 | Palavra "medium" como severidade do Security Hub | A política proíbe a palavra solta em títulos (colide com `(medium confidence)`); o corpo usa "medium severity" | (a) manter; (b) trocar tudo por "moderate" | (a) |
| A3 | Datas de leitura dos lotes 1–4 | Cada skill cita datas por fonte de 14/10 a 22/10; verdadeiras, mas mais antigas que a releitura de 23/10 | (a) deixar; (b) passada mecânica unificando para 23/10 as fontes dos fatos compartilhados | (b), no P7 |
| A4 | Alvo Terraform `~> 1.16` com 1.17.0 estável (21/10) | Decisão sua (22/10); 1.17.0 está como risco de versão em todas | (a) manter; (b) migrar depois do commit | (a) |

## B. Lacunas de pesquisa conhecidas (não confirmadas; ficam como itens "unverified")

CloudFront: argumentos do logging v2 (delivery destination/delivery) e a afirmação "endpoint de site S3 serve só HTTP"; WAF: HCL de `aws_wafv2_web_acl_rule_group_association` e nomes completos do APIGateway.11; API Gateway: variante edge do domínio e JWT route; SES: ausência de recurso v2 de espera de verificação, sufixo do CNAME DKIM; X-Ray: unicidade de prioridade e regra Default; DynamoDB: nome da métrica de escrita do autoscaling; SAM: versão mínima do Terraform no hook, `ignore_changes` do stack set; Cost Management: destroy de cost allocation tag, cancelamento de Savings Plan. Opções: (a) aceitar como lacunas documentadas; (b) nova rodada de pesquisa direcionada nas 6 mais úteis. Recomendação: (a).

## C. Itens leves deixados por unidade (julgamento, fora dos graves/médios)

Lambda (L2 `function_response_types`, datas de runtime repetidas, bloco 🚫 do papel da VPC só como comentário); Secrets Manager; Cognito (4); SES (N3/N4/N6); SAM (3); Cost Management (L3/5/6/7/9/10, F17 elementos); API Gateway (L-9 nomes do APIGateway.11); Organizations (N2/N3/N5); S3/Route 53 (itens do §C anterior). Recomendação: aceitar; nenhum afeta fato.

## D. Herdados de frentes anteriores

- Cópias órfãs em `workspace/.claude/skills/` (mantidas por decisão sua).
- 10 links de blueprint pendentes em skills AWS migradas (Frente 2) e sobreposições de tópico.
- Links entre pacotes OCI/terraform que resolvem só no `apm install` (verify_package acusa; esperado).
- Consolidação dos fatos de família OCI.
- `verify_skill.py` quebra ao imprimir emoji no console cp1252 (não bloqueia; correção de 1 linha no script).

## E. Plano de commit proposto (G3)

1. `feat(aws-terraform): add 26 AWS Terraform skills + instructions` — `packages/aws-terraform/`
2. `feat(terraform): add terraform-engineer agent + provision-aws-terraform` — `packages/terraform/`
Workspace de trabalho (`workspace/aws-terraform/`) NÃO versionado (mesma decisão das outras frentes). Sem push (G4 é seu). Antes: P6 (qualidade), P7 (varredura), P8 (`apm install` + `.claude/` + contagens + docs).
