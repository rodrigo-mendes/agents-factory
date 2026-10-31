# Composite action login-oci

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Inputs per family design: `auth-mode` (`api-key` default or `token-exchange`) and `region`. Credentials are not inputs: the caller job sets them as `env` from environment secrets, and the composite reads that environment (family decision). Token-exchange script: [path A](./path-a-token-exchange.md).

## Contents

- Action file
- Caller job (reusable workflow body)
- Notes

## Action file

Path: `./.github/actions/cloud/login-oci/action.yml` (family rule 5 layout).

```yaml
# Representative, adapt to your environment
name: login-oci
description: Prepare OCI credentials for the CLI, the Terraform provider and the oci backend
inputs:
  auth-mode:
    description: api-key (default) or token-exchange
    required: false
    default: api-key
  region:
    description: OCI region identifier, for example us-ashburn-1
    required: true
outputs:
  key-path:
    description: Signing key file under RUNNER_TEMP (api-key mode only)
    value: ${{ steps.key.outputs.key-path }}
runs:
  using: composite
  steps:
    - name: Validate auth-mode
      shell: bash
      env:
        AUTH_MODE: ${{ inputs.auth-mode }}
      run: |
        case "$AUTH_MODE" in
          api-key|token-exchange) ;;
          *) echo "unsupported auth-mode: $AUTH_MODE" >&2; exit 1 ;;
        esac
    - name: Export region
      shell: bash
      env:
        REGION_INPUT: ${{ inputs.region }}
      run: |
        echo "OCI_CLI_REGION=$REGION_INPUT" >> "$GITHUB_ENV"
        echo "OCI_REGION=$REGION_INPUT" >> "$GITHUB_ENV"
    - name: Write API key file
      id: key
      if: inputs.auth-mode == 'api-key'
      shell: bash
      run: |
        : "${OCI_CLI_KEY_CONTENT:?set OCI_CLI_KEY_CONTENT from an environment secret}"
        umask 077
        printf '%s\n' "$OCI_CLI_KEY_CONTENT" > "$RUNNER_TEMP/oci_api_key.pem"
        echo "key-path=$RUNNER_TEMP/oci_api_key.pem" >> "$GITHUB_OUTPUT"
    - name: Token exchange
      if: inputs.auth-mode == 'token-exchange'
      shell: bash
      run: bash "$GITHUB_ACTION_PATH/exchange.sh"
```

Source for the variable names and the key-as-file rule: https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clienvironmentvariables.htm and https://developer.hashicorp.com/terraform/language/backend/oci

## Caller job (reusable workflow body)

```yaml
# ./.github/workflows/_oci-deploy.yml (representative)
on:
  workflow_call:
    inputs:
      environment: { type: string, required: true }
      region:      { type: string, required: true }
    # no `secrets:` block: the job declares `environment:` and reads that
    # environment's secrets directly (the caller never passes them)
permissions:
  contents: read
jobs:
  deploy:
    runs-on: ubuntu-latest
    timeout-minutes: 30
    environment: ${{ inputs.environment }}
    env:
      OCI_CLI_USER: ${{ secrets.OCI_CLI_USER }}
      OCI_CLI_TENANCY: ${{ secrets.OCI_CLI_TENANCY }}
      OCI_CLI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
      OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_CLI_KEY_CONTENT }}
      OCI_TENANCY_OCID: ${{ secrets.OCI_CLI_TENANCY }}
      OCI_USER_OCID: ${{ secrets.OCI_CLI_USER }}
      OCI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
      OCI_PRIVATE_KEY: ${{ secrets.OCI_CLI_KEY_CONTENT }}
    steps:
      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
      - id: login
        uses: ./.github/actions/cloud/login-oci
        with:
          auth-mode: api-key
          region: ${{ inputs.region }}
      - uses: hashicorp/setup-terraform@dfe3c3f87815947d99a8997f908cb6525fc44e9e # v4.0.1
        with:
          terraform_version: "1.17.1"
          terraform_wrapper: false
      - name: terraform init (identifiers only; backend body owned by the Terraform skill)
        shell: bash
        env:
          KEY_PATH: ${{ steps.login.outputs.key-path }}
        run: |
          terraform init -input=false \
            -backend-config="tenancy_ocid=$OCI_CLI_TENANCY" \
            -backend-config="user_ocid=$OCI_CLI_USER" \
            -backend-config="fingerprint=$OCI_CLI_FINGERPRINT" \
            -backend-config="private_key_path=$KEY_PATH" \
            -backend-config="region=$OCI_CLI_REGION"
```

## Notes

- `environment` is `<env>` for deploy and `<env>-pr` for pull requests (for example `prod` and `prod-pr`); the Free variant has no environments, see [plan variants](./plan-variants.md) (repository secrets, with a warning).
- The `token-exchange` step runs the file `exchange.sh` stored next to `action.yml`; its content is the script block in [path A](./path-a-token-exchange.md).
- The checkout step comes first because a local `./.github/actions/...` reference needs the repository files on disk.
- OCIDs and the fingerprint are identifiers; the secret (key content) reaches only a mode 600 file (documented warning: avoid plaintext secrets in `-backend-config`).
- Backend environment-variable names other than the documented `OCI_region` example are not listed on the backend page (unverified), so the skill passes identifiers with `-backend-config`.
- `id-token: write` is not needed in `api-key` mode; add it only to the job that uses `token-exchange` (family rule 7).
- Pass untrusted values through `env`, not inline expressions; see `automating-github-repos-with-actions`.
