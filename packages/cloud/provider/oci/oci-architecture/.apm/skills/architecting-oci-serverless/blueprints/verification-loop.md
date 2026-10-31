# Verification Loop

Run after every serverless environment configuration. All 7 checks must pass before declaring the environment production-ready.

## 1. Network Isolation

```bash
# Verify Functions subnet is private
oci fn application get --application-id <OCID> --query 'data."subnet-ids"'
# Exit code: 0 (success) | 1 (auth/network error)
oci network subnet get --subnet-id <SUBNET_OCID> --query 'data."prohibit-public-ip-on-vnic"'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: true
```

## 2. IAM Policies

```bash
# Verify no wildcard policies on function dynamic groups
oci iam policy list --compartment-id <TENANCY_OCID> --all \
# Exit code: 0 (success) | 1 (auth/network error)
  | grep -i "manage all-resources"
  # Exit code: 0 (match found) | 1 (no match)
# Expected: empty (no matches)

# Verify dynamic group matching rule
oci iam dynamic-group get --dynamic-group-id <OCID> \
# Exit code: 0 (success) | 1 (auth/network error)
  --query 'data."matching-rule"'
# Expected: "ALL {resource.type = 'fnfunc', resource.compartment.id = '...'}"
```

## 3. Function Configuration

```bash
# Verify all functions have explicit timeout and memory
oci fn function list --application-id <app_ocid> \
# Exit code: 0 (success) | 1 (auth/network error)
  | jq '.data[] | {name: .["display-name"], timeout: .["timeout-in-seconds"], memory: .["memory-in-mbs"]}'
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
# Flag any function with timeout=300 or null
```

## 4. Credential Scan

```bash
# Scan function configs for leaked secrets
oci fn function list --application-id <APP_OCID> --all \
# Exit code: 0 (success) | 1 (auth/network error)
  --query 'data[*].config' | grep -iE 'password|secret|key|token'
  # Exit code: 0 (match found) | 1 (no match)
# Expected: No matches for actual credential values (OCIDs are acceptable)
```

## 5. API Gateway Validation

```bash
# Verify deployment has rate limiting and auth
oci api-gateway deployment get --deployment-id <deployment_ocid> | \
  jq '.data.specification | {
  # Exit code: 0 (success) | 1 (parse error) | 5 (no output)
    rate_limiting: .request_policies.rate_limiting,
    auth: .request_policies.authentication.type,
    access_log: .logging_policies.access_log.is_enabled,
    execution_log: .logging_policies.execution_log.is_enabled
  }'
```

## 6. Observability

```bash
oci fn application get --application-id <OCID> --query 'data."trace-config"."is-enabled"'
# Exit code: 0 (success) | 1 (auth/network error)
# Expected: true
```

## 7. End-to-End Smoke Test

```bash
# Health check (anonymous)
curl -s -o /dev/null -w "%{http_code}" https://<apigw-hostname>/v1/health
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
# Expected: 200

# Authenticated endpoint without token (should fail)
curl -s -o /dev/null -w "%{http_code}" https://<apigw-hostname>/v1/items
# Exit code: 0 (success) | 1 (connection error) | 22 (HTTP error with -f)
# Expected: 401
```

## Troubleshooting

| Symptom | Root Cause | Fix |
|---------|-----------|-----|
| `502 Bad Gateway` | Missing IAM policy | Add `Allow dynamic-group <gw-dg> to use fn-invocation` |
| `404` on API GW | Path mismatch | Align deployment path-prefix + route path |
| `504 timeout` | Function timeout too short OR missing outbound connectivity | Increase timeout; check subnet route table |
| `FunctionInvokeError` | Image not in OCIR or not pullable | Add `Allow service FaaS to read repos in tenancy` |
| `404-NotAuthorizedOrNotFound` | Dynamic Group rule mismatch or IAM propagation | Fix matching rule; wait 60s for propagation |
