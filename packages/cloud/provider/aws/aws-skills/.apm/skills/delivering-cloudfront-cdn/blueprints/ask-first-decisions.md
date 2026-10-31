# Ask First Decisions — delivering-cloudfront-cdn

Full decision matrices D1-D4. Summary in [../SKILL.md](../SKILL.md).
Source: research_cloud_AWS_CloudFront_CDN_2026.md (research date 2026-08-26; official AWS docs accessed 2026-08-26).

---

## D1 — CloudFront Functions vs Lambda@Edge

**Ask**: "Does the logic need the request body, network calls, third-party libraries, or origin-facing triggers?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| CloudFront Functions (JS ES5.1, runtime 2.0) | Sub-ms latency, millions rps, cost, KeyValueStore access | No network/filesystem/body access; viewer events only; 2 MB memory, 10 KB code | Cache-key normalization, header rewrites, redirects, JWT validation |
| Lambda@Edge (Node.js/Python) | Network + filesystem + body access, third-party libs, 4 event triggers | Up to 10,000 rps per Region, higher latency, up to 30 s | Origin-facing logic, body inspection, AWS SDK/API calls |

**Cost**: CloudFront Functions is about 1/6 the price per invocation; Lambda@Edge is billed per request plus duration.
**Scaling**: Functions scale to millions rps; Lambda@Edge caps at 10,000 rps per Region.
**Lock-in**: both AWS-proprietary; ES5.1 function logic is more portable.
**Notes**: origin-facing Lambda@Edge triggers run at the regional edge cache / Origin Shield Region, not at every edge location. KeyValueStore is available only to CloudFront Functions runtime 2.0.

**Architect instruction**: if yes to any question, use Lambda@Edge; otherwise CloudFront Functions.

Source: [Functions vs Lambda@Edge](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/edge-functions-choosing.html) (accessed 2026-08-26)

---

## D2 — Pay-as-you-go vs flat-rate pricing plans

**Ask**: "What is the expected monthly traffic volume and spike profile?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Pay-as-you-go | Pay only for usage; unlimited scale | Cost variability; DDoS/spike cost exposure | Steady or very large workloads with committed-use discounts |
| Flat-rate plan (Free / Pro $15 / Business $200 / Premium $1,000 per month) | Fixed monthly price, no overage, bundled WAF + DDoS + bot management + DNS | Feature gating by tier | Small/medium sites wanting predictable spend and bundled protection |

**Tier gates**: viewer mTLS = Premium; origin mTLS and bot controls = Business and above; AI dashboard = Business and above (per SKILL.md).
**Cost**: research states flat-rate absorbs spikes up to roughly 3x the monthly allowance with no overage. Lambda@Edge invocations are still billed at standard rates.
**Lock-in**: AWS-only; plans do not change the architecture.

**Architect instruction**: confirm required features against the tier gate before committing.

Source: [Flat-rate plans: new features (Networking blog, 2026-03)](https://aws.amazon.com/blogs/networking-and-content-delivery/amazon-cloudfront-flat-rate-pricing-plans-new-features-and-expanded-capabilities/) (accessed 2026-08-26). Source dated 2026-03; verify current tier pricing and gates before design commitment.

---

## D3 — Origin Shield: enable or not

**Ask**: "How geographically spread are viewers, and what type of origin is it?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| Origin Shield enabled (single Region) | Higher hit ratio, fewer origin requests, origin availability | Extra per-request charge; poor fit for low-cacheability dynamic content | Global viewers, just-in-time packaging/live video, on-prem or bandwidth-limited origins, multi-CDN |
| No Origin Shield (default regional edge cache) | No extra cost | Duplicate origin requests across regional edge caches | Low traffic or single-Region viewer base |

**Cost**: charged per request that traverses Origin Shield as an incremental layer; requests landing in the same Region as Origin Shield are skipped (no charge).
**Lock-in**: per-origin toggle, reversible.

**Architect instruction**: enable in the Region with lowest latency to the origin.

Source: [Origin Shield](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/origin-shield.html) (accessed 2026-08-26)

---

## D4 — Geo-restriction: CloudFront vs AWS WAF geo-match vs third-party

**Ask**: "Is the restriction country-level for the whole distribution, per path, or finer than country?"

| Option | Optimizes | Sacrifices | Best When |
|--------|-----------|------------|-----------|
| CloudFront geographic restrictions | Simple country allow/deny | Country-level only; whole-distribution scope; ~99.8% IP accuracy | Blanket country licensing rules |
| AWS WAF geo-match rule | Per-path/per-rule granularity, combinable with other rules | Requires WAF; still country-level | Mixed rules, partial-path restrictions |
| Third-party geolocation + signed URLs | City/postal/lat-long granularity, per-file | Custom app logic; extra vendor | Sub-country or per-file control |

**Note**: `/.well-known/pki-validation/` is exempt from geo-restriction so managed certificate validation succeeds; keep WAF/bot rules from blocking it.

Source: [Geographic restrictions](https://docs.aws.amazon.com/AmazonCloudFront/latest/DeveloperGuide/georestrictions.html) (accessed 2026-08-26)
