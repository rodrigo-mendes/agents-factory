# Path A: token exchange (optional, medium confidence)

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Path B (API key) stays the default. The exchange mechanism is official; using it with GitHub tokens is documented only by an Oracle A-Team post (community), and consumption of an external token by the CLI and provider is unverified.

## Contents

- What Path A does and does not remove
- Trust definition
- Exchange script
- Provider and CLI consumption
- Limits

## What Path A does and does not remove

- GitHub OIDC token (issuer `https://token.actions.githubusercontent.com`, JWKS `https://token.actions.githubusercontent.com/.well-known/jwks`) is exchanged at `https://<domainURL>/oauth2/v1/token` for a User Principal Session Token, validated by an Identity Propagation Trust.
- The exchange call still authenticates with the client id and secret of an identity-domain confidential application, so one static secret remains.
- OCIR login still needs an auth token (`login-ocir` requires `auth_token`).
- The newer workload-identity flow with an ephemeral resource principal token has no page on docs.oracle.com that the research could read, so it is left out (unverified).

Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm

## Trust definition

Run once by an Identity Domain Administrator. Use a non-admin confidential app in `oauthClients`. Never copy `sub eq *`.

```json
{
  "schemas": ["urn:ietf:params:scim:schemas:oracle:idcs:IdentityPropagationTrust"],
  "name": "github-actions-my-repo",
  "type": "JWT",
  "issuer": "https://token.actions.githubusercontent.com",
  "publicKeyEndpoint": "https://token.actions.githubusercontent.com/.well-known/jwks",
  "active": true,
  "oauthClients": ["<non-admin-confidential-app-client-id>"],
  "allowImpersonation": true,
  "subjectType": "User",
  "impersonationServiceUsers": [
    { "rule": "sub eq repo:my-org/my-repo:environment:prod", "value": "<ci_prod_service_user_id>" }
  ]
}
```

- Repositories created after 2026-07-15 emit `repo:OWNER@OWNER-ID/REPO@REPO-ID:environment:prod` (unverified: the immutable form is not shown on the Oracle page); older ones keep `repo:OWNER/REPO:...` unless they opt in. Write the rule for the format your repository emits.
- The attribute table names the field `impersonatingServiceUsers` while examples use `impersonationServiceUsers`; check the domain API.
- The page says "Use unique issuer", so one GitHub issuer per domain means one trust with several rules (medium confidence).
- Whether OCI validates the JWT `aud` claim, and against what, is not documented (unverified).

## Exchange script

File `./.github/actions/cloud/login-oci/exchange.sh` (create it next to `action.yml`; the composite runs it in `token-exchange` mode). The job needs `permissions: id-token: write` and env `OCI_WIF_CLIENT_ID`, `OCI_WIF_CLIENT_SECRET`, `OCI_DOMAIN_URL`, `OCI_WIF_AUDIENCE`, `OCI_TENANCY_OCID` from environment secrets.

```bash
#!/usr/bin/env bash
# Representative, adapt to your environment
set -euo pipefail
umask 077; mkdir -p "$HOME/.oci"
JWT=$(curl --fail --silent --show-error -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \
  "$ACTIONS_ID_TOKEN_REQUEST_URL&audience=$OCI_WIF_AUDIENCE" | jq -r .value)
openssl genrsa -out "$HOME/.oci/wif_key.pem" 2048
openssl rsa -in "$HOME/.oci/wif_key.pem" -pubout -out "$HOME/.oci/wif_pub.pem"
PUB=$(grep -v -- '-----' "$HOME/.oci/wif_pub.pem" | tr -d '\n')   # encoding expected by public_key: unverified
curl --fail --silent --show-error --location "https://$OCI_DOMAIN_URL/oauth2/v1/token" \
  -u "$OCI_WIF_CLIENT_ID:$OCI_WIF_CLIENT_SECRET" \
  --data-urlencode 'grant_type=urn:ietf:params:oauth:grant-type:token-exchange' \
  --data-urlencode 'requested_token_type=urn:oci:token-type:oci-upst' \
  --data-urlencode "public_key=$PUB" \
  --data-urlencode "subject_token=$JWT" \
  --data-urlencode 'subject_token_type=jwt' | jq -r .token > "$HOME/.oci/upst"
printf '[CI]\ntenancy=%s\nregion=%s\nkey_file=%s\nsecurity_token_file=%s\n' \
  "$OCI_TENANCY_OCID" "$OCI_REGION" "$HOME/.oci/wif_key.pem" "$HOME/.oci/upst" > "$HOME/.oci/config"
echo "OCI_CLI_PROFILE=CI" >> "$GITHUB_ENV"
echo "OCI_CLI_AUTH=security_token" >> "$GITHUB_ENV"
```

## Provider and CLI consumption

```hcl
# Terraform 1.17.x; external token consumption is unverified
provider "oci" {
  auth                = "SecurityToken"
  config_file_profile = "CI"
  region              = var.region
}
```

The `oci` backend accepts `auth = "SecurityToken"` and `config_file_profile`. These entries are documented for tokens created by `oci session authenticate`, not for an exchanged token (unverified). Run a manual smoke test before adopting Path A.
Source: https://docs.oracle.com/en-us/iaas/Content/dev/terraform/configuring.htm and https://docs.oracle.com/en-us/iaas/Content/API/SDKDocs/clitoken.htm

## Limits

- The Terraform page warns that a session token "expires after one hour"; for exchanged tokens about 60 minutes applies (medium confidence). Do not use Path A for jobs that may run longer.
- OCI Audit shows the impersonating principal in `source_authn_prin`; audit queries were not researched.
