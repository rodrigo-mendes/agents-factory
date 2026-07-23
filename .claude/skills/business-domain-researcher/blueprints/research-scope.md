# Research Scope Detail — business-domain-researcher

Detailed format templates for each research scope area. The agent fills these during the research
phase and includes the completed versions in the output file.

---

## Scope 2 — Three-Tier Operational Guardrails

### ✅ Always Do: Mandatory Domain Practices

Identify non-negotiable standards required by regulation, professional ethics, or organizational policy:
- Obligatory disclosures, record-keeping, and audit trail requirements
- Consent, privacy, and data handling obligations (LGPD, GDPR, HIPAA, etc. as applicable)
- Mandatory SLA thresholds and response time commitments
- Required documentation before, during, and after interactions
- Escalation triggers that cannot be bypassed

**Format per item**:
```
Practice: [Name]
Why: [Regulatory or policy basis — cite specific article, section, or policy]
How: [Minimal process description or checklist]
Applies When: [Trigger conditions]
Source: [Link to regulation, policy document, or standard]
```

---

### ⚠️ Escalate/Validate: Human Decision Required

Valid approaches that require human validation before execution:
- Decisions with financial, legal, or reputational impact above defined thresholds
- Cases involving ambiguous customer intent or conflicting stakeholder needs
- Situations not covered by existing policy (novel cases)
- Actions requiring cross-functional approval (Legal, Finance, Leadership)

**Format per item**:
```
Decision Point: [What requires human judgment]
Options: [A, B, C]
Tradeoffs: [Each path implies which outcomes, risks, stakeholders affected]
Escalation Path: [Who to involve — role, not name — and by when]
When to Escalate: [Specific triggers and context indicators]
Source: [Internal policy or SLA document]
```

---

### 🚫 Never Do: Prohibited Actions

Hard prohibitions, ethical violations, legal risks, and policy breaches:
- Actions that expose the organization to regulatory sanctions
- Communications that may constitute commitments beyond agent authority
- Data handling that violates privacy regulations or consent scope
- Bypassing mandatory human approval steps

**Format per item**:
```
Prohibition: [What NOT to do]
Why: [Legal, ethical, or policy reason — cite specific risk]
Instead: [Correct alternative approach]
Impact: [Regulatory sanction | Legal liability | Reputational damage | Policy breach]
Severity: [CRITICAL | HIGH | MEDIUM]
Source: [Regulation article, policy section, or legal opinion]
```

---

## Scope 3 — Policy & Regulatory Update Handling

- Breaking changes from regulatory updates (new laws, revised norms, court rulings)
- Transition path with effective dates and organizational deadlines
- Compatibility matrix: which existing practices must be retired vs. can coexist
- Deprecation warnings for practices that will become non-compliant

---

## Scope 4 — Stakeholder Interoperability

For each item in {{STAKEHOLDER_SYSTEMS_LIST}}:

```
Interface: {{DOMAIN_OR_FUNCTION_NAME}} ↔ [Stakeholder/System]
Collaboration Mode: [Handoff | Shared ownership | Approval gate | Information feed]
SLA: [Response time commitments between functions]
Trigger: [When does {{DOMAIN_OR_FUNCTION_NAME}} initiate contact with this stakeholder?]
Protocol: [Communication channel, required format, required information]
Risks: [What breaks at the seams — data gaps, delays, misinterpretation]
Source: [Internal RACI, SLA document, or process map]
```

---

## Scope 5 — Process Verification

Exact verification steps for:

**Interaction Initiation**:
```
Step: [How to open an interaction following mandatory protocol]
Checklist: [Required items before proceeding]
Expected State: [What a correctly opened interaction looks like]
```

**In-Process Compliance**:
```
Step: [Ongoing compliance checkpoints during execution]
Audit Trail: [What must be recorded and where]
Expected State: [Compliant in-progress state]
```

**Interaction Closure**:
```
Step: [Mandatory closure procedures]
Follow-up: [Required post-interaction actions — SLA, documentation, handoff]
Expected State: [Successfully closed and compliant interaction]
```

**Escalation Verification**:
```
Step: [How to verify a correctly executed escalation]
Confirmation: [What confirms the escalation was received and acted upon]
Expected State: [Escalation accepted, owner assigned, timeline set]
```

---

## Scope 6 — Scenario Simulation & Edge Cases

**Format per item**:
```
Scenario: [Name + category]
Trigger: [What situation activates this scenario]
Agent Response: [Expected behavior under guardrails]
Edge Variant: [What changes at the boundary of this scenario]
Human Handoff: [At what point does the agent hand off to a human?]
Reference: [Policy section, training guide, or industry standard case]
```

---

## Scope 7 — Operational Scale Considerations

- Volume boundaries: what breaks when interaction volume spikes (peak periods, campaigns)
- Escalation capacity: human team throughput as a constraint on autonomous agent volume
- Common failure modes at scale (queue overflow, SLA breach cascades, ambiguous-case accumulation)
- Regulatory monitoring and reporting requirements at scale
- Audit and compliance review cadence
