# Validate: federating-github-actions-oci (P6 r1, 2026-10-30)

Score: 90.0 (1 HIGH, 1 MEDIUM, 3 LOW). SKILL.md 135 lines. SHAs match F2, F10, F34, F35. Rule 13/16 model correct and the clearest in the family (N8 rejects required reviewers). Verification Loop, 5 scenarios, register counts (11/1/7/5) correct.

## HIGH
- H1 (rule 10, cross-skill, blueprints/login-oci-action.md:76-80,88-91): the reusable `_oci-deploy.yml` declares `secrets: OCI_CLI_USER ... required: true` under `workflow_call` while the job sets `environment: ${{ inputs.environment }}`. A caller job cannot use `environment:` and cannot read the callee's environment secrets, so with `required: true` it must pass repository-scoped secrets, defeating environment-scoped secrets. Composing A4/M4 says an environment secret works only when not declared required. Fix: drop the `secrets:` block (read environment secrets inside the called job) or mark them `required: false` and say why.

## MEDIUM
- M1 (A4 consistency): immutable environment `sub` stated as fact at never-do-patterns.md:72, path-a-token-exchange.md:43, plan-variants.md:37; the aws skill tags the same string (unverified, its U1). Fix: add (unverified) or reference the aws register.

## LOW
- L1 (A4, SKILL.md:59,88; blueprints): "family rule 13/5/7" references are unresolvable at run time.
- L2 (login-oci-action.md:62): composite calls `exchange.sh`, which exists only inline in path-a-token-exchange.md; say the file must be created.
- L3 (login-oci-action.md:97,103): checkout without `persist-credentials: false`; `setup-terraform` without `terraform_wrapper: false` (differs from the terraform skill pin pattern).
