---
description: 'Provision OCI Vault resources (Vault + Keys + Secrets + Rotation) with Terraform'
agent: oci-terraform
argument-hint: 'Secret names, key algorithm, rotation policy, consuming services'
---

# Add Vault

**Skill**: `provisioning-oci-vault`

## What this does

Provisions OCI Vault resources (Vault, Master Encryption Keys, Secrets, Rotation policies) with Terraform for secrets management and encryption.

## Required information

1. **New vault or existing?**: Create a new vault or use existing?
2. **Secrets**: Name and purpose of each secret to create
3. **Key algorithm**: AES (symmetric) or RSA (asymmetric)? Key length?
4. **Rotation policy**: Auto-rotation interval? (30/60/90 days or custom)
5. **Consumers**: Which functions/services will read these secrets?
6. **Vault type**: Default or Virtual Private?
7. **Compartment**: Target compartment OCID

## What will be generated

- `oci_kms_vault` resource (if new vault)
- `oci_kms_key` with algorithm and protection mode
- `oci_vault_secret` for each secret
- Rotation configuration
- Variables with OCID validation
- Outputs for secret OCIDs (for function configuration)
