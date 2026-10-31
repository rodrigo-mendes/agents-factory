# Composite actions

Back to [SKILL.md](../SKILL.md). GitHub.com docs as of 2026-10-30. Reusable-workflow rules are in [always-do patterns](./always-do-patterns.md).

## Rules

- `runs.using` must be `composite`; `shell` is required on every `run` step; outputs need `value` (https://docs.github.com/en/actions/reference/workflows-and-actions/metadata-syntax).
- Inputs are read through the `inputs` context; a composite action does not get `INPUT_<NAME>` variables, and `required: true` does not raise an error by itself, so validate in a step (same page).
- The `secrets` context is not available in composite actions; the caller passes secrets as inputs (https://docs.github.com/en/actions/reference/workflows-and-actions/contexts).
- GitHub recommends the `.github/actions` subfolder; family layout is `.github/actions/<domain>/<name>/action.yml` (https://docs.github.com/en/actions/creating-actions/creating-a-composite-action).
- A composite action logs as one step of the caller's job and cannot choose a runner; keep it short so a failure is easy to locate. Up to 10 composite actions can nest in one workflow.
- Action versions never come from GitHub's doc examples; use the family facts pins.

## Example: `./.github/actions/node/setup/action.yml`

```yaml
name: node-setup
description: Install Node.js and project dependencies for one app directory
inputs:
  node-version:
    description: Node.js major
    required: true
  working-directory:
    description: App directory containing package-lock.json
    required: true
  npm-token:
    description: Optional read token for a private registry, passed by the caller
    required: false
    default: ""
outputs:
  node-path:
    description: Path of the node binary
    value: ${{ steps.which.outputs.path }}
runs:
  using: composite
  steps:
    - uses: actions/setup-node@949feb2413d6458794dcd2491c4babbbce0c15c1 # v7.1.0
      with:
        node-version: ${{ inputs.node-version }}
    - name: Fail fast on missing required input
      shell: bash
      env:
        WD: ${{ inputs.working-directory }}
      run: test -n "$WD" || { echo "working-directory is required"; exit 1; }
    - name: Install
      shell: bash
      working-directory: ${{ inputs.working-directory }}
      env:
        NODE_AUTH_TOKEN: ${{ inputs.npm-token }}
      run: npm ci
    - id: which
      shell: bash
      run: echo "path=$(command -v node)" >> "$GITHUB_OUTPUT"
```

The built-in dependency cache of `setup-node` is left out on purpose: its input names were not confirmed (unverified). Cache semantics that were confirmed: restore by exact `key`, then `restore-keys`; 10 GB default per repository; entries unused for 7 days are removed; anyone with read access can read cache contents, so never cache credentials (https://docs.github.com/en/actions/reference/workflows-and-actions/dependency-caching). Direct use of `actions/cache` pins v6.1.0 = `55cc8345863c7cc4c66a329aec7e433d2d1c52a9`.

## Composite action or reusable workflow

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| Composite action | Runs in the caller's job, shares the workspace, no extra runner | No secrets context, one log step, no jobs or environments | Setup toolchain, install, lint, compute metadata |
| Reusable workflow | Own jobs and runners, secrets, environments, separate logs | New runner per job (share files by artifact); 50 unique per file | A whole stage: build, test matrix, deploy |

Source: https://docs.github.com/en/actions/concepts/workflows-and-actions/reusing-workflow-configurations
