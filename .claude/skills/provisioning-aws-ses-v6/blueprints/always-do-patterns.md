# Always-Do Patterns — provisioning-aws-ses-v6

Index of the always-do blueprints, split by topic. Each pattern has HCL and cites its official
source (dated 2026-10-23).

| # | Pattern | Blueprint |
|---|---|---|
| 1 | Terraform block (`~> 1.16`, `~> 6.69`) and S3 backend with `use_lockfile` | [always-do-identity-dns](./always-do-identity-dns.md#1-terraform-block-and-s3-backend) |
| 2 | Domain identity, Easy DKIM, BYODKIM, per-Region identity | [always-do-identity-dns](./always-do-identity-dns.md#2-domain-identity-and-easy-dkim) |
| 3 | Custom MAIL FROM subdomain | [always-do-identity-dns](./always-do-identity-dns.md#3-custom-mail-from) |
| 4 | Configuration set with `tls_policy = "REQUIRE"` and tags | [always-do-sending-config](./always-do-sending-config.md#4-configuration-set) |
| 5 | Event destination with `enabled = true` | [always-do-sending-config](./always-do-sending-config.md#5-event-destination) |
| 6 | Dedicated IP pool, tagged contact list, identity policy | [always-do-sending-config](./always-do-sending-config.md#6-dedicated-ip-pool-contact-list-and-identity-policy) |
| 7 | Account-level VDM (`aws_sesv2_account_vdm_attributes`) | [always-do-sending-config](./always-do-sending-config.md#7-account-level-vdm) |
| 8 | `terraform test` with `mock_provider` | [always-do-sending-config](./always-do-sending-config.md#8-terraform-test) |
| 9 | Classic `aws_ses_*` family (separate) | [always-do-classic-family](./always-do-classic-family.md#9-classic-aws_ses-identity-policy) |
