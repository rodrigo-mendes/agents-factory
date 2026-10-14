output "log_group_id" {
  value       = var.enable_logging ? oci_logging_log_group.this[0].id : null
  description = "OCID do Log Group"
}

output "notification_topic_id" {
  value       = var.enable_monitoring_alarms ? oci_ons_notification_topic.alerts[0].id : null
  description = "OCID do Notification Topic para alarmes"
}

output "alarm_subscription_id" {
  value       = length(oci_ons_subscription.alarm_email) > 0 ? oci_ons_subscription.alarm_email[0].id : null
  description = "OCID da subscription de email do tópico de alarmes (null se não configurada)"
}
