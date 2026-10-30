# Never-do patterns with examples

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Every row has a documented alternative.

## Contents

- N1 Repository-scoped deploy secrets
- N2 Deploy credentials in pull_request
- N3 Key material in files or -backend-config
- N4 Output masking off
- N5 Wildcard impersonation rule
- N6 Admin app for the exchange
- N7 TLS verification off
- N8 Required reviewers as default gate
- N9 Service user for Path B
- N10 Administrator key for CI

## N1 Repository-scoped deploy secrets

Any workflow on any branch reads repository secrets; environment secrets go only to jobs that pass the environment rules.

```yaml
# ❌ env: OCI_CLI_KEY_CONTENT: ${{ secrets.OCI_PROD_KEY }}   (repository secret, no environment)
# ✅
environment: prod   # secret on the environment, deployment branch main
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## N2 Deploy credentials in pull_request

```yaml
# ❌ on: pull_request  ->  environment: prod
# ✅ on: pull_request  ->  environment: prod-pr   # read-only CI user
```

Branch code runs during plan; this is a family decision (rule 13), not a vendor claim.

## N3 Key material in files or -backend-config

The backend page: "Avoid hardcoding these values directly in your configuration or using the `-backend-config` flag with plaintext secrets."

```bash
# ❌ terraform init -backend-config="private_key=$OCI_CLI_KEY_CONTENT"
# ❌ private_key_path = "./ci-key.pem"   # committed next to the code
# ✅ umask 077; printf '%s\n' "$OCI_CLI_KEY_CONTENT" > "$RUNNER_TEMP/oci_api_key.pem"
#    terraform init -input=false -backend-config="private_key_path=$RUNNER_TEMP/oci_api_key.pem"
```

Source: https://developer.hashicorp.com/terraform/language/backend/oci

## N4 Output masking off

`silent: false` streams command output to the log and "may leak confidential information".

```yaml
# ❌ silent: false
# ✅ query: "data[].\"secret-name\""   # default masking kept
```

Source: https://raw.githubusercontent.com/oracle-actions/run-oci-cli-command/368cc7991534d1b8074846d10e1d84ac4c0d1a28/action.yml

## N5 Wildcard impersonation rule

Oracle's example maps `sub eq *`; rules stop at the first match and every GitHub repository shares one issuer, so a wildcard lets any repository impersonate the service user.

```json
// ❌ { "rule": "sub eq *", "value": "<ci_service_user_id>" }
// ✅ { "rule": "sub eq repo:my-org/my-repo:environment:prod", "value": "<ci_prod_service_user_id>" }
```

Repositories created after 2026-07-15 use `repo:OWNER@OWNER-ID/REPO@REPO-ID:environment:prod` (unverified, see [path A](./path-a-token-exchange.md)).
Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm and https://docs.github.com/en/actions/reference/security/oidc

## N6 Admin app for the exchange

The page recommends a second application without any admin role for the exchange call, listed in `oauthClients`.

```text
❌ OCI_WIF_CLIENT = client id and secret of the app holding Identity Domain Administrator
✅ OCI_WIF_CLIENT = confidential app with no admin role, listed in the trust's oauthClients
```

## N7 TLS verification off

Oracle's examples show `-k`; copying it exposes the GitHub JWT and the client secret.

```bash
# ❌ curl -k --location "https://$OCI_DOMAIN_URL/oauth2/v1/token" ...
# ✅ curl --fail --silent --show-error --location "https://$OCI_DOMAIN_URL/oauth2/v1/token" ...
```

## N8 Required reviewers as default gate

Required reviewers, wait timers and custom rules are public-repo only on Free, Pro and Team; on private repos the gate silently does not exist.

```text
❌ prod: Required reviewers = platform-team   (private repo on Team)
✅ prod: Deployment branches = main; approval = PR review on protected main
```

Source: https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments

## N9 Service user for Path B

```text
❌ serviceUser=true user as CI user (cannot hold API keys or passwords)
✅ regular user ci-app-deploy-<env>; serviceUser=true only as the Path A impersonation target
```

Source: https://docs.oracle.com/en-us/iaas/Content/Identity/api-getstarted/json_web_token_exchange.htm

## N10 Administrator key for CI

Administrators can push to any repository in the tenancy and manage other users' credentials.

```text
❌ OCI_CLI_USER = ocid1.user.oc1..<admin-human>   (member of Administrators)
✅ OCI_CLI_USER = ocid1.user.oc1..<ci-app-deploy>  (own group; push-only and bucket-scoped policies)
```

Source: https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm
