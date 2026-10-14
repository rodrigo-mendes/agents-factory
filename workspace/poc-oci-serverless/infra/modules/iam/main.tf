# ==============================================================================
# Module: IAM
# ==============================================================================
# Dynamic Groups + Policies para Functions e API Gateway
# ==============================================================================

# ------------------------------------------------------------------------------
# Dynamic Groups
# ------------------------------------------------------------------------------

resource "oci_identity_dynamic_group" "functions" {
  compartment_id = var.tenancy_ocid
  name           = "dg-functions-${var.project_name}-${var.environment}"
  description    = "Dynamic group for Functions in ${var.compartment_name}"
  matching_rule  = "ALL {resource.type = 'fnfunc', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = var.tags
}

resource "oci_identity_dynamic_group" "api_gateway" {
  compartment_id = var.tenancy_ocid
  name           = "dg-apigw-${var.project_name}-${var.environment}"
  description    = "Dynamic group for API Gateways in ${var.compartment_name}"
  matching_rule  = "ALL {resource.type = 'ApiGateway', resource.compartment.id = '${var.compartment_ocid}'}"

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Policies
# ------------------------------------------------------------------------------

resource "oci_identity_policy" "faas_network" {
  compartment_id = var.tenancy_ocid
  name           = "policy-faas-network-${var.project_name}-${var.environment}"
  description    = "Permite FaaS service usar VCN"
  statements = [
    "Allow service FaaS to use virtual-network-family in compartment ${var.compartment_name}",
    "Allow service FaaS to read repos in tenancy",
  ]

  freeform_tags = var.tags
}

resource "oci_identity_policy" "apigw_invoke_functions" {
  compartment_id = var.compartment_ocid
  name           = "policy-apigw-invoke-${var.project_name}-${var.environment}"
  description    = "Permite API Gateway invocar Functions"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.api_gateway.name} to use fn-invocation in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

resource "oci_identity_policy" "functions_access_services" {
  compartment_id = var.compartment_ocid
  name           = "policy-functions-services-${var.project_name}-${var.environment}"
  description    = "Permite Functions acessar serviços OCI via Resource Principal"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read secret-bundles in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage objects in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage log-content in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use metrics in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Streaming (Pattern event-driven pub/sub) — PRODUCER apenas
# ------------------------------------------------------------------------------
# Skill: provisioning-oci-streaming + provisioning-oci-iam.
#
#  - Producer (DG functions): publica no stream via stream-push. Este statement
#    referencia SOMENTE a Dynamic Group (sem function_id) → NÃO cria ciclo.
#
# ⚠️ RELOCADO (quebra de ciclo): as 3 statements do serviceconnector
#    (STREAM_READ/STREAM_CONSUME + fn-function + fn-invocation) foram MOVIDAS para
#    o módulo dedicado `infra/modules/iam-sch` porque precisam escopar
#    target.stream.id e target.function.id (least-privilege). Escopá-las aqui
#    exigiria referenciar module.app_evt_consumer_*.function_id, o que criaria o
#    ciclo iam → app → iam (as apps já têm depends_on = [module.iam]) e quebraria
#    o `terraform validate`. O módulo iam-sch depende de streaming + apps e não é
#    referenciado por elas → DAG sem ciclo. Ver modules/iam-sch/main.tf.
resource "oci_identity_policy" "streaming" {
  compartment_id = var.compartment_ocid
  name           = "policy-streaming-${var.project_name}-${var.environment}"
  description    = "Producer (Functions DG) publica no stream via stream-push. Statements do Service Connector Hub estão em modules/iam-sch (least-privilege, quebra de ciclo)."
  statements = [
    # Producer (Functions DG) publica no stream
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to use stream-push in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Management Dashboards
# ------------------------------------------------------------------------------
# Permite gerenciar Management Dashboards + Saved Searches e ler as fontes de
# dados (metrics, apm-domains) que os dashboards consultam.
#
# NOTA: o import de dashboards é executado pela identidade que roda o Terraform
# (usuário via SecurityToken no ambiente dev), NÃO por uma dynamic group. O grupo
# de usuários do deployer deve receber estas permissões separadamente — este
# módulo não conhece o nome desse grupo. Concedemos aqui à dynamic group de
# Functions o acesso de LEITURA às fontes de dados (metrics/apm) para runtime;
# ajuste o subject para o grupo do deployer se o apply de dashboards for feito
# por outra identidade.
resource "oci_identity_policy" "management_dashboards" {
  compartment_id = var.compartment_ocid
  name           = "policy-dashboards-${var.project_name}-${var.environment}"
  description    = "Gerência de Management Dashboards/Saved Searches e leitura das fontes (metrics, apm-domains)"
  statements = [
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage management-dashboard in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to manage management-saved-search in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read metrics in compartment ${var.compartment_name}",
    "Allow dynamic-group ${oci_identity_dynamic_group.functions.name} to read apm-domains in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Management Dashboards — audiência de LEITURA (visualização)
# ------------------------------------------------------------------------------
# Management Dashboards não têm conceito de "público": a visibilidade é 100% IAM.
# Esta policy concede LEITURA dos dashboards + saved searches + fontes de dados
# (metrics, apm) a usuários humanos, para que enxerguem/rendam os dashboards.
# Habilite via var.dashboard_viewers_all_users (todos usuários da tenancy) e/ou
# var.dashboard_viewer_groups (grupos específicos). Se nenhum, a policy não é criada.
locals {
  dashboard_viewer_actions = [
    "read management-dashboard-family",
    "read metrics",
    "read apm-domains",
  ]

  dashboard_any_user_statements = var.dashboard_viewers_all_users ? [
    for a in local.dashboard_viewer_actions :
    "Allow any-user to ${a} in compartment ${var.compartment_name} where request.principal.type = 'user'"
  ] : []

  dashboard_group_statements = flatten([
    for g in var.dashboard_viewer_groups : [
      for a in local.dashboard_viewer_actions :
      "Allow group ${g} to ${a} in compartment ${var.compartment_name}"
    ]
  ])

  dashboard_viewer_statements = concat(
    local.dashboard_any_user_statements,
    local.dashboard_group_statements,
  )
}

resource "oci_identity_policy" "dashboard_viewers" {
  count          = length(local.dashboard_viewer_statements) > 0 ? 1 : 0
  compartment_id = var.compartment_ocid
  name           = "policy-dashboard-viewers-${var.project_name}-${var.environment}"
  description    = "Leitura de Management Dashboards/Saved Searches e fontes (metrics, apm) para a audiência de visualização"
  statements     = local.dashboard_viewer_statements

  freeform_tags = var.tags
}

# ------------------------------------------------------------------------------
# Read-only do compartment — grupo dedicado de visualização
# ------------------------------------------------------------------------------
# Grupo IAM (na tenancy) + membership dos usuários informados + policy que
# concede LEITURA de todos os recursos do compartment (read all-resources).
# Habilite via var.readonly_viewer_group_name; usuários via
# var.readonly_viewer_user_ids (OCIDs; o data source por name é inviável numa
# tenancy com milhares de usuários — filtro server-side não casa e o list estoura).
resource "oci_identity_group" "readonly_viewers" {
  count          = var.readonly_viewer_group_name != "" ? 1 : 0
  compartment_id = var.tenancy_ocid
  name           = var.readonly_viewer_group_name
  description    = "Read-only em todos os recursos do compartment ${var.compartment_name}"

  freeform_tags = var.tags
}

resource "oci_identity_user_group_membership" "readonly" {
  for_each = var.readonly_viewer_group_name != "" ? toset(var.readonly_viewer_user_ids) : []

  group_id = oci_identity_group.readonly_viewers[0].id
  user_id  = each.value
}

resource "oci_identity_policy" "readonly_viewers" {
  count          = var.readonly_viewer_group_name != "" ? 1 : 0
  compartment_id = var.compartment_ocid
  name           = "policy-readonly-${var.project_name}-${var.environment}"
  description    = "Leitura de todos os recursos do compartment para o grupo read-only"
  statements = [
    "Allow group ${var.readonly_viewer_group_name} to read all-resources in compartment ${var.compartment_name}",
  ]

  freeform_tags = var.tags
}
