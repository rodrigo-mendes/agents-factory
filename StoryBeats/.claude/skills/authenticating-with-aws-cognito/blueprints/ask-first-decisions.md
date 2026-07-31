# Ask First Decisions — Amazon Cognito (2025 feature-plan model)

Source: [research_aws-cognito_v1.md](../../../../StoryBeat/docs/research_aws-cognito_v1.md) — verified 2026-07-31

Before choosing any of the options below, ask the user to confirm the business context.
Do not assume the answer from technical context alone.

---

## Decision 1: Enable Self-Service Sign-Up?

**Why this is a decision point:** Enabling self-service sign-up allows anyone on the public internet
to create an account in the pool. This is correct for B2C apps and wrong for internal/enterprise apps.

| Context | Decision | Configuration |
|---|---|---|
| Public B2C app (anyone can register) | Enable | Default pool configuration |
| Internal/corporate app, admin-provisioned users | Disable | `AdminCreateUserConfig.AllowAdminCreateUserOnly = true` |
| B2B SaaS with tenant admin self-onboarding | Ask about tenant onboarding flow | Possibly a Lambda custom-auth + admin creation hybrid |

```bash
# ✅ Disable self-service sign-up (internal/enterprise pools)
aws cognito-idp update-user-pool \
  --user-pool-id <POOL_ID> \
  --admin-create-user-config '{"AllowAdminCreateUserOnly":true}'
```

Source: [User pools sign-up](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-user-identity-pools.html)

---

## Decision 2: Enable Identity-Pool Guest (Unauthenticated) Access?

**Why this is a decision point:** Unauthenticated access grants AWS credentials to any caller that
knows the identity pool ID (which is not secret). Every unauthenticated user gets the same IAM role.

| Context | Decision | Notes |
|---|---|---|
| Mobile app fetching public assets pre-login | Enable — with a strictly scoped unauthenticated role | Role must allow only the minimum required (e.g., read a specific public S3 prefix) |
| Web app, all resources require auth | Deactivate | Default; safer; no unauthenticated credentials issued |
| You are unsure | Deactivate | You can activate later; you cannot un-expose credentials already issued |

```bash
# ✅ Deactivate guest access (default-safe)
aws cognito-identity update-identity-pool \
  --identity-pool-id <POOL_ID> \
  --identity-pool-name <NAME> \
  --no-allow-unauthenticated-identities

# ✅ Enable with minimal unauthenticated role (if explicitly needed)
# The unauthenticated IAM role's policy must restrict to public-read resources only
```

Source: [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)

---

## Decision 3: Activate Social IdPs (Google, Facebook, Apple, Amazon)?

**Why this is a decision point:** Social IdPs allow public account creation with social credentials
beyond your control. They expand the attack surface and blur the trust boundary.

| Context | Decision | Notes |
|---|---|---|
| Public consumer app (B2C) | Enable for the required social providers | Keep social separate from enterprise IdPs — different trust level |
| Internal/corporate app | Disable all social IdPs | Use SAML/OIDC enterprise IdPs only |
| Multi-tenant SaaS with both enterprise and public tenants | Separate pools per trust tier | Enterprise tenants: SAML/OIDC only; public tenants: social allowed |

**Trade-off matrix:**

| Factor | Social IdPs enabled | Social IdPs disabled |
|---|---|---|
| Account creation control | Low — public accounts, hard to restrict | High — admin or SAML/OIDC only |
| User experience | Higher (fewer passwords) | Depends on enterprise SSO UX |
| Security posture | Lower for corporate data | Higher |
| Compliance (SOC2, ISO27001) | Requires additional controls | Easier to satisfy |

Source: [User pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/user-pool-security-best-practices.html)

---

## Decision 4: Enhanced vs Basic Identity-Pool Flow?

**Why this is a decision point:** The enhanced flow is simpler and more secure; the basic flow gives
the application client-side role-selection control at the cost of complexity and security surface.

| Flow | When to use | Trade-offs |
|---|---|---|
| **Enhanced** (`GetCredentialsForIdentity`) | Default for all new implementations | Simpler; scope-down policy on unauthenticated creds; AWS-recommended |
| **Basic/classic** (`GetOpenIdToken` → app calls `AssumeRoleWithWebIdentity`) | Only when custom role-selection logic is required client-side | Application is responsible for role selection; more complex; higher error surface |

```python
# ✅ Enhanced flow (recommended default)
response = client.get_credentials_for_identity(
    IdentityId=identity_id,
    Logins={'cognito-idp.us-east-1.amazonaws.com/<POOL_ID>': id_token}
)

# ⚠️ Basic flow — only use when custom role logic is required
oidc_token_resp = client.get_open_id_token(
    IdentityId=identity_id,
    Logins={'cognito-idp.us-east-1.amazonaws.com/<POOL_ID>': id_token}
)
# Application then calls sts.assume_role_with_web_identity with custom role selection
```

Source: [Identity pool security best practices](https://docs.aws.amazon.com/cognito/latest/developerguide/identity-pools-security-best-practices.html)

---

## Decision 5: Refresh-Token Lifetime?

**Why this is a decision point:** Longer lifetimes improve UX but increase the window of exposure if
a refresh token is stolen. The right value depends on the risk profile and session-revocation capability.

| User context | Suggested lifetime | Rationale |
|---|---|---|
| High-security (banking, healthcare) | 1–24 hours | Short-lived; pair with re-auth prompts |
| Standard enterprise app | 1–30 days | Balance UX and security |
| Consumer app (B2C) | 30–90 days | Better UX; acceptable for low-sensitivity data |
| CLI / automation (non-human) | Use client-credentials (M2M) — no refresh token | M2M tokens are short-lived and not user-bound |

**Required regardless of choice:**
```python
# ✅ Always revoke refresh token on sign-out
boto3.client('cognito-idp').revoke_token(
    Token=refresh_token,
    ClientId=CLIENT_ID
    # ClientSecret=... if confidential client
)
# Or global sign-out to revoke all sessions
boto3.client('cognito-idp').global_sign_out(AccessToken=access_token)
```

Configure via pool client:
```bash
aws cognito-idp update-user-pool-client \
  --user-pool-id <POOL_ID> \
  --client-id <CLIENT_ID> \
  --refresh-token-validity 30 \
  --token-validity-units '{"RefreshToken":"days"}'
```

Source: [Quotas — session validity parameters](https://docs.aws.amazon.com/cognito/latest/developerguide/quotas.html)
