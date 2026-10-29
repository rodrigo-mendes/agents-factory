# Migration Notes

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28.

## Breaking changes

None for security, OIDC, SmallRye JWT, HTTP permissions or Lambda HTTP in 3.40. The wiki says "Quarkus 3.40 LTS is the direct continuation of 3.39 so we don't expect any changes requiring manual intervention in 3.40" ([Migration Guide 3.40](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40)). Migration guides 3.31 to 3.39 were not read for security entries (unverified).

## Deprecations relevant to this skill

| Item | Change | Source |
|---|---|---|
| `quarkus-junit5` | renamed `quarkus-junit` in Quarkus 3.31; applies to the test dependencies | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 |
| `quarkus-test-amazon-lambda`, `LambdaClient` | removed in Quarkus 3.31; test with `quarkus-junit` and RestAssured against the mock event server | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 |

No configuration key renames are documented for 3.40.

## Upgrade steps (representative)

1. Align the Quarkus platform BOM to 3.40.1.1.
2. Re-run the security tests in [testing and verification](./testing-and-verification.md); no key renames are documented for 3.40.
3. Re-check the three `quarkus.lambda-http.*` role keys and `enable-security` in the configuration reference, because the Lambda HTTP extensions are preview.

## Compatibility matrix

| Dependency | Min | Max | Notes |
|---|---|---|---|
| `io.quarkus:quarkus-amazon-lambda-http` | 3.40.1.1 | 3.40.x | depends on `quarkus-vertx-http`, `quarkus-security`, `quarkus-amazon-lambda`, `aws-lambda-java-core`, `microprofile-jwt-auth-api` (POM) |
| `io.quarkus:quarkus-amazon-lambda-rest` | 3.40.1.1 | 3.40.x | same runtime dependencies (POM) |
| `io.quarkus:quarkus-oidc` | 3.40.x (platform) | 3.40.x | inside the Lambda HTTP extensions: (unverified) |
| `io.quarkus:quarkus-smallrye-jwt` | 3.40.x (platform) | 3.40.x | artifact name per the security-jwt guide |
| Quarkus 4 | n/a | n/a | out of scope (family rule 1); not asserted |

## Quarkus 4

Out of scope. Pin 3.40.x. Quarkus 4.0.0 is "Upcoming" with no date on https://quarkus.io/releases (High).
