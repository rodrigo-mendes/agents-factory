---
kind: report
from: "@oci-debugger"
to: "<@oci-deployer | @oci-terraform | @oci-functions-java | @oci-observability>"
refs: deploy-report.md
capability: <capability-slug>
outcome: <success | partial | failed | needs-input>
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

Hand off: run `/develop-java-function` (`@oci-functions-java`) # Java code fix
  — or —
Hand off: run `/deploy-oci-function` (`@oci-deployer`)   # configuration/dependency/image fix
  — or —
Hand off: run `/provision-oci-infra` (`@oci-terraform`)     # infra/network/IAM fix
  — or —
Hand off: run `/observe-oci-workload` (`@oci-observability`) # observability gap (logs, alarms, APM, dashboards)
<one-line why>. Context: this file.

## Open issues / blockers

- None.
