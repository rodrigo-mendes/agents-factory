# Evaluation Scenarios — designing-oci-networking

## Scenario 1: Canonical — Private Subnet Serverless API Topology

```json
{
  "skills": ["designing-oci-networking"],
  "query": "Design a VCN for an OCI serverless API: API Gateway exposed to the internet, Functions in a private subnet, Functions need access to OCI Vault and Object Storage but not to the internet directly.",
  "expected_behavior": [
    "Creates two regional subnets: public (API Gateway) and private (Functions) — NOT AD-specific",
    "Attaches Internet Gateway to the public subnet route table (0.0.0.0/0 → IGW)",
    "Attaches NAT Gateway and Service Gateway to the private subnet route table",
    "Routes OCI service CIDR (all-<region>-services-in-oracle-services-network) to Service Gateway — free, keeps traffic on OCI backbone",
    "Sets prohibit_public_ip_on_vnic = true on the private subnet",
    "Creates NSG for API Gateway (ingress 443 from 0.0.0.0/0) and NSG for Functions (ingress from API Gateway NSG OCID only)",
    "Does NOT use Security Lists as primary mechanism (NSGs are the primary firewall)"
  ]
}
```

## Scenario 2: Edge Case — NSG Rule Limit Approaching

```json
{
  "skills": ["designing-oci-networking"],
  "query": "My Functions NSG already has 100 rules and I need to add 30 more ingress rules for different microservices. What are my options?",
  "expected_behavior": [
    "Identifies the hard limit: 120 rules per NSG (ingress + egress combined, not per direction)",
    "Calculates that adding 30 more would exceed the limit (100 + 30 = 130 > 120)",
    "Proposes NSG splitting: create a second NSG for the additional microservices, attach both to the Functions VNIC (limit: 5 NSGs per VNIC)",
    "Recommends refactoring to use NSG-to-NSG source references (inter-NSG rules) to reduce rule count where services share the same source group",
    "Flags if the microservice count growth suggests a Hub-Spoke DRG v2 topology review is warranted",
    "Does NOT recommend using Security Lists as a workaround that bypasses NSG micro-segmentation"
  ]
}
```

## Scenario 3: Edge Case — Missing Service Gateway Causes OCIR Pull Failure

```json
{
  "skills": ["designing-oci-networking"],
  "query": "My Functions in a private subnet fail to deploy with 'image pull failed' errors. The NAT Gateway exists and Functions can reach external APIs. What network issue should I check?",
  "expected_behavior": [
    "Identifies OCIR (OCI Container Registry) as an OCI service reachable via Service Gateway — not NAT",
    "Checks whether Service Gateway exists in the VCN (should be exactly 1 per VCN)",
    "Verifies the private route table has a route for the OCI services CIDR pointing to the Service Gateway",
    "Checks NSG egress rules allow traffic to the service CIDR label (not just 0.0.0.0/0 via NAT)",
    "Runs gateway presence verification: oci network service-gateway list --compartment-id <ocid> --vcn-id <vcn-ocid>",
    "Does NOT recommend opening NAT egress specifically to OCIR endpoints as a workaround"
  ]
}
```

## Scenario 4: Ask-First Decision — NSG vs Security List Selection

```json
{
  "skills": ["designing-oci-networking"],
  "query": "Should I use NSGs or Security Lists for my VCN? Someone on the team says Security Lists are simpler.",
  "expected_behavior": [
    "Recommends NSGs as the primary security mechanism per OCI Best Practices 2024",
    "Explains the key advantage: NSG rules can reference other NSGs as sources/destinations (not just CIDRs), enabling micro-segmentation without tracking IP ranges",
    "Notes that NSGs and Security Lists use UNION logic — most permissive rule wins when both apply",
    "Warns that combining both creates complex rule evaluation that is difficult to audit",
    "Identifies the valid exception: Security Lists may be needed for legacy resources or services that do not support NSG attachment",
    "Does NOT accept 'Security Lists are simpler' as sufficient justification to skip NSGs in a new architecture"
  ]
}
```

## Scenario 5: Misuse Case — Private Subnet Route to Internet Gateway

```json
{
  "skills": ["designing-oci-networking"],
  "query": "I want my Functions in the private subnet to have full internet access for dependency downloads. Can I just add a route from the private subnet to the Internet Gateway?",
  "expected_behavior": [
    "Blocks this pattern: routing a private subnet to the Internet Gateway is a CRITICAL Never Do anti-pattern",
    "Explains that the Internet Gateway requires a public IP on the VNIC — Functions in a private subnet have no public IP so the route is non-functional AND misleadingly permissive",
    "Correct alternative for internet egress: NAT Gateway (unidirectional, no public IP required)",
    "For OCI services (OCIR, Vault, Object Storage): Service Gateway is free and preferred over NAT",
    "Runs detection check: oci network route-table get --rt-id <private-rt-ocid> to confirm no IGW route exists",
    "Does NOT add the IGW route and advise the user to 'try it and see'"
  ]
}
```
