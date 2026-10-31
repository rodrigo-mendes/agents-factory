# Evaluation Scenarios — provisioning-aws-acm-v6

Four scenarios (canonical, edge, misuse rejection, anti-pattern trap).
Each scenario uses `success_criteria: { must_pass, must_not }` for deterministic LLM-as-judge scoring.

---

## Scenario 1 — Canonical: Public certificate with Route 53 DNS validation

```json
{
  "skills": ["provisioning-aws-acm-v6"],
  "query": "Generate Terraform for a public ACM certificate for app.example.com validated through Route 53 and used by an ALB HTTPS listener. Use hashicorp/aws 6.x and Terraform 1.16.",
  "success_criteria": {
    "must_pass": [
      "Sets required_version = \"~> 1.16\" and hashicorp/aws version ~> 6.69",
      "Uses validation_method = \"DNS\"",
      "Creates aws_route53_record with for_each over domain_validation_options",
      "Creates aws_acm_certificate_validation with certificate_arn and validation_record_fqdns",
      "The listener references aws_acm_certificate_validation.<n>.certificate_arn",
      "Sets lifecycle { create_before_destroy = true } on the certificate",
      "Adds tags to the certificate",
      "Puts no provider alias on aws_route53_record"
    ],
    "must_not": [
      "Reference aws_acm_certificate.<n>.arn directly in the listener instead of the validation resource",
      "Set allow_overwrite = true without asking",
      "Pin provider version 6.57.0"
    ]
  }
}
```

---

## Scenario 2 — Edge Case: CloudFront certificate

```json
{
  "skills": ["provisioning-aws-acm-v6"],
  "query": "My provider region is eu-west-1 but I need an ACM certificate for a CloudFront distribution. How do I provision and validate it in Terraform 6.x?",
  "success_criteria": {
    "must_pass": [
      "States the certificate must be requested (or imported) in us-east-1 for CloudFront viewer HTTPS",
      "Offers provider alias (aws.us_east_1) or region = \"us-east-1\" as the two options",
      "Puts the matching aws_acm_certificate_validation in the same Region as the certificate",
      "Does not put a provider alias or region on aws_route53_record (Route 53 is global)",
      "Notes that for CloudFront-to-ELB origin HTTPS any Region works"
    ],
    "must_not": [
      "Create the viewer certificate in eu-west-1",
      "Add provider = aws.us_east_1 to aws_route53_record",
      "Claim the same-Region validation requirement is explicitly documented without noting it is inferred"
    ]
  }
}
```

---

## Scenario 3 — Misuse Rejection: Imported certificate with private_key and validation_method

```json
{
  "skills": ["provisioning-aws-acm-v6"],
  "query": "Import our own certificate into ACM with Terraform: set certificate_body, private_key, and validation_method = \"DNS\". Also tell me ACM will auto-renew it.",
  "success_criteria": {
    "must_pass": [
      "Rejects validation_method on an imported certificate (must not be set)",
      "Recommends private_key_wo + private_key_wo_version instead of private_key because private_key is stored in state",
      "States that private_key_wo requires Terraform >= 1.11.0",
      "States imported certificates are not eligible for managed renewal"
    ],
    "must_not": [
      "Accept private_key as the recommended approach",
      "Accept validation_method on an imported certificate",
      "Claim ACM auto-renews imported certificates"
    ]
  }
}
```

---

## Scenario 4 — Anti-Pattern Trap: Legacy snippet and CNAME cleanup

```json
{
  "skills": ["provisioning-aws-acm-v6"],
  "query": "Review: required_version >= 1.7, S3 backend with dynamodb_table, provider = aws.us_east_1 on aws_route53_record, allow_overwrite = true is required, a note that 198-day validity is a v6 provider change, and I plan to delete the validation CNAMEs after issuance to tidy the zone. Is this right for aws 6.x?",
  "success_criteria": {
    "must_pass": [
      "Replaces >= 1.7 with ~> 1.16 and dynamodb_table with use_lockfile = true",
      "States Route 53 is global so the provider alias on aws_route53_record is unnecessary",
      "States allow_overwrite defaults to false and is not recommended for most environments, so it is not required by default (ask before enabling it)",
      "States 198-day validity is an AWS service change, and the 6.0.0 upgrade guide has no ACM entries",
      "Rejects deleting the validation CNAMEs of an in-use certificate because renewal stops"
    ],
    "must_not": [
      "Accept dynamodb_table without noting it is deprecated",
      "Accept that allow_overwrite = true is required",
      "Accept deleting the validation CNAMEs",
      "Attribute 198-day validity to a provider change"
    ]
  }
}
```
