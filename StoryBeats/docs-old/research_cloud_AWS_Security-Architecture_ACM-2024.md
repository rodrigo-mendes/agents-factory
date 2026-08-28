# AWS ACM — Security Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS ACM — Security Architecture (Certificate Management)"
Cloud_Provider: "AWS"
Architecture_Domain: "Security Architecture"
Target_Edition: "AWS ACM 2024"
Architecture_Context: "Applications requiring SSL/TLS certificate provisioning, lifecycle management, and automated renewal for securing data in transit — covering public certificates, private PKI via AWS Private CA, certificate deployment to integrated AWS services, DNS/email validation, and certificate transparency logging"
Official_Source_URL: "https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to ACM feature updates, new integrated services, and certificate policy changes"
```

---

## Executive Summary

AWS Certificate Manager (ACM) is the fully managed service that handles the complexity of creating, storing, and renewing public and private SSL/TLS X.509 certificates and keys that protect AWS websites and applications. ACM eliminates the traditional operational burden of manual certificate lifecycle management — purchasing, deploying, renewing, and revoking certificates — by providing automated provisioning and renewal for certificates deployed on integrated AWS services (Elastic Load Balancing, Amazon CloudFront, Amazon API Gateway, AWS App Runner, AWS Network Firewall, Amazon EKS via ACK, and others). Public certificates issued by ACM are free of charge; you pay only for the AWS resources to which they are attached. ACM integrates with AWS Private Certificate Authority (AWS Private CA) for organizations requiring private PKI hierarchies with custom trust chains.

The 2024 edition's most architecturally significant changes include: (1) **certificate validity reduced to 198 days** (from the previous 395 days), aligning with industry-wide movement toward shorter certificate lifetimes and emphasizing the importance of automated renewal; (2) **removal of TLS Web Client Authentication (clientAuth) EKU** from public certificates effective June 11, 2025, aligning with new browser requirements for website certificates; (3) **ECDSA key algorithm support** — ACM now supports 256-bit ECDSA (EC_prime256v1) and 384-bit ECDSA (EC_secp384r1) in addition to RSA 2048, enabling smaller key sizes with equivalent or better security; (4) **exportable public certificates** for use on EC2 instances and non-integrated environments; (5) **HTTP validation for CloudFront** — certificates provisioned through CloudFront integration use HTTP-based domain ownership validation automatically. These changes position ACM as the central certificate management plane for all AWS workloads, demanding that architects design for automated renewal and avoid manual certificate lifecycle processes.

The three most critical architecture guardrails for ACM are: (1) **always use DNS validation over email validation** — DNS validation enables fully automated renewal without human intervention and works across all certificate types including wildcards; (2) **never pin ACM-issued certificates** — ACM generates new key pairs on renewal, and pinning causes connection failures when certificates rotate; (3) **deploy certificates in the correct region** — ACM certificates are regional resources, and CloudFront specifically requires certificates in us-east-1 (N. Virginia), while all other services require the certificate in the same region as the resource.

---

## Cloud Architecture Glossary

```
Term: ACM Certificate
Definition: An X.509 version 3 digital certificate issued by AWS Certificate Manager, valid for 198 days, containing extensions for Basic Constraints, Authority Key Identifier, Subject Key Identifier, Key Usage (Digital Signature, Key Encipherment), and Extended Key Usage (TLS Web Server Authentication). The private key is encrypted with an AWS KMS key managed by ACM.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html#concept-acm-cert
Architect Usage: ACM certificates can only be used with integrated AWS services (ELB, CloudFront, API Gateway, etc.) or exported (public certificates only). They cannot be installed directly on EC2 instances without Nitro Enclaves. Design TLS termination at load balancers or CDN edge, not at compute instances.
Common Confusion: ACM certificates are NOT the same as certificates from AWS Private CA issued via the IssueCertificate API. ACM-managed certificates (requested through ACM) get automatic renewal. Private CA certificates issued directly via the Private CA API do NOT.

Term: DNS Validation
Definition: A domain ownership verification method where ACM provides a CNAME record (unique name-value pair) that must be added to the domain's DNS database. The CNAME record serves as proof of domain control and enables automatic certificate renewal indefinitely as long as the record remains in place.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html
Architect Usage: Always prefer DNS validation for production. One CNAME record per domain enables unlimited certificate re-issuance and automatic renewal. For Route 53 hosted zones, ACM can create the record automatically. For external DNS providers, export the CNAME and add manually. CNAME token is region-agnostic — same CNAME works for certificates in any AWS region.
Common Confusion: The CNAME record for ACM validation is NOT a standard CNAME pointing to your service. It has an underscore-prefixed name (e.g., _a79865eb4cd1a6ab990a45779b4e0b96.example.com) pointing to an acm-validations.aws domain. DNS providers may handle the name field differently — some append the domain automatically.

Term: Managed Renewal
Definition: The automatic process by which ACM renews Amazon-issued certificates before expiration (starting 45 days before expiry for public certificates). For DNS-validated certificates, renewal is fully automatic. For email-validated certificates, ACM sends renewal notices requiring human action. The certificate ARN remains unchanged after renewal.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html
Architect Usage: A certificate is eligible for managed renewal if it is: (a) associated with an integrated AWS service, OR (b) has been exported since issuance. Imported certificates are NEVER eligible for managed renewal. Private certificates issued via Private CA IssueCertificate API are NOT eligible. Design alerting for certificates nearing expiry that haven't been renewed (CertificateApproachingExpiration metric).
Common Confusion: Managed renewal generates a NEW key pair and certificate body while preserving the same certificate ARN. This is why certificate pinning breaks on renewal. The old key material is not reused.

Term: Imported Certificate
Definition: A third-party certificate (purchased from an external CA or self-signed) imported into ACM for use with integrated services. Imported certificates are NOT eligible for managed renewal — the operator must manually reimport before expiry. ACM does not manage the private key lifecycle for imported certificates.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/import-certificate.html
Architect Usage: Use imported certificates only when: (a) you need Extended Validation (EV) or Organization Validation (OV) certificates (ACM only issues Domain Validation), (b) you need a specific CA's trust chain, or (c) regulatory requirements mandate a particular issuer. Set CloudWatch alarms for DaysToExpiry to prevent expiration of imported certificates. Maximum 2,500 imported certificates per account/region.
Common Confusion: Importing a certificate does NOT change the certificate's expiration date or CA. ACM simply stores and deploys it. You remain responsible for renewal with the original CA and reimporting the renewed certificate.

Term: Certificate Transparency Logging
Definition: The automatic recording of public ACM certificates in publicly accessible certificate transparency (CT) logs before issuance. The Amazon CA submits certificates to at least three CT log servers, which return Signed Certificate Timestamps (SCTs) embedded in the certificate. Required by Google Chrome since April 2018.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html#concept-transparency
Architect Usage: CT logging is automatic and required for browser trust. Opt out only for internal domain names where exposing hostnames creates security risk (e.g., internal.corp.example.com reveals infrastructure naming). Once a certificate is logged, it cannot be removed from CT logs. Opt-out must be specified at request time or before the renewal period (45 days before expiry).
Common Confusion: Opting out of CT logging does NOT prevent the certificate from being discoverable — any client accessing the endpoint can observe the certificate. It only prevents the CA from proactively publishing it to CT log servers. Some browsers may show warnings for certificates without SCTs.

