# Rollback and Old-Version Cleanup

Back to [SKILL.md](../SKILL.md). Mutating commands run only after an explicit user approval relayed by the orchestrator: rollback with `approval: rollback alias=<alias> to=<PREV version> by=<user> at=<UTC> relayed-by=<orchestrator>`; cleanup is never run by the deployer (no approval line exists for it): the deployer returns the exact command as a proposal under `## Cleanup proposal` in the deploy-report, which does not change the outcome (a good release stays `success`); after E9 the user runs the listed commands themselves if they want. Representative commands, none executed by the research.

## Contents

- [Rollback by alias](#rollback-by-alias)
- [SnapStart 14-day caveat](#snapstart-14-day-caveat)
- [Rollback channel](#rollback-channel)
- [Old-version cleanup](#old-version-cleanup)

## Rollback by alias

AWS has no dedicated rollback page (the `lambda-rollback` URL returned an empty body, coverage limit L3). The documented mechanism is the weighted-alias page plus the runtime rollback page.

```bash
PREV=<previous version number recorded before the deploy>
REV=$(aws lambda get-alias --function-name my-function --name live --query RevisionId --output text)
aws lambda update-alias --function-name my-function --name live \
  --function-version "$PREV" --routing-config 'AdditionalVersionWeights={}' --revision-id "$REV"   # only with the approval: rollback line
aws lambda invoke --function-name my-function --qualifier live --cli-binary-format raw-in-base64-out \
  --payload file://smoke-event.json --log-type Tail out.json > meta.json
jq -e '.StatusCode==200 and (has("FunctionError")|not) and .ExecutedVersion=="'"$PREV"'"' meta.json
```

- The example in the guide passes `--routing-config AdditionalVersionWeights={}`; the command resets routing ([weighted aliases](https://docs.aws.amazon.com/lambda/latest/dg/configuring-alias-routing.html)).
- `--revision-id` avoids overwriting an alias changed since you read it ([update-alias](https://docs.aws.amazon.com/cli/latest/reference/lambda/update-alias.html)). The `RevisionId` field of `get-alias` is (medium confidence), register M5.
- Published versions are immutable snapshots; redirecting traffic to an earlier version rolls back code and configuration, and in Function update runtime mode the runtime version too ([runtime rollback](https://docs.aws.amazon.com/lambda/latest/dg/runtime-management-rollback.html), [versions](https://docs.aws.amazon.com/lambda/latest/dg/configuration-versions.html)).
- `ExecutedVersion` must equal `PREV` after the move; if not, check for leftover weights.

## SnapStart 14-day caveat

Family fact (orchestrator-verified 2026-10-28): for SnapStart on Java, Lambda deletes a version's snapshot after 14 days without an invocation; the version goes `Inactive`; the next invoke returns `SnapStartNotReadyException` and a new snapshot is initialised. Wait for `Active`, then invoke again ([SnapStart activate](https://docs.aws.amazon.com/lambda/latest/dg/snapstart-activate.html)).

```bash
aws lambda wait published-version-active --function-name my-function --qualifier "$PREV"
aws lambda get-function-configuration --function-name my-function:"$PREV" \
  --query '{State:State,Opt:SnapStart.OptimizationStatus}'     # Expected: Active, On
```

Consequence for the procedure: before a rollback to a version that may have been idle 14 days, expect the first invoke to fail and the version to need time to re-initialise; do not report the rollback as failed until the wait finishes. Whether the same applies to Python and .NET SnapStart versions is not stated in the research; treat it as (unverified), register U6.

## Rollback channel

| Option | Optimizes | Sacrifices | Best when |
|---|---|---|---|
| A Terraform: set the alias target to the previous version, plan `-out`, approval, apply | one source of truth, reviewed | minutes of exposure | non-urgent regressions |
| B Emergency CLI `update-alias` (above), then reconcile Terraform | seconds to restore | out-of-band change; the next plan may report the alias as drifted (medium confidence), register M4 | user-approved incident response |

Both are mutating: A needs the `approval: apply` line, B the `approval: rollback` line ([C3](./ask-first-decisions.md#c3-rollback-channel)).

## Old-version cleanup

Why delete: every function version and layer version consumes code storage, and the quota is 300 GB per Region, not increasable ([quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html)). That quota is the reason for cleanup on Java.

SnapStart cost is not a reason for Java: on Java managed runtimes SnapStart has no additional cost. For Python and .NET, each published SnapStart version accrues caching charges while active (minimum 3 hours) and AWS recommends deleting unused versions with `ListVersionsByFunction` and `DeleteFunction` ([SnapStart](https://docs.aws.amazon.com/lambda/latest/dg/snapstart.html)). A Serverless Land "Lambda Version Cleanup" pattern is linked from that page but was not fetched (unverified), register U4.

```bash
aws lambda list-versions-by-function --function-name my-function --query 'Versions[].Version'
aws lambda delete-function --function-name my-function --qualifier <old N>   # PROPOSAL only: never run by the deployer
```

- Keep the version the alias points to and `PREV`. A version referenced by an alias cannot be deleted ([delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html)).
- Without `--qualifier`, all versions and aliases are deleted and a deleted function cannot be recovered ([delete-function](https://docs.aws.amazon.com/cli/latest/reference/lambda/delete-function.html)).
- The deployer never runs cleanup: it returns the exact command as a proposal under `## Cleanup proposal` in the deploy-report, which does not change the outcome (a good release stays `success`); the user runs the listed commands themselves if they want, never in the release that might need `PREV`.
- How many versions to keep is a user decision; the research gives no number.
