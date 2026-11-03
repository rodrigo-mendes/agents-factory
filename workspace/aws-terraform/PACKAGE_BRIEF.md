# Package brief — aws-terraform (new build, per-unit research)

Frente 5: pacote de skills HCL AWS + o agente executor `terraform-engineer` (no pacote `terraform`).
Pesquisa antiga em `workspace/terraform/` (26 arquivos, 2026-05, Terraform 1.7/1.9 EOL, aws 6.47.0)
serve só de referência; cada unidade é re-pesquisada na versão atual.

```yaml
slug: aws-terraform
language: en
frameworks:
  - Terraform 1.16.x (1.16.6, 2026-10-14; G1b) — 1.17.0 em RC
  - hashicorp/aws provider 6.x (~> 6.69; 6.69.0, 2026-10-14)
needs:
  - 26 skills version-locked, uma por serviço AWS, para provisionar via Terraform
  - agente executor terraform-engineer (pacote terraform) consumindo-as
legacy_source: workspace/terraform/ (referência, não base de autoria)
deliverables: [skills, agent, rules, readme]
agent_kind: executor
research_worker: researching-technical-frameworks
rounds: 3
```

## Unidades (26) — naming `provisioning-aws-<service>-v6`
acm, api-gateway, cloudfront, cloudtrail, cloudwatch, cognito, cost-management, dynamodb,
eventbridge, iam, kms, lambda, organizations, parameter-store, route53, s3, sam, ses, sns, sqs,
secrets-manager, shield, step-functions, vpc, waf, xray

Piloto (P3): **vpc**. Template herdado: formato híbrido do stripe-java (registros U/M/L,
Tag-to-register mapping, cenários `success_criteria: {must_pass, must_not}`).
