# Multi-Tenant Isolation

Back to [SKILL.md](../SKILL.md). Quarkus 3.40.1.1. Fetched 2026-10-28. Family rule 6: the tenant comes from the token, never from the path alone. Violating it is a Never Do ([N1](./never-do-patterns.md#n1-tenant-from-the-path-header-or-body-alone-high), [N2](./never-do-patterns.md#n2-authorization-on-a-writable-custom-attribute-high), [N7](./never-do-patterns.md#n7-custom-attributes-expected-in-the-access-token-high)).

## Contents

- [The three rules](#the-three-rules)
- [Where the tenant claim lives](#where-the-tenant-claim-lives)
- [Check in the resource method](#check-in-the-resource-method)
- [Central check with an augmentor](#central-check-with-an-augmentor)
- [Tenant models](#tenant-models)
- [Observability](#observability)
- [Checklist](#checklist)

## The three rules

1. **N1.** Never trust a tenant taken from the path, a header or the body alone. Only claims of a verified token are trusted: "Don't trust the claims in an access token until you verify the signature."
2. **N2.** Never decide on a custom attribute that app clients can write. AWS: "In that case, remove the attribute from the `WriteAttributes` of every app client in your user pool."
3. **Rule 3.** Take the tenant from a verified claim in a token whose attribute users cannot write, and use that claim to scope every query.

## Where the tenant claim lives

| Token | Tenant claim | Source |
|---|---|---|
| ID token | `custom:tenantId`: "Amazon Cognito writes custom attribute values to the ID token as strings regardless of attribute type"; default token type of `custom:` attributes is "ID" | [ID token](https://docs.aws.amazon.com/cognito/latest/developerguide/amazon-cognito-user-pools-using-the-id-token.html), [pre token generation](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html) |
| Access token | Only with event version V2_0/V3_0 ("In user pools with the Essentials or Plus feature plan") | [pre token generation](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-lambda-pre-token-generation.html) |
| Pool per tenant | The signed `iss` identifies the pool | [multi-tenancy guide](https://quarkus.io/version/3.40/guides/security-openid-connect-multitenancy) |

An immutable custom attribute "can be updated once, during user creation". Set it from `AdminCreateUser` or an admin process. "A value that a user writes through one app client appears in the tokens that all app clients issue." Pool configuration: `provisioning-aws-cognito-v6`; architecture: `securing-aws-cognito`.

## Check in the resource method

Option A (HTTP API, claims from the injected event):

```java
// Quarkus 3.40.1.1; accessor chain from aws-lambda-java-events (unverified)
@GET
@Path("/tenants/{tenantId}/orders")
@Authenticated
public Response list(@PathParam("tenantId") String pathTenant, @Context APIGatewayV2HTTPEvent event) {
    Map<String, String> claims = event.getRequestContext().getAuthorizer().getJwt().getClaims();
    String tokenTenant = claims.get("custom:tenantId");
    if (tokenTenant == null || !tokenTenant.equals(pathTenant)) {
        return Response.status(Response.Status.FORBIDDEN).build();   // missing claim also refuses
    }
    return Response.ok(repo.findByTenant(tokenTenant)).build();      // scope by the claim, not the path
}
```

Option B reads the claim with `JsonWebToken.getClaim("custom:tenantId")` (signature in medium confidence, see [option B](./option-b-in-function-oidc.md#tenant-from-the-verified-token)). A missing claim is a refusal, never a fallback to the path.

## Central check with an augmentor

Repeating the check in every method is error-prone. The interface `io.quarkus.security.identity.SecurityIdentityAugmentor` with `public Uni<SecurityIdentity> augment(SecurityIdentity identity, AuthenticationRequestContext context)` is documented; the example uses `QuarkusSecurityIdentity.builder(identity).addPermission(...)`. An augmentor can turn the tenant claim into a permission such as `tenant:<id>`, which `@PermissionChecker` methods (`io.quarkus.security.PermissionChecker`, returning `boolean` or `Uni<Boolean>`) compare with the path parameter ([authorize web endpoints reference](https://quarkus.io/version/3.40/guides/security-authorize-web-endpoints-reference)).

- Whether augmentors run for identities built by `LambdaIdentityProvider` or `enable-security` is (unverified), and whether `QuarkusSecurityIdentity.Builder` has `addAttribute` (only `addPermission` was seen) is (unverified). Test it with a cross-tenant request before relying on it; until then keep the check in the resource method.

## Tenant models

Pooled (one pool, tenant claim), pool per tenant with Quarkus OIDC multi-tenancy, or pool per tenant behind a REST `COGNITO_USER_POOLS` authorizer (1,000-pool limit). The choice is [Ask First K3](./ask-first-decisions.md#k3-tenant-model). `quarkus.oidc.<tenant>.tenant-paths` only selects which issuer's keys check the token; it proves tenant membership only when each tenant has its own issuer.

## Observability

Log `requestId` and `tenantId` as JSON, with `tenantId` from the claim, never from the path; no tokens and no PII (family rule 7). Count 401 and 403 per route (engineering practice, no page: medium confidence). Keep metric dimensions bounded: no per-tenant dimension without an ADR.

## Checklist

- [ ] Tenant read from a verified claim; a missing claim refuses with 403.
- [ ] A path tenant, when present, must equal the claim.
- [ ] The tenant attribute is absent from `WriteAttributes` of every app client.
- [ ] Every repository call is scoped by the claim value.
- [ ] A cross-tenant test (tenant A calling `/tenants/B/...`) returns 403.
