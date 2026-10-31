# Always-Do Patterns — provisioning-aws-s3-v6

Index of the always-do blueprints, split by topic. Each pattern has complete HCL and cites its
official source (fetched 2026-10-14).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-bucket-foundation](./always-do-bucket-foundation.md#1-terraform-block-and-s3-backend) |
| 2 | Bucket resource, ownership controls (`BucketOwnerEnforced`), standalone satellite resources | [always-do-bucket-foundation](./always-do-bucket-foundation.md#2-bucket-resource-and-ownership-controls) |
| 3 | Bucket-level public access block — all four booleans explicit | [always-do-bucket-foundation](./always-do-bucket-foundation.md#3-bucket-level-public-access-block) |
| 4 | Account-level public access block — one per account, no `region` | [always-do-bucket-foundation](./always-do-bucket-foundation.md#4-account-level-public-access-block) |
| 5 | SSE configuration with `bucket_key_enabled` for SSE-KMS | [always-do-security-encryption](./always-do-security-encryption.md#5-sse-configuration) |
| 6 | TLS enforcement via bucket policy `Deny aws:SecureTransport = false` (S3.5) | [always-do-security-encryption](./always-do-security-encryption.md#6-tls-enforcement-via-bucket-policy) |
| 7 | Access logging with bucket policy grant (not deprecated ACL) | [always-do-security-encryption](./always-do-security-encryption.md#7-access-logging) |
| 8 | Lifecycle configuration with `filter {}`, `abort_incomplete_multipart_upload`, noncurrent expiry | [always-do-lifecycle-versioning](./always-do-lifecycle-versioning.md#8-lifecycle-configuration) |
| 9 | Versioning with timing `depends_on` and lifecycle for cost control | [always-do-lifecycle-versioning](./always-do-lifecycle-versioning.md#9-versioning) |
| 10 | `aws_s3_object` with `source_hash` for KMS-encrypted objects | [always-do-objects-testing](./always-do-objects-testing.md#10-aws_s3_object) |
| 11 | `terraform test` with `mock_provider` and CI pipeline commands | [always-do-objects-testing](./always-do-objects-testing.md#11-terraform-test-and-ci) |
