# Evaluation report: provisioning-aws-dynamodb-v6 (round 1)

Method: no sub-agents. I answered each scenario myself using only SKILL.md and the linked blueprints, then judged the answer. The skill was read from `packages/aws-terraform/.apm/skills/provisioning-aws-dynamodb-v6/`.

Scenarios found: 5, which meets the minimum of 3.

## Scenario 1: Protected on-demand table. PASS (6/6 must_pass, 0/3 must_not violated)

My response used `always-do-foundation.md` section 1 and section 2.

| Criterion | Verdict | Evidence |
|---|---|---|
| required_version `~> 1.16` and aws `~> 6.69` | PASS | foundation s1: `required_version = "~> 1.16"`, `version = "~> 6.69"` |
| Explicit `billing_mode = "PAY_PER_REQUEST"` | PASS | foundation s2: `# default is PROVISIONED; always set explicitly` |
| Attribute blocks only for keys | PASS | the s2 example defines only `pk` and `sk` |
| `deletion_protection_enabled = true` and PITR enabled | PASS | foundation s2 HCL |
| `server_side_encryption { enabled = true, kms_key_arn }` | PASS | foundation s2: `kms_key_arn = var.kms_key_arn # customer managed key` |
| Marks names and values as examples | PASS | `# example` comments are on the names and values |

| must_not | Verdict | Evidence |
|---|---|---|
| Non-key attributes | OK | none added |
| `dynamodb_table` lock or lock table | OK | the backend uses `use_lockfile = true` |
| Claims Security Hub requires a CMK | OK | the Ask First row says no control requires one |

## Scenario 2: Separate GSI resource and warm throughput. PASS (5/5, 0/2)

| Criterion | Verdict | Evidence |
|---|---|---|
| Correct arguments | PASS | indexes s3: required `table_name`, `index_name`, `key_schema`, `projection`. `provisioned_throughput` is for PROVISIONED tables and `on_demand_throughput` only for PAY_PER_REQUEST. |
| No inline GSI blocks on the table | PASS | HCL comment `# table WITHOUT inline global_secondary_index blocks`. never-do-table-indexes s2 gives the reason. |
| Ask first, noting the experimental flag as medium confidence | PASS | SKILL.md Ask First row: "table page calls it 'experimental' while the resource page shows no warning (medium confidence)" |
| >= 6.57.1 no longer replaces the table; 6.57.0 never pinned | PASS | SKILL.md Always Do, Never Do and Version Context |
| Setting both warm_throughput values to the default causes diffs | PASS | SKILL.md Never Do; never-do-table-indexes s4 |

| must_not | Verdict | Evidence |
|---|---|---|
| Wrong argument names on the resource | OK | none used |
| "Experimental" stated as fact | OK | it is attributed to the table page and tagged medium confidence |

Note: foundation s5 also says base-table read warm throughput cannot be decreased. This is a useful caveat and does not conflict with the criteria.

## Scenario 3: CMK "required" by Security Hub. PASS (4/4, 0/3)

| Criterion | Verdict | Evidence |
|---|---|---|
| Rejects the claim | PASS | SKILL.md Ask First: "no Security Hub DynamoDB control requires a customer managed key" |
| `alias/aws/dynamodb` is the AWS managed key; no block means the AWS owned key | PASS | foundation s2 table: "block absent or enabled=false -> AWS owned key (default)" |
| `kms_key_arn` is for other keys; `enabled = true` alone selects AWS managed | PASS | never-do-table-indexes s5 |
| Offers the three key types as a user decision, with a pointer to kms-v6 | PASS | Ask First row: "A customer managed key is created in provisioning-aws-kms-v6" |

| must_not | Verdict | Evidence |
|---|---|---|
| Sets `kms_key_arn` to the alias ARN | OK | it appears only as a WRONG example |
| Calls `alias/aws/dynamodb` the default key | OK | the default is the AWS owned key |
| Says Security Hub requires a CMK | OK | rejected |

## Scenario 4: Legacy snippet. PASS (4/4, 0/3)

| Criterion | Verdict | Evidence |
|---|---|---|
| Rejects `dynamodb_table` and gives `use_lockfile = true` | PASS | never-do-replication-provider s3 |
| Rejects mixing replica mechanisms and gives `ignore_changes = [replica]` | PASS | never-do-replication-provider s1; SKILL.md Never Do row |
| Rejects GSI `hash_key`/`range_key` and gives `key_schema` | PASS | never-do-table-indexes s3 |
| Cites the S3 backend docs or the table page for each rejection | PASS | each Never Do row carries a source URL |

| must_not | Verdict | Evidence |
|---|---|---|
| Accepts `dynamodb_table` | OK | rejected |
| Accepts both replica mechanisms | OK | rejected |
| Says global_table V1 is deprecated | OK | the Ask First row says only "use `replica` for V2" and "many restrictions" |

## Scenario 5: Unverified handling. PASS (4/4, 0/3)

| Criterion | Verdict | Evidence |
|---|---|---|
| Write-capacity metric type is unverified | PASS | indexes s4: "write-capacity metric type is not stated there (unverified)"; U1 |
| Kinesis precision default not stated; set explicitly or ask | PASS | replication s7 comment; U2 says "set it explicitly or ask" |
| Contributor insights mode values not listed; none invented | PASS | replication s7; U3 |
| TTL timing unverified; no deadline given | PASS | foundation s2 comment; U4 |

| must_not | Verdict | Evidence |
|---|---|---|
| TTL deadline stated | OK | none given |
| Mode values invented | OK | none given |
| Kinesis default stated as fact | OK | none given |

## Summary

| Scenario | Pass rate | Verdict |
|---|---|---|
| 1 | 6/6 must_pass, 0 must_not violated | PASS |
| 2 | 5/5, 0 violated | PASS |
| 3 | 4/4, 0 violated | PASS |
| 4 | 4/4, 0 violated | PASS |
| 5 | 4/4, 0 violated | PASS |

Overall: 23/23 must_pass and 0/14 must_not violated, so 5/5 scenarios PASS.

## Criterion and skill observations (no failures; minor)

- S3 must_pass 1 says the Security Hub page "lists no control requiring a CMK". The skill asserts this but only describes DynamoDB.1, .2, .4, .5 and .6. The bibliography covers DynamoDB.1-7, and .3 and .7 are never described. The claim is sourced and acceptable, but it is a weak spot. Suggested fix: add a one-line note in `unverified-and-risks.md` stating that DynamoDB.3 and DynamoDB.7 were checked and are not about CMKs, or flag that as unverified.
- S1 must_pass 6 ("marks as examples") depends on the `# example` comments in the blueprints. It is satisfied only if the answer reproduces them. This is stable but implicit.
- The `target_tracking_scaling_policy_configuration` block names are tagged U6 (unverified) in the skill. No scenario tests this, so the criteria cannot catch a regression there. Optional fix: add a scenario or must_pass for it.

Fixes needed: none required. Optional: the S3 control-coverage note above.
