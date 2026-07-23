# Evaluation Scenarios — requirements-methodology-researcher

Used to verify that the skill activates correctly, enforces framework-edition fidelity,
applies testability guardrails, and refuses anti-pattern artifacts with correct alternatives.

---

## Scenario 1: Canonical research request — Scrum User Stories (standard path)

```json
{
  "skills": ["requirements-methodology-researcher"],
  "query": "Research Scrum user story practices for a 5-person B2B SaaS product team using Scrum Guide 2020 and Jira for backlog management. We need to know how to write valid user stories with acceptance criteria.",
  "expected_behavior": [
    "Identifies Scrum Guide 2020 (Schwaber & Sutherland, scrumguides.org) as the primary authoritative source",
    "Documents the mandatory artifact elements: specific persona (not 'user'), need statement (what, not how), benefit clause (measurable outcome), and at least one acceptance criterion",
    "Applies INVEST checklist as a quality gate: Independent, Negotiable, Valuable, Estimable, Small, Testable",
    "Documents Jira artifact mapping: Summary = story title, Description = full story + AC, Labels or custom fields for Definition of Ready status",
    "Flags Scrum 2020 change: Sprint Goal is a commitment (not a suggestion) — affects how stories link to sprint objectives",
    "Produces a minimal valid artifact (standard user story template) and a production reference artifact for a B2B SaaS context",
    "All sources cite the Scrum Guide 2020 edition specifically, not earlier versions"
  ],
  "success_criteria": {
    "must_pass": [
      "scrumguides.org identified as authoritative source with edition year 2020",
      "All three story components documented: persona, need, benefit",
      "INVEST checklist present with human-evaluable questions for each letter",
      "Jira artifact mapping covers required fields and gap warnings (what Jira cannot enforce automatically)",
      "Minimal valid artifact is a complete, copy-ready user story — not just a template skeleton"
    ],
    "must_not": [
      "Cite Scrum Guide 2017 or earlier practices without flagging they are superseded",
      "Use 'as a user' as a valid persona example without flagging the anti-pattern",
      "Omit the benefit clause from the mandatory elements",
      "Reference velocity-as-commitment (removed in Scrum 2020) as a valid practice"
    ]
  }
}
```

---

## Scenario 2: Edge case — story too large / epic decomposition needed

```json
{
  "skills": ["requirements-methodology-researcher"],
  "query": "Our team in a SAFe 6.0 context has this story: 'As a customer, I want to manage my account so that I can control all my settings.' Help us research how to handle it.",
  "expected_behavior": [
    "Identifies SAFe 6.0 (scaledagileframework.com) as the authoritative source for this context",
    "Immediately detects the story as too broad: 'manage my account' and 'all my settings' are compound and non-specific — fails the Small and Testable criteria of INVEST",
    "Applies story splitting guidance: identifies appropriate split patterns (CRUD operations, user roles, workflow steps, data variations)",
    "Produces 'Before → After' split example: the oversized story decomposes into 3+ valid stories (e.g., update email, change password, manage notification preferences)",
    "Documents SAFe 6.0 distinction: Feature (business capability, too large for one sprint) vs. Story (implementable in one iteration) — the original story is Feature-level",
    "Documents team context signal: in a scaled org with 3+ squads, Feature ownership vs. Story authorship must be explicit",
    "All citations reference SAFe 6.0 specifically, not SAFe 5.x or earlier"
  ],
  "success_criteria": {
    "must_pass": [
      "Story identified as too large (Feature-level, not Story-level) with INVEST Small/Testable failure cited",
      "At least one concrete split pattern applied with a Before→After example",
      "SAFe 6.0 Feature/Story distinction documented with scaledagileframework.com reference",
      "Each resulting story in the split has its own acceptance criterion",
      "Team context (scaled org, 3 squads) reflected in the ownership guidance"
    ],
    "must_not": [
      "Accept 'manage my account' as a valid single user story without flagging the scope issue",
      "Produce acceptance criteria that describe UI screens instead of observable user behavior",
      "Reference SAFe 5.x practices without confirming they apply to SAFe 6.0",
      "Split the story by technical layer (backend story + frontend story) — this is the forbidden technical-layer split anti-pattern"
    ]
  }
}
```

