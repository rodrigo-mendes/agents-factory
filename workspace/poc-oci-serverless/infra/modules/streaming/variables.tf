variable "compartment_ocid" {
  type        = string
  description = "OCID do compartment onde o Stream Pool e o Stream são criados"

  validation {
    condition     = can(regex("^ocid1\\.compartment\\.", var.compartment_ocid))
    error_message = "compartment_ocid deve ser um OCID válido (ocid1.compartment.*)."
  }
}

variable "subnet_id" {
  type        = string
  description = "DEPRECADO/NÃO-USADO: o pool agora é público (sem private endpoint). Mantido opcional para compatibilidade de chamada; pode ser null."
  default     = null

  validation {
    condition     = var.subnet_id == null || can(regex("^ocid1\\.subnet\\.", var.subnet_id))
    error_message = "subnet_id deve ser null ou um OCID válido (ocid1.subnet.*)."
  }
}

variable "nsg_ids" {
  type        = list(string)
  description = "DEPRECADO/NÃO-USADO: o pool agora é público (sem private endpoint). Mantido opcional para compatibilidade de chamada."
  default     = []
}

variable "kms_key_id" {
  type        = string
  description = "OCID da KMS Key (CMEK) para criptografar o Stream Pool. Vazio = chave gerenciada pela Oracle."
  default     = ""

  validation {
    condition     = var.kms_key_id == "" || can(regex("^ocid1\\.key\\.", var.kms_key_id))
    error_message = "kms_key_id deve ser vazio ou um OCID válido de KMS key (ocid1.key.*)."
  }
}

variable "stream_name" {
  type        = string
  description = "Nome do Stream (topic) principal de eventos"
  default     = "event-stream"

  validation {
    condition     = length(var.stream_name) > 0 && length(var.stream_name) <= 192
    error_message = "stream_name deve ser não-vazio e no máximo 192 caracteres."
  }
}

variable "partitions" {
  type        = number
  description = <<-EOT
    Número de partições do Stream. IMUTÁVEL após criação — o provider marca
    `# forces replacement` e um apply destrói/recria o stream com PERDA de todas as
    mensagens em buffer e RESET dos cursores dos connectors SCH. O recurso tem
    lifecycle.prevent_destroy = true, então alterar este valor exige remover a
    proteção e planejar a migração (novo stream + migrar consumers) explicitamente.
    Dimensionar p/ o pico de throughput (1 MB/s write, 2 MB/s read por partição).
  EOT
  default     = 3

  validation {
    condition     = var.partitions >= 1 && var.partitions <= 50
    error_message = "partitions deve ser entre 1 e 50."
  }
}

variable "retention_in_hours" {
  type        = number
  description = <<-EOT
    Retenção das mensagens em horas (24–168, máx 7 dias). Read-only/IMUTÁVEL após
    criação — não pode ser alterado in-place; mudar o valor força destroy/recreate
    do stream (mesma perda de dados/cursores que `partitions`). Com
    lifecycle.prevent_destroy = true, uma mudança exige migração planejada
    (novo stream com a retenção desejada + migrar consumers).
  EOT
  default     = 168

  validation {
    condition     = var.retention_in_hours >= 24 && var.retention_in_hours <= 168
    error_message = "retention_in_hours deve ser entre 24 e 168 (máx 7 dias)."
  }
}

variable "project_name" {
  type        = string
  description = "Nome do projeto (usado no naming dos recursos)"
}

variable "environment" {
  type        = string
  description = "Nome do ambiente (dev, staging, prod)"
}

variable "tags" {
  type        = map(string)
  description = "Freeform tags aplicadas ao Stream Pool e ao Stream"
  default     = {}
}
