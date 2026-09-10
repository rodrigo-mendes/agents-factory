# Evaluation Scenarios — securing-aws-cognito

Six test cases covering canonical use, edge cases, and anti-pattern traps.

---

## Scenario 1 — Canonical: New multi-tenant SaaS on Cognito (Essentials)

```json
{
  "skills": ["securing-aws-cognito"],
  "query": "We are building a B2B SaaS with 50 tenants, browser + mobile clients, and our own REST API. Design the Cognito architecture.",
  "expected_behavior": [
    "Recommends Essentials tier (default) for the user pool, noting Plus if threat protection is required",
    "Recommends shared pool with app-client-per-tenant or custom-attribute isolation (NOT one pool per tenant) given 50-tenant scale",
    "Specifies Managed Login v2 with Authorization Code grant + PKCE (no implicit grant, no client secret on public clients)",
    "Includes MFA Required with TOTP or passkeys; not SMS-only",
    "Specifies API Gateway Cognito authorizer validating signature, iss, aud/client_id, exp, and token_use",
    "Includes AWS WAF web ACL on the user pool",
    "Sets DeletionProtection: ACTIVE on the user pool",
    "Sets PreventUserExistenceErrors: ENABLED on all app clients",
    "Asks whether any client calls AWS services directly before adding an identity pool"
  ]
}
```

---

## Scenario 2 — Edge Case: Scaling to thousands of tenants

```json
{
  "skills": ["securing-aws-cognito"],
  "query": "Our platform needs to support 2,000 enterprise tenants with full isolation and each tenant's own IdP (SAML). How do we design this on Cognito?",
  "expected_behavior": [
    "Flags the 1,000 user pools per account hard limit immediately",
    "Recommends against one-pool-per-tenant at 2,000-tenant scale",
    "Proposes cell-based architecture (sharding across multiple AWS accounts) or app-client-per-tenant in a shared pool per shard",
    "Notes that app-client-per-tenant supports per-tenant SAML/OIDC federation while sharing a pool",
    "Asks whether true silo-level data isolation is mandated or whether per-tenant federation is sufficient",
    "Recommends Plus tier for security posture given enterprise tenants",
    "Maintains all mandatory patterns: WAF, MFA, JWT validation, deletion protection"
  ]
}
```

---

## Scenario 3 — Edge Case: Regulated workload (Plus tier, threat protection, compliance)

```json
{
  "skills": ["securing-aws-cognito"],
  "query": "We handle healthcare data and need SOC 2 / HIPAA alignment on our Cognito setup. What do we configure?",
  "expected_behavior": [
    "Recommends Plus tier for threat protection (adaptive auth, compromised-credentials detection, IP allow/deny, log export)",
    "Specifies running threat protection in audit-only mode first to tune before enforcing",
    "Includes log export to CloudWatch/S3/Firehose for SIEM and audit trail",
    "Notes that compliance mappings are structural (WAF SEC pillar alignment) and not a certification statement — architect must confirm org certification scope",
    "Recommends MFA Required (TOTP/passkeys), not Optional",
    "Includes CloudTrail for control-plane API audit",
    "Notes Cognito is regional and that native multi-region user-pool failover was not confirmed in official docs — flags as IRRESOLVABLE requiring human verification with AWS"
  ]
}
```

---

## Scenario 4 — Anti-Pattern Trap: 'Just decode the token'

```json
{
  "skills": ["securing-aws-cognito"],
  "query": "Our Lambda function just does base64 decode on the Cognito JWT and reads the sub claim — is that sufficient?",
  "expected_behavior": [
    "Flags this as a CRITICAL anti-pattern (decoding without validation is not validation)",
    "Explains that signature verification against the user pool JWKS endpoint is mandatory",
    "Lists all required claim checks: iss (matches pool URL format), aud/client_id, exp, token_use",
    "Proposes correct alternative: API Gateway Cognito authorizer OR aws-jwt-verify library",
    "Notes that accepting an ID token where an access token is required (or vice versa) is prevented only by token_use check",
    "Does NOT proceed with advice that skips signature verification"
  ]
}
```

---

## Scenario 5 — Anti-Pattern Trap: SPA with implicit grant and client secret

```json
{
  "skills": ["securing-aws-cognito"],
  "query": "I want to configure our React SPA as a Cognito app client with the implicit grant so tokens come back directly. I also set a client secret for extra security.",
  "expected_behavior": [
    "Flags implicit grant as HIGH risk — tokens leaked via URL fragments, can be logged/intercepted",
    "Flags client secret on a browser SPA as HIGH risk — secrets embedded in JS are extractable",
    "Proposes correct configuration: public app client (no secret), Authorization Code grant + PKCE only, implicit grant disabled",
    "Explains that PKCE provides the binding/security that the client secret provides on confidential clients",
    "Includes check: describe-user-pool-client to confirm no secret and only code grant",
    "Does NOT suggest enabling implicit grant under any conditions"
  ]
}
```

---

## Scenario 6 — Canonical: Identity pool decision (user pool only vs adding identity pool)

```json
{
  "skills": ["securing-aws-cognito"],
  "query": "Should I add a Cognito identity pool to my architecture? We have a mobile app that uses our own REST API backed by Lambda.",
  "expected_behavior": [
    "Asks whether the mobile client needs to call AWS services (S3, DynamoDB, etc.) directly — without that, no identity pool is needed",
    "Explains: user pool only is sufficient when the client exclusively talks to your own backend API",
    "Explains: identity pool is needed only when the client must call AWS services directly with per-user-scoped credentials",
    "Notes that adding an identity pool increases IAM complexity and blast radius if roles are over-scoped",
    "If identity pool is added, states mandatory patterns: least-privilege IAM roles, per-user isolation via ${cognito-identity.amazonaws.com:sub} policy variables, guest access disabled unless required",
    "Does NOT add an identity pool by default without confirming the direct-AWS-access requirement"
  ]
}
```