---

## Scenario 3: Misuse / out-of-scope — producing a Definition of Done autonomously

```json
{
  "skills": ["requirements-methodology-researcher"],
  "query": "Generate a Definition of Done for our 5-person Scrum team working on a healthcare SaaS product.",
  "expected_behavior": [
    "Identifies that Definition of Done is a team-specific commitment — per Scrum Guide 2020, the Scrum Team creates and owns the DoD, not an external agent",
    "Classifies this as Low Confidence / Ask First: the agent cannot autonomously produce a binding DoD because it encodes team-specific quality commitments, regulatory obligations, and organizational standards that are not known without explicit team input",
    "Asks clarifying questions before producing any output: (a) What are the healthcare regulatory requirements (HIPAA, ANVISA)? (b) Does the team have automated testing? (c) What security review is required before release? (d) What documentation is mandatory?",
    "May produce a DoD template or starter checklist as a facilitation aid, clearly labeling it as a starting point for team discussion — NOT as a binding definition",
    "Documents that the healthcare context introduces compliance-specific DoD items (e.g., audit trail for user actions, security scan clean, data handling verified) that require qualified input"
  ],
  "success_criteria": {
    "must_pass": [
      "Scrum Guide 2020 cited: DoD is a Scrum Team commitment, not externally imposed",
      "Agent explicitly declines to produce a binding DoD without team input",
      "Clarifying questions listed before any template is provided",
      "Healthcare regulatory context flagged as requiring specialized input",
      "If a template is offered, it is labeled as a facilitation aid, not a final output"
    ],
    "must_not": [
      "Produce a DoD and present it as ready-to-adopt without team discussion",
      "Omit the healthcare/regulatory dimension from the DoD considerations",
      "Treat DoD as equivalent to acceptance criteria on a single story",
      "Reference Scrum 2017 or earlier DoD guidance as the current standard"
    ]
  }
}
```

---

## Scenario 4: Anti-pattern trap — solution-prescriptive story and untestable acceptance criteria

```json
{
  "skills": ["requirements-methodology-researcher"],
  "query": "Write this user story: 'As a user, I want a React dropdown with lazy loading so that the page is fast.'",
  "expected_behavior": [
    "Detects two anti-patterns simultaneously and flags both explicitly",
    "Anti-pattern 1: 'as a user' — non-specific persona; fails role specificity requirement",
    "Anti-pattern 2: 'React dropdown with lazy loading' — solution-prescriptive; describes implementation (React, lazy loading) instead of the user need; violates Negotiable in INVEST",
    "Anti-pattern 3 (implied): 'so that the page is fast' — vague benefit; not measurable; acceptance criterion cannot be derived from this",
    "Does NOT produce the story as requested",
    "Asks the clarifying questions needed to rewrite it correctly: 'Who is the user? (persona) What are they trying to accomplish? (need) What would a measurably fast page mean to them? (observable outcome)'",
    "Provides a corrected version once the team answers the clarifying questions: e.g., 'As a procurement manager, I want to browse the product catalog without waiting for the full list to load, so that I can find items quickly even when the catalog has 10,000+ entries.'"
  ],
  "success_criteria": {
    "must_pass": [
      "Both anti-patterns named explicitly: non-specific persona AND solution-prescriptive need statement",
      "Vague benefit flagged: 'fast' is not measurable/testable",
      "Story production refused until clarifying questions are answered",
      "Corrected version demonstrates specific persona, need (what, not how), and measurable outcome",
      "Corrected acceptance criteria are observable and non-prescriptive (no mention of React or lazy loading)"
    ],
    "must_not": [
      "Produce the story with 'as a user' and the React implementation detail intact",
      "Add acceptance criteria that reference UI components (dropdowns, lazy loading) instead of observable user behavior",
      "Silently replace the anti-patterns without explaining what was wrong and why",
      "Accept 'the page is fast' as a valid benefit statement"
    ]
  }
}
```
