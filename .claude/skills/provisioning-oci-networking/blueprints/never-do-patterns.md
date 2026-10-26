### 🚫 Never Do

**Anti-Pattern**: Use `cidr_block` (singular) on VCN

```hcl
# 🚫 WRONG: cidr_block is DEPRECATED in OCI Provider v6.x+
resource "oci_core_vcn" "bad" {
  compartment_id = var.compartment_ocid
  cidr_block     = "10.0.0.0/16"  # DEPRECATED — will be removed
  display_name   = "vcn-bad"
}

# ✅ CORRECT: Use cidr_blocks (list) — supports multi-CIDR, forward-compatible
resource "oci_core_vcn" "good" {
  compartment_id = var.compartment_ocid
  cidr_blocks    = ["10.0.0.0/16"]  # LIST format
  display_name   = "vcn-good"
  dns_label      = "main"
}
```
**Why it is prohibited**: `cidr_block` does not support multi-CIDR and will be removed in future provider versions. Once migrated to `cidr_blocks`, reverting is impossible.
**Actual impact**: Terraform plan reports constant diff; future provider upgrades will fail.
**Introduced in**: Deprecated since OCI Provider v5.x, enforced in v6.x+
**Source**: [oci_core_vcn](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_vcn)

---

**Anti-Pattern**: Route rules using deprecated `cidr_block`

```hcl
# 🚫 WRONG: cidr_block in route_rules is DEPRECATED
resource "oci_core_route_table" "bad" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id

  route_rules {
    cidr_block        = "0.0.0.0/0"  # DEPRECATED — use destination
    network_entity_id = oci_core_internet_gateway.main.id
  }
}

# ✅ CORRECT: Use destination + destination_type (OCI Provider v6.x+)
resource "oci_core_route_table" "good" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id

  route_rules {
    network_entity_id = oci_core_internet_gateway.main.id
    destination       = "0.0.0.0/0"
    destination_type  = "CIDR_BLOCK"        # or "SERVICE_CIDR_BLOCK" for SGW
    description       = "Internet via IGW"
  }
}
```
**Why it is prohibited**: `cidr_block` in route_rules cannot express `SERVICE_CIDR_BLOCK` type needed for Service Gateway routes. Will be removed in future versions.
**Actual impact**: Terraform plan warnings; inability to route to Oracle Services via SGW.
**Source**: [oci_core_route_table](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_route_table)

---

**Anti-Pattern**: AD-specific subnets instead of regional

```hcl
# 🚫 WRONG: AD-specific subnet eliminates cross-AD HA
resource "oci_core_subnet" "bad" {
  compartment_id    = var.compartment_ocid
  vcn_id            = oci_core_vcn.main.id
  cidr_block        = "10.0.1.0/24"
  availability_domain = "Uocm:PHX-AD-1"  # Locks to single AD
}

# ✅ CORRECT: Regional subnet (omit availability_domain) — cross-AD HA
resource "oci_core_subnet" "good" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  cidr_block                 = "10.0.1.0/24"
  prohibit_internet_ingress  = true
  prohibit_public_ip_on_vnic = true
  # No availability_domain = regional
}
```
**Why it is prohibited**: AD-specific subnets restrict all resources to a single Availability Domain. Oracle explicitly recommends regional subnets.
**Actual impact**: Single AD failure takes down all resources in that subnet; no automatic cross-AD failover.
**Source**: [oci_core_subnet](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_subnet)

---

**Anti-Pattern**: Private subnet without `prohibit_internet_ingress`

