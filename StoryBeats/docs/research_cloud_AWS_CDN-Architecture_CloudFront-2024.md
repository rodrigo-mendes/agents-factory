# AWS CloudFront — CDN & Edge Architecture Knowledge Base

---

## Metadata

```yaml
Full_Name: "AWS CloudFront — CDN & Edge Architecture"
Cloud_Provider: "AWS"
Architecture_Domain: "CDN Architecture"
Target_Edition: "AWS CloudFront 2024"
Architecture_Context: "Content delivery and edge computing for distributed applications — covering static/dynamic content acceleration, origin shielding, edge functions, security at the edge, caching strategies, and global distribution patterns"
Official_Source_URL: "https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Introduction.html"
Output_Format: Markdown
Primary_Audience: Cloud Architects and Tech Leads
Research_Date: "2026-05-28"
Currency_Threshold: "2027-05-28 — review required after this date due to CloudFront feature updates, edge location expansions, and pricing changes"
```

---

## Executive Summary

Amazon CloudFront is AWS's globally distributed content delivery network (CDN) that accelerates delivery of static and dynamic web content through a worldwide network of 600+ edge locations and 13 regional edge caches. CloudFront acts as a reverse proxy cache, routing viewer requests to the nearest edge location via the AWS backbone network, providing lower latency, higher transfer rates, and reduced origin load. Beyond caching, CloudFront serves as a security perimeter (AWS WAF, Shield, OAC), an edge compute platform (CloudFront Functions, Lambda@Edge), and a traffic management layer (origin failover, geographic restrictions, signed URLs/cookies).

The 2024 edition's most architecturally significant advances are: (1) **Multi-tenant distributions (CloudFront SaaS Manager) GA** — enabling SaaS providers to manage hundreds of customer domains through a single distribution with per-tenant customization; (2) **CloudFront VPC Origins** — allowing distributions to fetch content directly from private resources within a VPC (ALB, NLB, EC2) without requiring public internet exposure; (3) **Anycast Static IPs** — providing stable IP addresses for allowlisting in enterprise firewall environments; (4) **gRPC support** — enabling CloudFront to proxy gRPC traffic to origins; (5) **Continuous deployment** — supporting blue-green testing of distribution configuration changes with traffic splitting before full promotion; (6) **Connection Functions** — enabling custom mTLS validation logic at the connection layer. These changes transform CloudFront from a pure CDN into a comprehensive edge platform supporting SaaS multi-tenancy, zero-trust networking, and progressive delivery.

The three most critical architecture guardrails for CloudFront are: (1) **always use Origin Access Control (OAC) for S3 origins** — without OAC, S3 buckets must be publicly accessible, creating a data exfiltration vector that bypasses CloudFront's access controls; (2) **enforce HTTPS everywhere (viewer-to-CloudFront and CloudFront-to-origin)** — HTTP connections expose data in transit and enable man-in-the-middle attacks; (3) **attach AWS WAF web ACL to all public-facing distributions** — CloudFront without WAF is vulnerable to application-layer attacks, bot abuse, and volumetric L7 DDoS that CloudFront's native throttling cannot mitigate.

---

## Cloud Architecture Glossary

