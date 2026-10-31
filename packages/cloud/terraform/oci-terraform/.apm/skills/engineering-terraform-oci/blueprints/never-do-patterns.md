# 🚫 Never Do — Terraform OCI Engineering Best Practices

## 1. Hardcode OCI API Keys in `.tf` Files (CRITICAL)

```hcl
# ❌ NEVER — credentials in version control
provider "oci" {
  user_ocid    = "ocid1.user.oc1..aaaaaaXXXXXXXXXX"
  private_key  = file("~/.oci/oci_api_key.pem")
  fingerprint  = "ab:cd:ef:12:34:56:78:90"
  tenancy_ocid = "ocid1.tenancy.oc1..aaaaaaaaXXXXXXXX"
}
```

```hcl
# ✅ DO — InstancePrincipal for OCI Compute runners (no secrets stored)
provider "oci" {
  region = var.region
  auth   = "InstancePrincipal"
}
# For GitHub Actions: inject via OCI_CLI_USER, OCI_CLI_KEY_CONTENT environment secrets
```

**Impact**: Credential compromise, unauthorized OCI resource access | **Severity**: CRITICAL

---

## 2. Local Backend for Team Environments (CRITICAL)

```hcl
# ❌ NEVER — in a shared or team environment
terraform {
  # No backend block = local terraform.tfstate
  # Or explicitly:
  backend "local" {
    path = "terraform.tfstate"
  }
}
```

```hcl
# ✅ DO — OCI Object Storage with built-in locking
terraform {
  backend "oci" {
    bucket = "tf-state-dev"
    key    = "app-one/terraform.tfstate"
    region = "us-ashburn-1"
  }
}
```

**Impact**: No locking → state corruption from concurrent applies; state lost if local disk fails | **Severity**: CRITICAL

---

## 3. Commit `*.tfstate` Files to VCS (CRITICAL)

```bash
# ❌ NEVER
git add terraform.tfstate    # contains passwords, private IPs, resource secrets
git commit -m "save state"
```

```bash
# ✅ DO — remote backend + .gitignore
echo "*.tfstate" >> .gitignore
echo "*.tfstate.*" >> .gitignore
# State lives exclusively in OCI Object Storage
```

**Impact**: Secret exposure (DB passwords, private keys, resource details in state); VCS has no concurrent-write protection | **Severity**: CRITICAL

---

## 4. Apply Without Reviewing `terraform plan` (CRITICAL)

```bash
# ❌ NEVER — blind apply
terraform apply -auto-approve
# Or: apply without -out (generates a new implicit plan — still review it)
terraform apply
```

```bash
# ✅ DO — explicit plan → review → apply from saved file
terraform plan -out=tfplan -var-file="terraform.tfvars"
terraform show -no-color tfplan | grep -E "^(Plan:|  [+~-])"   # review summary
# Look for: "will be destroyed", "forces replacement"
terraform apply tfplan
```

**Impact**: Silent destructive changes (forced replacements, unexpected destroys) reach production without human review | **Severity**: CRITICAL

---

## 5. `terraform force-unlock` Without Confirming No Active Run (HIGH)

```bash
# ❌ NEVER — blindly break the lock
terraform force-unlock <LOCK_ID>
# May interrupt a legitimate in-progress apply by a teammate or CI job
```

```bash
# ✅ DO — verify before unlocking
# 1. Check CI/CD system for active Terraform runs on this workspace
# 2. Check with teammates if they have an apply in progress
# 3. Confirm the lock is stale (abandoned job, crashed runner)
# Only then:
terraform force-unlock <LOCK_ID>
```

**Impact**: State corruption if two applies run concurrently after forced unlock | **Severity**: HIGH

---

## 6. `terraform taint` — Removed Command (HIGH)

```bash
# ❌ NEVER — command removed in Terraform v1.x
terraform taint oci_core_instance.web
# Error: "terraform taint" was removed in Terraform v1.0.
# Use "terraform apply -replace" instead, to force replacement of a particular resource instance.
```

```bash
# ✅ DO — use -replace flag
terraform apply -replace="oci_core_instance.web"
# Or for multiple resources:
terraform apply \
  -replace="oci_core_instance.web" \
  -replace="oci_core_instance.worker"
```

**Impact**: CI/CD pipeline failure; confusing error message for engineers expecting the old behavior | **Severity**: HIGH

---

## 7. Branch-per-Environment Strategy (HIGH)

```bash
# ❌ NEVER — environments as Git branches
git checkout dev  && terraform apply   # dev environment
git checkout prod && terraform apply   # prod environment
# State between branches diverges; merges conflict; config drift is invisible
```

```
# ✅ DO — single main branch, directory-per-environment
main branch:
  dev/  → terraform apply   (isolated dev state)
  prod/ → terraform apply   (isolated prod state, after PR approval + plan review)
```

**Why**: Branch merges with diverged state produce destructive applies. Directory-per-environment enforces isolation through separate backend configs, not Git branching.

**Impact**: State diverges between branches; merges become destructive or impossible; configuration drift undetectable until an apply | **Severity**: HIGH

---

## 8. Apply a Stale Plan File (HIGH)

```bash
# ❌ NEVER — apply a plan generated from a different code version
git pull origin main       # code changed since tfplan was generated
terraform apply tfplan     # plan references old resource addresses / values
# Apply may create, destroy, or update resources based on outdated intent
```

```bash
# ✅ DO — always regenerate plan immediately before applying
terraform init
terraform plan -out=tfplan -var-file="terraform.tfvars"
# Review the fresh plan output
terraform apply tfplan
# The apply must happen in the same CI job/session that generated the plan
```

**Impact**: Resources created/destroyed/updated that don't match current code intent | **Severity**: HIGH
