# State backends: S3 and oci

Back to [SKILL.md](../SKILL.md). Terraform 1.17.1; research date 2026-10-30. One state per environment and component; locking on; versioning on; no secrets in backend values.

## AWS: S3 with lock file

```hcl
# backend.tf (partial configuration)
terraform {
  backend "s3" {
    use_lockfile = true
    encrypt      = true
  }
}
```

```text
# infra/env/prod/network.s3.tfbackend  (non-secret values only)
bucket = "acme-tfstate-prod"
key    = "network/prod/terraform.tfstate"
region = "eu-west-1"
```

```bash
terraform init -input=false -backend-config=../env/prod/network.s3.tfbackend
```

| Item | Value | Source |
|---|---|---|
| Locking | `use_lockfile = true`; default `false`, so unlocked unless set | https://developer.hashicorp.com/terraform/language/backend/s3 |
| DynamoDB | `dynamodb_table` is deprecated and "will be removed in a future minor version" | same page |
| IAM for the lock file | `s3:GetObject`, `s3:PutObject`, `s3:DeleteObject` | same page |
| Versioning | "highly recommended" for state recovery | same page |
| KMS (optional) | `kms_key_id` needs `kms:Encrypt`, `kms:Decrypt`, `kms:GenerateDataKey` | same page |
| Mechanism | S3 conditional writes (`If-None-Match`): first write wins, later ones get 412; that `use_lockfile` uses exactly this is inferred (medium confidence, register M5) | https://docs.aws.amazon.com/AmazonS3/latest/userguide/conditional-writes.html |

Migration from DynamoDB: add `use_lockfile = true` beside `dynamodb_table`, run `terraform init -reconfigure` per component, and after one clean cycle remove `dynamodb_table`. The page says both arguments may be set simultaneously; whether `-reconfigure` or `-migrate-state` is needed for a lock-only change is (unverified), see register U4. Other deprecated arguments: `endpoint` (use `endpoints.s3`) and `force_path_style` (use `use_path_style`).

## OCI: native `oci` backend

```hcl
terraform {
  backend "oci" {
    bucket    = "acme-tfstate-prod"
    namespace = "acmetenancyns"
    region    = "eu-frankfurt-1"
    key       = "functions/prod/terraform.tfstate"
    auth      = "APIKey"
  }
}
```

| Item | Value | Source |
|---|---|---|
| What it is | stores state in OCI Object Storage; locks with the `If-None-Match: *` header | https://developer.hashicorp.com/terraform/language/backend/oci |
| Minimum CLI | Terraform v1.12.0 | https://docs.oracle.com/en-us/iaas/Content/dev/terraform/object-storage-state.htm |
| S3-compatible route | deprecated by Oracle; use only if you cannot reach 1.12.0 | same page |
| Versioning | "highly recommended" on the bucket | https://developer.hashicorp.com/terraform/language/backend/oci |
| Workspaces | non-default workspaces use prefix `tf-state-env` (`workspace_key_prefix`); this family uses a key per environment and component instead | same page |
| Env vars | prefix `OCI_` first, then no prefix; `bucket` and `namespace` cannot come from environment variables | same page |

Authentication in CI (login mechanics belong to `federating-github-actions-oci`):

- Default: `auth = "APIKey"` with key material from the `<environment>` environment secrets, never repository secrets, never in the backend block. HashiCorp "strongly recommend[s]" environment variables for credentials. The exact environment variable names for API-key material are not on the page (unverified), see register U5.
- Option: `SecurityToken` through OCI token exchange for a GitHub OIDC token (medium confidence, see register M6; only Oracle A-Team community material documents it with GitHub Actions).
- Listed but not applicable to GitHub-hosted runners: `InstancePrincipal`, `ResourcePrincipal`, `InstancePrincipalWithCerts`, `OKEWorkloadIdentity`; their use on self-hosted OCI runners is (unverified), see register U9.

Migration from S3-compatible to `oci`: change the block and run `terraform init -migrate-state`; the exact procedure between these two backends is not on the pages read (unverified), see register U4.

## Rules shared by both backends

- Pass only non-secret values with `-backend-config`; they are persisted in the `.terraform` directory and in plan files.
- One key (or file) per environment and component; the plan artifact name carries both.
- Locking through the OCI S3-compatible endpoint is not documented in the sources read (unverified), see register U4.
- Never run `terraform force-unlock` before identifying the lock holder (factory rule; see `terraform-standards`).
