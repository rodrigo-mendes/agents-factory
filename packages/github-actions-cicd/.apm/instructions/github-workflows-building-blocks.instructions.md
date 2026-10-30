---
name: github-workflows-building-blocks
description: "Guardrails for reusable workflows (_*.yml) and composite actions: typed contract, environment as input, secrets as inputs, no hardcoded environment values, SHA-pinned cross-repo refs. Use when creating or editing a building block."
applyTo: "**/.github/workflows/_*.{yml,yaml},**/.github/actions/**/action.{yml,yaml}"
---

# Building blocks: reusable workflows and composite actions

Reusable workflows are `_<domain>-<name>.yml` (workflows cannot live in subfolders); composite actions are `.github/actions/<domain>/<name>/action.yml`. Facts live in the skills below.

## Rules

1. A reusable workflow declares typed `inputs`, explicit `outputs`, each secret by name, and its own minimal `permissions`.
2. The deploy environment is an input; the block sets `environment: ${{ inputs.environment }}` on its job. Callers do not hold block logic.
3. Composite actions cannot read secrets directly: receive them as inputs from the calling job.
4. No hardcoded account IDs, regions, role ARNs, OCIDs, URLs or environment names; take them from inputs or environment variables.
5. Cross-repo references (central blocks repo) use a full commit SHA, never a branch or floating tag.
6. Examples and references use real paths: `./.github/workflows/_<name>.yml`, `./.github/actions/<domain>/<name>`.
7. Event text goes through `env:`, never inside `run:`.

## Load the skill

- `composing-github-actions-pipelines` for the block contract, catalog and central blocks repo.
- `federating-github-actions-aws-oidc`, `federating-github-actions-oci` for login composites.
- `securing-supply-chain-github-actions` for `_security-scan`.

## Always Do

- Document each input and output with `description`.
- Keep one responsibility per block; split build, publish and deploy.
- Pin every nested action by SHA with the tag as a comment.

## Never Do

- Use `secrets: inherit`. Alternative: declare and pass each secret by name.
- Read `secrets.*` inside a composite action. Alternative: add an input and pass it from the job.
- Hardcode environment values in a block. Alternative: typed input with no default for sensitive values.
- Reference a central-repo block by `@main`. Alternative: full SHA with tag comment.
- Put block logic in a `ci-`/`cd-` caller. Alternative: move it to a `_` workflow or composite.
