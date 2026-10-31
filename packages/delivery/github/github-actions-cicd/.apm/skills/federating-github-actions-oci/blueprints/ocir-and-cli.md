# OCIR and OCI CLI actions

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Image build and push belong to `publishing-container-images-github-actions`; this blueprint covers only login and CLI commands.

## Contents

- OCIR login with login-ocir
- Fallback: plain docker login
- Registry host form
- OCI CLI with run-oci-cli-command
- Node 20 risk

## OCIR login with login-ocir

`login-ocir` v1.3.0 requires the input `auth_token`, needs the five `OCI_CLI_*` variables, outputs `ocir_endpoint` and `ocir_username`, logs in Docker and Podman, and logs out in a `post` step. It declares `runs.using: node20`. An OCIR login always needs an auth token: IAM service users cannot hold API keys or passwords, and the action has no token-exchange input.

```yaml
# Representative, adapt to your environment
environment: prod
env:
  OCI_CLI_USER: ${{ secrets.OCI_CLI_USER }}
  OCI_CLI_TENANCY: ${{ secrets.OCI_CLI_TENANCY }}
  OCI_CLI_FINGERPRINT: ${{ secrets.OCI_CLI_FINGERPRINT }}
  OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_CLI_KEY_CONTENT }}
  OCI_CLI_REGION: ${{ vars.OCI_CLI_REGION }}
steps:
  - id: ocir
    uses: oracle-actions/login-ocir@d65011bf8c9300e51a98658388a0fb46d1ed54b1 # v1.3.0
    with:
      auth_token: ${{ secrets.OCIR_AUTH_TOKEN }}
  - name: Use outputs
    shell: bash
    env:
      ENDPOINT: ${{ steps.ocir.outputs.ocir_endpoint }}
    run: echo "registry host is $ENDPOINT"
```

Whether `login-ocir` handles identity-domain usernames is not documented (unverified).
Source: https://raw.githubusercontent.com/oracle-actions/login-ocir/d65011bf8c9300e51a98658388a0fb46d1ed54b1/action.yml and https://github.com/oracle-actions/login-ocir

## Fallback: plain docker login

Oracle documents `docker login` with username `<tenancy-namespace>/<username>` and the auth token as password. Use it when the node20 action fails or a third-party action is refused.

```yaml
- name: Login to OCIR without a third-party action
  shell: bash
  env:
    OCIR_HOST: ${{ vars.OCIR_HOST }}
    OCIR_USERNAME: ${{ vars.OCIR_NAMESPACE }}/${{ vars.OCIR_USER }}
    OCIR_AUTH_TOKEN: ${{ secrets.OCIR_AUTH_TOKEN }}
  run: printf '%s' "$OCIR_AUTH_TOKEN" | docker login "$OCIR_HOST" --username "$OCIR_USERNAME" --password-stdin
```

Pre-create the repositories: a policy on a non-root compartment does not allow creating a repository in the root compartment, so a first push to a missing repository fails.
Source: https://docs.oracle.com/en-us/iaas/Content/Registry/Tasks/registrypushingimagesusingthedockercli.htm and https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm

## Registry host form

Two forms appear in official pages: `ocir.<region-identifier>.oci.oraclecloud.com` (docker push how-to) and `<region-identifier>.ocir.io` or `<region-key>.ocir.io` (prerequisites table, OC1 realm only). Which is preferred is unverified. Use the `ocir_endpoint` output when `login-ocir` runs; otherwise ask which form the tenancy already uses.
Source: https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registryprerequisites.htm

## OCI CLI with run-oci-cli-command

`run-oci-cli-command` v1.3.2 takes `command` and optional `query`; the release note reads "fix: handle successful commands with no output". Keep `silent` at its default. The action declares `runs.using: node20`.

```yaml
- id: ns
  uses: oracle-actions/run-oci-cli-command@368cc7991534d1b8074846d10e1d84ac4c0d1a28 # v1.3.2
  with:
    command: os ns get
    query: data
```

Source: https://github.com/oracle-actions/run-oci-cli-command/releases/tag/v1.3.2

## Node 20 risk

Runners default to Node 24 since 2026-06-16 and removed Node 20 on 2026-09-23; the changelog does not say what happens to actions that declare `node20` (unverified). Run one smoke job (`os ns get`) on a GitHub-hosted runner before relying on either action. If it fails, switch OCIR to the plain `docker login` above and run `oci` directly after installing the CLI; no CLI release is pinned by this skill.
Source: https://github.blog/changelog/2026-09-23-deprecation-of-node-20-on-github-actions-runners/

`oracle-actions/get-ocir-repository` exists in the organization but has no pinned SHA in the family facts, so no example is given; create repositories with Terraform or the console.
