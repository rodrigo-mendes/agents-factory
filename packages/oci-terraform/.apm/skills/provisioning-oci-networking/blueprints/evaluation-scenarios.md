# Evaluation Scenarios — provisioning-oci-networking

## Scenario 1: Canonical — Full Serverless VCN with NSGs

```json
{
  "skills": ["provisioning-oci-networking"],
  "query": "Create a Terraform networking module for OCI serverless with a VCN, public subnet for API Gateway, private subnet for Functions, Internet Gateway, NAT Gateway, Service Gateway, and NSGs.",
  "expected_behavior": [
    "Uses cidr_blocks (list) on oci_core_vcn, not deprecated cidr_block",
    "Creates regional subnets (omits availability_domain on both)",
    "Sets prohibit_internet_ingress = true on private subnet",
    "Creates all three gateways: IGW, NAT GW, SGW",
    "SGW filter uses 'All .* Services In Oracle Services Network' regex",
    "Public route table: 0.0.0.0/0 -> IGW",
    "Private route table: 0.0.0.0/0 -> NAT GW + SGW SERVICE_CIDR_BLOCK destination",
    "Creates two NSGs: apigw and functions with inter-NSG egress/ingress rules",
    "Outputs vcn_id, subnet_public_id, subnet_private_id, nsg_apigw_id, nsg_functions_id"
  ]
}
```

## Scenario 2: Edge Case — Missing Service Gateway Scope

```json
{
  "skills": ["provisioning-oci-networking"],
  "query": "My Functions can't pull container images from OCIR and can't write logs. The Service Gateway exists but uses the Object Storage service filter only.",
  "expected_behavior": [
    "Identifies root cause: SGW scoped to Object Storage only, not All Services",
    "Shows wrong pattern: filter name = 'OCI .* Object Storage'",
    "Shows correct pattern: filter name regex = 'All .* Services In Oracle Services Network'",
    "Explains that OCIR, Vault, Logging, Streaming all require 'All Services'",
    "Provides updated oci_core_service_gateway HCL with correct services data source",
    "Notes the route rule destination_type must be SERVICE_CIDR_BLOCK for SGW routes"
  ]
}
```

## Scenario 3: Edge Case — Missing IAM Policy for NSG-Gated Subnet

```json
{
  "skills": ["provisioning-oci-networking"],
  "query": "API Gateway gets 502 errors calling Functions. Both are deployed in the correct subnets and NSGs are configured. What networking issues should I check?",
  "expected_behavior": [
    "Checks NSG egress rule from APIGW NSG to Functions NSG on TCP port range (the Functions port)",
    "Checks NSG ingress rule on Functions NSG from APIGW NSG",
    "Notes that NSGs use inter-NSG references (source_type = NETWORK_SECURITY_GROUP), not CIDR",
    "Distinguishes networking issue from IAM policy issue (fn-invocation policy)",
    "Provides OCI CLI command to list NSG rules for diagnostic: oci network nsg rules list",
    "Does NOT suggest Security List 0.0.0.0/0 as workaround"
  ]
}
```

## Scenario 4: Misuse — AD-Specific Subnet Request

```json
{
  "skills": ["provisioning-oci-networking"],
  "query": "Create a subnet pinned to availability domain AD-1 for our Functions to ensure they run in the same AD as our compute instances.",
  "expected_behavior": [
    "Flags the request as an anti-pattern (AD-specific subnet eliminates cross-AD HA)",
    "Explains Oracle mandates regional subnets (omit availability_domain) for Functions",
    "Shows that regional subnets provide cross-AD redundancy automatically",
    "Offers alternative: tag-based co-location or compartment organization if grouping is the goal",
    "Does NOT generate an oci_core_subnet with availability_domain set"
  ]
}
```

## Scenario 5: Edge Case — CIDR Migration (cidr_block to cidr_blocks)

```json
{
  "skills": ["provisioning-oci-networking"],
  "query": "Our existing VCN was created with the deprecated cidr_block attribute. How do I migrate to cidr_blocks without destroying and recreating the VCN?",
  "expected_behavior": [
    "Identifies cidr_block -> cidr_blocks as the critical breaking change",
    "Explains that changing this attribute in-place causes Terraform to destroy/recreate the VCN",
    "Recommends using a moved block or terraform state mv for safe migration",
    "Notes DNS label is also immutable (change = destroy/recreate)",
    "Provides the correct cidr_blocks syntax: cidr_blocks = [var.vcn_cidr_block]",
    "Warns about downstream dependency chain: subnets, routes, NSGs all depend on VCN"
  ]
}
```
