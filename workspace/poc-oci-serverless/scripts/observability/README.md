# Scripts de validação de observabilidade — MOVIDOS

Os scripts que ficavam aqui foram movidos para dentro do skill (fonte única, sem duplicação):

**`.claude/skills/validating-oci-observability/scripts/`**

Contém: `validate-observability.sh` (orquestrador), `check-logs.sh`, `check-metrics.sh`,
`check-traces.sh`, `check-alarms.sh`, `smoke-invoke.sh`, `trigger-alarm-test.sh`,
`deploy-and-validate.sh` (runbook), `lib-common.sh`, `README.md`.

## Como usar

Via o skill **`validating-oci-observability`** (documenta quando e como usar cada script),
ou direto — os scripts resolvem o repo root via `git`, então rodam de qualquer diretório:

```bash
.claude/skills/validating-oci-observability/scripts/validate-observability.sh
```

Pré-requisitos e detalhe por script: veja
`.claude/skills/validating-oci-observability/SKILL.md`.
