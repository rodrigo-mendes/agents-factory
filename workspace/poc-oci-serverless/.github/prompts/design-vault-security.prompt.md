---
description: 'Design OCI Vault security architecture including secrets management, encryption strategy, and key rotation'
agent: oci-serverless-architect
argument-hint: 'Secret types, rotation requirements, compliance constraints'
---

# Design Vault Security

**Skill**: `designing-oci-vault-security`

## What this does

Designs the secrets management and encryption strategy using OCI Vault — key hierarchy, secret rotation, access control, and compliance alignment.

## Required information

1. **Secret types**: What secrets need management? (API keys, DB credentials, certificates, tokens)
2. **Rotation requirements**: Auto-rotation interval? Manual rotation for any secrets?
3. **Encryption needs**: Data at rest encryption? Which services need envelope encryption?
4. **Consuming services**: Which functions/services read these secrets?
5. **Compliance constraints**: Regulatory requirements? (PCI-DSS, HIPAA, SOC2)
6. **Key protection**: Software-protected or HSM-protected keys?
7. **Multi-region**: Cross-region replication needed?

## What will be delivered

- Key hierarchy design (master keys, data encryption keys)
- Secret categorization and rotation strategy
- Access control model (which dynamic groups access which secrets)
- Envelope encryption pattern for sensitive data
- Compliance alignment assessment
- Implementation guidance with `@oci-terraform` for provisioning
