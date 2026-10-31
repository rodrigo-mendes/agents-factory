# Evaluation Scenarios — provisioning-aws-ses-v6

Four scenarios plus one family-mixing check (canonical, edge, misuse rejection, anti-pattern trap).
Each uses `success_criteria: { must_pass, must_not }` for LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Domain identity with configuration set and events

```json
{
  "skills": ["provisioning-aws-ses-v6"],
  "query": "Generate Terraform for an SES domain identity with Easy DKIM, a custom MAIL FROM subdomain, a configuration set that requires TLS, and an SNS event destination for bounces and complaints. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Uses aws_sesv2_email_identity, aws_sesv2_email_identity_mail_from_attributes, aws_sesv2_configuration_set and aws_sesv2_configuration_set_event_destination",
      "Sets delivery_options { tls_policy = \"REQUIRE\" } and tags on the configuration set",
      "Sets enabled = true inside event_destination",
      "Names DKIM CNAME records <token>._domainkey.<domain>",
      "Marks example values and does not invent the DKIM CNAME value suffix (flags it as unverified or asks)"
    ],
    "must_not": [
      "Mix aws_ses_* arguments into the aws_sesv2_* resources",
      "Use dynamodb_table in the S3 backend",
      "Hardcode a <token>.dkim.amazonses.com suffix as established fact"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: Several Regions and sandbox

```json
{
  "skills": ["provisioning-aws-ses-v6"],
  "query": "We send from example.com in eu-west-1 and us-east-1. How do I model identities and what about the SES sandbox?",
  "success_criteria": {
    "must_pass": [
      "States a separate identity must be created and verified in each Region (region argument per Region)",
      "States the sandbox status is unique per AWS Region",
      "States AWS documents the console and the aws sesv2 put-account-details CLI command for production access",
      "Treats whether a Terraform resource exists for production access as unverified and asks about it"
    ],
    "must_not": [
      "Claim Terraform cannot request production access",
      "Claim one identity covers all Regions"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Production access via Terraform and a wrong resource name

```json
{
  "skills": ["provisioning-aws-ses-v6"],
  "query": "Write Terraform that moves my SES account out of the sandbox and enables VDM with aws_sesv2_account_vdm_options.",
  "success_criteria": {
    "must_pass": [
      "Corrects the resource name: aws_sesv2_account_vdm_options is not documented; the documented resource is aws_sesv2_account_vdm_attributes with vdm_enabled",
      "Does not invent a resource or argument for production access; points to the documented console / CLI route and marks the Terraform question unverified",
      "Asks whether the account-level resource is owned by this configuration (destroy behaviour is unverified)"
    ],
    "must_not": [
      "Use aws_sesv2_account_vdm_options",
      "Invent a Terraform resource for leaving the sandbox",
      "State flatly that Terraform cannot do it"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: MAIL FROM, DKIM names, event bus

```json
{
  "skills": ["provisioning-aws-ses-v6"],
  "query": "Review: behavior_on_mx_failure = \"REJECT_MESSAGE\" with no mail_from_domain; two MX records on the MAIL FROM subdomain; DKIM CNAME named _<token>._domainkey.example.com; an event_bridge_destination pointing at my custom bus; provider pinned to 6.57.0.",
  "success_criteria": {
    "must_pass": [
      "Rejects REJECT_MESSAGE without mail_from_domain (required in that case)",
      "Rejects multiple MX records; recommends exactly one",
      "Rejects the underscore-prefixed DKIM name; gives <token>._domainkey.<domain>",
      "Rejects the custom bus (only the default bus is supported)",
      "Rejects pinning 6.57.0 (withdrawn); recommends ~> 6.69"
    ],
    "must_not": [
      "Present the rejections without citing the provider or AWS page"
    ]
  }
}
```

---

## Scenario 5 — Family mixing: classic and v2

```json
{
  "skills": ["provisioning-aws-ses-v6"],
  "query": "Set behavior_on_mx_failure to UseDefaultValue on aws_sesv2_email_identity_mail_from_attributes, and manage the same identity with aws_ses_domain_identity too.",
  "success_criteria": {
    "must_pass": [
      "Uses USE_DEFAULT_VALUE for the v2 resource and notes UseDefaultValue belongs to the classic aws_ses_domain_mail_from",
      "Marks managing one identity with both families as unverified (no provider page documents conflicts) and asks first"
    ],
    "must_not": [
      "Copy classic value casing into the v2 resource",
      "State that both families conflict, or that they are safe together, as fact"
    ]
  }
}
```
