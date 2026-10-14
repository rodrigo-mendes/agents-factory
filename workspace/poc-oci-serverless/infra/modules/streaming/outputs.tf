output "stream_id" {
  description = "OCID do Stream event-stream (usado pelo producer para PutMessages e pelos Service Connectors como source)"
  value       = oci_streaming_stream.event_stream.id
}

output "stream_pool_id" {
  description = "OCID do Stream Pool (público)"
  value       = oci_streaming_stream_pool.this.id
}

output "messages_endpoint" {
  description = "Endpoint de mensagens público do Stream (usado pelo producer como STREAM_MESSAGES_ENDPOINT; alcançável via NAT egress)"
  value       = oci_streaming_stream.event_stream.messages_endpoint
}

output "stream_name" {
  description = "Nome do Stream (topic)"
  value       = oci_streaming_stream.event_stream.name
}
