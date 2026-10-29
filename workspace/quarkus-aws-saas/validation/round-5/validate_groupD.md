# Round 5 validation, group D (independent pass)

Rubric: 100 - 6/HIGH - 2.5/MEDIUM - 0.5/LOW. Read-only. No script, agent or network use. `verify_skill.py` was not run, so link and anchor checks were done by reading.

## Score table

| Skill | HIGH | MEDIUM | LOW | Score |
|---|---|---|---|---|
| coordinating-agent-handoffs | 0 | 2 | 4 | 93.0 |
| specifying-changes-with-openspec-v1-15 | 2 | 2 | 4 | 81.0 |
| syncing-spec-from-code (command, agent spec-synchronizer) | 0 | 1 | 4 | 95.5 |
| observe-aws-workload (command, agent aws-observability) | 0 | 4 | 4 | 88.0 |
| integrating-stripe-quarkus-v3-40 | 1 | 1 | 3 | 90.0 |

Paths: H = packages/handoff-core/.apm/skills/coordinating-agent-handoffs; O = .../specifying-changes-with-openspec-v1-15; S = .../syncing-spec-from-code; OB = packages/aws-observability/.apm/skills/observe-aws-workload; ST = packages/quarkus-aws-saas/.apm/skills/integrating-stripe-quarkus-v3-40.

