# Ask First Decisions — OCI Vault Provisioning

> 📎 **Architecture decisions**: For detailed trade-off analysis of Vault types, key protection modes, key algorithms, and secret rotation strategies, consult the skill `designing-oci-vault-security`. This section covers the **Terraform implementation** and highlights **immutable** properties that require destroy/recreate.

---

## Decision Point: Vault Type Selection (IMMUTABLE — cannot migrate after creation)

> 📎 See `designing-oci-vault-security` for full architecture decision factors (compliance frameworks, cross-region DR, cost analysis).

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| DEFAULT | Cost ($0, up to 20 key versions free) | Isolation (shared HSM), limits (10 keys), no replication, 200 ops/sec | Dev/test, POC, learning, low key volume |
| VIRTUAL_PRIVATE | Isolation (dedicated HSM), 1000 keys, 1000+ ops/sec, cross-region replication | Cost (~$530/month per vault) | Production, compliance (PCI/SOC2/HIPAA), multi-region DR |

**Agent Behavior**:
"Before provisioning a vault, ask the user:
'Is this a production environment? Are there compliance requirements (PCI-DSS, SOC2, HIPAA)? Do you need cross-region DR for secrets?'
⚠️ Vault type is IMMUTABLE — cannot be changed from DEFAULT to VIRTUAL_PRIVATE without destroy/recreate."

**Decision Factors**:
- Environment type (production → VIRTUAL_PRIVATE)
- Compliance framework requirements (FIPS 140-2 Level 3)
- Need for cross-region replication (requires VP)
- Key count (DEFAULT limited to 10)
- Budget (~$530/month per VP vault)

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

## Decision Point: Key Protection Mode (IMMUTABLE — cannot change after creation)

> 📎 See `designing-oci-vault-security` for full architecture decision factors (FIPS 140-2 Level 3, compliance).

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| HSM | Security — FIPS 140-2 Level 3, crypto entirely in hardware | Cost (higher per-operation ~$0.03–$0.05/10K ops) | Production, compliance mandated |
| SOFTWARE | Cost — lower per-operation charges, same API | FIPS Level 3 for crypto operations | Dev/test, high-volume non-regulated |
| EXTERNAL | Sovereignty — key material outside OCI | Latency (+10-50ms), availability, AES-ONLY | Regulatory mandate for keys outside cloud |

**Agent Behavior**:
"Before creating an encryption key, ask the user:
'Does this workload require FIPS 140-2 Level 3 for the cryptographic operations?
Is this a production or development environment?'
⚠️ Protection mode is IMMUTABLE — this decision cannot be changed after key creation."

**Decision Factors**:
- FIPS 140-2 Level 3 requirement (HSM vs. SOFTWARE)
- Environment type (production → HSM)
- Algorithm requirements (EXTERNAL supports AES only)

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

## Decision Point: Key Algorithm Selection (IMMUTABLE — cannot change after creation)

> 📎 See `designing-oci-vault-security` for full architecture decision factors (use case matching).

**Available Options**:
| Option | Algorithm + Length | Best For | Constraint |
|--------|-------------------|----------|------------|
| AES-256 | `AES`, length=32 | Data encryption (CMEK), envelope encryption — **default choice** | Symmetric |
| RSA-4096 | `RSA`, length=512 | Key wrapping, TLS certificates, legacy signing | Asymmetric — slow for large volumes |
| ECDSA P-256 | `ECDSA`, length=32 | JWT signing, API token signing | Asymmetric — not for encryption |
| ECDSA P-384 | `ECDSA`, length=48 | Government/compliance >128-bit security | Greater overhead than P-256 |

**Agent Behavior**:
"Use AES-256 as default for data encryption. Only ask when use case involves signing or key wrapping:
'Is this key for data encryption, digital signatures, or key wrapping?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

## Decision Point: Secret Rotation Strategy

**Available Options**:
| Option | Approach | Optimizes For | Choose When |
|--------|----------|---------------|-------------|
| ADB Native | `target_system_type = "ADB"` | Simplicity — Vault rotates directly in Autonomous DB | Autonomous Database credentials |
| Function-based | `target_system_type = "FUNCTION"` | Flexibility — custom logic for any system | API keys, tokens, non-ADB databases |
| Manual | No `rotation_config` | Zero overhead | Dev/test only, low-sensitivity |
| Auto-generation | `enable_auto_generation = true` | Zero human knowledge of credentials | Passwords that don't need to be known by humans |

**Agent Behavior**:
"Ask the user:
'Is the secret for Autonomous Database? Which system is the credential for?
Is there an existing rotation Function?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/Vault/Tasks/managingsecrets.htm

---

## Decision Point: Single Vault vs. Multiple Vaults per Environment

**Available Options**:
| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| 1 Vault per environment | Simplicity, cost (1× $530/month per env) | Blast radius (vault compromise affects all keys) | Small teams, single project |
| Multiple Vaults per domain | Isolation (security vs. data vs. signing) | Cost ($530/vault × N), complexity | Compliance, multi-team, high sensitivity |
| 1 Vault shared across envs | Minimal cost | Zero isolation — dev can affect prod | **NEVER for production** — POC only |

**Agent Behavior**:
"Ask the user:
'How many teams access the vault? Does compliance require segregation of keys by security domain?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm
