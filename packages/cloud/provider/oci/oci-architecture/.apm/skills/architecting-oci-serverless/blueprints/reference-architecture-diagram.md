# Reference Architecture Diagram

ASCII topology of a production OCI serverless backend: tenancy → compartment → VCN with public subnet (API Gateway + Internet Gateway) and private subnet (OCI Functions + Service/NAT gateways) → downstream OCI services.

```
┌─────────────────────────────────────────────────────────────┐
│                    OCI TENANCY                               │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Compartment: serverless-prod                 │  │
│  │                                                       │  │
│  │  ┌─── VCN (10.0.0.0/16) ────────────────────────┐   │  │
│  │  │                                                │   │  │
│  │  │  ┌── Public Subnet (10.0.0.0/24) ──────────┐ │   │  │
│  │  │  │  API Gateway ←── Internet Gateway        │ │   │  │
│  │  │  │  (rate limit, JWT, CORS)                 │ │   │  │
│  │  │  └──────────────┬───────────────────────────┘ │   │  │
│  │  │                 │ (VCN internal)               │   │  │
│  │  │  ┌── Private Subnet (10.0.1.0/24) ─────────┐ │   │  │
│  │  │  │  OCI Functions (Application)             │ │   │  │
│  │  │  │  ├── func-hello                          │ │   │  │
│  │  │  │  ├── func-orders                         │ │   │  │
│  │  │  │  └── func-users                          │ │   │  │
│  │  │  │       │                                  │ │   │  │
│  │  │  │       ├─→ Service GW → OCI Vault         │ │   │  │
│  │  │  │       ├─→ Service GW → Autonomous DB     │ │   │  │
│  │  │  │       ├─→ Service GW → Object Storage    │ │   │  │
│  │  │  │       └─→ NAT GW → External APIs        │ │   │  │
│  │  │  └──────────────────────────────────────────┘ │   │  │
│  │  └────────────────────────────────────────────────┘   │  │
│  │                                                       │  │
│  │  IAM: Dynamic Groups + Scoped Policies               │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key design decisions shown**:
- API Gateway is the sole public-facing entry point (public subnet)
- Functions are isolated in private subnet — no public IPs
- OCI services reached via Service Gateway (stays on Oracle backbone, no NAT cost)
- External APIs reached via NAT Gateway
- IAM enforced at compartment boundary via Dynamic Groups + scoped policies
