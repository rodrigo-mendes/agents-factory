# Phase 2 — User Interview (question script)

### Phase 2: User Interview (REQUIRED)

Before planning instruction files, ask the user these questions to calibrate the output. Present ALL questions at once, grouped by category.

#### 2.1 — Project Structure Questions

```
📁 PROJECT STRUCTURE

Q1: How is your Terraform project organized?
   a) Monorepo — all infrastructure in one repository
   b) Polyrepo — separate repos per service/environment
   c) Hybrid — shared modules repo + deployment repos
   d) Not decided yet — recommend best option for my context

Q2: How do you separate environments (dev/staging/prod)?
   a) Directory per environment (environments/dev/, environments/prod/)
   b) Terraform workspaces
   c) Terragrunt with hierarchy
   d) Separate repos per environment
   e) Not decided yet — recommend based on team size

Q3: How do you organize files within a stack/module?
   a) Single main.tf (small stacks)
   b) Split by purpose (main.tf, variables.tf, outputs.tf, providers.tf)
   c) Split by resource type (network.tf, compute.tf, iam.tf, storage.tf)
   d) Follow whatever the research recommends
```

#### 2.2 — Module Strategy Questions

```
📦 MODULE DESIGN

Q4: What is your module strategy?
   a) Resource modules — thin wrappers (1-3 resources per module)
   b) Infrastructure modules — composed stacks (networking, compute layers)
   c) Both — resource modules composed into infrastructure modules
   d) No modules yet — inline resources only
   e) Not decided — recommend based on project scale

Q5: Where do you source modules from?
   a) Local paths only (./modules/)
   b) Private Git repos with version tags
   c) Terraform Registry (public or private)
   d) Mix of sources
   e) Not decided yet

Q6: How strict is your module versioning?
   a) Exact pinning (version = "1.2.3")
   b) Pessimistic constraint (version = "~> 1.2")
   c) Range constraint (version = ">= 1.0, < 2.0")
   d) No versioning yet
```

#### 2.3 — State & Backend Questions

```
🔒 STATE MANAGEMENT

Q7: What backend do you use for Terraform state?
   a) S3 + DynamoDB (AWS)
   b) OCI Object Storage
   c) Azure Blob Storage
   d) GCS (Google Cloud Storage)
   e) Terraform Cloud / Enterprise
   f) Local state (development only)
   g) Not decided yet — recommend for {{CLOUD_PROVIDER}}

Q8: How do you isolate state files?
   a) One state per environment (dev.tfstate, prod.tfstate)
   b) One state per component × environment
   c) One state per service/domain
   d) Monolithic state (everything in one)
   e) Not decided yet
```

#### 2.4 — CI/CD & Testing Questions

```
🔄 CI/CD & TESTING

Q9: What CI/CD platform do you use for Terraform?
   a) GitHub Actions
   b) GitLab CI
   c) Terraform Cloud / Enterprise
   d) Atlantis
   e) Spacelift / env0
   f) Jenkins
   g) None yet — recommend one
   h) Other: ___

Q10: What testing tools do you use or want to adopt?
   a) terraform validate + terraform fmt only
   b) tflint
   c) tfsec / Trivy
   d) Checkov
   e) OPA / Conftest
   f) terraform test (native)
   g) Terratest (Go)
   h) None yet — recommend a testing stack
   (Select all that apply)

Q11: Do you enforce policy-as-code?
   a) Yes — OPA/Rego
   b) Yes — Sentinel (Terraform Cloud)
   c) Yes — Checkov custom policies
   d) No — but I want to start
   e) No — not needed for now
```

#### 2.5 — Team & Governance Questions

```
👥 TEAM & GOVERNANCE

Q12: What is your team size for Terraform work?
   a) Solo developer
   b) Small team (2-5)
   c) Medium team (5-15)
   d) Large / platform team (15+)

Q13: Do you need compliance enforcement?
   a) Yes — specific standards (SOC2, HIPAA, PCI-DSS, LGPD)
   b) Yes — internal policies only
   c) No — general best practices are enough

Q14: Do you use terraform-docs for module documentation?
   a) Yes — auto-generated README.md
   b) No — manual documentation
   c) No documentation yet — I want to start
```

#### 2.6 — Existing Skills & Integrations

```
🔗 EXISTING ECOSYSTEM

Q15: Do you have existing Terraform skills in .claude/skills/?
   a) Yes — I have provider-specific skills (list them)
   b) No — this will be my first Terraform instructions
   c) I have the research file but no skills yet

Q16: Do you want the instructions to route to specialized prompts?
   a) Yes — integrate with existing prompts in .claude/skills/
   b) No — standalone instructions are enough
   c) Yes — but I need to create the prompts first
```

---
