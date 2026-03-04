# Guía de Uso: Prompt Terraform para Creación de Skills

Este documento describe cómo usar el prompt `technical-framework-researcher-terraform.prompt.md` para investigar y crear skills de Terraform.

## Estructura Rápida

```bash
# Para crear un skill de Terraform + AWS RDS:
CLOUD_PROVIDER="AWS"
SERVICE_NAME="RDS PostgreSQL"
TERRAFORM_VERSION="1.7"
PROVIDER_VERSION="aws v5.x"
USE_MODULES="yes"
USE_WORKSPACES="yes"
INTEGRATION_PARTNERS_LIST="VPC, Security Groups, Secrets Manager, CloudWatch, IAM"
```

## Diferencias vs. Prompt Original

| Aspecto | Original | Terraform |
|---------|----------|-----------|
| **Enfoque** | Librerías/frameworks genéricos | Infrastructure as Code (IaC) |
| **State Management** | N/A | ✅ Backend config, locking, encryption |
| **Seguridad** | General | ✅ Secrets, IAM, VPC, encryption |
| **Módulos** | Yes/no | ✅ Estructura standard HCL |
| **CLI Validation** | lint, type check, tests | ✅ terraform fmt, validate, plan, apply |
| **Versiones** | Source version only | ✅ Terraform + Provider + Dependencies |
| **Guardrails** | 3-tier genérico | ✅ Específico para IaC (state corruption, drift) |
| **Anti-patrones** | Código | ✅ HCL + riesgos de infraestructura |

## Ejemplo: Crear Skill `terraform-aws-rds`

### Paso 1: Llenar Variables
```markdown
CLOUD_PROVIDER: AWS
SERVICE_NAME: RDS PostgreSQL
TERRAFORM_VERSION: 1.7
PROVIDER_VERSION: aws v5.45+
INTEGRATION_PARTNERS_LIST: VPC, Security Groups, Secrets Manager, Parameter Store, IAM, CloudWatch
```

### Paso 2: Ejecutar Investigación (con el prompt)
El prompt te guiará a:
- ✅ Buscar docs en Terraform Registry
- ✅ Validar patterns en AWS docs
- ✅ Documentar anti-patterns de seguridad
- ✅ Crear ejemplos HCL funcionales
- ✅ Incluir comandos CLI con outputs esperados

### Paso 3: Output → Skill
```bash
research_AWS_RDS_PostgreSQL_v5.45.md
  ↓
  ├─ SKILL.md (skill específico)
  ├─ SKILL.terraform.hcl (código ready-to-use)
  └─ README.md (documentación)
```

## Patrones Incluidos (vs. Original)

### Nuevos en Terraform

#### 1. **State Management** (único de IaC)
```yaml
Local Development:
  - Archivo: terraform.tfstate
  - Riesgo: Single point of failure
  
Production:
  - Backend: S3 + DynamoDB
  - Encryption: AES256
  - Locking: DynamoDB table
```

#### 2. **Module Architecture** (único de IaC)
```
modules/
├── vpc/
│   ├── main.tf (resources)
│   ├── variables.tf (inputs)
│   ├── outputs.tf (exports)
│   └── versions.tf (constraints)
```

#### 3. **Provider Credentials** (único de IaC)
```hcl
# Precedencia: env vars > config > IAM role
provider "aws" {
  assume_role { role_arn = "..." }  # Safer
}
```

#### 4. **Drift Detection** (único de IaC)
```bash
terraform plan  # Compara estado local vs actual
terraform refresh  # Actualiza estado desde AWS
terraform import  # Reconoce recursos manuales
```

## Diferencias Críticas

### Validación
- **Original**: `pytest`, `eslint`, type checkers
- **Terraform**: `terraform validate`, `terraform fmt`, `tfsec`, `checkov`

### Testing
- **Original**: Unit tests, mocks, coverage
- **Terraform**: Terratest, terraform test, compliance scanning

### Secrets
- **Original**: Environment variables, .env files
- **Terraform**: AWS Secrets Manager, Parameter Store, no hardcoding

### Seguridad
- **Original**: Code injection, data validation
- **Terraform**: State exposure, credential leaks, 0.0.0.0/0 rules, public buckets

## Checklist: ¿Cuándo Usar Este Prompt?

✅ **Usar este prompt si:**
- [ ] Necesitas code Terraform para AWS/GCP/Azure
- [ ] Requieres módulos reutilizables
- [ ] Necesitas seguridad + estado + drift management
- [ ] Quieres patterns de multi-ambiente

❌ **No usar si:**
- [ ] Solo necesitas librerías Python/Node.js
- [ ] No necesitas IaC (Infrastructure as Code)
- [ ] Buscas patrones de aplicación, no infraestructura

## Próximos Pasos

1. **Copia el prompt** a tu agent/workflow
2. **Rellena INPUT VARIABLES** para tu caso
3. **Ejecuta investigación** (prompts de research)
4. **Genera output** en formato markdown
5. **Convierte a SKILL.md** usando el template

## Estructura de Output del Skill

```markdown
# SKILL.md

## Metadata
Full_Name: "Terraform AWS RDS PostgreSQL"
Target_Service: "RDS"
Provider_Version: "aws v5.45+"
Terraform_Version: "1.7+"

## Mandatory Patterns
- [ ] Terraform block with backend
- [ ] Provider with assume_role
- [ ] Variable validation
- [ ] Output definitions
- [ ] Encryption at rest & in transit

## Anti-Patterns
- [ ] Hardcoded credentials
- [ ] No state encryption
- [ ] Public RDS instance
- [ ] No security group
- [ ] No backup enabled

## Integration Examples
- RDS ↔ VPC (private subnet, security group)
- RDS ↔ Secrets Manager (password rotation)
- RDS ↔ CloudWatch (monitoring)

## CLI Validation
```bash
terraform init
terraform validate
tfsec .
terraform plan -out=tfplan
terraform apply tfplan
```

## Code Example
[Complete, working main.tf with all best practices]
```

---

## Referencia Rápida: Variables del Prompt

| Variable | Ejemplo | Impacto |
|----------|---------|--------|
| `CLOUD_PROVIDER` | AWS, Google Cloud, Azure | Selecciona provider y docs |
| `SERVICE_NAME` | S3, RDS, CloudFront | Define resource types |
| `TERRAFORM_VERSION` | 1.7, 1.8 | Valida sintaxis HCL |
| `PROVIDER_VERSION` | aws v5.x | Documentación registry |
| `USE_MODULES` | yes/no | Estructura del output |
| `USE_WORKSPACES` | yes/no | Multi-environment patterns |
| `INTEGRATION_PARTNERS_LIST` | VPC, IAM, KMS... | Examples de integración |

---

**Nota**: Este prompt es **específicamente diseñado para Terraform**. Si necesitas investigar otras tecnologías (Python, JavaScript, etc.), usa el prompt original `technical-framework-researcher.prompt.md`.