```
Term: Distribution
Definition: The fundamental CloudFront resource — a configuration that tells CloudFront which origins to fetch content from, how to cache it, which edge functions to apply, and how to serve it to viewers. Each distribution gets a unique domain name (d111111abcdef8.cloudfront.net) and can be associated with custom domain names (CNAMEs). Supports up to 25 origins and 25 cache behaviors per distribution.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-working-with.html
Architect Usage: A distribution is the unit of deployment and configuration for CDN delivery. Create separate distributions for different applications/services unless they share domain ownership. Multi-tenant distributions (SaaS Manager) enable single-distribution management for hundreds of tenants.
Common Confusion: Distribution ≠ "CDN endpoint." A distribution is the full configuration object (origins, behaviors, policies, edge functions, security). The CloudFront domain name is just one attribute. Also confused with "deployment" — a distribution is persistent; deployments change its configuration.

Term: Edge Location
Definition: A data center in CloudFront's global network where content is cached and served to viewers. CloudFront has 600+ edge locations across 100+ cities in 50+ countries. Edge locations are the first tier in CloudFront's three-tier caching hierarchy (edge location → regional edge cache → origin).
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/LocationsOfEdgeServers.html
Architect Usage: Edge locations determine end-user latency. CloudFront automatically routes requests to the nearest edge location using anycast routing. Architects cannot select specific edge locations — CloudFront manages this automatically. Geographic restrictions can exclude countries but not select specific POPs.
Common Confusion: Edge location ≠ AWS Region. Edge locations are independent of AWS Regions and are purpose-built for content delivery, not general compute. Lambda@Edge runs at regional edge caches (13 locations), not at all 600+ edge locations. CloudFront Functions DO run at all edge locations.

Term: Regional Edge Cache
Definition: A mid-tier caching layer between edge locations and the origin, deployed in 13 AWS Regions. Regional edge caches have larger storage than edge locations and serve as cache aggregation points. When content expires from an edge location but is still in the regional edge cache, CloudFront serves it from there without returning to the origin.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/HowCloudFrontWorks.html#CloudFrontRegionaledgecaches
Architect Usage: Regional edge caches improve cache hit ratio for content that isn't popular enough to stay in a single edge location's cache. They reduce origin load by consolidating origin requests from multiple edge locations. Origin Shield sits at this tier, adding a centralized cache layer.
Common Confusion: Regional edge cache ≠ Origin Shield. Regional edge caches exist automatically (13 locations). Origin Shield is an opt-in feature that designates ONE regional edge cache as the single point of origin access, further consolidating requests. They are architecturally related but functionally distinct.

Term: Origin Shield
Definition: An optional additional caching layer at a single regional edge cache that acts as the sole point of contact between CloudFront and the origin. All cache misses from all regional edge caches route through Origin Shield, maximizing cache hit ratio and minimizing origin requests to potentially a single request per object globally.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html
Architect Usage: Enable Origin Shield when: (1) viewers are geographically dispersed; (2) origin has limited capacity or high per-request cost (image transformation, just-in-time packaging); (3) multi-CDN architecture where CloudFront fronts other CDNs. Choose the Origin Shield region closest to your origin for lowest latency. Not beneficial for dynamic (non-cacheable) content — Origin Shield adds an extra hop without caching benefit.
Common Confusion: Origin Shield is NOT a WAF or security feature — it's purely a caching optimization layer. It adds per-request cost ($0.0075-$0.009 per 10,000 requests depending on region). Origin Shield does NOT work with gRPC traffic. Requests that naturally route to the same regional edge cache as Origin Shield incur no additional charges.

Term: Cache Policy
Definition: A reusable configuration that determines what values CloudFront includes in the cache key (headers, cookies, query strings) and the TTL settings (minimum, maximum, default TTL). Cache policies are attached to cache behaviors and control how CloudFront identifies cached objects and how long they remain valid.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html
Architect Usage: Fewer values in the cache key = higher cache hit ratio. Include ONLY the headers, cookies, and query strings that your origin uses to generate different responses. Use managed cache policies (CachingOptimized, CachingDisabled, CachingOptimizedForUncompressedObjects) as starting points. Separate cache policies from origin request policies — they serve different purposes.
Common Confusion: Cache policy ≠ origin request policy. Cache policy controls what's in the cache key (identification) and TTLs. Origin request policy controls what's forwarded to the origin on cache miss (additional headers/cookies/query strings the origin needs but that shouldn't vary the cache). Including something in the cache key automatically forwards it to the origin; the reverse is NOT true.

Term: Cache Behavior
Definition: A rule within a distribution that matches a URL path pattern (e.g., /images/*, /api/*, *.js) and defines how CloudFront handles matching requests — which origin to use, which cache policy, which origin request policy, which edge functions, viewer protocol policy, and TTL settings. A distribution has one default behavior (*) and up to 24 additional ordered behaviors.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html#DownloadDistValuesCacheBehavior
Architect Usage: Use cache behaviors to differentiate caching strategy by content type: static assets (long TTL, no cookies in cache key), dynamic API responses (short TTL or cache disabled, specific headers in cache key), media files (long TTL, range request support). Behaviors are evaluated in order — place more specific patterns before generic ones.
Common Confusion: Cache behaviors are matched by path pattern ONLY — not by host header, HTTP method, or query parameters. You cannot create a behavior that applies only to POST requests or only to a specific subdomain (without using separate distributions). The default behavior (*) catches everything not matched by other behaviors.

Term: Origin Access Control (OAC)
Definition: The recommended mechanism for restricting S3 bucket origin access to only CloudFront. OAC uses the CloudFront service principal (cloudfront.amazonaws.com) with SigV4 signing to authenticate requests from CloudFront to S3. OAC replaces the legacy Origin Access Identity (OAI) and supports all S3 regions, SSE-KMS encryption, and PUT/DELETE operations.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html
Architect Usage: ALWAYS use OAC for S3 bucket origins. This ensures: (1) S3 bucket can remain private (Block Public Access enabled); (2) content is only accessible via CloudFront (enforcing WAF, geo-restrictions, signed URLs); (3) SSE-KMS encrypted objects are accessible. Configure the S3 bucket policy to allow cloudfront.amazonaws.com with a Condition on the distribution ARN.
Common Confusion: OAC ≠ OAI. OAI is legacy and does not support SSE-KMS, opt-in regions, or PUT/DELETE. OAC is the recommended replacement. OAC does NOT work with S3 website endpoints (configured as static website hosting) — use a custom origin instead. OAC applies to S3 bucket origins only, not to custom HTTP origins.

Term: CloudFront Functions
Definition: Lightweight JavaScript functions that run at all 600+ CloudFront edge locations with submillisecond startup time, capable of handling millions of requests per second. Functions execute on viewer-request and viewer-response events. Limited to 10 KB code size, 2 MB memory, maximum 1ms execution time, no network access, no file system access.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-functions.html
Architect Usage: Use CloudFront Functions for high-scale, latency-sensitive transformations that don't require network access: URL rewrites/redirects, header manipulation, cache key normalization, request/response header injection, A/B testing via cookie/header routing, simple authorization (JWT validation from KV store). Native to CloudFront — build, test, deploy entirely within CloudFront.
Common Confusion: CloudFront Functions ≠ Lambda@Edge. CloudFront Functions are simpler, faster, cheaper (1/6 the price), run at all edge locations, but have severe restrictions (no network I/O, 1ms execution, 10KB code, JavaScript only). Lambda@Edge is more powerful (Node.js/Python, 30s execution, network access, 50MB package) but runs only at regional edge caches. Choose based on capability needs, not just cost.

Term: Lambda@Edge
Definition: An extension of AWS Lambda that runs functions at CloudFront's 13 regional edge cache locations. Supports Node.js and Python runtimes. Functions can be triggered on four events: viewer-request, viewer-response, origin-request, origin-response. Supports up to 30 seconds execution (origin-facing) or 5 seconds (viewer-facing), 128-10,240 MB memory, network access, and 50 MB deployment package.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/lambda-at-the-edge.html
Architect Usage: Use Lambda@Edge when you need capabilities CloudFront Functions cannot provide: dynamic origin selection, authentication against external IdPs (network calls), image resizing/transformation, A/B testing with external configuration, content generation at the edge, complex authorization logic, bot detection with external API calls.
Common Confusion: Lambda@Edge functions must be authored in us-east-1 (N. Virginia) and are replicated globally by CloudFront. You cannot view CloudWatch Logs in us-east-1 — logs appear in the region where the function executed. Lambda@Edge does NOT support all Lambda features (no VPC access, no environment variables, no layers for viewer-facing triggers, no provisioned concurrency). Cold starts affect latency (100-500ms).

Term: Signed URLs and Signed Cookies
Definition: Mechanisms for serving private content through CloudFront by requiring viewers to present a cryptographic signature. Signed URLs are per-object (or wildcard path) with expiration. Signed Cookies allow access to multiple objects without modifying URLs. Both use RSA key pairs — CloudFront validates the signature against a trusted key group (public key) before serving content.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html
Architect Usage: Use signed URLs for: individual file downloads, RTMP streams (legacy), situations where cookies aren't supported (API clients). Use signed cookies for: access to multiple files (HLS video segments), maintaining clean URLs, situations where modifying all URLs is impractical. Implement URL/cookie signing in your application server — CloudFront only validates, never generates.
Common Confusion: Signed URLs/cookies ≠ OAC. They serve different purposes: OAC restricts origin access (CloudFront → S3). Signed URLs restrict viewer access (viewer → CloudFront). Use BOTH together for defense in depth: OAC prevents direct S3 access; signed URLs prevent unauthorized CloudFront access. Signed URLs work with any origin type; OAC works only with S3 bucket origins.

Term: Origin Failover (Origin Group)
Definition: A high-availability mechanism where CloudFront automatically fails over from a primary origin to a secondary origin when the primary returns specific HTTP error codes (500, 502, 503, 504, 403, 404 — configurable). An origin group contains one primary and one secondary origin. Failover happens per-request, not per-distribution.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html
Architect Usage: Use origin groups for: (1) S3 cross-region replication + CloudFront failover (primary bucket → replica bucket); (2) multi-region API failover (primary ALB → secondary ALB); (3) primary/fallback content (dynamic origin → static error page origin). Configure failover criteria based on the HTTP status codes that indicate a true origin failure vs expected application errors.
Common Confusion: Origin failover is NOT automatic DNS failover or health-check-based failover. It triggers on HTTP response codes from the primary, PER REQUEST. If the primary returns a 500, that specific request fails over — other requests still try the primary first. There is no "circuit breaker" — every request tries the primary before potentially failing over.

Term: Continuous Deployment
Definition: A CloudFront feature that enables safe testing of distribution configuration changes by splitting traffic between a primary (production) distribution and a staging distribution. You configure a traffic percentage (1-15%) or specific header-based routing to direct some viewers to the staging configuration. After validation, promote the staging configuration to production.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html
Architect Usage: Use continuous deployment for testing risky configuration changes before full rollout: cache policy changes (risk of cache miss storm), new edge functions, origin changes, security policy updates. This is CloudFront's native canary deployment mechanism — safer than modifying production distributions directly.
Common Confusion: Continuous deployment ≠ canary releases at the application level. It tests CloudFront distribution configuration changes, not application code changes. The staging distribution serves the same origins (unless you change the origin in staging config). Traffic split is by viewer session (sticky) not by individual request.

Term: VPC Origins
Definition: A CloudFront origin type that connects directly to private resources within a VPC (Application Load Balancers, Network Load Balancers, EC2 instances) without requiring those resources to have public IP addresses or internet-facing configurations. CloudFront establishes private connectivity through AWS-managed ENIs in the VPC.
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html
Architect Usage: Use VPC Origins when backend services must remain completely private (no public subnets, no NAT gateway for origin traffic). This eliminates the need for an internet-facing ALB/NLB and reduces attack surface. VPC Origins provide the security benefits of a private API without the complexity of CloudFront → API Gateway → VPC Link chains.
Common Confusion: VPC Origins ≠ VPC Link (API Gateway). VPC Origins are a CloudFront-native feature for private origin connectivity. They are also different from PrivateLink — VPC Origins are managed by CloudFront, not customer-provisioned interface endpoints. VPC Origins require specific security group configuration to allow CloudFront's managed ENI traffic.

Term: AWS WAF Integration
Definition: CloudFront natively integrates with AWS WAF (Web Application Firewall) to inspect and filter HTTP/HTTPS requests at edge locations before they reach the origin. A WAF web ACL is attached to the CloudFront distribution and evaluates every request against configured rules (rate limiting, IP blocking, managed rule groups, custom rules).
Provider Docs Section: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-awswaf.html
Architect Usage: Always attach a WAF web ACL to public-facing CloudFront distributions. WAF at CloudFront edge rejects malicious requests before they consume origin resources or Lambda@Edge compute. Use AWSManagedRulesCommonRuleSet + rate-based rules as minimum. CloudFront + WAF is the first line of defense — cheaper to block at edge than to process at origin.
Common Confusion: WAF at CloudFront ≠ WAF at ALB. If you use both CloudFront and ALB, place WAF at CloudFront (blocks traffic earlier, protects the entire path). WAF rules at the ALB only protect traffic reaching the ALB — CloudFront traffic has already consumed bandwidth and edge resources. Some organizations use both for defense-in-depth with different rule sets.
```

---

## Architecture Framework Analysis: AWS Well-Architected — CloudFront CDN

