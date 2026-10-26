# Evaluation Scenarios — provisioning-aws-parameter-store-v6

Five scenarios (canonical, edge, misuse rejection, two anti-pattern traps). Each uses
`success_criteria: { must_pass, must_not }` for LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Config and Secret Parameters

```json
{
  "skills": ["provisioning-aws-parameter-store-v6"],
  "query": "Generate Terraform for a plain endpoint parameter and a database password SecureString under /myapp/prod/. Use hashicorp/aws 6.x and Terraform 1.16, and keep the password out of state.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Names start with / and use a hierarchy",
      "Writes the SecureString with value_wo plus value_wo_version",
      "Uses insecure_value for the non-secret String parameter",
      "Sets key_id to a customer managed key or asks whether key-policy control is needed"
    ],
    "must_not": [
      "Use value for the SecureString while claiming the state has no plaintext",
      "Use insecure_value on the SecureString",
      "Pin version 6.57.0"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Tiers and Intelligent-Tiering

```json
{
  "skills": ["provisioning-aws-parameter-store-v6"],
  "query": "Should I set tier = \"Intelligent-Tiering\" on my parameters, and what happens if I later change an Advanced parameter back to Standard in Terraform?",
  "success_criteria": {
    "must_pass": [
      "Explains Intelligent-Tiering is a default-tier setting that creates Standard unless Advanced is needed and then upgrades one-way",
      "States that changing Advanced to Standard in Terraform recreates the resource",
      "Notes Advanced parameters are charged",
      "Asks the user before choosing a tier"
    ],
    "must_not": [
      "Describe Intelligent-Tiering as a third tier with its own limits",
      "Claim the downgrade causes a persistent error requiring terraform state rm"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: insecure_value and Ephemeral name

```json
{
  "skills": ["provisioning-aws-parameter-store-v6"],
  "query": "Use insecure_value for my SecureString so the diff is readable, and read it back with an ephemeral aws_ssm_parameter that takes name.",
  "success_criteria": {
    "must_pass": [
      "Rejects insecure_value with SecureString because it cannot be used with that type",
      "States the ephemeral aws_ssm_parameter requires arn, not name",
      "Offers value_wo plus value_wo_version for the SecureString write"
    ],
    "must_not": [
      "Accept insecure_value on a SecureString",
      "Write name on the ephemeral resource"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Ephemeral Resource Does Not Protect Writes

```json
{
  "skills": ["provisioning-aws-parameter-store-v6"],
  "query": "I read my secret with the ephemeral aws_ssm_parameter and write it into another SecureString with value. Is the plaintext kept out of state?",
  "success_criteria": {
    "must_pass": [
      "States that writing a SecureString with value stores the plaintext in state",
      "Recommends value_wo plus value_wo_version as the documented write-only alternative to value, needing Terraform >= 1.11",
      "Tags the ephemeral minimum CLI version as unverified or medium confidence"
    ],
    "must_not": [
      "Claim the ephemeral read alone keeps written values out of state (writing with value = still stores plaintext)",
      "State a minimum Terraform version for ephemeral resources as fact"
    ]
  }
}
```

---

## Scenario 5 — Anti-Pattern Trap: Legacy Claims

```json
{
  "skills": ["provisioning-aws-parameter-store-v6"],
  "query": "An older guide says overwrite is deprecated since provider v5.0 and causes perpetual diffs. Should I remove it, and are there Security Hub controls for my parameters?",
  "success_criteria": {
    "must_pass": [
      "States overwrite is documented on the current page without a deprecation marker, default false on create and true afterward",
      "Treats overwrite use as an Ask First decision (adopt vs import)",
      "States none of the Security Hub SSM.1-SSM.7 controls evaluates Parameter Store parameters"
    ],
    "must_not": [
      "Claim overwrite is deprecated",
      "Invent a Security Hub control for parameters",
      "State parameter name length or character limits as fact"
    ]
  }
}
```
