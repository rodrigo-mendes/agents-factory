# AWS commands

Two commands cover AWS directly. Most AWS knowledge is reached without a command: Claude loads the
AWS skills automatically when your request matches them.

## Commands

| Job | Command | Routes to | Argument hint |
|---|---|---|---|
| Advise on an AWS architecture | [`/aws-architecture-advisor`](../../packages/cloud/provider/aws/aws-architect/README.md#aws-architecture-advisor) | `aws-architect` | `<question or scope>` |
| Observe a deployed Lambda: validate, provision or review | [`/observe-aws-workload`](../../packages/cloud/provider/aws/aws-observability/README.md#observe-aws-workload) | `aws-observability` | `<function-name> region=<r> [mode=validate\|provision\|review]` |

## Examples

Ask for a design review:

```
/aws-architecture-advisor review my VPC design
```

Validate a deployed function's observability live (read-only):

```
/observe-aws-workload orders-api region=eu-west-1 mode=validate
```

Provision observability for a function from a work-order:

```
/observe-aws-workload orders-api region=eu-west-1 mode=provision wo=openspec/changes/orders/handoff/wo-09-observability.md
```

## Modes of `/observe-aws-workload`

| Mode | Changes anything? | Use it for |
|---|---|---|
| `validate` | No. Reads logs, metrics, traces, alarms and dashboards. | Proving that a deployed workload is observable. |
| `provision` | Writes Terraform only. It does not apply it. | Creating log groups, alarms, dashboards and tracing config. |
| `review` | No. Checks a spec's observability section. | Reviewing SLOs, log fields, retention and sampling before build. |

`provision` and `review` need `wo=`, the work-order that defines the scope.

## Not for

- Deploying or diagnosing Lambda functions. Those are the `aws-lambda` agents (deployer and
  debugger). They have no command; the orchestrator of the SaaS flow starts them. See
  [saas-quarkus-aws](saas-quarkus-aws.md).
- Writing Terraform for a service: use [terraform](terraform.md).

## Related

- Packages: [`aws-architect`](../../packages/cloud/provider/aws/aws-architect/README.md),
  [`aws-observability`](../../packages/cloud/provider/aws/aws-observability/README.md),
  [`aws-skills`](../../packages/cloud/provider/aws/aws-skills/README.md),
  [`aws-lambda`](../../packages/cloud/provider/aws/aws-lambda/README.md).
