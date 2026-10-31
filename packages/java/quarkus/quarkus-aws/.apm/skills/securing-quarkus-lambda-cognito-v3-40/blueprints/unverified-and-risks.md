# Unverified Register, Risks and Bibliography

Research date 2026-10-28. Back to [SKILL.md](../SKILL.md). The research reports a quality score of 88%, a deep run using all 3 iterations, and 6 triangulated claims. Family facts verified by the orchestrator on 2026-10-28 keep the tags of the family facts file.

## Contents

- [Version-lifetime risk](#version-lifetime-risk)
- [Unverified items](#unverified-items)
- [Irresolvable items](#irresolvable-items)
- [Medium-confidence items](#medium-confidence-items)
- [Coverage limits](#coverage-limits)
- [Tag to register mapping](#tag-to-register-mapping)
- [Source Bibliography](#source-bibliography)

## Version-lifetime risk

- Quarkus 3.40 was released 2026-09-30 as an LTS and is community-maintained until 2027-09-30; latest patch 3.40.1.1 (2026-10-19) (High; https://quarkus.io/releases). The 3.40 documentation is new and may still change.
- Quarkus 4.0.0 is "Upcoming" with no date on the releases page (High). Quarkus 4 content is rejected for this skill; the 3.40 patterns are not asserted for Quarkus 4.
- `quarkus-amazon-lambda-http` and `quarkus-amazon-lambda-rest`: the guide states "This technology is considered preview", so backward compatibility is not guaranteed (High; https://quarkus.io/version/3.40/guides/aws-lambda-http).
- Cognito and API Gateway pages are current AWS pages with no page date shown; behaviour such as the pre token generation event versions or the authorizer limits can change. Re-read them before relying on a limit.

## Unverified items

11 unverified items (do not assert them).

| ID | Item | Impact and workaround |
|---|---|---|
| U1 | `quarkus-oidc` bearer authentication inside `quarkus-amazon-lambda-http` or `-rest` is not documented; the Lambda HTTP guide never mentions `quarkus-oidc`, SmallRye JWT or bearer tokens | Option B could fail at runtime. Run an integration test with a real Cognito token in `sam local` or a deployed stage |
| U2 | Whether `quarkus.http.auth.permission.*` path policies are evaluated in the Lambda HTTP extensions | Path policies might silently not apply. Rely on annotations; test each path |
| U3 | Whether the mock event server (dev and test) passes an authorizer context so `enable-security` works in `@QuarkusTest` | Option A tests may not cover role mapping. Use `sam local` with `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` (local only) or a unit test with a constructed event |
| U4 | Interaction when both `enable-security` and `quarkus-oidc` are active (which identity wins) | Do not combine without a real-token test |
| U5 | Whether `SecurityIdentityAugmentor` runs for identities built by `LambdaIdentityProvider` or `enable-security`; whether `QuarkusSecurityIdentity.Builder` has `addAttribute` (only `addPermission` was seen) | Keep the tenant check in the resource method |
| U6 | Cold-start latency of the OIDC JWKS and discovery fetch in Lambda, and whether it happens during a SnapStart snapshot | Unknown latency; possible stale state after restore. Measure |
| U7 | API Gateway authorizer against Lambda invocation pricing (pricing pages not read) | Give no cost verdict; ask the user for pricing data |
| U8 | Security-related entries in the migration guides 3.31 to 3.39 (only 3.40 was read; 3.40 has none) | Read the wiki migration pages before an upgrade from an earlier version |
| U9 | The `issuer` value in the discovery document of an updated issuer (`issuer-cognito-idp` host), that is the exact `auth-server-url` to use | Fetch a real pool's `/.well-known/openid-configuration` |
| U10 | Package of `LambdaAuthenticationRequest` (not shown in the guide) and the `aws-lambda-java-events` accessor names (`getRequestContext().getAuthorizer().getJwt().getClaims()`) | Check the javadoc or source at 3.40.1.1 before compiling the sample |
| U11 | Quarkus behaviour when the authorizer claims come from an access token: the guide's Principal path `...claims.cognito:username` does not match (access tokens carry `username`; M2M tokens carry neither `username` nor `cognito:groups`; family fact, High for the Cognito claims, verified 2026-10-28 on https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html) | Do not assert the Principal name for an access token; identify users and tenants by `sub` or a custom attribute; M2M tokens get no roles from `cognito:groups`; test with a real access token |

## Irresolvable items

0 irresolvable items. Facts that documentation cannot resolve are listed once under unverified items.

## Medium-confidence items

13 medium-confidence items (M1 to M8 from the research, M9 from the family facts, M10 from a later review, M11 to M13 from a later review).

| ID | Item | Why medium |
|---|---|---|
| M1 | `quarkus-oidc` likely works in the Lambda HTTP extensions | Inference from the extension POM dependencies on `quarkus-vertx-http` and `quarkus-security`; no page documents it |
| M2 | `quarkus.oidc.roles.role-claim-path` needs double quotes for `cognito:groups` | The reference says to quote "namespace-qualified claim names" and gives only a `/` example |
| M3 | `JsonWebToken.getClaim(String)` signature | The MicroProfile JWT API was not read |
| M4 | The default ID-token audience check uses `quarkus.oidc.client-id`; setting `quarkus.oidc.token.audience` for access tokens without `aud` rejects them | Inference from the reference wording and the Cognito access-token page |
| M5 | An HTTP API JWT authorizer takes a single issuer | Inferred from the singular `Issuer` in the AWS CLI and CloudFormation examples |
| M6 | `@OidcSecurity(claims = @Claim(key, value))` attribute names | From a tool summary of the bearer guide, not quoted |
| M7 | Array claims such as `cognito:groups` reach the Lambda event as a bracketed string `[ a b ]` | Implied by the default matcher description; the AWS page shows only string claims |
| M8 | Deny-unannotated-endpoints as the family default | Engineering judgement |
| M9 | The defaults of `quarkus.lambda-http.enable-security` (`false`), `map-cognito-to-roles` (`true`), `cognito-role-claim` (`cognito:groups`) and `cognito-claim-matcher` | Family fact (rule 13): the defaults are stated by the configuration reference, not by the guide (the guide only says to add `enable-security=true` and that groups map unless `map-cognito-to-roles=false`). The research quotes the all-config rows (read to 100,000 of 232,437 characters, L1) as High; no verbatim quote is recorded here, so the family tag (medium confidence) applies to all four |
| M10 | Counting 401 and 403 per route as the monitoring practice | Engineering practice; no page |
| M11 | Defaults of the `quarkus.oidc` reference keys: `token.forced-jwk-refresh-interval` `10M`, `jwks.resolve-early` `true`, `jwks.cache-size` `10`, `jwks.cache-time-to-live` `10M`, `roles.source` `accesstoken` for `service` applications | Reference page read through a summarising tool; no verbatim quote of the default rows is recorded (family rule 13) |
| M12 | SmallRye JWT defaults: `smallrye.jwt.jwks.refresh-interval` 60 min, `forced-refresh-interval` 30 min | Security-jwt page read through a summarising tool; no verbatim quote recorded (family rule 13) |
| M13 | `quarkus.security.jaxrs.deny-unannotated-endpoints` default `false` | Reference page read through a summarising tool; no verbatim quote recorded (family rule 13) |

## Coverage limits

3 coverage limits (parts of pages not read, or read through summarisation).

| ID | Limit |
|---|---|
| L1 | https://quarkus.io/version/3.40/guides/all-config was read from character 0 to 100,000 of 232,437; the four `quarkus.lambda-http.*` rows were quoted from that range |
| L2 | https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication was read from character 0 to 100,000 of 109,477; the part after "Step Up Authentication" was not read |
| L3 | https://quarkus.io/version/3.40/guides/security-authentication-mechanisms was read from character 0 to 100,000 of 110,821; the default of `quarkus.http.auth.proactive` was not confirmed |

All pages were read through a summarising fetch tool; quoted sentences were returned verbatim, other wording is a paraphrase by the tool.

## Tag to register mapping

| Tag text used in the skill | Where | Register id |
|---|---|---|
| (unverified) `quarkus-oidc` inside the Lambda HTTP extensions | SKILL.md Version Context and Ask First K1; ask-first-decisions K1 and K3; option-b header and open points; testing tests list; migration-notes matrix; evaluation-scenarios 2 | U1 |
| (unverified) `quarkus.http.auth.permission.*` in Lambda | always-do-patterns 8; option-a limits; option-b open points | U2 |
| (unverified) mock event server and authorizer context | option-a limits; testing mocking | U3 |
| (unverified) identity when `enable-security` and `quarkus-oidc` both active | SKILL.md Ask First K1; ask-first-decisions K1; option-b open points; evaluation-scenarios 2 | U4 |
| (unverified) `SecurityIdentityAugmentor` for Lambda identities, `addAttribute` | option-a limits; multi-tenant-isolation augmentor | U5 |
| (unverified) cold-start and SnapStart effect of the JWKS fetch | ask-first-decisions K1; option-b reference keys | U6 |
| (unverified) pricing and latency data | SKILL.md Ask First K1; ask-first-decisions K1; evaluation-scenarios 6 | U7 |
| (unverified) security entries in migration guides 3.31 to 3.39 | migration-notes breaking changes | U8 |
| (unverified) `issuer` of the updated issuer's discovery document | SKILL.md Ask First K4; ask-first-decisions K4 | U9 |
| (unverified) `LambdaAuthenticationRequest` package, event accessor names | always-do-patterns 4; option-a lifecycle code and custom mapping; multi-tenant-isolation code; evaluation-scenarios 1 and 5 | U10 |
| (medium confidence) `quarkus-oidc` likely works in Lambda HTTP | SKILL.md Version Context and Ask First K1; ask-first-decisions K1; option-b header; evaluation-scenarios 2 | M1 |
| (medium confidence) quoting of `role-claim-path` | option-b roles section; testing tests list; evaluation-scenarios 2 | M2 |
| (medium confidence) `JsonWebToken.getClaim` signature | option-b tenant code; multi-tenant-isolation | M3 |
| (medium confidence) default ID-token audience check and `token.audience` | option-b audience section | M4 |
| (medium confidence) one issuer per HTTP JWT authorizer | SKILL.md Ask First K3; ask-first-decisions K3 | M5 |
| (medium confidence) `@OidcSecurity` attribute names | testing mocking | M6 |
| (medium confidence) bracketed string array claims | always-do-patterns 3 | M7 |
| (medium confidence) deny-by-default as family default | SKILL.md Ask First K6; ask-first-decisions K6 | M8 |
| (medium confidence) `enable-security` default `false`; role-mapping key defaults | SKILL.md Version Context and Quick Reference; always-do-patterns 1 and 3; option-a what the integration does and lifecycle; evaluation-scenarios 1 | M9 |
| (medium confidence) count 401/403 per route | multi-tenant-isolation observability | M10 |
| (medium confidence) `quarkus.oidc` reference-key defaults | SKILL.md Quick Reference; option-b reference keys | M11 |
| (medium confidence) SmallRye JWT refresh defaults | ask-first-decisions K7 | M12 |
| (medium confidence) `deny-unannotated-endpoints` default | SKILL.md Quick Reference; ask-first-decisions K6 | M13 |
| (unverified) Quarkus behaviour with an access token on the `cognito:username` Principal path | SKILL.md Ask First K2; always-do-patterns 2; option-a what the integration does; ask-first-decisions K2; evaluation-scenarios 1 | U11 |
| read to 100,000 of 232,437 characters | option-a what the integration does | L1 |
| read to 100,000 of 109,477 characters (L2) | option-b configuration; testing mocking | L2 |
| read to 100,000 of 110,821 characters (L3), proactive default not confirmed | ask-first-decisions K7; option-b open points | L3 |

## Source Bibliography

All read 2026-10-28.

**Quarkus 3.40 and registry**

| # | URL | Coverage | Used for |
|---|---|---|---|
| S1 | https://quarkus.io/version/3.40/guides/aws-lambda-http | Security Integration section in full | Principal paths, roles, `LambdaIdentityProvider`, `FORCE_USER_NAME`, preview status |
| S2 | https://quarkus.io/version/3.40/guides/all-config | 0 to 100,000 of 232,437 (L1) | `quarkus.lambda-http.*` keys and defaults |
| S3 | https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication | 0 to 100,000 of 109,477 (L2) | discovery, roles, test support |
| S4 | https://quarkus.io/version/3.40/guides/security-oidc-configuration-properties-reference | two passes, complete | `required-claims`, `token.audience`, JWKS keys |
| S5 | https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy | complete | tenant resolution |
| S6 | https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference | complete | annotations, augmentor, deny-by-default |
| S7 | https://quarkus.io/version/3.40/guides/security-jwt | complete | SmallRye JWT keys |
| S8 | https://quarkus.io/version/3.40/guides/security-authentication-mechanisms | 0 to 100,000 of 110,821 (L3) | `quarkus-oidc` against SmallRye JWT |
| S9 | https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.40 | official wiki, versioned by name | no changes in 3.40 |
| S10 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-http/3.40.1.1/quarkus-amazon-lambda-http-3.40.1.1.pom | full | dependencies |
| S11 | https://repo1.maven.org/maven2/io/quarkus/quarkus-amazon-lambda-rest/3.40.1.1/quarkus-amazon-lambda-rest-3.40.1.1.pom | full | dependencies |

**AWS official (current pages, no page date shown)**

| # | URL | Used for |
|---|---|---|
| A1 | https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-tokens-verifying-a-jwt.html | `token_use`, `client_id`, `aud`, `iss`, key rotation |
| A2 | https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-access-token.html | access-token claims, `sub`, revocation |
| A3 | https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-id-token.html | ID-token claims, `custom:` attributes |
| A4 | https://docs.aws.amazon.com/cognito/latest/developerguide/federation-endpoints.html | discovery and JWKS URLs, issuer formats |
| A5 | https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-refresh-token.html | refresh-token lifetime and rotation |
| A6 | https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html | V2_0/V3_0 access-token customization |
| A7 | https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-settings-attributes.html | `WriteAttributes`, immutable attributes |
| A8 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html | HTTP JWT authorizer checks and cache |
| A9 | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-integrate-with-cognito.html | REST API Cognito integration |
| A10 | https://docs.aws.amazon.com/apigateway/latest/developerguide/apigateway-enable-cognito-user-pool.html | `COGNITO_USER_POOLS` authorizer, 1,000-pool limit |
| A11 | https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html | event payload |

**Family facts (orchestrator-verified)**: https://quarkus.io/releases ; https://quarkus.io/version/3.40/guides/aws-lambda-http (preview status, security opt-in); https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31 (`quarkus-junit5` rename, removal of `quarkus-test-amazon-lambda`). Validation: two WebSearch queries found no official page documenting `quarkus-oidc` inside `quarkus-amazon-lambda-http`; the results were not used as evidence. Community sources: none used. The extension source repository (https://github.com/quarkusio/quarkus) was not fetched (page not recorded).
