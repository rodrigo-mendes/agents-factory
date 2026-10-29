# Round 1 TEST — batches 1-2 (skill-evaluator, 2026-10-28; saved by orchestrator)

| Skill | Pass |
|---|---|
| developing-quarkus-amazon-lambda-v3-40 | 6/6 |
| developing-quarkus-amazon-lambda-http-v3-40 | 6/6 (note: add pointer to the Cognito access-token caveat in its Security section) |
| securing-quarkus-lambda-cognito-v3-40 | 5/6 effective — S1 passes literally but encodes `cognito:username` for all tokens; contradicts family fact (access tokens carry `username`) → fix scenario must_pass #2 AND skill (SKILL.md:49, always-do 32-35/42, option-a:37, register) |
| integrating-quarkus-amazon-data-v3-40 | 6/6 |
| integrating-quarkus-amazon-messaging-v3-40 | 6/6 (advisory: `AWS_REGION` stated untagged at SKILL.md:55 / always-do A4:78 vs data skill medium/unverified → tag + link data C3) |
| testing-quarkus-amazon-lambda-v3-40 | 6/6 (advisory: enable-security default untagged SKILL.md:84, http-lambda-testing.md:59) |