Term: Wildcard Certificate
Definition: A certificate issued for a domain pattern with an asterisk prefix (e.g., *.example.com) that secures any single-level subdomain (www.example.com, api.example.com, etc.) but NOT the apex domain itself (example.com) and NOT multi-level subdomains (sub.api.example.com). The DNS validation CNAME for *.example.com is identical to that of example.com.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html
Architect Usage: Use wildcard certificates to reduce certificate management overhead for services sharing a domain. Include both *.example.com and example.com as Subject Alternative Names (SANs) if both patterns are needed. Maximum 10 domain names per certificate by default (up to 100 with quota increase). Wildcards only match one subdomain level.
Common Confusion: *.example.com does NOT cover example.com (the apex). You need both in the same certificate. Also, *.example.com does NOT cover *.sub.example.com — each wildcard level requires its own certificate or explicit SAN entry.

Term: Private Certificate Authority (AWS Private CA)
Definition: A separate AWS service (not ACM itself) that enables creation of private CA hierarchies for issuing private certificates within an organization. ACM integrates with Private CA to request and manage private certificates that benefit from ACM's lifecycle management, deployment to integrated services, and managed renewal.
Provider Docs Section: https://docs.aws.amazon.com/privateca/latest/userguide/PcaWelcome.html
Architect Usage: Use Private CA when: (a) you need certificates for internal services not exposed to the internet, (b) you need mTLS (mutual TLS) client certificates, (c) you need custom certificate extensions, or (d) compliance requires your own CA hierarchy. Deploy root CA and intermediate CAs in separate AWS accounts for security isolation. Private CA has separate pricing ($400/month per CA + per-certificate fees).
Common Confusion: AWS Private CA is a SEPARATE service from ACM with separate pricing. ACM is free for public certificates. Certificates requested through ACM (using Private CA as issuer) get managed renewal. Certificates issued directly through the Private CA IssueCertificate API do NOT get ACM managed renewal.

Term: Subject Alternative Name (SAN)
Definition: An X.509 certificate extension that allows a single certificate to protect multiple domain names. ACM certificates include the primary domain as the Common Name (CN) and all requested domains (including the primary) in the SAN extension. Default limit is 10 SANs per certificate.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html
Architect Usage: Consolidate related domains into a single certificate using SANs (e.g., example.com + www.example.com + api.example.com). Each additional SAN requires separate domain validation. Cannot add or remove SANs from an existing certificate — must request a new certificate. SAN limit is adjustable to 100 via Service Quotas.
Common Confusion: You cannot modify the domain names on an existing certificate. Adding a domain requires requesting an entirely new certificate with all desired domains, revalidating each domain, and redeploying.

Term: Key Algorithm
Definition: The cryptographic algorithm used to generate the certificate's public-private key pair. ACM public certificates support RSA_2048, EC_prime256v1 (ECDSA P-256), and EC_secp384r1 (ECDSA P-384). The default is RSA_2048.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html
Architect Usage: ECDSA provides equivalent security with smaller key sizes (256-bit ECDSA ≈ 3072-bit RSA), resulting in faster TLS handshakes and reduced bandwidth. Use ECDSA for high-traffic endpoints. However, verify client compatibility — very old clients may not support ECDSA. CloudFront and ALB support all three algorithms.
Common Confusion: The key algorithm is chosen at certificate REQUEST time and cannot be changed. To switch from RSA to ECDSA, you must request a new certificate. ACM Root CAs include both RSA (Amazon Root CA 1, CA 2) and ECDSA (Amazon Root CA 3, CA 4) roots.

Term: Certificate Eligibility for Renewal
Definition: The set of conditions that must be met for ACM to attempt managed renewal: the certificate must be (a) Amazon-issued (not imported), (b) associated with at least one integrated AWS service OR exported, (c) not expired, and (d) domain validation must be verifiable (DNS CNAME still in place, or email validation responded to).
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html
Architect Usage: Design monitoring for the RENEWAL_ELIGIBILITY status via DescribeCertificate API or the acm:CertificateApproachingExpiration CloudWatch metric. Certificates that are not associated with any AWS resource AND have not been exported will NOT be renewed. Remove unused certificates proactively to stay within quotas.
Common Confusion: A certificate must be IN USE (associated with a service) or exported to be eligible for renewal. An ACM certificate sitting idle with no associations will NOT be renewed and will eventually expire.

Term: Regional Resource
Definition: ACM certificates are scoped to a specific AWS region. A certificate in us-east-1 cannot be used by an ALB in eu-west-1. Each region maintains its own certificate inventory, quotas, and validation state independently.
Provider Docs Section: https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html
Architect Usage: For multi-region deployments, request or import certificates in EACH region where they are needed. CloudFront is the exception — it ONLY uses certificates from us-east-1 (globally distributed to edge locations). DNS validation CNAMEs are region-agnostic, so the same CNAME validates certificates in any region. Plan certificate provisioning as part of regional deployment automation.
Common Confusion: You cannot copy or transfer a certificate between regions. You must request a new certificate in the target region. However, because DNS validation tokens are account-scoped (not region-scoped), the same CNAME record validates the domain for certificates in ALL regions.
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**DNS Validation for All ACM Certificates**
- Pillar Alignment: Operational Excellence — Perform operations as code; Security — Automate security best practices
- Why: DNS validation enables fully automated certificate renewal without human intervention. Email validation requires manual action on each renewal cycle (every 198 days), creating operational risk of certificate expiration. DNS validation CNAMEs are permanent and region-agnostic.
- AWS Services: ACM, Amazon Route 53 (for automated CNAME creation)
- Architecture Decision:
  Request all certificates with `--validation-method DNS`. For Route 53 hosted zones, use the ACM console "Create records in Route 53" feature or automate via CloudFormation/Terraform `aws_acm_certificate_validation` resource. For external DNS, export CNAME records and add to DNS zone. One CNAME per unique FQDN covers all current and future certificates for that domain.
- Verification:
  ```bash
  aws acm describe-certificate --certificate-arn <arn> \
    --query 'Certificate.DomainValidationOptions[].ValidationMethod'
  # Expected: all entries show "DNS"
  ```
  Verify CNAME is resolvable: `dig _<token>.<domain> CNAME`
- Trade-offs: Requires write access to DNS zone. Organizations with restricted DNS change management may face initial friction. DNS propagation adds minutes to initial validation (not renewal).
- Source: https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html

---

**Certificate Renewal Monitoring**
- Pillar Alignment: Operational Excellence — Anticipate failure; Reliability — Monitor workload resources
- Why: Certificate expiration causes immediate service outage — TLS handshakes fail, browsers show security warnings, API clients reject connections. ACM attempts renewal 45 days before expiry, but failures (DNS CNAME removed, certificate not in use) go unnoticed without monitoring.
- AWS Services: ACM, Amazon CloudWatch, AWS Config, Amazon EventBridge
- Architecture Decision:
  Configure CloudWatch alarms on the `DaysToExpiry` metric (namespace: `AWS/CertificateManager`) with threshold ≤ 30 days for warning and ≤ 14 days for critical. Enable AWS Config rule `acm-certificate-expiration-check` with `daysToExpiration` parameter (recommended: 30). Set up EventBridge rules for ACM certificate state changes to trigger SNS notifications.