```
Pillar: Performance Efficiency
Definition: The ability to use computing resources efficiently to meet system requirements and to maintain that efficiency as demand changes and technologies evolve.
Key Design Principles:
  - Go global in minutes (CloudFront automatically distributes content to 600+ edge locations)
  - Use serverless architectures (CloudFront is fully managed, auto-scaling, zero server management)
  - Experiment more often (continuous deployment for safe config testing)
  - Consider mechanical sympathy (cache policies, compression, HTTP/2, HTTP/3 for optimal transport)
Applies To CDN Architecture: CloudFront is the primary AWS mechanism for global latency reduction. Cache policies must be tuned per content type (static: long TTL; dynamic: short TTL or bypass). Origin Shield centralizes cache for geographically dispersed viewers. Edge functions (CloudFront Functions) enable sub-millisecond request manipulation at scale.
Assessment Questions:
  1. Are cache policies optimized per cache behavior (minimal cache key values for maximum hit ratio)?
  2. Is Origin Shield enabled for origins with geographically dispersed viewers?
  3. Are appropriate edge functions used (CloudFront Functions for lightweight, Lambda@Edge for complex) rather than processing at origin?
Source: https://docs.aws.amazon.com/wellarchitected/latest/performance-efficiency-pillar/welcome.html

Pillar: Security
Definition: The ability to protect data, systems, and assets while delivering business value through risk assessments and mitigation strategies.
Key Design Principles:
  - Implement a strong identity foundation (OAC for S3, signed URLs/cookies for viewers, WAF for request filtering)
  - Enable traceability (CloudFront access logs, real-time logs, CloudTrail for API operations)
  - Apply security at all layers (WAF at edge, HTTPS enforcement, field-level encryption, geographic restrictions)
  - Automate security best practices (AWS Shield Standard included, Shield Advanced for DDoS mitigation)
  - Protect data in transit and at rest (TLS 1.2/1.3, viewer mTLS, OAC with SSE-KMS)
Applies To CDN Architecture: CloudFront is both a content delivery layer AND a security perimeter. All public content must flow through CloudFront with WAF attached. S3 origins must use OAC (never public buckets). HTTPS must be enforced (viewer-to-edge and edge-to-origin). Signed URLs/cookies protect premium content. Geographic restrictions comply with content licensing/sanctions.
Assessment Questions:
  1. Is OAC configured for all S3 bucket origins with public access blocked on the bucket?
  2. Is AWS WAF attached to all public-facing CloudFront distributions with rate-based rules?
  3. Is HTTPS required both viewer-to-CloudFront (redirect HTTP to HTTPS) and CloudFront-to-origin (HTTPS only)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/security-pillar/welcome.html

Pillar: Reliability
Definition: The ability of a workload to perform its intended function correctly and consistently when it's expected to.
Key Design Principles:
  - Automatically recover from failure (origin failover via origin groups)
  - Scale horizontally (CloudFront auto-scales — no user action required)
  - Stop guessing capacity (serverless, no pre-provisioning)
  - Manage change through automation (continuous deployment for safe configuration changes)
Applies To CDN Architecture: CloudFront is inherently highly available (global, multi-AZ edge locations, automatic failover between POPs). Reliability concerns shift to: origin availability (use origin groups for failover), configuration safety (use continuous deployment), and cache invalidation correctness (use versioned URLs over invalidation API).
Assessment Questions:
  1. Are origin groups configured for critical origins with appropriate failover criteria?
  2. Is Origin Shield enabled to reduce load on capacity-constrained origins?
  3. Is continuous deployment used for configuration changes to prevent production incidents?
Source: https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html

Pillar: Cost Optimization
Definition: The ability to run systems to deliver business value at the lowest price point.
Key Design Principles:
  - Adopt a consumption model (CloudFront charges per request + data transfer — pay only for what you use)
  - Measure overall efficiency (cache hit ratio as primary cost metric — higher ratio = less origin traffic)
  - Stop spending money on undifferentiated heavy lifting (managed CDN vs self-hosted)
  - Analyze and attribute expenditure (CloudFront cost allocation tags, per-distribution billing)
Applies To CDN Architecture: Maximize cache hit ratio (reduce origin fetches = reduce origin compute/transfer cost). Use CloudFront Security Savings Bundle (30% savings with 1-year commitment). Enable compression (Gzip/Brotli) to reduce data transfer. Data transfer from AWS origins to CloudFront is free. Consider price class restrictions to limit edge locations if global coverage isn't needed.
Assessment Questions:
  1. Is the cache hit ratio > 90% for static content (< 90% indicates cache key or TTL misconfiguration)?
  2. Is compression enabled for text-based content types (HTML, CSS, JS, JSON, XML)?
  3. Are CloudFront Security Savings Bundles evaluated for predictable traffic patterns?
Source: https://docs.aws.amazon.com/wellarchitected/latest/cost-optimization-pillar/welcome.html

Pillar: Operational Excellence
Definition: The ability to support development and run workloads effectively, gain insight into their operations, and continuously improve supporting processes and procedures.
Key Design Principles:
  - Perform operations as code (CloudFormation/CDK for distribution configuration, IaC for cache/origin policies)
  - Make frequent, small, reversible changes (continuous deployment with traffic splitting)
  - Refine operations procedures frequently (monitor cache hit ratio, latency percentiles, error rates)
  - Anticipate failure (origin failover, stale-while-revalidate headers, custom error pages)
  - Learn from operational events (real-time logs to Kinesis, access log analysis)
Applies To CDN Architecture: All distribution configurations must be managed via IaC. Monitor: cache hit ratio, origin latency, 4XX/5XX rates, edge function errors/throttles. Use custom error pages for graceful degradation. Use real-time logs for operational alerting (vs standard logs for analytics). Configure stale-while-revalidate for resilience during origin failures.
Assessment Questions:
  1. Are all CloudFront distributions managed via Infrastructure as Code with version control?
  2. Are CloudWatch alarms configured for 5XX error rates, origin latency, and cache hit ratio drops?
  3. Are custom error pages configured for common error codes (403, 404, 500, 502, 503, 504)?
Source: https://docs.aws.amazon.com/wellarchitected/latest/operational-excellence-pillar/welcome.html

Pillar: Sustainability
Definition: Minimizing the environmental impact of running cloud workloads.
Key Design Principles:
  - Maximize utilization (CDN caching reduces redundant origin processing)
  - Reduce downstream resources (compression reduces data transfer volume)
  - Use managed services (CloudFront is serverless — no idle infrastructure)
Applies To CDN Architecture: CDN caching is inherently sustainability-positive — each cache hit eliminates an origin request (saved compute, storage I/O, network). Compression reduces bytes transferred. CloudFront Functions at edge eliminate need for origin-region compute for simple transformations. Price class restrictions can limit to regions with higher renewable energy usage.
Source: https://docs.aws.amazon.com/wellarchitected/latest/sustainability-pillar/sustainability-pillar.html
```

---

## Architecture Guardrails

### ✅ Mandatory Patterns

**Origin Access Control (OAC) for All S3 Origins**
- Pillar Alignment: Security
- Why: Without OAC, S3 bucket objects must be publicly accessible for CloudFront to serve them. This means anyone with the direct S3 URL can bypass CloudFront — circumventing WAF rules, signed URLs, geographic restrictions, and access logging. The Well-Architected Security pillar mandates "protect data in transit and at rest" and "automate security best practices."
- AWS Services: Amazon CloudFront (OAC), Amazon S3 (bucket policy), AWS KMS (for SSE-KMS support)
- Architecture Decision:
  Create an OAC with "Sign requests (recommended)" signing behavior. Attach to the S3 origin in the distribution. Configure S3 bucket policy allowing `cloudfront.amazonaws.com` service principal with `s3:GetObject` action, conditioned on `AWS:SourceArn` matching the distribution ARN. Enable S3 Block Public Access on the bucket. For SSE-KMS encrypted objects, grant CloudFront KMS decrypt permission in the key policy.
- Verification:
  ```bash
  # Check distribution origin has OAC attached
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.Origins.Items[].OriginAccessControlId"
  # Must return non-empty OAC IDs for S3 origins
  
  # Verify S3 bucket blocks public access
  aws s3api get-public-access-block --bucket <BUCKET_NAME>
  # All four settings must be true
  
  # Test direct S3 access is denied
  curl -I https://<bucket>.s3.<region>.amazonaws.com/<object>
  # Should return 403 Forbidden
  ```
- Trade-offs: OAC adds SigV4 signing overhead (negligible latency). Migrating from OAI requires updating bucket policies to support both during transition. OAC does not work with S3 website endpoints — use custom origin for static website hosting.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

**HTTPS Enforcement (Viewer and Origin)**
- Pillar Alignment: Security
- Why: HTTP connections expose content and headers (including cookies, authorization tokens) to interception. The Well-Architected Security pillar requires "protect data in transit." CloudFront supports TLS 1.2 and 1.3 — there is no valid reason to serve production content over HTTP.
- AWS Services: Amazon CloudFront (viewer protocol policy, origin protocol policy), AWS Certificate Manager (TLS certificates for custom domains)
- Architecture Decision:
  Set viewer protocol policy to "Redirect HTTP to HTTPS" (preferred — maintains backward compatibility) or "HTTPS Only" (strict — returns 403 for HTTP). For custom origins, set origin protocol policy to "HTTPS Only" (never "HTTP Only" or "Match Viewer" for production). For S3 origins with OAC, HTTPS is used automatically when signing is enabled. Use TLS 1.2 minimum security policy (TLSv1.2_2021 recommended).
- Verification:
  ```bash
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy"
  # Must return "redirect-to-https" or "https-only" — never "allow-all"
  
  # Test HTTP redirect
  curl -I http://<distribution-domain>/
  # Should return 301/302 redirect to HTTPS
  ```
- Trade-offs: "HTTPS Only" breaks clients that don't support HTTPS (extremely rare in 2024). "Redirect HTTP to HTTPS" adds one round trip for HTTP clients. ACM certificates for custom domains require validation and must be in us-east-1.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https.html

**AWS WAF on All Public-Facing Distributions**
- Pillar Alignment: Security
- Why: CloudFront's native throttling does not protect against application-layer attacks (SQL injection, XSS, credential stuffing, bot abuse). AWS WAF at the CloudFront edge rejects malicious requests before they consume origin resources, Lambda@Edge compute, or bandwidth. The Well-Architected Security pillar mandates "apply security at all layers."
- AWS Services: AWS WAF (web ACL, managed rules, rate-based rules), Amazon CloudFront (WAF association), AWS Shield Standard (included with CloudFront)
- Architecture Decision:
  Create a WAF web ACL (CLOUDFRONT scope, must be in us-east-1) and attach to the CloudFront distribution. Minimum rule set: (1) AWSManagedRulesCommonRuleSet (OWASP top 10); (2) AWSManagedRulesKnownBadInputsRuleSet (Log4j, path traversal); (3) Rate-based rule at 2000-10000 requests per 5 minutes per IP; (4) AWSManagedRulesBotControlRuleSet for consumer-facing properties.
- Verification:
  ```bash
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.WebACLId"
  # Must return a valid WAF web ACL ARN — empty string = unprotected
  
  aws wafv2 get-web-acl --name <ACL_NAME> --scope CLOUDFRONT --id <ACL_ID> --region us-east-1 --query "WebACL.Rules[].Name"
  # Should list at minimum rate-based and managed rule group rules
  ```
- Trade-offs: WAF adds ~1-2ms latency per request. WAF cost: $5/month per web ACL + $1/month per rule + $0.60 per million requests. For high-traffic distributions (>1B requests/month), WAF cost becomes significant — evaluate managed rule necessity per behavior.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-awswaf.html

**Cache Policy Optimization per Content Type**
- Pillar Alignment: Performance Efficiency, Cost Optimization
- Why: A default "cache everything with all headers/cookies/query strings" approach reduces cache hit ratio to near-zero — every unique header combination creates a separate cache entry. The Well-Architected Performance Efficiency pillar mandates "consider mechanical sympathy." Proper cache policy design is the single most impactful performance optimization for CDN.
- AWS Services: Amazon CloudFront (cache policies, origin request policies, cache behaviors)
- Architecture Decision:
  Create separate cache behaviors per content type with appropriate policies: (1) Static assets (images, CSS, JS, fonts): use `CachingOptimized` managed policy (TTL 86400s, no headers/cookies/query in cache key), enable compression; (2) Dynamic HTML: include relevant query params only, no cookies unless personalization varies content, short TTL (60-300s); (3) API responses: `CachingDisabled` or include Authorization + specific query params in cache key, TTL 0-60s; (4) Media/video: long TTL, range request support.
- Verification:
  ```bash
  # Check cache hit ratio in CloudWatch
  aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name CacheHitRate \
    --dimensions Name=DistributionId,Value=<DIST_ID> --statistics Average --period 3600
  # Static content should be >90%; overall >80%
  
  # Review cache policy configuration
  aws cloudfront get-cache-policy --id <POLICY_ID> --query "CachePolicy.CachePolicyConfig.ParametersInCacheKeyAndForwardedToOrigin"
  ```
- Trade-offs: Overly restrictive cache keys (too few values) can serve incorrect content (e.g., same response for authenticated/unauthenticated). Overly broad cache keys (too many values) reduce hit ratio. Balance correctness vs performance through careful analysis of what actually varies responses.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/controlling-the-cache-key.html

**Access Logging Enabled for All Distributions**
- Pillar Alignment: Operational Excellence, Security
- Why: Without access logging, you cannot: analyze traffic patterns, detect abuse, debug cache behavior, measure performance, investigate security incidents, or optimize costs. The Well-Architected Operational Excellence pillar mandates "enable traceability."
- AWS Services: Amazon CloudFront (standard logs to S3, real-time logs to Kinesis Data Streams), Amazon S3 (log storage), Amazon Athena (log analysis)
- Architecture Decision:
  Enable standard access logs (free, delivered to S3 with ~30 minute delay) for all distributions. For operational alerting, additionally configure real-time logs (Kinesis Data Streams → Lambda/Firehose) with sampling (1-100% of requests). Standard log fields include: timestamp, edge location, bytes, status, referer, user-agent, cache result type (Hit/Miss/Error), time-to-first-byte. Store logs in a dedicated S3 bucket with lifecycle rules (transition to Glacier after 90 days).
- Verification:
  ```bash
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.Logging"
  # Enabled must be true, Bucket must be a valid S3 bucket
  ```
- Trade-offs: Standard logs are free but delayed (~30 min) and incomplete (best-effort delivery). Real-time logs provide low-latency access but cost: Kinesis Data Streams pricing ($0.015/shard-hour + $0.014/million PUT records). Log storage in S3 adds marginal cost — use lifecycle policies to manage.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/AccessLogs.html

**Custom Error Pages for Graceful Degradation**
- Pillar Alignment: Reliability, Operational Excellence
- Why: Default CloudFront error pages expose technical details and provide poor user experience. Custom error pages maintain brand consistency and can serve cached fallback content during origin outages, implementing graceful degradation.
- AWS Services: Amazon CloudFront (custom error responses), Amazon S3 (static error page hosting)
- Architecture Decision:
  Configure custom error responses for: 403 (Forbidden → custom "Access Denied" page), 404 (Not Found → custom 404 page), 500/502/503/504 (Server errors → "Service Unavailable" page with error caching TTL of 10-60 seconds). Set error caching minimum TTL to prevent overwhelming a failing origin with retry storms. For SPAs (single-page apps), return 200 with index.html for 403/404 to enable client-side routing.
- Verification:
  ```bash
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.CustomErrorResponses.Items[].ErrorCode"
  # Should include at minimum: 403, 404, 500, 502, 503, 504
  ```
- Trade-offs: Custom error pages add configuration complexity. Error caching TTL prevents rapid recovery detection (cached error served until TTL expires). SPA configurations (returning 200 for 404) mask legitimate 404 errors from monitoring.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GeneratingCustomErrorResponses.html

---

### ⚠️ Architectural Decisions

**CloudFront Functions vs Lambda@Edge**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | CloudFront Functions | CloudFront-native JavaScript functions | Speed (submillisecond), scale (millions RPS), cost (1/6 of Lambda@Edge) | Capabilities (no network I/O, 1ms max, 10KB code, JS only, viewer events only) | URL rewrites, header manipulation, simple auth token validation, cache key normalization, redirects |
  | Lambda@Edge | Lambda at regional edge caches (Node.js/Python) | Capabilities (network access, 30s execution, 50MB package, origin events) | Latency (cold starts 100-500ms), cost (6x CloudFront Functions), scale (throttle limits per region) | Image transformation, dynamic origin selection, external auth validation, content generation, A/B with external config |
  | No edge function (origin-side) | Origin compute (Lambda/ECS/EC2) | Flexibility (any language, any resource, no edge restrictions) | Latency (full round-trip to origin), cost (origin compute per request) | Complex business logic, database access, stateful operations, operations needing VPC resources |

- Cost Profile: CloudFront Functions: $0.10/million invocations. Lambda@Edge: $0.60/million invocations + $0.00000625125/128MB-ms. Origin (Lambda): $0.20/million + duration + data transfer from origin.
- Architect Instruction: "Ask 'Does this request manipulation need network access or more than 1ms of compute?' — if NO, use CloudFront Functions. If YES, 'Does it need VPC access or more than 30 seconds?' — if NO, use Lambda@Edge. If YES, process at origin."
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html

**Origin Type: S3 vs ALB/NLB vs API Gateway vs VPC Origin**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | S3 Bucket Origin | S3 + OAC | Simplicity, cost (free origin transfer), durability, static content | Dynamic capabilities (no server-side processing at origin) | Static websites, SPAs, media files, software downloads, static API responses |
  | ALB/NLB (public) | Internet-facing load balancer | Flexibility, any compute backend, health checks | Security (LB must be internet-facing), additional LB cost | Dynamic APIs, microservices, containerized backends, ECS/EKS services |
  | API Gateway | API Gateway Regional endpoint | API management features (auth, throttling, validation) | Double API management (CloudFront + APIGW), latency | APIs already using API Gateway, serverless backends via Lambda |
  | VPC Origin (private) | CloudFront → private ALB/NLB/EC2 | Security (no public exposure), simplicity (no internet-facing infra) | Newer feature, limited origin types | Security-sensitive backends that must remain fully private |

