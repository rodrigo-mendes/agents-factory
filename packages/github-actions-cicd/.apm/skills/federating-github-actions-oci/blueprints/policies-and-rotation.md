# Policies, capabilities and rotation

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Group and compartment names are placeholders (Representative, adapt to your tenancy).

## Contents

- Users and groups
- OCIR push-only policy
- State bucket policy
- PR-only read user
- User capabilities
- Rotation with overlap

## Users and groups

One deploy user per environment (`ci-app-deploy-dev`, `ci-app-deploy-prod`) and one `ci-app-pr` user, each a regular user in its own group. Upload one API public key per user (maximum three) and generate one auth token on the user that pushes images (maximum two, they do not expire).
Source: https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm

## OCIR push-only policy

The repository policy page gives the push-restricted form with `request.permission` filters and the compartment form separately.

```text
Allow group ci-app-deploy to manage repos in tenancy where ANY {request.permission = 'REPOSITORY_READ', request.permission = 'REPOSITORY_UPDATE', request.permission = 'REPOSITORY_CREATE'}
Allow group ci-app-deploy to manage repos in compartment app-prod
```

Combining compartment scope with the permission filter in one statement is a composition of the two documented forms (medium confidence). Pull access for the PR user uses the `read` verb ("pull images, layers, and manifests").
Source: https://docs.oracle.com/en-us/iaas/Content/Registry/Concepts/registrypolicyrepoaccess.htm

## State bucket policy

The backend stores a lock object such as `tf-state-env/development/path/to/my/key.lock` in the same bucket, so the deploy group needs object management there. Scope it with the documented condition and enable bucket versioning ("highly recommended").

```text
Allow group ci-app-deploy to read buckets in compartment app-shared
Allow group ci-app-deploy to manage objects in compartment app-shared where target.bucket.name='tfstate-app'
```

Source: https://developer.hashicorp.com/terraform/language/backend/oci and https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm

## PR-only read user

Grant `ci-app-pr` read and inspect verbs only (verb semantics per the OCI policy documentation), for example `Allow group ci-app-pr to read all-resources in compartment app-dev`. Such a user cannot write the backend lock object; whether PR plans run with locking disabled is unverified and belongs to the Terraform skill. Identity-domain group prefix syntax in policies was not confirmed (unverified); copy the syntax your tenancy already uses.
Source: https://docs.oracle.com/en-us/iaas/Content/Identity/Concepts/commonpolicies.htm

## User capabilities

Identity-domain capabilities are local password, API keys, auth token, SMTP credentials, customer secret keys, OAuth 2.0 client credentials and database passwords; an administrator selects or clears each. The deploy user needs API keys, plus auth token only when it pushes images. Clearing the rest is least privilege by design, not stated by the page (medium confidence).
Source: https://docs.oracle.com/en-us/iaas/Content/Identity/users/edit-users-capabilities.htm

## Rotation with overlap

The per-user limits leave room to add the new credential before deleting the old one (overlap procedure, medium confidence; no official rotation page was found).

1. Upload a new API public key, or generate a new auth token, for the CI user.
2. Update the environment secrets (`OCI_CLI_FINGERPRINT` and `OCI_CLI_KEY_CONTENT`, or `OCIR_AUTH_TOKEN`).
3. Run a smoke job (`oci os ns get`).
4. Delete the old key or token.

Auth tokens never expire, so rotation is the only bound on their lifetime. Oracle states no rotation interval (unverified); treat it as an organisational decision.
Source: https://docs.oracle.com/iaas/Content/Identity/access/working-with-console-passwords-and-API-keys.htm and https://docs.oracle.com/iaas/Content/Identity/Tasks/managingcredentials.htm
