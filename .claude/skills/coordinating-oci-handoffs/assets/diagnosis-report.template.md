---
kind: report
from: "@oci-debugger"
to: "<@oci-deployer | @oci-terraform | @oci-functions-java>"
refs: deploy-report.md
capability: <capability-slug>
outcome: <success | partial | failed>
createdAt: <ISO 8601>
---

## What changed

- (diagnosis only — @oci-debugger never edits code)

## Root cause

<one-line root cause>

## Evidence

- CLI output / grep result / smoke body that proves the diagnosis

## Exact fix

<file + exact change to apply, e.g. pom.xml dependency block, tfvars key, IAM policy>

## Classification

<code | config | infra>

## Next action

Hand off: run `/deploy-function` (`@oci-deployer`)   # code/config fix
  — or —
Hand off: `@oci-terraform`                            # infra/network/IAM fix
<one-line why>. Context: this file.

## Open issues / blockers

- None.