- Cost Profile: S3: $0.023/GB stored + free CloudFront-to-S3 transfer. ALB: $0.0225/hour + LCU. API Gateway: $3.50/M requests (REST). VPC Origin: CloudFront pricing + LB pricing (no additional VPC origin charge).
- Architect Instruction: "Ask 'Is this content static or server-generated?' — static = S3. 'Must the backend remain private?' — if YES, use VPC Origin. 'Do you need API management (rate limiting, request validation)?' — if YES, API Gateway. Otherwise, ALB/NLB."
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/DownloadDistS3AndCustomOrigins.html

**Caching Strategy: Long TTL + Invalidation vs Short TTL vs Versioned URLs**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | Long TTL + Invalidation | CloudFront cache (TTL days-years) + invalidation API | Cache hit ratio, origin cost reduction | Invalidation propagation time (seconds-minutes), invalidation cost ($0.005/path after first 1000 free/month) | Content that rarely changes but needs immediate update when it does (homepage, product images) |
  | Short TTL (seconds-minutes) | CloudFront cache with stale-while-revalidate | Freshness, minimal stale content | Lower cache hit ratio, more origin requests, higher origin load | Dynamic content that changes frequently (API responses, prices, inventory) |
  | Versioned URLs (cache busting) | Application-level URL versioning (hash in filename) | Perfect cache hit ratio + instant update (new URL = new object), no invalidation cost | Application complexity (build tooling for hash generation, URL management) | Static assets deployed with application (JS, CSS bundles with content hash) |

- Cost Profile: Long TTL: lowest origin cost, $0.005/path invalidation after free tier. Short TTL: higher origin cost (more fetches). Versioned URLs: lowest CDN cost (never invalidate, infinite TTL) + negligible edge storage.
- Architect Instruction: "Ask 'Can the content be versioned in the URL (content hash)?' — if YES (build assets), use versioned URLs with TTL of 1 year. If NO (dynamic HTML, images with stable URLs), 'How stale can it be?' — if hours-days acceptable, use long TTL with invalidation. If seconds, use short TTL with stale-while-revalidate."
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Expiration.html

**Price Class: All Edge Locations vs Limited**
- Options:

  | Option | AWS Service | Optimizes | Sacrifices | Best When |
  |--------|-------------|-----------|------------|-----------|
  | PriceClass_All | All 600+ edge locations worldwide | Global performance (lowest latency everywhere) | Cost (highest per-GB in Africa, South America, Asia) | Global audience, latency-sensitive globally, premium user experience worldwide |
  | PriceClass_200 | US, Canada, Europe, Asia, Middle East, Africa (excludes South America, Australia) | Balanced cost and coverage | Latency in excluded regions (served from further edge locations) | Primary audience in Northern Hemisphere, cost-conscious with broad reach |
  | PriceClass_100 | US, Canada, Europe only | Lowest cost per GB | Latency in Asia, Africa, South America, Australia | Audience primarily in US/Europe, tight budget constraints |

- Cost Profile: Data transfer ranges from $0.085/GB (US/Europe) to $0.170/GB (South America/Australia). PriceClass_100 saves 20-50% for workloads with southern hemisphere traffic by routing those viewers to the cheapest edge locations.
- Architect Instruction: "Ask 'Where are your users?' — if global, PriceClass_All. If 90%+ in US/Europe, PriceClass_100 saves money with minimal latency impact for your majority audience."
- Source: https://aws.amazon.com/cloudfront/pricing/

---

### 🚫 Anti-Patterns

**S3 Origins Without Origin Access Control (Public Buckets)**
- Risk Level: CRITICAL
- Why: Security pillar violation — "Protect data at all layers." A public S3 bucket with CloudFront in front provides zero access control — anyone who discovers the S3 URL directly bypasses CloudFront's WAF, signed URLs, geographic restrictions, and logging. Data exfiltration occurs without detection.
- Instead:
  Enable S3 Block Public Access. Configure OAC on CloudFront with "Sign requests" enabled. Set bucket policy allowing only `cloudfront.amazonaws.com` principal conditioned on distribution ARN. Deny all other access.
- Detection:
  ```bash
  aws s3api get-public-access-block --bucket <BUCKET_NAME>
  # All four fields must be true
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.Origins.Items[?S3OriginConfig].OriginAccessControlId"
  # Must be non-empty for S3 origins
  ```
- Impact: Data breach via direct S3 access, WAF/security bypass, compliance violation, cost amplification (direct S3 requests billed differently), audit logging gap.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

**Serving Content Over HTTP (No HTTPS Enforcement)**
- Risk Level: CRITICAL
- Why: Security pillar violation — "Protect data in transit." HTTP traffic is unencrypted and vulnerable to man-in-the-middle attacks, credential theft, content injection, and session hijacking. Modern browsers flag HTTP as "Not Secure," damaging user trust.
- Instead:
  Set viewer protocol policy to "Redirect HTTP to HTTPS" on ALL cache behaviors. Set origin protocol policy to "HTTPS Only" for custom origins. Use ACM certificates for custom domain names. Use TLSv1.2_2021 minimum security policy.
- Detection:
  ```bash
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.CacheBehaviors.Items[].ViewerProtocolPolicy"
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.DefaultCacheBehavior.ViewerProtocolPolicy"
  # Any "allow-all" = HTTP allowed = anti-pattern
  ```
- Impact: Data interception, credential theft, session hijacking, SEO penalty (Google downgrades HTTP), browser security warnings, compliance violation (PCI-DSS 4.1).
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/using-https.html

**Forwarding All Headers/Cookies/Query Strings in Cache Key**
- Risk Level: HIGH
- Why: Performance Efficiency pillar violation. Including all request attributes in the cache key creates unique cache entries for virtually every request — reducing cache hit ratio to near-zero. This turns CloudFront into an expensive proxy rather than a CDN, with every request hitting the origin.
- Instead:
  Use cache policies with ONLY the headers, cookies, and query strings that actually vary origin responses in the cache key. Use separate origin request policies to forward values the origin needs but that shouldn't be in the cache key. Typical static assets need ZERO headers/cookies/query strings in the cache key.
- Detection:
  ```bash
  # Check cache hit ratio — should be >80% overall, >95% for static
  aws cloudwatch get-metric-statistics --namespace AWS/CloudFront --metric-name CacheHitRate \
    --dimensions Name=DistributionId,Value=<DIST_ID> --statistics Average --period 86400
  # < 50% cache hit ratio = likely forwarding too many values
  ```
- Impact: Degraded performance (origin hit on every request), increased origin cost, increased origin latency for viewers, higher data transfer costs, potential origin overload during traffic spikes.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cache-hit-ratio.html

**No WAF on Public-Facing Distribution**
- Risk Level: HIGH
- Why: Security pillar violation — "Apply security at all layers." CloudFront without WAF is exposed to L7 DDoS, SQL injection, XSS, path traversal, credential stuffing, and automated bot abuse. Native CloudFront throttling is account-level and insufficient for application-layer protection.
- Instead:
  Attach WAF web ACL (CLOUDFRONT scope, us-east-1) to every public-facing distribution. At minimum: AWSManagedRulesCommonRuleSet + rate-based rule (2000-10000 req/5min/IP). For e-commerce/auth flows: add AWSManagedRulesBotControlRuleSet.
- Detection:
  ```bash
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.WebACLId"
  # Empty string = no WAF attached
  ```
- Impact: Application-layer attacks succeed, origin compromise, data breach, service degradation from bot traffic, cost amplification from attack traffic.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-awswaf.html

**Using Legacy OAI Instead of OAC**
- Risk Level: MEDIUM
- Why: OAI (Origin Access Identity) is a legacy mechanism that does not support: (1) S3 buckets in opt-in regions launched after December 2022; (2) SSE-KMS encrypted objects; (3) PUT/DELETE requests to S3. AWS recommends migrating all OAIs to OAC.
- Instead:
  Create a new OAC, update the S3 bucket policy to allow both OAI and OAC during migration, switch the distribution to use OAC, verify functionality, then remove OAI from bucket policy.
- Detection:
  ```bash
  aws cloudfront list-cloud-front-origin-access-identities --query "CloudFrontOriginAccessIdentityList.Items[].Id"
  # Any results = legacy OAI still in use
  aws cloudfront get-distribution --id <DIST_ID> --query "Distribution.DistributionConfig.Origins.Items[].S3OriginConfig.OriginAccessIdentity"
  # Non-empty = using OAI
  ```
