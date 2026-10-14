---
description: 'Provision OCI Streaming resources (Stream Pool + Streams + Connect Harness) with Terraform'
agent: oci-terraform
argument-hint: 'Stream name, partitions, retention period'
---

# Add Streaming

**Skill**: `provisioning-oci-streaming`

## What this does

Provisions OCI Streaming resources (Stream Pools, Streams, Connect Harness) with Terraform for Kafka-compatible event streaming.

## Required information

1. **Stream name**: Name for the stream
2. **Stream pool**: Use existing pool or create new?
3. **Partitions**: Number of partitions (affects throughput and ordering)
4. **Retention (hours)**: How long to retain messages? (24-168 hours)
5. **Encryption**: Use custom encryption key from Vault?
6. **Connect Harness**: Need Kafka Connect integration?
7. **Compartment**: Target compartment OCID

## What will be generated

- `oci_streaming_stream_pool` resource (if new pool)
- `oci_streaming_stream` with partition and retention config
- `oci_streaming_connect_harness` (if Kafka Connect needed)
- Custom encryption key reference (if Vault integration)
- Variables with validation blocks
- Outputs for stream OCID and messages endpoint
