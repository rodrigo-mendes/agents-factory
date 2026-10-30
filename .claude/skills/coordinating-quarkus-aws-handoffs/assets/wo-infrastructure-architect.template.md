---
kind: work-order
id: wo-<nn>-infrastructure-architect
from: building-aws-saas-serverless-quarkus-react-nextjs
to: aws-infrastructure-architect
change: <change-id>
task: spec                       # E1-E4 work-orders use task: spec
refs: [verify-E2a]               # E2c starts after the solution architecture is verified; E4: [verify-E4-index]
requirements: [R1]
status: pending
createdAt: <ISO 8601 UTC>
---

## Scope

Stage: E2c (AWS infrastructure design) | E4 (`infra-design.md` of the change). Designs the AWS infrastructure that runs the
parts of E2a; never changes parts or contracts, never writes Terraform.
Output: files + `result-<nn>-infrastructure-architect.md` (kind `report`, outcome `success|partial|failed|needs-input`).
- E2c: `openspec/specs/infrastructure/spec.md` (12 sections: environments and accounts, part -> service map, network, edge, identity, secrets, data, observability, Terraform layout, CI/CD, cost, risks) and ADRs in `openspec/specs/infrastructure/adr/`.
- E4: `openspec/changes/<id>/infra-design.md` (new or changed resources per environment, IAM per Lambda, secrets, alarms, Terraform modules touched, pipeline effect, extra cost).
- The observability section is verified by `aws-architect-reviewer` (8-item check); `aws-observability` Mode A is not used in this flow.

## Skills

- <aws-skills the change needs, e.g. applying-aws-serverless-well-architected-lens, delivering-cloudfront-cdn, federating-github-actions-aws-oidc>

## Requirements

- R1: <requirement text> - infra consequence: <what must exist>.

## Applicable ADRs

- `architecture/adr/<NNN>-...`, `infrastructure/adr/<NNN>-...` - <what each forces>.

## Constraints

- GitHub plan and repo visibility (interview B8): <Free | Pro/Team | Enterprise | public>; Free means the weaker variant was accepted by the user.
- Inputs: `openspec/specs/architecture/spec.md`, contracts, `<paths>`. Unknown account/region -> `needs-input`.

## Limits

- review_rounds: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] All 12 sections present (E2c) or all parts of the change covered (E4); every claim cites a skill or is tagged `(unverified)`.
- [ ] ADRs use `assets/adr.template.md` with `area: infrastructure`, status `proposed`.
- [ ] Result record valid; the independent reviewer is `aws-architect-reviewer` (verify-E2c / verify-E4-infra).
