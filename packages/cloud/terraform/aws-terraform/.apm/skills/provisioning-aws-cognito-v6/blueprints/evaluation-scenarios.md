# Evaluation Scenarios — provisioning-aws-cognito-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap). Each uses `success_criteria: { must_pass, must_not }`.

---

## Scenario 1 — Canonical: user pool, web client, custom domain

```json
{
  "skills": ["provisioning-aws-cognito-v6"],
  "query": "Generate Terraform for a Cognito user pool with email sign-in and MFA, a web app client using the authorization code flow, and a custom domain auth.example.org. hashicorp/aws 6.x, Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Uses username_attributes (not together with alias_attributes)",
      "Sets at least one MFA method block when mfa_configuration is ON or OPTIONAL",
      "Sets allowed_oauth_flows_user_pool_client = true alongside allowed_oauth_flows = [\"code\"]",
      "Keeps default_redirect_uri (if set) inside callback_urls and uses https URLs",
      "Uses an ISSUED ACM certificate in us-east-1 as certificate_arn for the custom domain",
      "Marks example values as examples or placeholders"
    ],
    "must_not": [
      "Use a certificate from another Region for the custom domain",
      "Pin aws 6.57.0",
      "Set username_attributes and alias_attributes together"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: removing SMS MFA and changing sign-in identifiers

```json
{
  "skills": ["provisioning-aws-cognito-v6"],
  "query": "We want to drop sms_configuration from an existing pool and switch sign-in from email to phone number. Can Terraform just update it in place?",
  "success_criteria": {
    "must_pass": [
      "States the provider page warning that the SMS configuration cannot be removed without recreating the user pool",
      "Mentions the page's suggestion to use taint to force recreation",
      "Quotes the AWS statement that after pool creation the sign-in attribute setting cannot be changed",
      "Does not state as fact whether the provider forces replacement on username_attributes",
      "Asks before proceeding because of the recreation impact"
    ],
    "must_not": [
      "Promise an in-place update for either change",
      "State as documented fact that the provider forces replacement on username_attributes"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: claims from the legacy checklist

```json
{
  "skills": ["provisioning-aws-cognito-v6"],
  "query": "In provider 6.x user_pool_tier replaces user_pool_add_ons.advanced_security_mode, ESSENTIALS includes adaptive authentication, and Cognito resources are not regional. Right?",
  "success_criteria": {
    "must_pass": [
      "States that both user_pool_tier and user_pool_add_ons.advanced_security_mode are documented on the provider page",
      "States that threat protection (including adaptive authentication) is a Plus-plan feature",
      "States that Cognito resources document the optional region argument (regional)",
      "Does not reproduce any of the three claims as true"
    ],
    "must_not": [
      "Tell the user to remove user_pool_add_ons because of user_pool_tier",
      "Attribute adaptive authentication to ESSENTIALS",
      "Say Cognito resources are global"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: broken client configuration

```json
{
  "skills": ["provisioning-aws-cognito-v6"],
  "query": "Review: a client with allowed_oauth_flows = [\"client_credentials\", \"code\"], explicit_auth_flows = [\"USER_PASSWORD_AUTH\", \"ALLOW_USER_SRP_AUTH\"], callback_urls = [\"http://app.example.org/cb\"], and no allowed_oauth_flows_user_pool_client. Is it fine for aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Rejects mixing client_credentials with other flows (it must be the only flow)",
      "Rejects combining legacy USER_PASSWORD_AUTH with ALLOW_* values",
      "Rejects the non-localhost http callback URL and asks for HTTPS",
      "Requires allowed_oauth_flows_user_pool_client = true before allowed_oauth_flows",
      "Cites the provider page or the AWS CreateUserPoolClient page for each rejection"
    ],
    "must_not": [
      "Accept any of the four problems as valid",
      "Cite workspace paths or research-file ids (the skill's own U#/M# register ids are allowed)"
    ]
  }
}
```