- Impact: Cannot use SSE-KMS encryption on S3 objects served via CloudFront, cannot serve content from newer AWS regions, cannot support upload (PUT) operations through CloudFront, technical debt.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

**Using Invalidation as Primary Cache Update Strategy**
- Risk Level: MEDIUM
- Why: Cost Optimization and Operational Excellence violation. Invalidation is: (1) slow (takes seconds to minutes to propagate globally); (2) costly ($0.005/path after 1000 free/month — expensive for millions of objects); (3) operationally brittle (race conditions between invalidation and origin update). Versioned URLs are always superior for application assets.
- Instead:
  Use versioned URLs (content hash in filename: `app.a1b2c3d4.js`) for application build assets — infinite TTL, never invalidate. Use `stale-while-revalidate` + short TTL for frequently changing content. Reserve invalidation API for emergency cache clearing only (security incident, wrong content published).
- Detection:
  ```bash
  aws cloudfront list-invalidations --distribution-id <DIST_ID> --query "InvalidationList.Items | length(@)"
  # Frequent invalidations (daily) = anti-pattern; should be rare (emergency only)
  ```
- Impact: Stale content served during propagation window, invalidation costs at scale, operational complexity (coordinating invalidation with deployment), potential for race conditions.
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/Invalidation.html

---

## Cloud-Native Design Patterns

**Static Website Hosting with CloudFront + S3**
- Category: Scalability / Cost Optimization
- Problem: Hosting static websites (SPAs, marketing sites, documentation) on traditional web servers incurs compute cost, requires capacity planning, and provides single-region performance.
- Solution on AWS:
  S3 bucket (origin, private with OAC) + CloudFront distribution (global delivery, HTTPS, custom domain) + Route 53 (DNS alias) + ACM (TLS certificate in us-east-1). For SPAs: configure custom error response returning 200 + /index.html for 403/404 to enable client-side routing. Use CloudFront Functions for URL rewrites (trailing slash normalization, default index.html for directory paths).
- Services Used: CloudFront (CDN, HTTPS termination), S3 (object storage/origin), Route 53 (DNS), ACM (TLS), CloudFront Functions (URL normalization)
- When to Apply: Any static content delivery; SPAs (React, Angular, Vue); documentation sites (Docusaurus, Hugo, MkDocs); marketing landing pages; software download distribution
- When NOT to Apply: Server-side rendered content requiring per-request computation; content requiring database queries; APIs with business logic
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Cost | Near-zero compute cost, pay only for storage + transfer | S3 eventual consistency (ms); limited server-side capability |
  | Scalability | Infinite scale, zero capacity planning | No server-side processing (all client-side or edge functions) |
  | Performance | Global sub-50ms latency for cached content | Initial cache miss (cold start) hits S3 origin |

- Complements: Lambda@Edge for server-side rendering at edge, CloudFront Functions for A/B testing, API Gateway for backend APIs
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/GettingStarted.SimpleDistribution.html

**Multi-Origin Architecture with Behavior-Based Routing**
- Category: Communication / Scalability
- Problem: Modern applications serve different content types (static assets, APIs, media, websockets) from different backends, each with different caching and security requirements.
- Solution on AWS:
  Single CloudFront distribution with multiple origins and cache behaviors: `/static/*` → S3 (OAC, long TTL, CachingOptimized policy); `/api/*` → ALB/API Gateway (short TTL or CachingDisabled, include Authorization header); `/media/*` → S3 or MediaPackage (long TTL, range request support); `Default (*)` → ALB (dynamic HTML, short TTL). Each behavior has independent: cache policy, origin request policy, edge functions, viewer protocol policy.
