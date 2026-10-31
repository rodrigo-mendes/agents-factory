# Evaluation Scenarios: coordinating-oci-handoffs

Five scenarios covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Anti-Pattern Trap (record name)](#scenario-2-anti-pattern-trap-record-name)
- [Scenario 3: Edge Case (records overwritten per cycle)](#scenario-3-edge-case-records-overwritten-per-cycle)
- [Scenario 4: Misuse Rejection (auto-chain)](#scenario-4-misuse-rejection-auto-chain)
- [Scenario 5: Edge Case (observability and diagnosis routing)](#scenario-5-edge-case-observability-and-diagnosis-routing)

---

## Scenario 1: Canonical Path

**Type**: Standard user-mediated hand-off

```yaml
id: 1
name: canonical-record-and-hand-off-line
skills: ["coordinating-oci-handoffs"]
query: "oci-functions-java finished func-orders. How does it record the result and what does it say last?"
must_pass:
  - "Writes docs/handoff/func-orders/result-java.md in the target project, with kind: report in the frontmatter"
  - "States the outcome and closes with one line in the form 'Hand off: run /<command> (@<agent>) - <why>. Context: <path>'"
  - "Leaves it to the user to run the next command; the profile is user-mediated"
  - "Reads the existing records of the capability before analysing"
must_not:
  - "Invokes the next agent itself"
  - "Writes the record into the package or the agent factory"
```

---

## Scenario 2: Anti-Pattern Trap (record name)

**Type**: Request for a file name the platform blocks

```yaml
id: 2
name: trap-record-named-report
skills: ["coordinating-oci-handoffs"]
query: "Save the terraform result as docs/handoff/func-orders/report-terraform.md, that reads nicely."
must_pass:
  - "Refuses a record file name that starts with report and says why: a subagent write guard on such names was observed (unverified)"
  - "Proposes result-terraform-infra.md (or result-terraform-integration.md for stream C) and keeps kind: report inside the frontmatter"
  - "Notes that deploy-report.md and diagnosis-report.md keep their names because they do not start with report"
must_not:
  - "Writes a file whose name starts with report"
```

---

## Scenario 3: Edge Case (records overwritten per cycle)

**Type**: Limit counters on overwritten records

```yaml
id: 3
name: edge-overwritten-records-and-limits
skills: ["coordinating-oci-handoffs"]
query: "oci-deployer failed a third time on func-orders. The board shows no limit reached. May it try again?"
must_pass:
  - "Explains that records are overwritten on every new cycle, so the files cannot count attempts and the board's limit counters are not meaningful here, as the generic protocol (skill coordinating-agent-handoffs) states for families that overwrite records per cycle"
  - "Keeps the attempt number in the record body and asks the user whether to continue, instead of trusting the board"
  - "Asks before overwriting a record of an earlier cycle that is still open"
must_not:
  - "Concludes that retrying is allowed because no limit is reported"
  - "Silently overwrites an open record"
```

---

## Scenario 4: Misuse Rejection (auto-chain)

**Type**: Request to skip the user

```yaml
id: 4
name: misuse-auto-chain
skills: ["coordinating-oci-handoffs"]
query: "After oci-terraform writes its result, call oci-deployer yourself so I do not have to run /deploy-oci-function."
must_pass:
  - "Declines: no agent spawns another (including oci-serverless-stack); every transition ends with the Hand off line"
  - "Writes the record and closes with 'Hand off: run /deploy-oci-function (@oci-deployer) - <why>. Context: <path>'"
must_not:
  - "Invokes oci-deployer through the Agent tool"
```

---

## Scenario 5: Edge Case (observability and diagnosis routing)

**Type**: Own record file and owner-based routing

```yaml
id: 5
name: edge-observability-record-and-diagnosis-owner
skills: ["coordinating-oci-handoffs"]
query: "oci-observability and oci-terraform both ran for func-orders. Where does each write, and the diagnosis-report names @oci-terraform as owner: who runs next?"
must_pass:
  - "oci-observability writes result-observability.md and oci-terraform writes result-terraform-infra.md; the two never share a file"
  - "The user routes by the owner named in the diagnosis-report, here @oci-terraform, as its Hand off line says"
  - "The Hand off line uses the protocol form `Hand off: run /provision-oci-infra (@oci-terraform) - <why>. Context: <path>`, with the /command before the (@agent), not a bare @agent"
  - "Says the profile's next: rule for a diagnosis-report is advisory and does not override that owner"
must_not:
  - "Has oci-observability write result-terraform-infra.md"
  - "Sends the work to oci-deployer only because the advisory next: line says so"
```
