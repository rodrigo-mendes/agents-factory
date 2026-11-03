# Package brief — terraform (agent layer only)

Frente 1 do plano: adicionar apenas a camada de agente ao pacote existente `packages/terraform`.
As 3 skills já existem (2 researchers + terraform-instructions-compiler); pesquisa/autoria de skills
são puladas.

```yaml
slug: terraform-agent               # workspace dir; o pacote alvo é packages/terraform (existente)
language: en
frameworks:
  - Terraform 1.x (provider aws ~> 6.x)
needs:
  - agent que orquestre o fluxo research → compile de rules Terraform (ou engenharia de HCL — decidir no G1)
legacy_source: none
deliverables: [agent, rules, orchestrator-skill]
agent_kind: executor                # a confirmar no G1 (executor vs advisory)
out_of_scope:
  - reescrever/retrabalhar as 3 skills existentes
  - gerar novas skills de conhecimento HCL (isso viria de outro pacote)
research_worker: terraform-engineering-best-practices-researcher
rounds: 3
```

## Nota de escopo para o G1
O pacote `packages/terraform` é um toolkit de **pesquisa + compilação de rules**, não um pacote de
conhecimento HCL. Logo, "agente de engenharia Terraform" tem duas leituras possíveis — ver G1.
