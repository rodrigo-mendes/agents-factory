# Quick Reference

## Memory → CPU Mapping

| Memory | CPU Fraction |
|--------|-------------|
| 128 MB | 1/8 CPU |
| 256 MB | 1/4 CPU |
| 512 MB | 1/2 CPU |
| 1024 MB | 3/4 CPU |
| 2048 MB | 1 CPU |

## Free Tier (per tenancy/month)

- 2 million invocations
- 400,000 GB-seconds
- API Gateway: 1M calls/month (Always Free)

## Service Equivalence (multi-cloud context)

| OCI | AWS | Azure | GCP |
|-----|-----|-------|-----|
| OCI Functions | Lambda | Azure Functions | Cloud Functions |
| API Gateway | API Gateway | API Management | Apigee |
| Dynamic Groups + Resource Principal | IAM Roles + STS | Managed Identity | Workload Identity |
| OCI Vault | Secrets Manager | Key Vault | Secret Manager |
| OCI Events | EventBridge | Event Grid | Eventarc |

## Essential OCI CLI Commands

```bash
# List functions in an application
oci fn function list --application-id <APP_OCID> --all

# Get function details
oci fn function get --function-id <FN_OCID>

# Invoke function (testing)
oci fn function invoke --function-id <FN_OCID> --body '{"key":"value"}' --file -

# Check application tracing
oci fn application get --application-id <APP_OCID> --query 'data."trace-config"'

# List API Gateway deployments
oci apigateway deployment list --compartment-id <COMP_OCID> --all

# Get deployment routes
oci api-gateway deployment get --deployment-id <deployment_ocid> | jq '.data.specification.routes'

# List Dynamic Groups
oci iam dynamic-group list --compartment-id <tenancy_ocid>

# List IAM Policies
oci iam policy list --compartment-id <compartment_ocid>

# Check Function logs
oci logging search --search-query 'search "<log_group_ocid>" | sort by datetime desc' --time-start <ISO8601> --time-end <ISO8601>
```

## Skill Cross-References

| Need | Use Skill |
|------|-----------|
| Terraform: Functions Application + Function | `provisioning-oci-functions` |
| Terraform: API Gateway + Deployment + Routes | `provisioning-oci-api-gateway` |
| Terraform: Dynamic Groups + IAM Policies | `provisioning-oci-iam` |
| Terraform: VCN + Subnets + NSGs + Gateways | `provisioning-oci-networking` |
| Terraform: Functions + API Gateway + IAM integrated | `provisioning-oci-serverless-stack` |
| Terraform: Events Rules for function triggers | `provisioning-oci-events` |
| Terraform: Streaming for async patterns | `provisioning-oci-streaming` |
| API Gateway architecture and design decisions | `designing-oci-api-gateway` |
| Network architecture and design decisions | `designing-oci-networking` |
| Vault security architecture | `designing-oci-vault-security` |
| Java: Function development with FDK | `developing-oci-functions-java` |
| Java: API Gateway typed events | `implementing-oci-functions-events` |
| Java: Object Storage integration | `integrating-oci-functions-objectstorage` |
| Java: REST API invocation | `invoking-rest-apis-from-oci-functions` |
| Java: Event publishing (Streaming, Notifications) | `publishing-events-from-oci-functions` |
