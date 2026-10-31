# Round 5 VALIDATE — group B (quality-validator, 2026-10-28; saved by orchestrator from the inline report)

| Skill | HIGH | MED | LOW | Score |
|---|---|---|---|---|
| logging-quarkus-lambda-v3-40 | 0 | 1 | 3 | 96.0 |
| tracing-quarkus-lambda-v3-40 | 0 | 2 | 5 | 92.5 |
| integrating-quarkus-amazon-messaging-v3-40 | 1 | 1 | 3 | 90.0 |
| monitoring-quarkus-lambda-v3-40 | 1 | 1 | 4 | 89.5 |
| observing-quarkus-lambda | 2 | 1 | 6 | 82.5 |

- messaging H1 rule 13: `aws-lambda-java-events` resolved version (unverified) vs family fact 42 (medium, 3.16.1). M1 (irresolvable) class vs policy (policy self-contradictory). L1 Region row no Q id; L2 Secrets Manager default page; L3 two URLs per bullet.
- logging M1 Scope line says `requestId` (key is `AWSRequestId`). L1 BOM coverage wording; L2 two URLs; L3 "family fact NN" dangling refs.
- tracing M1 Version Context row cites POM for S7/S8 claims. M2 "no OTel→X-Ray route documented" absence of evidence untagged. L1 caveat in Always Do; L2 M7 omits java-core/events; L3 lowercase sentence; L4 alternative in ❌ cell; L5 old ADOT pages provenance note.
- monitoring H1 rule 13: log ingestion $0.50/GB (medium) vs logging (unverified, $0.25 vs $0.50 conflict). M1 scenario criterion: JSON wrapping is M12 medium. L1 ✅ cells no URL; L2 example timestamp outside the 2 h window; L3 C-ids; L4 multi-claim bullets.
- umbrella H1 ask-first:16 calls gRPC OTLP to X-Ray "a route to check (unverified)" vs tracing F9 High (HTTP only). H2 wrapping claim untagged (monitoring M12). M1 request-id spelling in correlation-recipe:17. L1 N5 stub; L2 OCI umbrella mention; L3 family fact 40 ref; L4 EMF PII citation; L5 no -v3-40 suffix (intentional); L6 register sections.
