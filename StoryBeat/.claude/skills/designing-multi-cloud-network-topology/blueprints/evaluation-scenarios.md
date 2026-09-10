# Evaluation Scenarios — designing-multi-cloud-network-topology

Skill under test: `designing-multi-cloud-network-topology`
Research source: `research_cloud_Multi_Cloud_Networking_Hub_Spoke_vs_Mesh_2024.md` (2026-08-28)

---

## Scenario 1 — Canonical: Enterprise hybrid network topology selection

```json
{
  "skills": ["designing-multi-cloud-network-topology"],
  "query": "We are building a hybrid enterprise network on AWS with 30 workload VPCs and an on-premises data center connected via Direct Connect. We need centralized egress inspection. Which topology and which AWS service should we use?",
  "expected_behavior": [
    "Recommends hub-spoke topology with AWS Transit Gateway as the transit hub",
    "States that Direct Connect gateway attaches to the Transit Gateway as the on-prem connectivity point",
    "Explains that centralized egress inspection is deployed at the hub (AWS Network Firewall in hub VPC)",
    "Notes hub-spoke scales as O(n) attachments vs O(n²) for full mesh",
    "Does NOT recommend VPC Peering as the primary topology for 30 VPCs"
  ]
}
```

---

## Scenario 2 — Canonical: Cross-provider hub service identification

```json
{
  "skills": ["designing-multi-cloud-network-topology"],
  "query": "What is the exact managed hub-spoke transit service name for each of AWS, Azure, and Google Cloud?",
  "expected_behavior": [
    "Names AWS Transit Gateway as the AWS hub service",
    "Names Azure Virtual WAN (virtual hub) as the Azure hub service",
    "Names GCP Network Connectivity Center (NCC) as the Google Cloud hub service",
    "Does not substitute generic terms like 'transit VPC' or 'hub VNet'",
    "Applies 🟡 Medium Confidence label to the cross-provider comparison"
  ]
}
```

---

## Scenario 3 — Anti-pattern trap: Non-transitive peering assumption

```json
{
  "skills": ["designing-multi-cloud-network-topology"],
  "query": "I have two spoke VPCs on AWS, each peered to a central hub VPC using AWS VPC Peering. Why can't spoke-A reach spoke-B?",
  "expected_behavior": [
    "Correctly identifies the cause: AWS VPC Peering is non-transitive",
    "Explains that A↔hub and hub↔B peerings do not yield A↔B connectivity",
    "Recommends migrating to AWS Transit Gateway for transitive spoke-to-spoke routing",
    "Notes the same non-transitivity applies to Azure VNet Peering and GCP VPC Network Peering",
    "Does NOT suggest any workaround that leaves the peering-only architecture intact"
  ]
}
```

---

## Scenario 4 — Edge case: Full mesh proposal at enterprise scale

```json
{
  "skills": ["designing-multi-cloud-network-topology"],
  "query": "Our team wants to avoid hub costs by using a full mesh of Azure VNet Peerings across 50 VNets. Is this viable?",
  "expected_behavior": [
    "Calculates or states the O(n²) peering count: 50×49/2 = 1,225 VNet peerings",
    "Identifies that this is the 🚫 Never Do 'full mesh at enterprise scale' anti-pattern",
    "Recommends Azure Virtual WAN as the correct alternative with 50 spoke attachments",
    "Notes that selective VNet Peering shortcuts can be added for specific high-throughput pairs",
    "Flags the Azure VWAN spoke ceiling (~500–600) as requiring verification per subscription"
  ]
}
```

---

## Scenario 5 — Capacity / constraint: GCP NCC spoke limit

```json
{
  "skills": ["designing-multi-cloud-network-topology"],
  "query": "We are planning a GCP Network Connectivity Center hub with 300 VPC spokes. Will this work?",
  "expected_behavior": [
    "States the GCP NCC quota: 250 active VPC spokes per hub (1,000 total including inactive)",
    "Flags that 300 active spokes exceeds the 250 active-spoke limit",
    "Recommends requesting a quota increase for per-project spoke count or splitting into multiple regional hubs",
    "Cites the NCC quotas source with 2026-08-28 access date",
    "Does not confuse NCC with plain GCP VPC Network Peering"
  ]
}
```