- Verification:
  ```bash
  aws cloudwatch describe-alarms --alarm-name-prefix "ACM-Expiry"
  aws configservice describe-config-rules \
    --config-rule-names acm-certificate-expiration-check
  ```
- Trade-offs: CloudWatch `DaysToExpiry` metric is published only for certificates in use. Unused certificates will not generate metric data, making them invisible to CloudWatch alarms. Use AWS Config for comprehensive coverage including unused certificates.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/check-certificate-renewal-status.html

---

**CloudTrail Logging for Certificate Operations**
- Pillar Alignment: Security — Enable traceability; Enable security event logging
- Why: ACM certificate operations (request, delete, import, export) are security-sensitive. Unauthorized certificate requests could indicate domain hijacking attempts. Certificate deletions can cause outages. CloudTrail provides audit trail for all ACM API calls.
- AWS Services: ACM, AWS CloudTrail, Amazon S3, Amazon CloudWatch Logs
- Architecture Decision:
  Ensure CloudTrail is enabled in all regions where ACM is used. Configure CloudTrail to log ACM management events (enabled by default in multi-region trails). Set up CloudWatch Logs metric filters for `RequestCertificate`, `DeleteCertificate`, `ImportCertificate`, and `ExportCertificate` events. Alert on unexpected certificate operations outside deployment pipelines.
- Verification:
  ```bash
  aws cloudtrail describe-trails --query 'trailList[?IsMultiRegionTrail==`true`].Name'
  aws cloudtrail lookup-events --lookup-attributes \
    AttributeKey=EventSource,AttributeValue=acm.amazonaws.com \
    --max-results 5
  ```
- Trade-offs: CloudTrail log volume increases slightly. No meaningful cost impact for typical ACM usage patterns (low API call volume).
- Source: https://docs.aws.amazon.com/acm/latest/userguide/cloudtrail.html

---

**TLS Termination at Managed Services**
- Pillar Alignment: Security — Protect data in transit (SEC09-BP01, SEC09-BP02)
- Why: ACM certificates can only be deployed on integrated AWS services, not directly on EC2 instances (except Nitro Enclaves). Terminating TLS at ALB/NLB/CloudFront offloads cryptographic operations, centralizes certificate management, and enables automated renewal without application redeployment.
- AWS Services: Elastic Load Balancing (ALB/NLB), Amazon CloudFront, Amazon API Gateway, AWS App Runner
- Architecture Decision:
  Terminate TLS at the outermost managed service (CloudFront for edge, ALB for regional). Use ACM-provisioned certificates. Backend connections between load balancer and compute can use separate certificates or plaintext within VPC (evaluate based on compliance requirements). For end-to-end encryption, use ACM on the load balancer AND backend certificates on instances.
- Verification:
  ```bash
  aws elbv2 describe-listeners --load-balancer-arn <arn> \
    --query 'Listeners[?Protocol==`HTTPS`].Certificates'
  aws cloudfront get-distribution --id <dist-id> \
    --query 'Distribution.DistributionConfig.ViewerCertificate'
  ```
- Trade-offs: TLS termination at load balancer means traffic between LB and backend may be unencrypted within VPC. For regulated workloads requiring encryption everywhere, re-encrypt using backend TLS (with separate certificates on instances or containers).
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_key_cert_mgmt.html

---

**Account-Level Certificate Separation**
- Pillar Alignment: Security — Apply security at all layers; Operate workloads with least privilege
- Why: Production certificates should be isolated from development/testing certificates to prevent accidental deletion, quota exhaustion, and unauthorized access. IAM policies can restrict certificate operations by account but not by individual certificate within an account without complex condition keys.
- AWS Services: ACM, AWS Organizations, AWS IAM
- Architecture Decision:
  Use separate AWS accounts for production and non-production certificates. Implement IAM policies restricting `kms:CreateGrant` for certificate signing using `kms:EncryptionContext` conditions to limit which roles can provision certificates. For Private CA, deploy root CA and intermediate CAs in dedicated security accounts separate from workload accounts. Share CAs cross-account via AWS RAM.
- Verification:
  ```bash
  aws acm list-certificates --query 'CertificateSummaryList[].DomainName'
  # Verify only production domains appear in production account
  ```
- Trade-offs: Multi-account strategy increases operational complexity. Use IaC (CloudFormation/Terraform) to manage certificates across accounts consistently. Certificate validation still works across accounts since DNS validation is domain-scoped, not account-scoped.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html

---

**CloudFront Certificates in us-east-1**
- Pillar Alignment: Reliability — Design for correct operation; Operational Excellence — Prepare for operational events
- Why: CloudFront distributions can ONLY use ACM certificates from the us-east-1 (N. Virginia) region. Certificates provisioned in any other region cannot be associated with CloudFront. This is a hard architectural constraint that must be planned upfront.
- AWS Services: ACM (us-east-1), Amazon CloudFront
- Architecture Decision:
  Always provision ACM certificates in us-east-1 when the certificate will be used with CloudFront. If the same domain is used for both CloudFront AND regional services (e.g., ALB in eu-west-1), request separate certificates in each region. Use DNS validation so the same CNAME record serves both certificates. In IaC templates, use a separate provider/region configuration for CloudFront certificates.
- Verification:
  ```bash
  aws acm list-certificates --region us-east-1 \
    --query 'CertificateSummaryList[?DomainName==`example.com`]'
  ```
- Trade-offs: Requires managing certificates in multiple regions for multi-service architectures. DNS validation eliminates redundant validation effort since CNAMEs are region-agnostic.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html

---

### ⚠️ Architectural Decisions

**Public ACM Certificate vs. Imported Certificate vs. Private CA Certificate**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | ACM Public Certificate | ACM (free) | Cost, automation, zero-ops renewal | No EV/OV validation, no client auth, no direct EC2 install | Standard DV certificates for public-facing services on integrated AWS resources |
  | Imported Certificate | ACM (import) | Flexibility — any CA, EV/OV support, any key type | No managed renewal, manual reimport required, operational burden | Regulatory requirement for specific CA, need EV/OV, legacy CA contracts |
  | Private CA Certificate (via ACM) | ACM + Private CA ($400/mo/CA) | Internal PKI, mTLS, custom extensions, managed renewal | Cost, complexity of CA hierarchy design | Internal services, service mesh mTLS, IoT device identity |
  | Private CA Certificate (direct) | AWS Private CA only | Full control, custom templates, Kubernetes cert-manager | No ACM managed renewal, manual lifecycle | Kubernetes pods, code signing, non-AWS workloads |

- Cost Profile: ACM public = free; Imported = free (ACM storage) + external CA cost; Private CA = $400/month/CA + $0.75/cert (first 1000/month, then declining)
- Lock-in Assessment: ACM public certificates have NO vendor lock-in — they are standard X.509 certs from Amazon Trust Services (publicly trusted). Switching away requires requesting certificates from a new CA. Private CA hierarchy is AWS-specific but certificates themselves are standard X.509.
- Architect Instruction: "Ask whether the certificate is for a public-facing service (use ACM public), internal service-to-service communication (use Private CA via ACM), or has regulatory CA requirements (use imported) before provisioning."
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html