- Services Used: CloudFront (routing/caching), S3 (static assets), ALB (dynamic backends), API Gateway (APIs), Lambda@Edge (dynamic origin selection if needed)
- When to Apply: Any application with mixed content types; microservices architectures fronted by a single domain; applications requiring different caching strategies per path
- When NOT to Apply: Simple single-origin static sites; applications that already use path-based routing at the ALB/API Gateway level without CDN benefit
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Performance | Optimal caching per content type | Configuration complexity (multiple behaviors/policies) |
  | Cost | Static assets cached long-term (fewer origin requests) | Multiple origins to manage and monitor |
  | Security | Per-path security policies (WAF rules, signed URLs on /media/*) | Behavior ordering matters — misconfig can expose content |

- Complements: API Gateway for API management, Lambda@Edge for dynamic origin selection, Origin Shield for origin protection
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-web-values-specify.html

**Edge-Side Image Optimization**
- Category: Performance / Cost Optimization
- Problem: Serving original high-resolution images to all devices wastes bandwidth, increases load time on mobile, and requires either pre-generating all variants (storage cost) or processing on every request (compute cost).
- Solution on AWS:
  CloudFront + Lambda@Edge (origin-response trigger) + S3 (original images). On cache miss: Lambda@Edge at origin-response resizes/reformats images based on viewer attributes (device type, Accept header, query parameters like `?w=300&q=80`). Transformed image is cached at edge with content-type-specific cache key (include width, quality, format in cache key). Origin Shield reduces duplicate transformations across regions.
- Services Used: CloudFront (caching transformed images), Lambda@Edge (image processing), S3 (original image storage), Origin Shield (consolidate processing requests), Sharp/libvips (in Lambda)
- When to Apply: Media-rich applications; e-commerce product images; user-uploaded content; responsive web design requiring multiple image sizes
- When NOT to Apply: Small number of images (pre-generate variants instead); content that doesn't benefit from transformation; latency-sensitive paths where Lambda@Edge cold start is unacceptable
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Bandwidth | 60-80% reduction for mobile; format optimization (WebP/AVIF) | Lambda@Edge invocation cost per unique variant |
  | Storage | No pre-generation of variants (on-demand) | Lambda@Edge cold start (100-500ms) on first request per variant |
  | UX | Optimal image quality for each device | Cache key cardinality (many variants = more origin-facing processing) |

- Complements: Origin Shield (reduces duplicate processing), CloudFront Functions (URL normalization for cache key), S3 Intelligent Tiering (original image storage)
- Source: https://aws.amazon.com/blogs/networking-and-content-delivery/image-optimization-using-amazon-cloudfront-and-aws-lambda/

**Origin Failover for High Availability**
- Category: Resilience
- Problem: Single-origin architectures fail completely when the origin becomes unavailable. API downtime or S3 service events cause cascading failures visible to all users globally.
- Solution on AWS:
  Configure an origin group with primary and secondary origins. Primary: production ALB/S3 bucket. Secondary: DR region ALB / S3 cross-region replica / static fallback page in a separate S3 bucket. Configure failover criteria: HTTP status codes 500, 502, 503, 504 (and optionally 403, 404). On failover error from primary, CloudFront automatically routes that request to the secondary origin.
- Services Used: CloudFront (origin groups), S3 (cross-region replication for S3 origins), ALB (multi-region deployments), Route 53 (health checks for non-CloudFront failover)
- When to Apply: Production workloads requiring >99.9% availability; critical content that must be served even during regional failures; multi-region architectures
- When NOT to Apply: Development/test environments; content where a brief outage is acceptable; workloads where origin unavailability should surface as an error (fail-fast)
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Availability | Automatic failover with zero manual intervention | 2x origin infrastructure cost (primary + secondary) |
  | Latency | No failover delay for viewers (per-request routing) | First request to secondary may be slower (cold cache) |
  | Consistency | Continued service during origin failure | Secondary may serve stale or incomplete content |

- Complements: S3 Cross-Region Replication, DynamoDB Global Tables, Aurora Global Database, Route 53 health checks
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/high_availability_origin_failover.html

**Zero-Trust Edge Security with CloudFront + WAF + OAC**
- Category: Security
- Problem: Traditional perimeter security (VPC boundaries) doesn't protect content delivered globally through CDN. Attackers can bypass CloudFront (direct origin access), exploit application vulnerabilities (injection), or abuse APIs (credential stuffing, DDoS).
- Solution on AWS:
  Defense-in-depth at edge: (1) CloudFront as the ONLY entry point (OAC blocks direct S3 access; security groups on ALB allow only CloudFront IP ranges); (2) WAF web ACL attached to distribution (L7 protection); (3) Shield Advanced for DDoS (L3/L4/L7); (4) Signed URLs/cookies for content authorization; (5) Geographic restrictions for compliance; (6) CloudFront Functions for token validation; (7) Origin custom headers as shared secret (CloudFront adds header, origin validates presence).
- Services Used: CloudFront (edge security perimeter), AWS WAF (application firewall), AWS Shield (DDoS protection), OAC (origin restriction), ACM (TLS), CloudFront Functions (token validation)
- When to Apply: All production public-facing content; applications handling PII or financial data; multi-tenant SaaS; applications subject to compliance (PCI-DSS, HIPAA, SOC2)
- When NOT to Apply: Internal-only content (use VPC/PrivateLink instead); development environments without sensitive data
- Trade-offs:

  | Dimension | Benefit | Cost |
  |-----------|---------|------|
  | Security | Multi-layer protection; attacks blocked at edge before reaching origin | WAF + Shield cost; configuration complexity |
  | Performance | Legitimate traffic unaffected (WAF <2ms latency) | False positives can block legitimate users (requires tuning) |
  | Operational | Centralized security management | WAF rule management, log analysis, incident response at edge |

- Complements: GuardDuty (threat detection), Security Hub (posture management), CloudTrail (API audit)
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/SecurityAndPrivateContent.html

---

## Security Architecture

**Content Access Control — OAC + Signed URLs + Geographic Restrictions**
- AWS Services:
  - Origin Access Control (OAC) — restricts S3 origin to CloudFront only
  - Signed URLs/Signed Cookies — restricts viewer access with time-limited cryptographic tokens
  - Key Groups — manage RSA public keys for signature validation (replaces legacy CloudFront key pairs)
  - Geographic Restrictions — block/allow countries based on viewer's GeoIP
  - CloudFront Functions — custom token validation, header-based access decisions
- Architecture:
  Three layers of access control: (1) OAC ensures content only accessible through CloudFront (prevents S3 direct access); (2) Signed URLs/cookies ensure only authorized viewers can access through CloudFront (time-limited, IP-restricted optionally); (3) Geographic restrictions comply with content licensing/sanctions. Key groups contain RSA-2048+ public keys for signature validation — application servers sign URLs with the corresponding private key.
- Configuration Essentials:
  - OAC: "Sign requests" mode, S3 bucket policy with CloudFront service principal + SourceArn condition
  - Signed URLs: RSA key pair, key group in CloudFront, custom/canned policy, expiration time
  - Geo-restriction: allowlist or blocklist of ISO 3166-1 alpha-2 country codes
- Verification:
  ```bash
  # Test direct S3 access blocked
  curl -I https://<bucket>.s3.<region>.amazonaws.com/<private-object>
  # Must return 403
  
  # Test unsigned CloudFront access blocked (for restricted content)
  curl -I https://<distribution>.cloudfront.net/<private-object>
  # Must return 403 (missing signature)
  ```
- Compliance Alignment: ITAR/EAR (geographic restrictions for export control), GDPR (geo-based content delivery), content licensing (geographic distribution rights)
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/PrivateContent.html

**DDoS Protection — Shield Standard + Shield Advanced + WAF**
- AWS Services:
  - AWS Shield Standard — automatic L3/L4 DDoS protection (included with CloudFront, no additional cost)
  - AWS Shield Advanced — enhanced L3/L4/L7 DDoS protection with 24/7 DRT support, cost protection, and advanced metrics ($3,000/month)
  - AWS WAF — L7 application firewall (rate-based rules, bot control, IP reputation)
  - CloudFront — inherent DDoS resilience through global distribution and anycast absorption
- Architecture:
  CloudFront provides inherent DDoS resistance: (1) Global distribution absorbs volumetric attacks across 600+ POPs; (2) Shield Standard automatically mitigates L3/L4 floods; (3) WAF rate-based rules cap per-IP request rates (L7 floods); (4) Shield Advanced adds DDoS Response Team support, cost protection (credits for scaling during attack), and application-layer automatic mitigation. For critical applications: CloudFront + Shield Advanced + WAF provides comprehensive protection.
- Configuration Essentials:
  - Shield Standard: automatic, no configuration
  - Shield Advanced: enable on CloudFront distribution, create DRT access role, configure proactive engagement
  - WAF rate-based rule: 100-10000 requests per 5 minutes, action = block
  - WAF Bot Control: targeted (common bots) or targeted + verification (challenge suspicious traffic)
- Verification:
  ```bash
  aws shield describe-protection --resource-arn arn:aws:cloudfront::<account>:distribution/<DIST_ID>
  # Should return protection details if Shield Advanced is enabled
  
  aws wafv2 get-web-acl-for-resource --resource-arn arn:aws:cloudfront::<account>:distribution/<DIST_ID>
  # Should return web ACL details
  ```
- Compliance Alignment: SOC2 CC6.6 (network controls), PCI-DSS 6.6 (application firewall), availability requirements
- Source: https://docs.aws.amazon.com/waf/latest/developerguide/shield-chapter.html

---

## Operational Patterns

**Observability: CloudFront Monitoring Stack**
- AWS Services:
  - CloudWatch Metrics (requests, bytes, error rates, cache hit ratio, origin latency — per distribution)
  - Standard Access Logs (S3-delivered, ~30 min delay, complete request details, free)
  - Real-Time Logs (Kinesis Data Streams, 1-100% sampling, <60s latency)
  - CloudTrail (API operations: CreateDistribution, UpdateDistribution, CreateInvalidation)
  - CloudFront Functions metrics (invocations, errors, compute utilization)
- Architecture:
  Three monitoring tiers: (1) Metrics — CloudWatch dashboards showing requests/sec, cache hit ratio, 4XX/5XX rates, origin latency P50/P90/P99; (2) Logs — standard logs to S3 + Athena for deep analysis; real-time logs to Kinesis → Lambda for operational alerting; (3) Traces — CloudTrail for configuration change audit. Alarms: 5XX rate > 1%, cache hit ratio < 80%, origin latency P99 > threshold.
- Cost Profile: Low-Medium. CloudWatch metrics: free (included). Standard logs: free (S3 storage cost only). Real-time logs: Kinesis Data Streams pricing ($0.015/shard-hour). Athena queries: $5/TB scanned.
- Automation:
  - CloudWatch alarms → SNS → PagerDuty for 5XX spikes
  - Real-time logs → Lambda → WAF rule update (auto-block abusive IPs)
  - AWS Config rules for compliance (distribution has WAF, HTTPS enforced, logging enabled)
- Runbook Skeleton:
  1. Detection: CloudWatch alarm (5XX > 1%, origin latency spike, cache hit ratio drop)
  2. Triage: Check origin health (is origin returning errors?); Check edge functions (Lambda@Edge throttled?); Check cache (invalidation storm?)
  3. Resolution: If origin down → verify origin failover activating; If edge function error → rollback function; If cache miss storm → increase TTL, enable Origin Shield
  4. Post-mortem: Analyze real-time logs, document root cause, update alarms/thresholds
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/MonitoringDistributions.html

**Cost Optimization: CloudFront FinOps**
- AWS Services:
  - CloudFront pricing (data transfer out + HTTP/S requests + edge function invocations + Origin Shield + real-time logs)
  - CloudFront Security Savings Bundle (up to 30% savings with 1-year commitment)
  - Price Classes (restrict edge locations for lower per-GB cost)
  - CloudWatch (CacheHitRate metric — primary cost optimization indicator)
- Architecture:
  Cost optimization levers: (1) Maximize cache hit ratio (reduces origin data transfer and compute); (2) Enable compression (Gzip/Brotli — 60-80% reduction for text content); (3) Use versioned URLs with long TTL (eliminates invalidation costs); (4) Evaluate Security Savings Bundle (30% discount on commit); (5) Use appropriate price class (PriceClass_100 if audience is US/EU only); (6) Free origin transfer from AWS origins (S3, ALB, API Gateway — you only pay for CloudFront-to-viewer transfer).
- Cost Profile:
  | Component | Rate | Optimization |
  |-----------|------|-------------|
  | Data Transfer (US/EU) | $0.085/GB | Compression, caching, price class |
  | HTTPS Requests | $0.0100/10K | Minimize unnecessary requests, prefetch |
  | HTTP Requests | $0.0075/10K | Redirect all to HTTPS |
  | Origin Shield | $0.0075/10K requests | Only enable where beneficial |
  | Lambda@Edge | $0.60/M invocations | Prefer CloudFront Functions when possible |
  | CloudFront Functions | $0.10/M invocations | 6x cheaper than Lambda@Edge |
  | Invalidation | $0.005/path (>1000/mo) | Use versioned URLs instead |
- Automation:
  - Budget alerts at 80%/100% of monthly CloudFront spend
  - Monitor cache hit ratio — alert if drops below 80% (indicates cost waste)
  - Periodic review of Lambda@Edge invocations — migrate to CloudFront Functions where possible
- Source: https://aws.amazon.com/cloudfront/pricing/

---

## Reference Architectures

**Global Web Application with CloudFront**
- Context: Full-stack web application with static frontend, dynamic API, and media assets served globally
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | Edge Security | AWS WAF + Shield | Application firewall, DDoS protection |
  | CDN/Edge | CloudFront | Global content delivery, HTTPS termination, routing |
  | Edge Compute | CloudFront Functions | URL rewrites, header manipulation, A/B routing |
  | Static Origin | S3 + OAC | Frontend assets (HTML, CSS, JS, images) |
  | Dynamic Origin | ALB + ECS/Lambda | API backend, server-side rendering |
  | Media Origin | S3 + Origin Shield | Video, large downloads |
  | DNS | Route 53 | Domain routing, health checks |
  | TLS | ACM (us-east-1) | Certificate management |

- Key Decisions: Cache behavior separation (static/API/media); TTL strategy per content type; edge function placement (CloudFront Functions vs Lambda@Edge); Origin Shield for media origin
- Scaling Path: Start with single-region origin → add Origin Shield → add multi-region origin with origin failover → add Lambda@Edge for edge rendering → evaluate continuous deployment for safe changes
- Source: https://aws.amazon.com/architecture/content-delivery/

**SaaS Multi-Tenant CDN (CloudFront SaaS Manager)**
- Context: SaaS platform serving multiple customer websites through a single CDN infrastructure
- Services Composition:

  | Layer | Service | Purpose |
  |-------|---------|---------|
  | CDN | CloudFront Multi-Tenant Distribution | Shared infrastructure, per-tenant customization |
  | Tenant Config | Distribution Tenants | Per-customer domain, TLS, origin mapping |
  | Edge Compute | CloudFront Functions | Tenant identification, routing, header injection |
  | TLS | ACM | Per-tenant custom domain certificates |
  | Origins | Multiple S3 buckets or ALBs | Per-tenant content storage |
  | DNS | Route 53 / Customer DNS | CNAME to distribution tenant domain |

- Key Decisions: Shared vs per-tenant origins; tenant isolation strategy; WAF rule sharing; custom domain onboarding automation
- Scaling Path: Start with standard distributions per tenant → migrate to multi-tenant distribution as tenant count grows → automate tenant provisioning via API → add per-tenant metrics/logging
- Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/distribution-config-options.html

---

## Provider Differentiators

```
Differentiator: CloudFront Functions (Sub-millisecond Edge Compute)
Category: Edge / Compute
Unique Value: JavaScript functions that execute at ALL 600+ edge locations with submillisecond startup — no other CDN provides equivalent scale + latency combination. Akamai EdgeWorkers and Cloudflare Workers run at fewer locations. CloudFront Functions handle millions of RPS at 1/6 the cost of Lambda@Edge.
Architecture Impact: Enables lightweight request/response manipulation at true edge scale without Lambda cold starts or regional edge cache routing. URL normalization, header manipulation, simple auth, and A/B testing can be done with effectively zero added latency.
When to Leverage: High-scale transformations (millions RPS); latency-critical manipulations; cache key normalization; redirects; viewer request/response header injection.
Caveat: Severe restrictions: 10KB code, 2MB memory, 1ms max execution, no network I/O, no file system, JavaScript only, viewer events only. Cannot replace Lambda@Edge for anything requiring network calls or complex logic.
Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/cloudfront-functions.html

Differentiator: Origin Shield (Centralized Cache Layer)
Category: Performance / Cost
Unique Value: Single-point-of-origin-contact architecture that consolidates ALL cache misses globally through one regional location. No other major CDN offers an equivalent named, opt-in centralized cache tier. Reduces origin requests by 50-90% for globally distributed viewers.
Architecture Impact: Transforms origin capacity planning — with Origin Shield, origin sees at most one request per unique object globally (per TTL period). Enables capacity-constrained origins (on-premises servers, expensive processing like image transformation) to serve global audiences.
When to Leverage: Origins with limited capacity; expensive per-request processing (just-in-time packaging, image transformation); globally distributed viewers hitting different regional edge caches; multi-CDN architectures.
Caveat: Additional per-request cost ($0.0075-$0.009/10K requests). Not beneficial for dynamic (non-cacheable) content. Does not work with gRPC. Adds latency for requests that must traverse an additional hop to Origin Shield region.
Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html

Differentiator: VPC Origins (Private Origin Connectivity)
Category: Security / Networking
Unique Value: CloudFront can fetch content directly from private VPC resources (ALB, NLB, EC2) without requiring any public internet exposure. No internet-facing load balancer or NAT gateway needed. AWS manages the private connectivity through ENIs in the VPC.
Architecture Impact: Eliminates the security trade-off of needing public-facing origins for CDN connectivity. Backend services remain completely private. Reduces attack surface by removing public load balancers. Simplifies architecture by eliminating the CloudFront → API Gateway → VPC Link chain.
When to Leverage: Zero-trust architectures; security-sensitive backends; compliance requirements prohibiting public endpoints; simplifying private origin connectivity.
Caveat: Relatively new feature (2024); requires specific security group configuration for CloudFront-managed ENIs; supported origin types limited to ALB, NLB, and EC2 instances.
Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/private-content-vpc-origins.html

Differentiator: Continuous Deployment (CDN-Level Canary)
Category: Change Management
Unique Value: Native traffic-splitting for CloudFront configuration changes — test new cache policies, edge functions, origin configurations, or security settings with a percentage of real traffic before full promotion. No other major CDN provides built-in blue-green testing of CDN configuration.
Architecture Impact: Reduces risk of CDN misconfigurations that historically caused production incidents (cache miss storms from policy changes, edge function bugs, broken origins). Enables safe experimentation with CDN configuration.
When to Leverage: Any production CloudFront configuration change; cache policy modifications; new edge function deployments; origin switches; security policy updates.
Caveat: Limited to 15% traffic maximum to staging; session-sticky routing (same viewer stays on same config); staging distribution shares the same domain name; not application-level canary (CDN config only).
Source: https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/continuous-deployment.html
```

---

## Scenario Coverage

**Standard Case**: Global web application with static + dynamic content
- Approach: CloudFront distribution with S3 origin (static, OAC, long TTL) + ALB origin (dynamic, short TTL) + WAF + HTTPS. Cache behaviors: `/static/*` → S3 (CachingOptimized), `/api/*` → ALB (CachingDisabled + origin request policy), `Default (*)` → ALB (short TTL). CloudFront Functions for URL normalization. Custom error pages for graceful degradation.
- Key Decisions: Price class (based on audience geography); Origin Shield (yes if viewers are globally distributed); cache TTL for dynamic HTML (balance freshness vs performance); compression (enable for text types).

**Edge Case**: Multi-tenant SaaS with 500+ customer domains
- Approach: CloudFront multi-tenant distribution with distribution tenants. Each tenant gets: custom domain, ACM certificate, optional custom origin. Shared WAF web ACL across all tenants. CloudFront Functions for tenant identification (based on Host header) and routing. Automated tenant provisioning via CloudFront API. Per-tenant access logging via log prefix.
- Key Decisions: Shared vs per-tenant WAF rules; tenant isolation level (shared origin vs per-tenant origin); custom domain onboarding automation; rate limiting per tenant.

**Anti-Pattern Case**: Developer wants to use CloudFront as a "simple proxy" without caching
- Clarification: "Ask: 'Why do you want to disable caching entirely?' If the answer is 'content changes frequently,' use short TTL (1-60 seconds) with stale-while-revalidate — you still get edge-level TLS termination, WAF protection, and HTTP/2 multiplexing benefits without caching issues. If truly no caching needed (real-time personalized per-request), confirm the workload still benefits from CloudFront's other features (WAF, Shield, geographic routing, compression). If none of those apply, consider whether CloudFront adds value at all — perhaps ALB/API Gateway directly is simpler."

---

## Service Equivalence Context

| Category | AWS | Google Cloud | Azure | Oracle Cloud (OCI) |
|----------|-----|-------------|-------|--------------------|
| **CDN** | CloudFront | Cloud CDN | Front Door / CDN | OCI CDN |
| **Edge Functions (lightweight)** | CloudFront Functions | — | Front Door Rules Engine | — |
| **Edge Functions (full)** | Lambda@Edge | — | — | — |
| **DDoS Protection** | Shield Standard/Advanced | Cloud Armor | DDoS Protection | OCI DDoS |
| **WAF at Edge** | AWS WAF (on CloudFront) | Cloud Armor | Azure WAF (on Front Door) | OCI WAF |
| **Origin Shielding** | Origin Shield | — | — | — |
| **Signed URLs** | CloudFront Signed URLs | Signed URLs (Cloud CDN) | SAS Tokens | Pre-authenticated Requests |
| **Multi-CDN Origin** | Origin Shield as origin-facing CDN | — | — | — |

> **⚠️ Important**: Azure Front Door combines CDN, WAF, load balancing, and routing into a single service — more comparable to CloudFront + WAF + Route 53 combined. Google Cloud CDN has significantly fewer features than CloudFront (no edge functions, limited cache control). CloudFront's edge function ecosystem (CloudFront Functions + Lambda@Edge) has no direct equivalent in other providers.
