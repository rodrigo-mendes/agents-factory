### ⚠️ Ask First

**Decision Point 1: Vault Type Selection**

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| Default Vault (`DEFAULT`) | Cost (free tier, up to 20 key versions) | Isolation — shares HSM with other tenants. Max 10 keys. | Dev/test, non-regulated workloads, low key count |
| Virtual Private Vault (`VIRTUAL_PRIVATE`) | Isolation — dedicated HSM partition, 1000 keys, cross-region replication | Cost (~$530/month per vault) | Production, compliance (PCI-DSS, HIPAA, SOC2), multi-region DR |
| Dedicated KMS | Maximum isolation — single-tenant HSM, PKCS#11 access | Cost ($$$$), operational overhead | Financial services, government, HSM-direct access |
| External KMS (EKMS) | Key sovereignty — keys never in OCI | Latency, availability dependency, AES-only | Regulatory mandates prohibiting key material in any cloud |

**Agent Behavior**:
"Before provisioning a vault, ask the user:
'What compliance frameworks govern this workload (PCI-DSS, HIPAA, SOC2, none)?
Is cross-region key replication required for disaster recovery?
What is the expected number of encryption keys needed?'"

**Decision Factors**:
- Compliance requirements (FIPS 140-2 Level 3, key isolation)
- Cross-region replication need (requires Virtual Private Vault)
- Key count (Default Vault limited to 10 keys)
- Budget (~$530/month per Virtual Private Vault)

**Source**: https://www.oracle.com/security/cloud-security/key-management/

---

**Decision Point 2: Key Protection Mode (⚠️ IMMUTABLE after creation)**

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| HSM (`protection_mode = "HSM"`) | Security — FIPS 140-2 Level 3, all crypto in hardware | Cost (higher per-operation ~$0.03-$0.05/10K ops), cannot export | Production, compliance-mandated workloads |
| Software (`protection_mode = "SOFTWARE"`) | Cost — lower per-operation charges, same API | FIPS Level 3 for crypto operations | Development/testing, high-volume low-sensitivity |
| External (`protection_mode = "EXTERNAL"`) | Key sovereignty — key material outside OCI | Latency, AES-only, external availability dependency | Regulatory mandates, multi-cloud key management |

**Agent Behavior**:
"Before creating an encryption key, ask the user:
'Does this workload require FIPS 140-2 Level 3 for the cryptographic operations themselves?
Is this a production or development environment?'
⚠️ Protection mode is IMMUTABLE after creation — this decision cannot be changed."

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

**Decision Point 3: Secret Storage Strategy**

| Option | Optimizes For | Sacrifices | Choose When |
|--------|--------------|-----------|-------------|
| OCI Vault Secrets | Security — encrypted with CMK, versioned, rotatable, auditable | Latency (~50-100ms API call), SDK dependency | All production workloads — default for credentials |
| Function Config Variables | Simplicity — no SDK code, available as env var | Security — not encrypted with CMK, visible in console, no rotation | Non-sensitive configuration only |

**Agent Behavior**:
"Before storing a configuration value, ask:
'Would exposure of this value cause a security incident?
If yes → it MUST go in Vault Secrets.
If no → Function config variables are acceptable.'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/Functions/Tasks/functionscreatingapps.htm

---

**Decision Point 4: Key Algorithm Selection**

| Option | Algorithm/Length | Optimizes For | Choose When |
|--------|----------------|---------------|-------------|
| AES-256 | `AES`, length 32 | Symmetric — fast, high throughput | Data encryption (CMEK), envelope encryption — **default** |
| RSA-4096 | `RSA`, length 512 | Asymmetric — signing, key wrapping, TLS | Digital signatures, certificate signing, external transport |
| ECDSA P-256 | `ECDSA`, length 32 | Small signatures, fast verification | JWT signing, API token signing |
| ECDSA P-384 | `ECDSA`, length 48 | Stronger ECDSA | Government/compliance > 128-bit security |

**Agent Behavior**:
"Use AES-256 as the default for data encryption. Only ask when the use case involves signing or key wrapping:
'Is this key for data encryption, digital signatures, or key wrapping?'"

**Source**: https://docs.oracle.com/en-us/iaas/Content/KeyManagement/Concepts/keyoverview.htm

---