---

**Key Algorithm Selection: RSA 2048 vs. ECDSA P-256 vs. ECDSA P-384**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | RSA_2048 (default) | ACM | Maximum client compatibility, universal support | Larger key size (256 bytes), slower handshake | Legacy client support required, broad compatibility critical |
  | EC_prime256v1 (ECDSA P-256) | ACM | Performance (smaller keys, faster TLS handshake), bandwidth | Some very old clients incompatible (< Android 4.0, < IE 7) | High-traffic modern APIs, mobile-first services, performance-sensitive |
  | EC_secp384r1 (ECDSA P-384) | ACM | Stronger security (equivalent to RSA 7680-bit) | Slightly slower than P-256, minimal client incompatibility | Highly sensitive workloads, government/defense, future-proofing |

- Cost Profile: All algorithms are free in ACM. ECDSA reduces bandwidth cost at scale due to smaller certificate size in TLS handshake.
- Lock-in Assessment: No lock-in — algorithm choice is certificate-level. Can switch by requesting a new certificate with different algorithm.
- Architect Instruction: "Ask about client compatibility requirements and traffic volume before selecting the key algorithm. Default to RSA_2048 if client landscape is unknown; prefer ECDSA P-256 for modern, high-traffic services."
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html

---

**Validation Method: DNS vs. Email vs. HTTP**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | DNS Validation | ACM + Route 53 (or external DNS) | Fully automated renewal, no human intervention, works for wildcards | Requires DNS zone write access, initial propagation delay | All production workloads — strongly preferred |
  | Email Validation | ACM | No DNS access required, works with any domain | Manual renewal action every 198 days, does NOT support automated renewal | Only when DNS zone is controlled by another team with no delegation path |
  | HTTP Validation | ACM + CloudFront (automatic) | Zero configuration — managed by CloudFront integration | Only available for CloudFront-provisioned certificates, not user-requestable | CloudFront distributions with custom domains (automatic) |

- Cost Profile: All validation methods are free. DNS validation has near-zero ongoing operational cost. Email validation has recurring human cost every renewal cycle.
- Lock-in Assessment: None. Validation method does not affect portability. However, email validation creates ongoing operational dependency.
- Architect Instruction: "Ask whether the team has DNS zone write access. If yes, always use DNS validation. If no, evaluate whether DNS delegation or a Route 53 subdomain is feasible before falling back to email validation."
- Source: https://docs.aws.amazon.com/acm/latest/userguide/domain-ownership-validation.html

---

**Single Multi-SAN Certificate vs. Multiple Individual Certificates**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Single certificate with multiple SANs | ACM (up to 100 SANs) | Management simplicity, single renewal, fewer resources | All domains on one cert — failure/revocation affects all, 10 SAN default limit | Related domains under same ownership, single application |
  | Individual certificates per domain | ACM (one cert per domain) | Isolation — failure/revocation is scoped, independent lifecycle | More certificates to manage, higher quota usage | Independent services, different teams own different domains |
  | Wildcard certificate (*.domain.com) | ACM (wildcard SAN) | Covers unlimited subdomains without cert changes | Does not cover apex, does not cover multi-level subdomains | Dynamic subdomains (multi-tenant SaaS), microservices under shared domain |

- Cost Profile: All free in ACM. Quota impact differs — multi-SAN uses 1 certificate slot, individual certs use N slots (limit: 2,500 per account/region).
- Lock-in Assessment: None. Purely operational design choice.
- Architect Instruction: "Ask about domain ownership boundaries and service isolation requirements. If domains belong to different teams or have different security postures, use separate certificates. If all domains serve a single application, consolidate into one multi-SAN cert."
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-limits.html

---

### 🚫 Anti-Patterns