```hcl
# 🚫 WRONG: Private subnet without internet ingress prohibition
resource "oci_core_subnet" "bad_private" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id
  cidr_block     = "10.0.1.0/24"
  display_name   = "private-but-not-really"
  # prohibit_internet_ingress defaults to false!
  # prohibit_public_ip_on_vnic defaults to false!
}

# ✅ CORRECT: Explicitly prohibit internet ingress and public IPs
resource "oci_core_subnet" "good_private" {
  compartment_id             = var.compartment_ocid
  vcn_id                     = oci_core_vcn.main.id
  cidr_block                 = "10.0.1.0/24"
  display_name               = "sn-private"
  prohibit_internet_ingress  = true   # MANDATORY
  prohibit_public_ip_on_vnic = true   # MANDATORY
}
```
**Why it is prohibited**: Without explicit prohibition, VNICs in "private" subnets can receive public IPs and internet traffic, completely negating the private classification.
**Actual impact**: Backend resources (Functions, databases) become internet-accessible.
**Source**: [oci_core_subnet](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_subnet)

---

**Anti-Pattern**: Service Gateway with only Object Storage

```hcl
# 🚫 WRONG: Only Object Storage — misses OCIR, Vault, Streaming, Logging
data "oci_core_services" "storage_only" {
  filter {
    name   = "name"
    values = ["OCI .* Object Storage"]
    regex  = true
  }
}

# ✅ CORRECT: "All Services" — covers OCIR, Vault, Streaming, Logging, Object Storage
data "oci_core_services" "all" {
  filter {
    name   = "name"
    values = ["All .* Services In Oracle Services Network"]
    regex  = true
  }
}
```
**Why it is prohibited**: OCI Functions require access to OCIR (Docker image pull), Vault KMS (secrets), Logging, and Streaming — none of which are covered by the Object Storage-only service.
**Actual impact**: Functions fail to start (cannot pull container images from OCIR), cannot access secrets from Vault, cannot send logs.
**Source**: [oci_core_service_gateway](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_service_gateway)

---

**Anti-Pattern**: Security List with `0.0.0.0/0` ingress all protocols

```hcl
# 🚫 WRONG: All protocols from all IPs — catastrophic blast radius
resource "oci_core_security_list" "bad" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id

  ingress_security_rules {
    source   = "0.0.0.0/0"
    protocol = "all"  # ALL protocols from ALL IPs
  }
}

# ✅ CORRECT: Restrict to TCP/443 (HTTPS) only
resource "oci_core_security_list" "good" {
  compartment_id = var.compartment_ocid
  vcn_id         = oci_core_vcn.main.id

  ingress_security_rules {
    source      = "0.0.0.0/0"
    protocol    = "6"  # TCP only
    stateless   = false

    tcp_options {
      min = 443
      max = 443
    }
  }
}
```
**Why it is prohibited**: Exposes every service on every port to the entire internet. Violates least-privilege principle.
**Actual impact**: Any service on any port becomes internet-accessible; catastrophic blast radius in case of exploit.
**Source**: [oci_core_security_list](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_security_list)

---

**Anti-Pattern**: Stateless NSG rules without matching pair

```hcl
# 🚫 WRONG: Stateless ingress WITHOUT matching egress rule
resource "oci_core_network_security_group_security_rule" "bad_stateless" {
  network_security_group_id = oci_core_network_security_group.functions.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = "0.0.0.0/0"
  source_type               = "CIDR_BLOCK"
  stateless                 = true  # Stateless requires explicit return rule
  # Missing: egress rule for return traffic!
}

# ✅ CORRECT: Use stateful rules (default) — return traffic handled automatically
resource "oci_core_network_security_group_security_rule" "good_stateful" {
  network_security_group_id = oci_core_network_security_group.functions.id
  direction                 = "INGRESS"
  protocol                  = "6"
  source                    = oci_core_network_security_group.apigw.id
  source_type               = "NETWORK_SECURITY_GROUP"
  stateless                 = false  # Stateful — return traffic automatic
}
```
**Why it is prohibited**: Stateless rules require explicit matching pairs (ingress + egress). Omitting the return rule silently drops response traffic.
**Actual impact**: Connections establish but responses are dropped; intermittent timeouts.
**Source**: [oci_core_network_security_group_security_rule](https://registry.terraform.io/providers/oracle/oci/latest/docs/resources/core_network_security_group_security_rule)

---

