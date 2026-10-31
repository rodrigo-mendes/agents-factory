# aws-lambda

Runtime-agnostic **AWS Lambda operations**.

| Kind | Names |
|---|---|
| skills | `deploying-aws-lambda` (pre-flight → plan → user-approved apply of the saved plan → waiters → publish/alias → smoke → rollback → cleanup), `debugging-aws-lambda` (symptom elimination tree A–H, read-only allowlist) |
| agents | `aws-lambda-deployer` (executor; applies only a plan whose file + sha256 carry a relayed user approval), `aws-lambda-debugger` (read-only; diagnosis and post-deploy verification) |
| rule | `aws-lambda-deployment-preflight` |

Terraform HCL is owned by `provisioning-aws-lambda-v6` (package aws-terraform). Never `-auto-approve`.

Depends on: factory-core, handoff-core, aws-skills, aws-terraform, aws-observability.
