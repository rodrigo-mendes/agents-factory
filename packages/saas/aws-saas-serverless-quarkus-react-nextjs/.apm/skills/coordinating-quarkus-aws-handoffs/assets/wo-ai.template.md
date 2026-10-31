---
kind: work-order
id: wo-<nn>-ai
from: building-aws-saas-serverless-quarkus-react-nextjs
to: quarkus-lambda-integrator    # same agent as `code`
role: ai                         # shares the agent of `code`: the board would show `code`; this field keeps `ai` visible in status.md
change: <change-id>
task: <task-id>
refs: []                         # fix round (I8): [<previous wo id>, review-<nn>]
requirements: [R3]
status: pending
createdAt: <ISO 8601 UTC>
---

## Functionality

Plain sentences: what the user gets and what happens when the AI fails or is slow. Example: when an item is created,
its category is suggested by the AI in the background; if the AI fails or times out the category is "outros" and nothing breaks for the user.

## Diagram

Sequence or flow copied from `changes/<id>/design/<flow>.md` (section 3), with the provider call and its timeout.

## Scope

One AI task = one AI service or one consumer that calls the LLM. Steps I0-I6 and I9 (I8 + I9 when `refs` holds a review).
Output: code + `result-<nn>-ai.md` (shape of `assets/result-code.template.md`; put `role: ai` in its frontmatter; the review goes to `langchain4j-reviewer` because the work-order lists it, and a failed build counts in `build_attempts` either way).

## Skills

- integrating-quarkus-langchain4j-v1-15 (only after the yes of the user to D1) - integrating-quarkus-amazon-messaging-v3-40
- testing-quarkus-amazon-lambda-v3-40 - refactoring-quarkus-java (always)

## Requirements

- R3: <requirement text> - scenarios: <names>, one test each (e.g. `R3_llmTimeout_fallsBackToOutros`).

## Applicable ADRs

- `architecture/adr/<NNN>-llm-provider.md` - provider and model decided. `infrastructure/spec.md` section 6: where the key lives.

## Constraints

- Ask-First resolved: `D1 -> 1.15.0.CR1 accepted (gate=D1-langchain4j)`.
- Model named explicitly; provider timeout and `@Timeout` smaller than the gateway timeout; fallback defined; key from Secrets Manager; prompt and response never in logs; tests use `@InjectMock`, no real provider call.

## Limits

- build_attempts: <effective value> - review_rounds: <effective value> - coverage_min: <effective value>   (source: profile | override | args)

## Acceptance criteria

- [ ] One passing test per scenario, including provider timeout and provider error.
- [ ] `mvn -q verify` green; coverage of new classes >= coverage_min; `function.zip` built.
- [ ] Review order: `langchain4j-reviewer` first, `quarkus-code-reviewer` only after the first is `approved` (hold, see wo-review). Every review record of the task carries `role: ai` (a changes-requested then goes back to the same agent).
- [ ] Result record valid, with `role: ai`, `spec_impact` and `## Spec impact`.
