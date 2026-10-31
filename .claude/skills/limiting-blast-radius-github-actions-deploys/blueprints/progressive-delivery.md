# Progressive delivery per target

Back to [SKILL.md](../SKILL.md). Research date 2026-10-30. Adapters are described in [reusable workflows](./reusable-workflows.md).

## Contents

- Summary table
- Lambda
- ECS
- S3 and CloudFront
- Vercel
- Terraform

## Summary table

| Target | Fraction mechanism | Smoke signal | Automatic rollback | Manual rollback |
|---|---|---|---|---|
| Lambda | alias `AdditionalVersionWeights` | invoke alias, check `x-amz-executed-version` | CodeDeploy alarms, or the adapter reverts weights | `update-alias` to the previous version |
| ECS | `CANARY`, `LINEAR`, `BLUE_GREEN` | lifecycle hook Lambda; ALB `HTTPCode_ELB_5XX_Count` | alarms and circuit breaker on rolling updates; other strategies (unverified) | redeploy the previous task definition revision |
| S3 + CloudFront | staging distribution weight up to 15 percent, or prefix switch | HTTP check on header-routed staging | none native (unverified) | origin path back to the previous prefix |
| Vercel | staged production (`--skip-domain`) | request the deployment URL before promote | none in the pages read (unverified) | `vercel rollback` |
| Terraform | small component per job | plan shows no unexpected destroy | none (unverified) | revert commit, reviewed plan |

## Lambda

Workflow alias shift is the default: publish a version, send a weight to it, smoke-test, then complete (`--function-version N`, weights `{}`) or revert (weights `{}` on the old version). Verify which version served through the `START ... Version:` log line, the `ExecutedVersion` metric dimension or the `x-amz-executed-version` header. "At low traffic levels, you might see a high variance between the configured and actual percentage", so a smoke test must invoke the alias enough times. Release steps (waiters, publish, alias) belong to `deploying-aws-lambda`.
Source: https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html

CodeDeploy option: a deployment group with `CodeDeployDefault.LambdaCanary10Percent5Minutes` or `LambdaLinear10PercentEvery{1,2,3,10}Minute(s)` can roll back automatically on failure or on a monitoring threshold; rollbacks are new deployments with new IDs. Choosing it so rollback survives a dead runner is (medium confidence).
Source: https://docs.aws.amazon.com/codedeploy/latest/userguide/deployment-configurations.html ; https://docs.aws.amazon.com/codedeploy/latest/userguide/deployments-rollback-and-redeploy.html

## ECS

`DeploymentConfiguration.strategy` accepts `ROLLING`, `BLUE_GREEN`, `LINEAR`, `CANARY`. `CANARY` shifts a small percentage first, then the rest after a period; `LINEAR` shifts in equal steps; `bakeTimeInMinutes` is required for `BLUE_GREEN`; lifecycle hooks can run Lambda functions. Deploy by image digest.
Source: https://docs.aws.amazon.com/AmazonECS/latest/APIReference/API_DeploymentConfiguration.html

```bash
# Representative; ROLLING with alarm and circuit-breaker rollback
aws ecs update-service --cluster prod --service orders --task-definition orders:57 \
  --deployment-configuration "alarms={alarmNames=[orders-5xx],enable=true,rollback=true},deploymentCircuitBreaker={enable=true,rollback=true}"
aws ecs wait services-stable --cluster prod --services orders
```

The alarm page limits alarms to services using the rolling update controller; whether alarms also cover `BLUE_GREEN`, `LINEAR` and `CANARY` is (unverified). If an alarm is already in ALARM when a deployment starts, ECS does not monitor alarms for that deployment; blue/green may double resource usage.
Source: https://docs.aws.amazon.com/AmazonECS/latest/developerguide/deployment-alarm-failure.html

## S3 and CloudFront

- Versioned prefix: upload to `s3://bucket/releases/<sha>/`, change the origin path to `/releases/<sha>`; rollback is the previous path. CloudFront serves cached objects until the TTL expires, so pair the switch with an invalidation (the invalidation API was not read, medium confidence).
- Continuous deployment: `copy-distribution --staging`, policy `SingleWeight` (`.01` to `.15`) or `SingleHeader`, promote with `update-distribution-with-staging-config`. Limits: weight at most 15 percent, 20 staging distributions per account, no HTTP/3, and "CloudFront sends all requests to the primary distribution during peak traffic hours". Using it to canary site content through a new origin path is (medium confidence).

Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistValuesOrigin.html ; https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment-quotas-considerations.html

## Vercel

Staged production: `vercel --prod --skip-domain` then `vercel promote <url>`, no rebuild. After `vercel rollback`, Vercel turns off auto-assignment of production domains; undo with `vercel promote`. Hobby rollback reaches only the previous deployment.
Source: https://vercel.com/docs/instant-rollback ; https://vercel.com/docs/cli/rollback

## Terraform

Split state by volatility, stateful versus stateless, team privilege and environment, so a plan for `app-compute` cannot destroy `data-db`. Each component has its own job, state key and role. Plan and apply mechanics: `automating-terraform-github-actions-v1-17`.
Source: https://developer.hashicorp.com/well-architected-framework/operational-excellence/operational-excellence-workspaces-projects
