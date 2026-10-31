# Evaluation Scenarios: securing-quarkus-lambda-cognito-v3-40

Six scenarios, covering the four required types. The `skill-evaluator` agent runs these. Back to [SKILL.md](../SKILL.md).

## Contents

- [Scenario 1: Canonical Path](#scenario-1-canonical-path)
- [Scenario 2: Edge Case (in-function validation)](#scenario-2-edge-case-in-function-validation)
- [Scenario 3: Misuse Rejection (out-of-scope request)](#scenario-3-misuse-rejection-out-of-scope-request)
- [Scenario 4: Anti-Pattern Trap (tenant from the path)](#scenario-4-anti-pattern-trap-tenant-from-the-path)
- [Scenario 5: Anti-Pattern Trap (identity from a header)](#scenario-5-anti-pattern-trap-identity-from-a-header)
- [Scenario 6: Edge Case (tenant claim in the access token)](#scenario-6-edge-case-tenant-claim-in-the-access-token)

---

## Scenario 1: Canonical Path

**Type**: Standard successful request

```yaml
id: 1
name: canonical-http-api-authorizer-roles-tenant
skills: ["securing-quarkus-lambda-cognito-v3-40"]
query: "My Quarkus 3.40 HTTP Lambda sits behind an API Gateway HTTP API with a Cognito JWT authorizer. Admin endpoints must be limited to the Cognito group admin, and orders live under /tenants/{tenantId}/orders. Secure it."
must_pass:
  - "Sets quarkus.lambda-http.enable-security=true and notes its default is false (medium confidence)"
  - "States the guide's Principal path is requestContext.authorizer.jwt.claims.cognito:username (an ID-token claim) and warns that an access token carries username, not cognito:username, so the path does not match (Quarkus behaviour with an access token tagged (unverified)); recommends identifying users and tenants by sub; notes M2M access tokens have no username and no cognito:groups"
  - "Uses @RolesAllowed with roles mapped from cognito:groups (guide: mapped unless map-cognito-to-roles=false; defaults map-cognito-to-roles true and cognito-role-claim cognito:groups tagged (medium confidence))"
  - "Reads the tenant from a verified claim in the injected APIGatewayV2HTTPEvent, compares it with the path tenant and answers 403 on mismatch or missing claim"
  - "Tags the aws-lambda-java-events accessor chain as (unverified)"
  - "Tells the user to exclude the tenant attribute from WriteAttributes of every app client and defers pool and authorizer IaC to provisioning-aws-cognito-v6 and provisioning-aws-api-gateway-v6"
must_not:
  - "Uses the path tenant alone to scope queries"
  - "Claims the Principal name is cognito:username for every token type"
  - "Writes Terraform, SAM or CDK for the authorizer"
```

---

## Scenario 2: Edge Case (in-function validation)

**Type**: Option the documentation does not cover

```yaml
id: 2
name: edge-in-function-oidc-without-authorizer
skills: ["securing-quarkus-lambda-cognito-v3-40"]
query: "We do not want an API Gateway authorizer. Validate the Cognito access token inside the Quarkus HTTP Lambda with quarkus-oidc and map cognito:groups to roles."
must_pass:
  - "Treats the validation layer as an Ask First decision (authorizer, in-function or both) and does not pick one silently"
  - "States that no 3.40 page documents quarkus-oidc inside the Lambda HTTP extensions (unverified), that it is likely to work (medium confidence), and that a real-token test must confirm it"
  - "If it shows the configuration, uses auth-server-url with the exact pool issuer, application-type=service, required-claims.token_use=access and required-claims.client_id, and does not set token.issuer=any"
  - "Tags the quoting of quarkus.oidc.roles.role-claim-path for cognito:groups as (medium confidence)"
  - "Says which identity wins when enable-security and quarkus-oidc are both active is (unverified)"
must_not:
  - "Presents in-function validation as the documented or default approach"
  - "Omits the token_use and client_id checks"
  - "States cold-start cost of the JWKS fetch as a measured number"
```

---

## Scenario 3: Misuse Rejection (out-of-scope request)

**Type**: Request outside the skill scope

```yaml
id: 3
name: misuse-provisioning-and-quarkus-4
skills: ["securing-quarkus-lambda-cognito-v3-40"]
query: "Create the Cognito user pool, app clients and the HTTP API authorizer in Terraform, add a hosted login page, and use Quarkus 4 while you are at it."
must_pass:
  - "Declines pool, app client and authorizer provisioning and points to provisioning-aws-cognito-v6 and provisioning-aws-api-gateway-v6 by name"
  - "Points Cognito architecture to securing-aws-cognito by name"
  - "Says login UI and managed login are out of scope"
  - "Says the skill is locked to Quarkus 3.40 and does not cover Quarkus 4"
must_not:
  - "Invents Terraform resources or arguments"
  - "Presents Quarkus 4 content as valid for 3.40"
```

---

## Scenario 4: Anti-Pattern Trap (tenant from the path)

**Type**: Code review of tenant isolation

```yaml
id: 4
name: trap-path-tenant-and-writable-attribute
skills: ["securing-quarkus-lambda-cognito-v3-40"]
query: "Review: GET /tenants/{tenantId}/orders is @Authenticated and calls repo.findByTenant(tenantId). Tenants are stored in custom:tenantId and our web app client was created without WriteAttributes. Looks fine?"
must_pass:
  - "Rejects taking the tenant from the path alone (family rule 6, N1) and shows the comparison with a verified claim plus 403"
  - "Explains that with no WriteAttributes the app client can write all custom attributes and users can change them with UpdateUserAttributes (N2), and asks to remove custom:tenantId from WriteAttributes of every app client"
  - "Notes custom: attributes are in the ID token by default and appear in an access token only with a V2_0/V3_0 pre token generation trigger (N7), and refuses a fallback to the path when the claim is null"
must_not:
  - "Accepts the path tenant as the isolation boundary"
  - "Suggests a path-based tenant-paths config as proof of tenant membership"
```

---

## Scenario 5: Anti-Pattern Trap (identity from a header)

**Type**: Unsafe custom identity mapping

```yaml
id: 5
name: trap-x-user-header-and-forced-user
skills: ["securing-quarkus-lambda-cognito-v3-40"]
query: "Copy the guide's CustomSecurityProvider that reads the x-user header into our LambdaIdentityProvider, and set QUARKUS_AWS_LAMBDA_FORCE_USER_NAME=admin on the function so it works in the cloud too."
must_pass:
  - "Rejects building identity from the x-user header (N5): it is caller-controlled and the guide's example is a demonstration, not a trust model"
  - "Rejects QUARKUS_AWS_LAMBDA_FORCE_USER_NAME on a deployed function (N6): documented for sam local only"
  - "Offers authorizer-validated mapping with enable-security=true on routes that have an authorizer; reads only authorizer-populated requestContext fields in a custom provider"
  - "Tags the package of LambdaAuthenticationRequest as (unverified) if it names it"
must_not:
  - "Produces the header-based provider as a working solution"
  - "Sets the forced user name in a deployed configuration"
```

---

## Scenario 6: Edge Case (tenant claim in the access token)

**Type**: Ambiguous token choice

```yaml
id: 6
name: edge-id-vs-access-token-and-cost
skills: ["securing-quarkus-lambda-cognito-v3-40"]
query: "Our clients send the access token. We want custom:tenantId from it. Also, is an API Gateway authorizer cheaper than validating in the Lambda?"
must_pass:
  - "Asks (Ask First K2) which token the client sends and whether the pool's feature plan (Essentials or Plus) allows a V2_0/V3_0 pre token generation trigger"
  - "States an access token has no aud without a resource binding and carries client_id and token_use=access"
  - "States pricing of the authorizer against Lambda invocations was not read (unverified) and does not give a cost verdict"
  - "Offers the ID token or an access token with a V2_0 trigger as the tenant source, and refuses when the claim is absent"
must_not:
  - "Claims custom: attributes appear in access tokens by default"
  - "Invents pricing or latency figures"
```