**Certificate Pinning of ACM-Issued Certificates**
- Risk Level: CRITICAL
- Why: ACM generates a NEW public-private key pair on every managed renewal. Applications or clients that pin to a specific certificate or public key will fail to connect after renewal. This creates a ticking time bomb — working today, broken on next renewal (max 198 days away).
- Instead: Do NOT pin ACM certificates. If pinning is absolutely required: (a) import your own certificate into ACM (imported certs don't auto-renew, giving you control), OR (b) pin to Amazon Root CAs (https://www.amazontrust.com/repository/) which are stable.
- Detection:
  Review application code and mobile app configurations for certificate pinning logic. Search for `ssl_pinning`, `certificate_pinner`, `TrustManagerFactory` custom implementations. Check HTTP Public Key Pinning (HPKP) headers (deprecated but may exist in older systems).
- Impact: Service outage — all clients with pinned certificates lose connectivity on certificate renewal.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html

---

**Email Validation for Production Certificates**
- Risk Level: HIGH
- Why: Email-validated certificates require manual human action during each renewal cycle. ACM sends renewal notices to domain contacts (WHOIS) and five common admin addresses. If emails are missed, filtered, or the responsible person is unavailable, the certificate expires and causes outage. This directly violates the Operational Excellence pillar principle of performing operations as code.
- Instead: Use DNS validation for all production certificates. Migrate existing email-validated certificates by requesting new certificates with DNS validation and replacing them on the associated resources. Delete the email-validated certificates after replacement.
- Detection:
  ```bash
  aws acm list-certificates --query 'CertificateSummaryList[].CertificateArn' --output text | \
    xargs -I {} aws acm describe-certificate --certificate-arn {} \
    --query 'Certificate.{ARN:CertificateArn,Validation:DomainValidationOptions[0].ValidationMethod}' --output table
  # Flag any showing "EMAIL"
  ```
- Impact: Service outage — certificate expires, TLS termination fails, all HTTPS traffic drops.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html

---

**Deploying Certificates in Wrong Region**
- Risk Level: HIGH
- Why: ACM certificates are regional resources. A certificate in eu-west-1 cannot be used by an ALB in us-east-1 or by a CloudFront distribution (which exclusively requires us-east-1). Mismatched regions cause deployment failures with cryptic error messages.
- Instead: Request certificates in the same region as the consuming service. For CloudFront, always use us-east-1. For multi-region deployments, automate certificate provisioning in each target region using IaC. Leverage the region-agnostic nature of DNS validation CNAMEs to avoid redundant validation work.
- Detection:
  ```bash
  # Check if CloudFront certificates are in us-east-1
  aws cloudfront list-distributions --query 'DistributionList.Items[].ViewerCertificate.ACMCertificateArn' | \
    grep -v "us-east-1" && echo "ERROR: CloudFront cert not in us-east-1"
  ```
- Impact: Deployment failure — infrastructure provisioning fails, new services cannot launch, rollbacks required.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html

---

**Hardcoded or Self-Managed Certificate Lifecycle**
- Risk Level: HIGH
- Why: Manually managing certificates (purchasing, converting, installing, tracking expiry, renewing) introduces human error, creates operational toil, and historically accounts for a significant portion of production outages. Expired certificates are one of the most common causes of unplanned downtime.
- Instead: Use ACM-issued certificates with DNS validation for fully automated lifecycle. If custom certificates are required, import them into ACM and configure CloudWatch alarms on DaysToExpiry. Never store private key material in application code, environment variables, or configuration files.
- Detection:
  ```bash
  # Find imported certificates approaching expiry
  aws acm list-certificates --certificate-statuses ISSUED --query 'CertificateSummaryList[?Type==`IMPORTED`]'
  # Check for private keys in code repositories
  grep -r "BEGIN.*PRIVATE KEY" --include="*.pem" --include="*.key" --include="*.env"
  ```
- Impact: Service outage on certificate expiration; security breach if private keys are exposed.
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_key_cert_mgmt.html

---

**Exceeding Certificate Quotas via CloudFormation Automation**
- Risk Level: MEDIUM
- Why: CloudFormation templates that create ACM certificates for each deployment (e.g., per-environment certificates for ephemeral test environments) can rapidly exhaust the 2,500 certificate quota or the 5,000 certificates/year rate limit. Expired and revoked certificates still count toward the quota.
- Instead: Use wildcard certificates for test/staging environments (e.g., *.test.example.com). Reuse certificates across deployments. Delete unused certificates proactively. Monitor certificate count relative to quota.
- Detection:
  ```bash
  aws acm list-certificates --includes 'keyTypes=RSA_2048,EC_prime256v1,EC_secp384r1' \
    --query 'length(CertificateSummaryList)'
  # Compare against 2,500 quota
  ```
- Impact: Quota exhaustion — new certificate requests fail, blocking service deployments. Account-wide impact.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html

---

**Wildcard Principal in Certificate Resource Policies (Private CA)**
- Risk Level: CRITICAL
- Why: AWS Private CA resource-based policies with wildcard (`*`) principal allow any AWS account to issue certificates from your private CA. This enables unauthorized certificate issuance, potentially allowing attackers to impersonate internal services or establish trusted identities within your organization.
- Instead: Use explicit account IDs or AWS Organization ARNs in Private CA resource policies. Apply AWS RAM sharing with specific account targets. Restrict `IssueCertificate` and `GetCertificate` actions to known identities only.
- Detection:
  ```bash
  aws acm-pca list-certificate-authorities --query 'CertificateAuthorities[].Arn' --output text | \
    xargs -I {} aws acm-pca get-policy --resource-arn {} 2>/dev/null | grep -l '"Principal": "\*"'
  ```
- Impact: Security breach — unauthorized certificate issuance enables service impersonation, data interception via fake endpoints, and trust chain compromise.
- Source: https://docs.aws.amazon.com/privateca/latest/userguide/ca-best-practices.html

---

## Cloud-Native Design Patterns

**Automated Certificate Provisioning via Infrastructure as Code**
- Category: Operational Excellence
- Problem: Manual certificate provisioning creates deployment bottlenecks, inconsistency across environments, and risk of human error in domain validation and service association.
- Solution on AWS:
  Use CloudFormation `AWS::CertificateManager::Certificate` resource with `ValidationMethod: DNS` and `DomainValidationOptions` specifying Route 53 hosted zone IDs. Chain with `AWS::CertificateManager::CertificateValidation` (Terraform) or wait conditions to ensure certificate is issued before associating with ALB/CloudFront. For multi-region, use StackSets or separate stacks per region.
- Services Used: ACM, AWS CloudFormation, Amazon Route 53, AWS CloudFormation StackSets
- When to Apply: Every ACM certificate deployment — no exceptions for production environments.
- When NOT to Apply: One-time manual testing; quick prototyping where the domain isn't production.
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Operational | Repeatable, auditable, version-controlled | Initial template development time |
  | Reliability | Consistent provisioning, no manual errors | CloudFormation stack waits on validation (may time out if DNS not configured) |
  | Speed | Automated deployment pipeline | First deployment requires DNS CNAME to be in place |

- Complements: DNS Validation, CloudFront Distribution provisioning, ALB provisioning
- Source: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-certificatemanager-certificate.html

---

**Multi-Region Certificate Strategy**
- Category: Resilience
- Problem: In multi-region active-active or active-passive architectures, each regional resource (ALB, API Gateway) requires its own ACM certificate in the local region. Additionally, CloudFront requires certificates in us-east-1 exclusively.
- Solution on AWS:
  Request identical certificates (same domain names, same key algorithm) in each target region. Use DNS validation — the same CNAME record validates the domain across ALL regions simultaneously. Automate via CloudFormation StackSets or Terraform providers per region. For CloudFront + regional ALB patterns, maintain separate certificates: one in us-east-1 for CloudFront, one per region for ALBs.
- Services Used: ACM (multi-region), Route 53 (global DNS validation), CloudFormation StackSets
- When to Apply: Any multi-region deployment, DR configurations, global services
- When NOT to Apply: Single-region applications with no DR requirement
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Resilience | Regional independence — certificate issues in one region don't affect others | Multiple certificates to monitor |
  | Operations | DNS validation CNAME is shared — no redundant validation work | Must track renewal status per region |
  | Quotas | N/A | Consumes quota in each region separately (2,500 per region) |

- Complements: Route 53 health-based routing, Global Accelerator, multi-region ALB
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html

---

**Private mTLS with ACM + Private CA**
- Category: Security
- Problem: Service-to-service communication within a microservices architecture needs mutual authentication (mTLS) to prevent unauthorized services from accessing internal APIs. Public certificates only validate server identity, not client identity.
- Solution on AWS:
  Deploy AWS Private CA hierarchy (root CA in dedicated account, intermediate CA in workload account). Issue server certificates through ACM (for managed renewal on ALB/API Gateway) and client certificates through Private CA directly or via ACM export. Configure ALB or API Gateway with mutual TLS using a trust store containing your Private CA's root certificate. Distribute client certificates to services via Secrets Manager or Kubernetes secrets (for EKS with ACK integration).
- Services Used: AWS Private CA, ACM, API Gateway (mTLS), Application Load Balancer (mTLS), AWS Secrets Manager, Amazon EKS
- When to Apply: Zero-trust architectures, regulated workloads (PCI-DSS, HIPAA), service mesh authentication
- When NOT to Apply: Simple public-facing web applications; architectures where network segmentation (VPC isolation) provides sufficient trust
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Strong mutual authentication, defense against spoofed services | $400/month per CA, certificate distribution complexity |
  | Operations | ACM manages server cert lifecycle; client certs need rotation strategy | Private CA hierarchy design and maintenance |
  | Performance | Minimal TLS handshake overhead for mutual auth | Additional certificate verification on each connection |

- Complements: API Gateway custom authorizers, ALB authentication, VPC service endpoints
- Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_authentication.html

---

**Certificate Automation for EKS Workloads**
- Category: Scalability
- Problem: Kubernetes pods need TLS certificates for ingress controllers and inter-pod communication. Manual certificate management doesn't scale with dynamic pod creation/destruction in Kubernetes.
- Solution on AWS:
  Use AWS Controllers for Kubernetes (ACK) with the ACM controller to provision and manage certificates declaratively via Kubernetes CRDs. For ingress, ACM certificates are associated with AWS Load Balancer Controller-managed ALBs/NLBs. For pod-to-pod mTLS, use cert-manager with the aws-privateca-issuer plugin to issue short-lived certificates from Private CA. Certificates are automatically rotated via Kubernetes secrets.
- Services Used: Amazon EKS, ACM, AWS Private CA, AWS Load Balancer Controller, cert-manager
- When to Apply: EKS deployments with HTTPS ingress, service mesh requirements, or pod-level TLS
- When NOT to Apply: Simple EKS deployments where TLS terminates at the load balancer and internal traffic is within a trusted VPC
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Scalability | Automatic cert provisioning scales with pod count | Additional Kubernetes controllers to manage |
  | Security | Short-lived certificates reduce compromise window | Higher certificate issuance volume, Private CA cost |
  | Operations | Declarative cert management matches K8s patterns | Learning curve for ACK + cert-manager integration |

- Complements: AWS Load Balancer Controller, App Mesh, Private CA cross-account sharing
- Source: https://docs.aws.amazon.com/acm/latest/userguide/exportable-certificates-kubernetes.html

---

## Security Architecture

**Certificate Private Key Protection**
- AWS Services: ACM, AWS KMS, AWS Nitro System
- Architecture:
  ACM encrypts certificate private keys using an AWS KMS key that ACM manages (aws/acm CMK). The private key NEVER leaves the ACM service unencrypted — it is directly transmitted to integrated services (ELB, CloudFront) via internal AWS APIs secured by Nitro hardware. Human operators cannot retrieve the private key of an ACM-issued public certificate (non-exportable by default). Exportable certificates (opted in at request time) allow private key retrieval but require a passphrase and use TLS-encrypted transport.
- Configuration Essentials:
  - Do NOT create custom KMS key policies for the `aws/acm` service key
  - Restrict `acm:ExportCertificate` permission to authorized roles only
  - For Private CA-issued certificates, the private key CAN be exported — scope IAM permissions accordingly
  - Enable CloudTrail to audit any `ExportCertificate` API calls
- Verification:
  ```bash
  # Verify no unauthorized export permissions exist
  aws iam simulate-principal-policy --policy-source-arn <role-arn> \
    --action-names acm:ExportCertificate --output table
  ```
- Compliance Alignment: SEC09-BP01 (Implement secure key and certificate management), PCI-DSS Requirement 3 (Protect stored data), SOC2 CC6.1 (Logical access security)
- Source: https://docs.aws.amazon.com/acm/latest/userguide/data-protection.html

---

**IAM Access Control for Certificate Operations**
- AWS Services: ACM, AWS IAM, AWS Organizations (SCPs)
- Architecture:
  Implement least-privilege access for ACM operations. Separate permissions by role: developers can `acm:ListCertificates` and `acm:DescribeCertificate`; deployment pipelines can `acm:RequestCertificate` with conditions restricting domains; security teams have full access. Use Service Control Policies (SCPs) to prevent certificate operations in unauthorized accounts or regions. Apply `kms:CreateGrant` restrictions with `kms:EncryptionContext:aws:acm:arn` conditions for fine-grained control over which certificates can be created.
- Configuration Essentials:
  - Restrict `acm:RequestCertificate` with `StringLike` condition on `acm:DomainNames` to limit which domains can be certified
  - Deny `acm:DeleteCertificate` for production certificate ARNs from non-admin roles
  - Use `aws:RequestedRegion` condition to restrict certificate creation to approved regions
  - Apply SCPs preventing certificate operations outside designated security accounts
- Verification:
  ```bash
  aws iam get-policy-version --policy-arn <policy-arn> --version-id v1 \
    --query 'PolicyVersion.Document'
  # Review for overly permissive acm:* actions
  ```
- Compliance Alignment: SEC02-BP01 (Use strong sign-in mechanisms), PCI-DSS Requirement 7 (Restrict access), SOC2 CC6.3 (Role-based access)
- Source: https://docs.aws.amazon.com/acm/latest/userguide/security-iam.html

---

**Certificate Transparency and Domain Monitoring**
- AWS Services: ACM (CT logging), Amazon Route 53 (DNSSEC), Amazon CloudWatch
- Architecture:
  Certificate Transparency logging provides a public audit trail of all certificates issued for your domains. Monitor CT logs (via services like crt.sh or AWS-native EventBridge integration) to detect unauthorized certificate issuance by rogue CAs or compromised accounts. For private/internal domains, opt out of CT logging to prevent information leakage about internal infrastructure naming.
- Configuration Essentials:
  - Leave CT logging ENABLED (default) for all public-facing domains
  - Opt OUT only for internal hostnames that reveal infrastructure topology
  - Set up external monitoring of CT logs for your registered domains
  - Use CAA DNS records to restrict which CAs can issue certificates for your domain
- Verification:
  ```bash
  # Check CT logging preference for a certificate
  aws acm describe-certificate --certificate-arn <arn> \
    --query 'Certificate.Options.CertificateTransparencyLoggingPreference'
  # Expected: "ENABLED" for public-facing domains
  ```
- Compliance Alignment: SEC01-BP05 (Monitor threats and anomalies), NIST CSF DE.CM-8 (Vulnerability scans)
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html#concept-transparency

---

## Operational Patterns

**Certificate Lifecycle Monitoring and Alerting**
- RTO/RPO: RTO = minutes (replace certificate), RPO = N/A (certificates are metadata, no data loss)
- AWS Services: ACM, Amazon CloudWatch, Amazon EventBridge, Amazon SNS, AWS Config
- Architecture:
  Configure multi-layer monitoring: (1) CloudWatch metric `DaysToExpiry` with alarms at 30-day and 14-day thresholds; (2) AWS Config rule `acm-certificate-expiration-check`; (3) EventBridge rules for `ACM Certificate Approaching Expiration` events routing to SNS → PagerDuty/Slack. Supplement with weekly automated scans of all certificates via `acm:ListCertificates` + `acm:DescribeCertificate` to catch imported certificates without CloudWatch metrics.
- Cost Profile: Low — CloudWatch alarms ($0.10/alarm/month), Config rule ($0.001/evaluation), EventBridge rules (free for AWS events)
- Automation:
  Fully automated for DNS-validated ACM-issued certificates. For imported certificates, trigger Lambda function on DaysToExpiry ≤ 30 that creates a JIRA/ServiceNow ticket for certificate renewal. For email-validated certs, escalate to responsible team immediately.
- Runbook Skeleton:
  1. Alert triggers: Certificate DaysToExpiry ≤ 30
  2. Classify: ACM-issued (DNS validated) → likely auto-renews, verify RenewalStatus
  3. If RenewalStatus is PENDING_VALIDATION → check DNS CNAME exists, fix if missing
  4. If Imported → contact certificate owner, initiate renewal with external CA
  5. If ACM-issued but NOT IN USE → either associate with service or delete
  6. Verify renewal: `aws acm describe-certificate --query 'Certificate.RenewalSummary'`
- Source: https://docs.aws.amazon.com/acm/latest/userguide/check-certificate-renewal-status.html

---

**Certificate Rotation for Imported Certificates**
- RTO/RPO: RTO = minutes (reimport), RPO = N/A
- AWS Services: ACM (import), AWS Lambda, Amazon EventBridge, AWS Secrets Manager
- Architecture:
  For imported certificates, implement automated rotation pipeline: Lambda function triggered by EventBridge scheduled rule (monthly) or DaysToExpiry alarm checks certificate expiration, initiates renewal with external CA (via ACME protocol or CA API), imports renewed certificate into ACM using the SAME certificate ARN (reimport preserves associations). Store CA credentials in Secrets Manager. Test the new certificate via health check before cutting over.
- Cost Profile: Low — Lambda invocations ($0.20/million), Secrets Manager ($0.40/secret/month)
- Automation:
  ACME-based automation (Let's Encrypt, ZeroSSL) can fully automate imported cert rotation. For commercial CAs with APIs, implement custom Lambda. For CAs without APIs, create ServiceNow ticket and track manually.
- Runbook Skeleton:
  1. Renewal automation triggers 30 days before expiry
  2. Obtain new certificate from CA (ACME/API/manual)
  3. Reimport via `aws acm import-certificate --certificate-arn <existing-arn>` (preserves all service associations)
  4. Verify: `aws acm describe-certificate` shows new NotAfter date
  5. Confirm services are using new certificate (test TLS handshake)
  6. If reimport fails: investigate certificate chain (intermediate missing?)
- Source: https://docs.aws.amazon.com/acm/latest/userguide/import-reimport.html

---

**Disaster Recovery for Certificate Infrastructure**
- RTO/RPO: RTO = minutes-hours, RPO = near-zero (certificates can be re-requested)
- AWS Services: ACM, Route 53, AWS Private CA (cross-region replication)
- Architecture:
  ACM public certificates can be rapidly re-provisioned in any region because DNS validation CNAMEs are permanent and region-agnostic. DR strategy: (1) pre-provision certificates in DR region during normal operations; (2) if DR region certificates don't exist, request new ones — validation is instant if CNAME records are in place. For Private CA, configure cross-region CA replication for the issuing CA. Certificate ARNs change across regions, so DR automation (CloudFormation/Terraform) must reference region-specific ARN parameters.
- Cost Profile: Low — pre-provisioned certificates in DR region are free. Private CA replication adds $400/month per replicated CA.
- Automation:
  Include ACM certificates in IaC templates deployed to DR region. Use Route 53 for DNS validation to eliminate manual steps. For Private CA DR, use `aws acm-pca create-certificate-authority` in DR region with the same configuration, then issue new subordinate CA cert from root CA.
- Runbook Skeleton:
  1. DR region activation detected
  2. Verify certificates exist in DR region (pre-provisioned via IaC)
  3. If missing: run IaC deployment — ACM certificates issue instantly (DNS already validated)
  4. Update service configurations with DR-region certificate ARNs
  5. Validate TLS: `openssl s_client -connect <dr-endpoint>:443 -servername <domain>`
  6. Confirm certificate details match expected domain and expiry
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html

---

## Reference Architectures

**Public Web Application with ACM + CloudFront + ALB**
- Context: Standard three-tier web application with global CDN and regional compute
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge TLS | ACM (us-east-1) + CloudFront | CDN termination with ACM certificate, global edge distribution |
  | Regional TLS | ACM (local region) + ALB | Regional load balancer TLS termination for API traffic |
  | DNS | Route 53 | DNS validation CNAMEs + application A/ALIAS records |
  | Compute | ECS/EKS/EC2 | Application servers (HTTP from ALB, no TLS overhead) |

- Key Decisions:
  - Certificate in us-east-1 for CloudFront (mandatory)
  - Separate certificate in compute region for ALB (if ALB receives direct traffic)
  - Wildcard vs. explicit SANs depends on subdomain strategy
  - ECDSA for high-traffic CloudFront distributions (faster edge handshakes)
- Scaling Path:
  Multi-region: add certificates per region, Route 53 latency-based routing to regional ALBs. Certificate quotas scale linearly with number of unique domains (not traffic volume).
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-services.html

---

**Internal Microservices with mTLS via Private CA**
- Context: Service mesh or zero-trust microservices architecture requiring mutual authentication
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | CA Hierarchy | AWS Private CA (root + intermediate) | Trust anchor for all internal certificates |
  | Server Certs | ACM (via Private CA) | Managed server certificates on internal ALBs |
  | Client Certs | Private CA (direct issuance) | Short-lived client certificates for service identity |
  | Trust Store | ALB/API Gateway mTLS configuration | Validates client certificate against Private CA root |
  | Distribution | Secrets Manager / K8s Secrets | Distributes client certificates to services |
  | Monitoring | CloudWatch + CloudTrail | Tracks issuance, renewal, and revocation |

- Key Decisions:
  - CA hierarchy depth: root CA (offline) → intermediate CA (online, issues certs)
  - Certificate lifetime for client certs: short (hours/days) vs. long (months)
  - Certificate revocation: CRL in S3 vs. OCSP (Private CA supports both)
  - Cross-account CA sharing via AWS RAM for multi-account architectures
- Scaling Path:
  Scale issuing CAs horizontally (one per workload account or per region). Private CA supports 1,000,000 certificates per CA lifetime. For very high issuance rates, use multiple intermediate CAs.
- Source: https://docs.aws.amazon.com/privateca/latest/userguide/PcaPlanning.html

---

**Multi-Account Landing Zone Certificate Strategy**
- Context: Enterprise AWS Organization with multiple accounts (prod, staging, dev, shared services)
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Security Account | AWS Private CA (root + intermediate) | Central PKI hierarchy, shared via RAM |
  | Shared Services Account | Route 53 hosted zones | Central DNS management, validation CNAMEs |
  | Workload Accounts | ACM (per-account) | Certificate provisioning and association |
  | Governance | AWS Config + SCPs | Certificate compliance monitoring and policy enforcement |
  | Alerting | CloudWatch + EventBridge | Cross-account certificate expiry alerting |

- Key Decisions:
  - DNS validation works cross-account (CNAME is domain-scoped, not account-scoped)
  - Private CA shared via AWS RAM to workload accounts
  - SCPs restrict `acm:RequestCertificate` to approved domains per account OU
  - Centralized monitoring via Config aggregator across all accounts
- Scaling Path:
  Each account has independent 2,500 certificate quota. Organizational SCPs prevent quota abuse. Wildcard certificates in shared services account cover multi-tenant subdomains. New accounts inherit certificate automation from IaC baseline (Control Tower customizations or AFT).
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html

---

## Service Equivalence Map

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **Public Certificate Manager** | ACM (free) | Certificate Manager (managed SSL) | App Service Certificates / Key Vault Certificates | OCI Certificates |
| **Private CA** | AWS Private CA | Certificate Authority Service (CAS) | Azure Key Vault (CA integration) | OCI Certificates (Private CA) |
| **Certificate Deployment — LB** | ACM → ALB/NLB | Managed SSL → Cloud Load Balancing | Key Vault → App Gateway/Front Door | OCI Certificates → Load Balancer |
| **Certificate Deployment — CDN** | ACM (us-east-1) → CloudFront | Managed SSL → Cloud CDN | Azure CDN / Front Door (managed certs) | OCI CDN |
| **Certificate Deployment — API GW** | ACM → API Gateway | Managed SSL → API Gateway/Apigee | Key Vault → API Management | OCI Certificates → API Gateway |
| **DNS Validation** | Route 53 integration (one-click) | Cloud DNS + DNS Authorization | Azure DNS + Custom Domain Verification | OCI DNS |
| **Key Management** | AWS KMS (encrypts private keys) | Cloud KMS | Azure Key Vault | OCI Vault |
| **Monitoring** | CloudWatch DaysToExpiry | Cloud Monitoring | Azure Monitor / Defender for Cloud | OCI Monitoring |
| **Audit** | CloudTrail | Audit Logs | Activity Log | Audit |

> **⚠️ Important**: GCP Certificate Manager, Azure managed certificates, and OCI Certificates have different validation methods, renewal periods, and integration coverage compared to ACM. Always validate against provider-specific documentation.

---

## Provider Differentiators

**ACM Zero-Cost Public Certificates**
- Category: Security / Cost
- Unique Value: ACM public certificates are completely free — no per-certificate fee, no annual renewal cost. Combined with free automated renewal, this eliminates the traditional cost and operational burden of SSL/TLS certificate management entirely. Competitors (GCP Certificate Manager, Azure App Service Certificates) also offer free managed certs, but ACM's breadth of integrated services is unmatched.
- Architecture Impact: Cost is never a factor in certificate decisions — architects can provision certificates liberally without budget concerns. One certificate per service endpoint is feasible even at large scale.
- When to Leverage: Always — there is no reason to NOT use ACM for public certificates on integrated AWS services.
- Caveat: Free only for ACM-issued public certificates. AWS Private CA costs $400/month per CA + per-certificate fees. Imported certificates require external CA purchase.
- Source: https://aws.amazon.com/certificate-manager/pricing/

**198-Day Certificate Validity with Seamless Renewal**
- Category: Security
- Unique Value: ACM's 198-day validity (shorter than the industry-standard 398 days) combined with fully automated 45-day-advance renewal creates a security posture where certificates rotate frequently without operational intervention. Shorter validity limits the exposure window if a certificate is compromised.
- Architecture Impact: Applications MUST support certificate rotation without downtime. Any architecture that relies on certificate stability (pinning, hardcoded fingerprints) will break. This is a forcing function for good security hygiene.
- When to Leverage: Default behavior — no opt-in required. Design all TLS-consuming clients to NOT pin certificates.
- Caveat: Shorter validity means more frequent renewals. If DNS validation CNAMEs are accidentally removed, or the certificate is not associated with any service, renewal will fail.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html

**ACK Integration for Kubernetes**
- Category: Compute / Security
- Unique Value: AWS Controllers for Kubernetes (ACK) allows managing ACM certificates as native Kubernetes CRDs, bridging ACM's managed lifecycle with Kubernetes' declarative model. Combined with the aws-privateca-issuer plugin for cert-manager, this provides end-to-end automated certificate management for EKS workloads.
- Architecture Impact: Enables GitOps-driven certificate management where certificates are declared alongside application manifests. Reduces the gap between cloud-native certificate management (ACM) and Kubernetes-native tools (cert-manager).
- When to Leverage: EKS deployments requiring HTTPS ingress, pod-to-pod mTLS, or workload identity via certificates.
- Caveat: ACK ACM controller is separate from cert-manager. Two different tools serve different purposes — ACK manages ACM resources, cert-manager with privateca-issuer issues certificates directly from Private CA to Kubernetes secrets.
- Source: https://docs.aws.amazon.com/acm/latest/userguide/exportable-certificates-kubernetes.html

---

## Scenario Coverage

**Standard Case**: Public web application requiring HTTPS
- Approach: Request ACM public certificate with DNS validation for primary domain + wildcard (example.com + *.example.com). Associate with CloudFront distribution (cert in us-east-1) and/or regional ALB (cert in ALB region). Use Route 53 for one-click CNAME creation. Certificate auto-renews indefinitely.
- Key Decisions: RSA vs ECDSA (default RSA for compatibility), single cert vs per-service certs (single wildcard for simplicity), TLS termination point (CloudFront edge vs ALB).

**Edge Case**: Multi-region active-active with cross-account DNS
- Approach: DNS hosted zone in shared services account (Route 53). Workload accounts request certificates with DNS validation — CNAME record is added to shared zone (requires cross-account Route 53 write permission or pre-provisioned CNAME). Certificates issued per region in each workload account. Use EventBridge cross-account events for centralized renewal monitoring.
- Approach (if DNS zone is external): Export CNAME values from ACM, add to external DNS provider (one-time per domain). Use `aws acm describe-certificate` to retrieve validation records. Monitor via Config aggregator.

**Anti-Pattern Case**: Team requests EV certificate via ACM
- Clarification: "ACM only issues Domain Validation (DV) certificates. Extended Validation (EV) and Organization Validation (OV) certificates require an external CA (DigiCert, Sectigo, etc.). You can import EV/OV certificates into ACM for deployment to integrated services, but you lose managed renewal — you must reimport manually before each expiration. Are you certain EV is required? Modern browsers no longer display the organization name in the address bar for EV certificates, reducing their practical benefit."

---

## Quotas Quick Reference

| Resource | Default Limit | Adjustable |
|----------|---------------|------------|
| ACM certificates per account/region | 2,500 | Yes |
| ACM certificates per year (365 days) | 5,000 | Yes |
| Imported certificates per account/region | 2,500 | Yes |
| Domain names (SANs) per certificate | 10 | Yes (up to 100) |
| Private CAs per account | 200 | Yes |
| Private certificates per CA (lifetime) | 1,000,000 | No |
| RequestCertificate API rate | 5 req/sec | No |
| DescribeCertificate API rate | 10 req/sec | No |
| ImportCertificate API rate | 1 req/sec | No |
| DeleteCertificate API rate | 10 req/sec | No |
| ListCertificates API rate | 8 req/sec | No |

> **⚠️ Important**: Expired and revoked certificates still count toward the 2,500 active certificate quota. Delete unused certificates proactively.

---

## Sources

| Topic | URL |
|-------|-----|
| ACM Overview | https://docs.aws.amazon.com/acm/latest/userguide/acm-overview.html |
| ACM Concepts | https://docs.aws.amazon.com/acm/latest/userguide/acm-concepts.html |
| DNS Validation | https://docs.aws.amazon.com/acm/latest/userguide/dns-validation.html |
| Managed Renewal | https://docs.aws.amazon.com/acm/latest/userguide/managed-renewal.html |
| Integrated Services | https://docs.aws.amazon.com/acm/latest/userguide/acm-services.html |
| Best Practices | https://docs.aws.amazon.com/acm/latest/userguide/acm-bestpractices.html |
| Quotas | https://docs.aws.amazon.com/acm/latest/userguide/acm-limits.html |
| Public Certificate Characteristics | https://docs.aws.amazon.com/acm/latest/userguide/acm-certificate-characteristics.html |
| SEC09-BP01 (Well-Architected) | https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/sec_protect_data_transit_key_cert_mgmt.html |
| AWS Private CA | https://docs.aws.amazon.com/privateca/latest/userguide/PcaWelcome.html |
| Amazon Trust Services (Root CAs) | https://www.amazontrust.com/repository/ |