Checked and clean for all five: frontmatter (name = folder; command skills carry the 4 coupled fields and `agent:` matches an existing agent), description under 300 chars with "Use when", SKILL.md line counts (H 204, O 113, S 115, OB 85, ST 117), blueprint files under 160 lines, Contents lists on blueprints over 100 lines, Quick Navigation link to the Verification Loop, relative links and anchors, tag-to-register mapping rows, register header counts. H documented flags, exit codes, record kinds, counters, drift definition and YAML subset all match scripts/*.py. Record names never start with "report" (the only "report-" strings are Never Do examples). The profile `quarkus-aws` roles and rules match the agent contracts for spec-synchronizer and aws-observability (roles `sync`, `observability`, `observability-live`, `observability-review`; outcomes success|partial|failed|needs-input and pass|fail; section names).

## 1. coordinating-agent-handoffs (93.0)

No HIGH.

- MEDIUM, SKILL.md:50 (also :123 and protocol.md:70): "Run `check_records.py`, then `detect_drift.py` and `board.py` after every record". detect_drift.py:101-104 exits 1 when `lastSyncedSha` is absent or "none". That is always the case before the first `board.py --sync-sha`, and for every `spec.kind: none` family such as OCI (board.py:68 writes "none"). Fix hint: qualify the step ("only when `spec.kind: openspec` and a baseline SHA was recorded; the baseline is `board.py --sync-sha <sha>`").
- MEDIUM, blueprints/record-kinds.md:33: work-order allowed values "pending, in-progress, done, blocked, cancelled (`completed` counts as done)". _handoff_lib.py:39 DEFAULT_ENUMS rejects `completed` unless a profile overrides `values:`. DONE_STATUSES (:19) only affects counting. Fix hint: say "`completed` is accepted only when the profile lists it under `values:`".
- LOW, SKILL.md (204 lines): over the hybrid target of 100-200 (hybrid-format-checklist.md:6). Trim the Quick Reference table, which duplicates the Scripts table.
- LOW, handoff-core/README.md:13-14 and quarkus-aws-saas/.../handoff-profile.yaml:4 state "a Claude Code subagent write guard blocks such names" as fact. blueprints/unverified-and-risks.md:20 (U2) says it is unverified and "observed in this build, not found in an official page". Fix hint: add (unverified) or reword as "factory convention".
- LOW, blueprints/unverified-and-risks.md:48 and :43: "Only U1-U5 are tagged in the skill text", yet U2 is mapped to "this register only" and no tag text exists. Also the section `Version-lifetime risk (irresolvable)` (:25) holds I1 and there are no separate Irresolvable or Medium headings (tag-notation-and-registers.md:13). Fix hint: remove U2 from the "tagged" claim; rename the heading to `Version-lifetime risk`.
- LOW, SKILL.md:58 makes project-wide `--include-worktree` Ask First, but :179, syncing-spec-from-code SKILL.md:37-39 and spec-synchronizer.agent.md:32-33 use it by default in E6-E8. The command explains it, the protocol skill does not. Fix hint: one sentence "a profile may mandate it for stages with uncommitted code".

## 2. specifying-changes-with-openspec-v1-15 (81.0)

- HIGH (family rule 13, same claim same tag), SKILL.md:91: Quick Reference "Archive target `openspec/changes/archive/YYYY-MM-DD-<change-name>/`" is untagged, sourced to the cli-archive spec. blueprints/always-do-patterns.md:130 tags the same claim "(medium confidence, L2: the cli-archive spec was read as paraphrased scenarios)". unverified-and-risks.md:71 and :105 list cli-archive as partly read, and the Quick Reference is listed there only for "requirement text maximum". Fix hint: add "(medium confidence, L2)" at :91 and add the row to the mapping at :105.
- HIGH (Always Do/Never Do hold High only; evidence-rule.md:18-19), SKILL.md:56 (Always Do 10: `validate <id> --type change --strict --json --no-interactive`), :58 (Always Do 12: `openspec --version` pin check) and :79 (Never Do alternative, same command). Their only source is cli.md, read through a summarising fetch with no recorded verbatim quote (research Bibliography S4 "full, summarizing fetch"; register L1, unverified-and-risks.md:70). L1 says such claims are (medium confidence, L1), with the single exception of the "stops before changing anything" quote. Fix hint: tag the flags (medium confidence, L1) and move them out of Always Do/Never Do alternatives, or quote the CLI lines verbatim in the research first.
- MEDIUM, SKILL.md:94-95 and :101 (`validate --concurrency` default 6 / `OPENSPEC_CONCURRENCY`, `--no-interactive`, `OPEN_SPEC_INTERACTIVE=0`, `CI`, telemetry opt-outs) and blueprints/non-interactive-and-windows.md:18, :20, :78: all from cli.md summary, untagged, while :23 of the same file tags the exit codes (medium confidence, L1). Fix hint: tag consistently with L1.
- MEDIUM, blueprints/never-do-patterns.md:38 "a dedicated `## RENAMED Requirements` section, applied first" is untagged. delta-format-and-archive.md:80 tags the archive merge order (medium confidence, L2). Fix hint: add the L2 tag or drop "applied first".
- LOW, SKILL.md:51 (Always Do 6) writes bold WHEN/THEN as a High rule, while always-do-patterns.md:64 and the register (I1) say enforcement is (unverified). Say "the schema and templates use bold" and keep the caveat in Ask First or the blueprint.
- LOW, SKILL.md:56 uses `validate <id> --type change ...` but :79 and never-do-patterns.md:75 omit `--type change` for the same command. Use one form.
- LOW, unverified-and-risks.md:28 and :32-36: unverified IDs are U1, U2, U3, U5, U6 (U4 retired). tag-notation-and-registers.md:17 wants plain contiguous IDs; renumber or keep the note.
- LOW, unverified-and-risks.md:18 "4 days before the research" is a relative phrase (hybrid-format-checklist.md:9). Use the two dates only.

## 3. syncing-spec-from-code (95.5)

No HIGH. The command and agent agree: Mode B only, same allowed commands, the uncovered-record scan, `delta_revisions`, spec.kind none stop, status `proposed`, inline return. Agent Mode A (verify) is correctly outside the command.

- MEDIUM, SKILL.md:19-25 and skill-structure.md ("Quick Navigation must link blueprints/evaluation-scenarios.md"): the nav links the section `#evaluation-scenarios`, not the file. The file is linked only at :31 and :115. Fix hint: put `[Evaluation scenarios](./blueprints/evaluation-scenarios.md)` in Quick Navigation.
- LOW, SKILL.md:52-53 Ask First "ask for the right dir or for the orchestrator to create it". The agent has Read/Grep/Glob/Bash only and is non-interactive (agent.md:9, :17). Say "return as a question to the orchestrator".
- LOW, SKILL.md:108 vs spec-synchronizer.agent.md:90: hand-off lines differ ("save spec-delta-<nn>.md" vs "save <record>"). The agent also lacks the exit-1 / missing `lastSyncedSha` hint that SKILL.md:33-35 requires (agent.md:59-67 only has the E5 note in the orchestrator docs). Align.
- LOW, SKILL.md:45-46 and agent.md:44-46 require bold WHEN/THEN as a check; openspec register I1 marks enforcement (unverified). Add the tag or phrase it as convention.
- LOW, SKILL.md:69-71 and blueprints/evaluation-scenarios.md:90: `<change-id>` resolves only to `openspec/changes/<id>/handoff`. Scenario 5 passes a capability id (`func-api-facade`) for the OCI layout `docs/handoff/{capability}`, which is undefined. State that with `--profile` the profile's `root` resolves the id.

## 4. observe-aws-workload (88.0)

No HIGH. Confirmed consistent: approval line formats (both lines identical to agent.md:29-30), `--i-have-user-approval` and `--alarm-name` (trigger-alarm-test.sh:21,37-38), exit codes 0/1/2/3 and 253 (cli-environment-and-exit-codes.md:48-92), role values and routing (profile yaml:85, :81).

- MEDIUM, SKILL.md:60-64 and :58 vs agent.md:39: the command maps review/provision/validate to Modes A/B/C and passes `mode=validate`; the agent intake requires "mode (A, B or C)" and never defines the words. Fix hint: add the mapping to the agent intake, or have the command pass the letter.
- MEDIUM, SKILL.md:4, :52-54, :75 vs agent.md:39,43-45: "What the agent needs" requires the spec path (review) and Terraform directory (provision), and the agent requires "the code owner and profile named in the work-order". The argument-hint and How to invoke have no `spec=`, `tf-dir=` or code-owner argument. The example at :69 (`mode=review nn=02`, no `wo=`) and the standalone claim at :66 can therefore only return needs-input. Fix hint: add the arguments or require `wo=` for review/provision and fix the example.
- MEDIUM, blueprints/evaluation-scenarios.md:41 expects "without them it would use `--skip logs,traces` and report `partial`". agent.md:76 says a failed precondition (missing relayed `logs-insights` line) means stop with needs-input or failed, and the agent never mentions `--skip` (validate-observability.sh:41,53,78-85 supports it). Fix hint: add the skip rule and outcome to agent Mode C step 1, or change the scenario.
- MEDIUM, SKILL.md:14-20: Quick Navigation links `#evaluation-scenarios`, not `blueprints/evaluation-scenarios.md` (skill-structure.md). Same fix as above.
- LOW, SKILL.md:37-38 vs :58 and :64: Ask First "Which mode, when ambiguous?" is unreachable because the command silently defaults to `validate`, the mode that touches live AWS. Either ask or document the default as deliberate.
- LOW, SKILL.md:4 `dashboards=<n1,n2>` vs validate-observability.sh:39 `--dashboard (repeatable)` and agent.md:77 `--dashboard D`. Say the list becomes repeated flags.
- LOW, SKILL.md:56 "`region=` is REQUIRED" vs :56 "pass `wo=`... reads these values from it instead" and Ask First :37 "when the work-order does not carry it". State which wins.
- LOW (evidence), agent.md:54, :58 and blueprints/evaluation-scenarios.md:14 state "X-Ray SDK maintenance mode since 2026-02-25" and "HTTP API has no X-Ray" with no inline URL (skill-structure.md hybrid rule; source is _family_facts_v3.40.md:34 and research F34/F35). Add the URL or a tag.

## 5. integrating-stripe-quarkus-v3-40 (90.0)

- HIGH (evidence-rule.md:18, skill-structure.md hybrid: Always Do holds a single High claim, no caveats), SKILL.md:51 (Always Do 5): the bullet carries a medium-confidence reason inline, "The reason (how the HTTP handler treats header values) is tagged (medium confidence, M15)". It has no inline URL of its own, and its basis is the handler source read via a summarising tool plus main-branch javadoc (register M15, L2; unverified-and-risks.md:118 maps this tag to "SKILL.md Always Do"). The register's own L2 rule makes the javadoc claims medium wherever they appear. Fix hint: move the rule into Ask First D9 (already there, with recommendation A) and keep in Always Do only a High statement, for example "Take the signature header from the request exactly as Stripe sends it".
- MEDIUM, SKILL.md:90 (and blueprints/always-do-patterns.md:53): retry backoff "`Thread.sleep`, base 500 ms doubling to 5 s, jitter 0.75 to 1.0" is untagged. The research (research_Stripe_Quarkus_Lambda_v3.40.md:619) records HttpClient.java (S13) as read "targeted" via the summarising tool, and no verbatim quote is recorded for these numbers. Rule 13 makes it (medium confidence) unless quoted. Fix hint: tag it or record the quote.
- LOW, blueprints/never-do-patterns.md:31-33 (N2 "Moved to Ask First D9") keeps a placeholder section and a numbering gap (SKILL.md Never Do has 7 rows against N1-N8). Renumber or drop the stub.
- LOW, SKILL.md:67: row D9 mixes two topics (signature header, plus the harm claims for request id and metadata) in one table cell of about 900 characters. Split into D9 and D10.
- LOW, SKILL.md:76 (Never Do alternative): "tenant + operation + business id" is the skill's own key design (research A8 only cites the cart-id strategy from Stripe), so this part of the alternative is a recommendation, not a High source. Phrase it as "a key derived from the business operation (Stripe: e.g. a cart id)" and move the composition to the patterns.

Other checks passed for ST: all research facts match (timeouts 30 000/80 000 ms, retries 0/2, 255 chars, 24 h, 15/30-day resend, 16 destinations, 29 s/30 s gateway timeouts, SQS 1 MiB, Java runtimes and SnapStart rows equal family-facts lines 15-16), family rules 3, 5, 6, 9, 10, 11 and 12 are applied, tag-to-register mapping covers every tag used.

## Cross-cutting notes

- Quick Navigation of both command skills does not link `blueprints/evaluation-scenarios.md` directly (skill-structure.md): the same fix applies to every command skill in the family.
- The contract fixes for observe-aws-workload (mode letters, missing arguments, `--skip`) should be done in the agent or the command together, to keep the profile roles and outcome words unchanged (family rules 14 and 15).
