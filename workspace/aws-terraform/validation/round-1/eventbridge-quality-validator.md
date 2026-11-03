# Quality validation round 1 — provisioning-aws-eventbridge-v6

Written by the orchestrator from the validator's returned report (the validator could not write files and had no WebFetch). Counts: HIGH 2 · MEDIUM 9 · LOW 8. ~60 claims sampled.

## HIGH
- H1 Lambda/SNS Never row overstated (SKILL.md:89, never-do-targets.md:75-99, hub row, Always bullet SKILL.md:59, eval scenario 1 must_not): the provider page says permissions must be set with aws_lambda_permission or aws_sns_topic_policy; the AWS page says Lambda/SNS/SQS accept either an IAM execution role or a resource-based policy. Two official sources differ -> not High; the WRONG example claims nothing grants events.amazonaws.com, false when role_arn is set.
- H2 Read dates: skill claims "Sources read 2026-10-23" for every URL, but the facts file dates F1/F7/F6/F11/F5 on 2026-10-14 and F3 on 2026-10-22.

## MEDIUM
1 SKILL.md:50 bullet mixes two claims; `~> 1.16`/`~> 6.69` are a user decision, not stated by the constraints page. 2 SKILL.md:58 "Terraform calls the API" inference. 3 SKILL.md:59 cites wrong page for events.amazonaws.com principal. 4 never-do-targets.md:93-98 CORRECT Lambda block lacks source_arn. 5 SKILL.md:26 "breaks installation" unsourced. 6 SKILL.md:124 absence claim untagged. 7 SKILL.md:126 upgrade path unsourced. 8 always-do-scheduler-integrations.md:13,:32 "endpoint must start with https" cited to scheduled-rules page. 9 connection-page inconsistency tagged in SKILL.md:72/U1 but untagged in always-do-scheduler-integrations.md:10-11.

## LOW
(1) register maps an (unverified) tag to coverage-limit id L1; (2) orphan "U3" mention; (3) eval scenario 4 last must_not vague; (4) `retention_days = 0` named; (5) `rate(1 hours)`; (6) "or any non-withdrawn patch" unsourced; (7) Always vs Ask First tension on policy vs permission; (8) encrypt = true unsourced, SNS never shown in HCL, `is_enabled` speculation, heading case.

## Rule checks
Never rows 11=11 one-to-one, 10/11 High (row 7 fails); Always 13 bullets mostly fine; no F#/M# ids in shipped text; legacy claims not reproduced; connection fragment marked.
