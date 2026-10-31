# Testing and Verification

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Test mechanics in depth: [testing-quarkus-amazon-lambda-v3-40](../../testing-quarkus-amazon-lambda-v3-40/SKILL.md). Lambda HTTP mechanics: [developing-quarkus-amazon-lambda-http-v3-40](../../developing-quarkus-amazon-lambda-http-v3-40/SKILL.md).

## Contents

- [Verification Loop](#verification-loop)
- [Tests that must exist](#tests-that-must-exist)
- [Mocking](#mocking)
- [Production readiness checklist](#production-readiness-checklist)

## Verification Loop

Representative commands; adapt to your environment (Quarkus 3.40.1.1 project).

```bash
# 1. Security keys present
grep -E "quarkus\.lambda-http\.enable-security|quarkus\.oidc\.(auth-server-url|token\.required-claims)" src/main/resources/application.properties
# Expected: Option A -> enable-security=true
#           Option B -> auth-server-url + required-claims.token_use + required-claims.client_id

# 2. Forbidden settings absent
grep -rnE "token\.issuer=any|QUARKUS_AWS_LAMBDA_FORCE_USER_NAME" src/ deploy/ || echo "OK: none"
# Expected: OK: none (N4, N6)

# 3. Tenant never read only from the path
grep -rnE "@PathParam\(\"tenantId\"\)" src/main/java
# Expected: every hit is compared with a token claim (N1)

# 4. Tests
./mvnw -q test
# Expected: BUILD SUCCESS, including the 401, 403 and cross-tenant cases below
```

## Tests that must exist

- No token gives 401. Valid token with a missing role gives 403. The bearer guide shows an invalid token giving 401 with `WWW-Authenticate: Bearer` and a missing role giving 403 (Option B).
- A valid token for tenant A calling `/tenants/B/...` gives 403 (family rule 6).
- An ID token presented where an access token is required gives 401 (Option B; [never-do N3](./never-do-patterns.md#n3-any-cognito-jwt-without-token_use-and-client-check-high)).
- A token from another app client of the same pool gives 401.
- `cognito:groups` role mapping, including the quoting of `role-claim-path` (medium confidence, see [option B](./option-b-in-function-oidc.md#roles-from-cognitogroups)).
- Option B only: a real Cognito token accepted through `quarkus-oidc` inside the Lambda extension, in `sam local` or a deployed stage. Without this test Option B is not confirmed (unverified).

## Mocking

Option B: `@TestSecurity` with `@OidcSecurity` (artifact `quarkus-test-security-oidc`) for claim and role cases, and `OidcWiremockTestResource` (artifact `quarkus-test-oidc-server`) for signed tokens. Both are documented in the [bearer guide](https://quarkus.io/version/3.40/guides/security-oidc-bearer-token-authentication) (read to 100,000 of 109,477 characters, L2).

```java
// Quarkus 3.40.1.1, quarkus-test-security-oidc
// @OidcSecurity(claims=...) / @Claim(key, value) attribute names: not quoted verbatim (medium confidence)
@QuarkusTest
class OrdersResourceTest {
    @Test
    @TestSecurity(user = "alice", roles = "tenant-user")
    @OidcSecurity(claims = { @Claim(key = "custom:tenantId", value = "A") })
    void crossTenantIsForbidden() {
        given().when().get("/tenants/B/orders").then().statusCode(403);
    }
}
```

Option A: the guide documents only `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` for `sam local`; never set it in a deployed configuration ([never-do N6](./never-do-patterns.md#n6-forced-user-name-outside-sam-local-high)). Whether the mock event server (dev 8080, test 8081; family fact) passes an authorizer context, so that `enable-security` can be tested in `@QuarkusTest`, is (unverified). A unit test of the tenant check can call the resource method with a constructed `APIGatewayV2HTTPEvent`. The family facts state that `quarkus-test-amazon-lambda` and `LambdaClient` were removed in Quarkus 3.31: test with `quarkus-junit` and RestAssured against the mock event server ([migration guide 3.31](https://github.com/quarkusio/quarkus/wiki/Migration-Guide-3.31)).

## Production readiness checklist

- [ ] One validation layer chosen deliberately (Ask First K1); every route has an authorizer (Option A) or `quarkus-oidc` (Option B).
- [ ] Issuer exact ([N4](./never-do-patterns.md#n4-issuer-verification-disabled-high)); `token_use` and `client_id` or `aud` checked.
- [ ] Roles from `cognito:groups`; scopes as `@PermissionsAllowed`.
- [ ] Tenant from a verified claim, compared with any path tenant; tenant attribute not in any `WriteAttributes`.
- [ ] `QUARKUS_AWS_LAMBDA_FORCE_USER_NAME` absent from deployed configs.
- [ ] Access-token lifetime chosen against the revocation requirement ([K5](./ask-first-decisions.md#k5-revocation-and-token-lifetime)); refresh token rotation enabled ("As a security best practice").
- [ ] Cognito "might rotate signing keys": keys from discovery or `jwks.json`, never pinned.
- [ ] Logs carry `requestId` and the claim tenant, no tokens, no PII.
