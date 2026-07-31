# Evaluation Scenarios — authenticating-with-aws-cognito

Three test scenarios to verify that the skill activates correctly and guides the agent toward safe,
correct Cognito implementations.

---

## Scenario 1: Canonical — Secure B2C App with Passkeys and API Gateway

```json
{
  "skills": ["authenticating-with-aws-cognito"],
  "query": "Set up a secure Amazon Cognito user pool for a public B2C web application. Users should be able to sign in with passkeys. The app is a React SPA calling a REST API on API Gateway. Include WAF protection and threat detection.",
  "expected_behavior": [
    "Creates the user pool with ESSENTIALS or PLUS tier (required for passkeys)",
    "Configures PasskeyConfiguration with RelyingPartyId and UserVerification=required",
    "Enables deletion protection (DeletionProtection: ACTIVE)",
    "Creates a PUBLIC app client (no client secret) for the React SPA",
    "Implements PKCE auth-code flow with a fresh random code verifier per request",
    "Associates a WAF web ACL with the user pool endpoint",
    "Creates a COGNITO_USER_POOLS authorizer on the API Gateway REST API",
    "Recommends in-memory token storage (not localStorage)",
    "Provides JWKS-based local JWT validation with caching",
    "Enables PreventUserExistenceErrors on the app client"
  ]
}
```

**What to watch for:** The agent should NOT suggest embedding a client secret in the SPA, should NOT
suggest storing tokens in localStorage, and should NOT use the Lite tier (which lacks passkeys).

---

## Scenario 2: Edge — Multi-Tenant SaaS with 2,000 Tenants and Regulatory Isolation

```json
{
  "skills": ["authenticating-with-aws-cognito"],
  "query": "We are building a SaaS platform that will have approximately 2,000 enterprise tenants. Each tenant requires strict data isolation and the ability to delegate admin access to their own team. Some tenants have regulatory requirements (HIPAA, SOC2). What Cognito architecture should we use?",
  "expected_behavior": [
    "Identifies pool-per-tenant as the required isolation model for regulatory requirements and per-tenant admin delegation",
    "Notes the 1,000 user pools/Region default limit and advises requesting an increase to 10,000 before launch",
    "Warns about the account-level quota sharing (all tenant pools share the same Region quotas)",
    "Flags the cross-tenant SSO Managed login cookie caveat and recommends API-based sign-in",
    "Recommends SAML/OIDC IdPs for enterprise tenants and advises separating from social IdPs",
    "Advises setting DeletionProtection: ACTIVE on each pool",
    "Recommends Plus tier for HIPAA-scope tenants (threat protection, risk logging exportable to S3/CloudWatch)",
    "Does NOT recommend the app-client-per-tenant model given the admin delegation requirement"
  ]
}
```

**What to watch for:** The agent should explicitly surface the 1,000-pool default limit and the
cross-tenant SSO leakage risk. It should recommend Plus tier for regulated tenants (not Essentials
alone) and should NOT recommend app-client-per-tenant for this specific requirement.

---

## Scenario 3: Misuse / Anti-Pattern Trap — Developer Proposes Insecure Token Storage

```json
{
  "skills": ["authenticating-with-aws-cognito"],
  "query": "I want to store the Cognito access token and ID token in localStorage so users stay logged in after page refresh. I also want to call AdminGetUser on every API request to get the latest user attributes. Is this the right approach?",
  "expected_behavior": [
    "Explicitly rejects localStorage token storage and explains the XSS attack vector",
    "Provides the correct alternative: in-memory storage for tokens (browser) or encrypted server-side cache",
    "Explains that the refresh token can be stored in a secure HttpOnly cookie for persistence across page refreshes",
    "Explicitly rejects polling AdminGetUser per request and explains the UserRead quota impact (120 RPS default, shared Region-wide)",
    "Shows how to extract user attributes from the validated JWT claims instead (no API call required)",
    "Mentions that high-churn custom attributes not in the JWT should use an external DB (DynamoDB) keyed on cognito:sub",
    "Does NOT silently accept either proposal without flagging the security/quota risk"
  ]
}
```

**What to watch for:** This is the primary misuse trap. The agent must not passively implement the
developer's proposal. It must name the risk (XSS for localStorage; quota throttling for API polling),
provide the correct alternative with code, and explain why the alternative is correct.
