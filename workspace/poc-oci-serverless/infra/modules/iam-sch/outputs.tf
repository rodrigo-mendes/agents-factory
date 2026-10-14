output "policy_streaming_sch_id" {
  value       = oci_identity_policy.streaming_sch.id
  description = "OCID da policy least-privilege do Service Connector Hub (STREAM_READ/STREAM_CONSUME em target.stream.id + fn-function/fn-invocation em target.function.id). Injetar em service_connector.iam_dependencies."
}

output "policy_streaming_sch_name" {
  value       = oci_identity_policy.streaming_sch.name
  description = "Nome da policy least-privilege do Service Connector Hub"
}
