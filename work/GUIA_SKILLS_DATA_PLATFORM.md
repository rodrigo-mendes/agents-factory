# Guia de Skills para Data Platform e Sistemas Distribuídos

## 1. Objetivo

Este documento propõe temas para pesquisar, aprofundar e transformar em skills para agentes de IA, com base nos conhecimentos identificados nos projetos Redis, Cassandra, ScyllaDB, Elasticsearch, Kafka, MySQL, Debezium, Docker e observabilidade.

A proposta é criar skills amplas, mas organizadas por domínio. Assim, um agente principal pode coordenar especialistas sem transformar todo o conhecimento em uma única skill difícil de manter.

## 2. Skill principal recomendada

### `data-platform-engineer`

Skill coordenadora para analisar, projetar, documentar, validar e operar plataformas de dados distribuídas.

Responsabilidades:

- Descobrir tecnologias e dependências em um repositório.
- Identificar fluxos de dados e componentes de uma arquitetura.
- Escolher tecnologias de persistência e mensageria.
- Projetar bancos NoSQL para IoT e séries temporais.
- Planejar alta disponibilidade e disaster recovery.
- Criar configurações Docker Compose e Kubernetes.
- Definir métricas, alertas e runbooks.
- Planejar benchmarks e testes de carga.
- Revisar segurança e preparação para produção.
- Gerar documentação técnica com evidências.

## 3. Domínios de conhecimento para aprofundar

## 3.1 Arquitetura de plataformas de dados

### Skill sugerida

`data-platform-architect`

### Temas de pesquisa

- Arquitetura orientada a eventos.
- Fluxos IoT entre dispositivos, gateways, Kafka e bancos.
- Separação entre ingestão, processamento e consulta.
- CQRS e event sourcing.
- Contratos de eventos e evolução de schemas.
- Idempotência, ordenação e reprocessamento.
- Dead-letter queues e mensagens inválidas.
- Escolha entre Redis, Cassandra, ScyllaDB e Elasticsearch.
- Trade-offs entre consistência, disponibilidade e latência.
- Diagramas de arquitetura e decisões técnicas.

### Saídas esperadas

- Diagrama da solução.
- Componentes e responsabilidades.
- Fluxo dos dados.
- Decisões arquiteturais.
- Riscos, limitações e alternativas.

## 3.2 Modelagem NoSQL e IoT

### Skill sugerida

`nosql-iot-data-modeler`

### Temas de pesquisa

- Modelagem orientada aos padrões de consulta.
- Chaves de partição e clustering keys.
- Particionamento por dispositivo e intervalo de tempo.
- Prevenção de hot partitions.
- Desnormalização para leituras rápidas.
- TTL e retenção de dados.
- `TimeWindowCompactionStrategy`.
- Consistência local e global.
- Replicação multi-datacenter.
- Modelagem de GPS, sensores, bateria, localização e eventos.
- Comparação entre Cassandra e ScyllaDB.
- Mappings e índices do Elasticsearch.
- Geolocalização e consultas temporais.

### Saídas esperadas

- Schema CQL.
- Mappings e índices Elasticsearch.
- Estratégia de particionamento.
- Estratégia de retenção.
- Exemplos de consultas.
- Avaliação de riscos de volume e crescimento.

## 3.3 Redis e dados em tempo real

### Skill sugerida

`redis-realtime-engineer`

### Temas de pesquisa

- Redis Pub/Sub.
- Redis Streams.
- Redis Lists.
- Redis Hashes.
- RedisJSON.
- RediSearch.
- RedisTimeSeries.
- TTL e expiração.
- Persistência RDB e AOF.
- Replicação Redis.
- Redis Sentinel.
- Redis Cluster.
- Sharding e distribuição de slots.
- Failover e split-brain.
- Cache stampede e invalidação de cache.
- Redis como cache, fila, store de estado e sistema de notificação.

### Saídas esperadas

- Recomendação da estrutura Redis adequada.
- Modelo de chaves.
- Política de TTL.
- Configuração de alta disponibilidade.
- Análise dos riscos de perda de mensagens.
- Estratégia de migração ou recuperação.

## 3.4 Kafka, streaming e mensageria

### Skill sugerida

`kafka-streaming-engineer`

### Temas de pesquisa

- Tópicos, partições e offsets.
- Consumer groups.
- Replication factor e ISR.
- Retenção e compactação de tópicos.
- Kafka Streams.
- Kafka Connect.
- Schema Registry.
- Processamento em lote.
- Processamento em tempo real.
- Ordenação de eventos.
- Reprocessamento.
- Backpressure.
- Exactly-once, at-least-once e at-most-once.
- Tópicos de erro e dead-letter queues.
- Kafka com Zookeeper e Kafka sem Zookeeper.
- Monitoramento de brokers e consumer lag.

### Saídas esperadas

- Desenho dos tópicos.
- Número recomendado de partições.
- Política de retenção.
- Estratégia de consumidores.
- Configuração de replicação.
- Plano de reprocessamento.
- Matriz de garantias de entrega.

## 3.5 CDC, Debezium e CQRS

### Skill sugerida

`cdc-cqrs-engineer`

### Temas de pesquisa

- MySQL binlog.
- Debezium snapshots.
- Eventos de `INSERT`, `UPDATE` e `DELETE`.
- Kafka Connect.
- Tópicos internos de configuração, offsets e status.
- Projeções materializadas.
- Reconstrução de projeções.
- Idempotência dos consumidores.
- Ordenação por chave.
- Evolução de schemas.
- Falhas durante a captura de mudanças.
- Recuperação de offsets.
- Reconciliação entre origem e projeção.

### Saídas esperadas

- Configuração de conectores Debezium.
- Fluxo MySQL -> Debezium -> Kafka -> projeções.
- Estratégia de recuperação.
- Regras de idempotência.
- Checklist de operação.
- Plano de reconstrução de dados.

## 3.6 Alta disponibilidade e disaster recovery

### Skill sugerida

`distributed-ha-engineer`

### Temas de pesquisa

- Replicação multi-datacenter.
- Quorum.
- Failover automático.
- Failback.
- RPO e RTO.
- Partições de rede.
- Split-brain.
- Seeds e descoberta de nós.
- Rack awareness.
- Replicação síncrona e assíncrona.
- Testes de falha de datacenter.
- Backup e restauração.
- Snapshots.
- Estratégias de disaster recovery.

### Saídas esperadas

- Matriz de falhas.
- Plano de failover.
- Plano de recuperação.
- Procedimentos operacionais.
- Estimativa de RPO/RTO.
- Testes de caos e recuperação recomendados.

## 3.7 Observabilidade e SRE

### Skill sugerida

`data-platform-observability`

### Temas de pesquisa

- Métricas, logs e traces.
- Prometheus.
- Grafana.
- JMX.
- Redis Exporter.
- Cassandra Exporter.
- Endpoints Prometheus do ScyllaDB.
- Healthchecks Docker.
- SLI, SLO e SLA.
- Alertas de latência, memória, disco e disponibilidade.
- Alertas de consumer lag.
- Métricas de throughput.
- Métricas de compactação.
- JVM heap e garbage collection.
- Runbooks de incidentes.

### Saídas esperadas

- Targets Prometheus.
- Dashboards Grafana.
- Regras de alerta.
- Runbook de diagnóstico.
- Lista de métricas essenciais.
- Critérios para classificar incidentes.

## 3.8 Performance e benchmarking

### Skill sugerida

`distributed-systems-performance`

### Temas de pesquisa

- NoSQLBench.
- YCSB.
- Throughput.
- Latência média, p95, p99 e p999.
- Testes de concorrência.
- Testes de longa duração.
- Testes de carga mista.
- Saturação de CPU, memória, disco e rede.
- JVM tuning.
- Compaction e memtables.
- Batch size.
- Número de threads.
- Hot partitions.
- Kafka consumer lag.
- Tamanho de mensagens.
- Testes de capacidade e ponto de ruptura.

### Saídas esperadas

- Plano de benchmark.
- Workload de teste.
- Métricas coletadas.
- Relatório comparativo.
- Recomendação de configuração.
- Critérios objetivos de aprovação.

## 3.9 Segurança e hardening

### Skill sugerida

`data-platform-security-reviewer`

### Temas de pesquisa

- Segredos expostos em Compose.
- Senhas em Markdown ou arquivos de configuração.
- Uso de tags `latest`.
- Kafka configurado com `PLAINTEXT`.
- TLS entre nós.
- Autenticação e autorização.
- Redis ACL.
- Cassandra Authenticator e Authorizer.
- Elasticsearch Security.
- Docker secrets.
- Rotação de credenciais.
- Princípio do menor privilégio.
- Segurança de redes Docker.
- Vulnerabilidades em imagens.
- Limites de recursos e isolamento.

### Saídas esperadas

- Relatório de riscos.
- Classificação por severidade.
- Correções sugeridas.
- Checklist para produção.
- Configurações endurecidas.
- Evidências de cada achado.

## 3.10 Docker, Kubernetes e plataforma

### Skill sugerida

`container-platform-engineer`

### Temas de pesquisa

- Docker Compose.
- Redes e volumes.
- Healthchecks.
- Dependências entre serviços.
- Resource limits.
- ConfigMaps e Secrets.
- StatefulSets.
- PersistentVolumes.
- Readiness e liveness probes.
- Deployments Kubernetes.
- Helm.
- Migração de Compose para Kubernetes.
- Operação em macOS e Podman.
- Estratégias de upgrade.
- Rollback.

### Saídas esperadas

- Compose validado.
- Manifestos Kubernetes.
- Helm chart.
- Plano de rollout.
- Plano de rollback.
- Matriz de volumes e persistência.

## 3.11 Documentação e extração de conhecimento

### Skill sugerida

`technical-knowledge-miner`

### Temas de pesquisa

- Extração de tecnologias de Markdown.
- Classificação entre uso real e mera menção.
- Matriz de evidências.
- Inventário de serviços.
- Geração de diagramas Mermaid.
- Geração de ADRs.
- Runbooks.
- Glossários técnicos.
- Identificação de lacunas documentais.
- Detecção de contradições entre Compose e documentação.
- Atualização automática da documentação.
- Controle de versões e validade das evidências.

### Saídas esperadas

- Relatório técnico.
- Matriz de tecnologias.
- Mapa de dependências.
- Lista de documentos faltantes.
- Evidências com caminho e linha.
- Grau de confiança da conclusão.

## 3.12 Engenharia de skills para agentes de IA

### Skill sugerida

`ai-skill-builder`

### Temas de pesquisa

- Definição de escopo da skill.
- Gatilhos de ativação.
- Entradas obrigatórias.
- Ferramentas permitidas.
- Formato de saída.
- Validação automática.
- Uso de evidências.
- Controle de incerteza.
- Prevenção de tecnologias inventadas.
- Separação entre análise e alteração de arquivos.
- Aprovação antes de mudanças destrutivas.
- Execução de testes após alterações.
- Delegação para skills especializadas.
- Composição de várias skills.
- Limites de autonomia do agente.

### Saídas esperadas

- Arquivo `SKILL.md`.
- Exemplos de entrada e saída.
- Critérios de sucesso.
- Limites operacionais.
- Estratégia de validação.
- Casos de falha conhecidos.

## 4. Organização modular recomendada

Em vez de criar uma única skill gigantesca, recomenda-se uma skill principal com módulos especializados:

```text
data-platform-engineer/
├── SKILL.md
├── architecture.md
├── redis.md
├── kafka.md
├── nosql.md
├── cdc.md
├── high-availability.md
├── observability.md
├── performance.md
├── security.md
├── containers.md
└── documentation.md
```

### Roteamento sugerido

| Solicitação | Módulo principal |
|---|---|
| Arquitetura geral | `architecture` |
| Redis ou cache | `redis` |
| Kafka ou eventos | `kafka` |
| Cassandra/ScyllaDB | `nosql` |
| MySQL + Debezium | `cdc` |
| Failover ou replicação | `high-availability` |
| Métricas e alertas | `observability` |
| Carga e latência | `performance` |
| Segurança | `security` |
| Compose/Kubernetes | `containers` |
| Relatórios Markdown | `documentation` |

## 5. Contrato comum para todas as skills

Cada skill deveria definir:

### Entradas

- Caminho do projeto.
- Objetivo da análise.
- Ambiente alvo: desenvolvimento, homologação ou produção.
- Restrições de alteração.
- Tecnologias envolvidas, quando conhecidas.

### Processo

1. Localizar arquivos relevantes.
2. Identificar o caminho que controla o comportamento.
3. Separar evidência confirmada de hipótese.
4. Analisar riscos e dependências.
5. Gerar uma proposta pequena e verificável.
6. Executar validação focada.
7. Produzir resultado com referências aos arquivos.

### Saídas

- Resumo executivo.
- Achados técnicos.
- Evidências.
- Riscos.
- Recomendações.
- Comandos de validação.
- Nível de confiança.
- Arquivos alterados, se houver.

### Regras de confiabilidade

- Não afirmar que um serviço está operacional somente porque aparece em um Compose.
- Não classificar uma tecnologia como utilizada apenas porque aparece em um comentário ou binding genérico.
- Diferenciar configuração efetiva, documentação, exemplo, alternativa e código gerado.
- Informar versões e caminhos sempre que disponíveis.
- Não ocultar riscos de segurança ou inconsistências de configuração.
- Validar alterações com testes, lint, compilação ou comandos específicos.

## 6. Priorização para aprofundamento

### Fase 1: núcleo técnico

1. Modelagem NoSQL e IoT.
2. Kafka e processamento de eventos.
3. Redis e padrões de tempo real.
4. Alta disponibilidade multi-datacenter.

### Fase 2: operação

5. Observabilidade e troubleshooting.
6. Performance e benchmarking.
7. CDC com Debezium.
8. Backup, disaster recovery e testes de falha.

### Fase 3: produção

9. Segurança e hardening.
10. Docker e Kubernetes.
11. CI/CD e governança de configurações.
12. FinOps e dimensionamento de infraestrutura.

### Fase 4: inteligência dos agentes

13. Extração de conhecimento técnico.
14. Geração de diagramas e runbooks.
15. Roteamento entre skills.
16. Validação baseada em evidências.
17. Avaliação automática da qualidade das respostas.

## 7. Agentes amplos possíveis

### Data Platform Architect

Projeta a arquitetura completa de ingestão, streaming, persistência e consulta.

### NoSQL and IoT Engineer

Modela dados, tabelas, índices, TTL, consultas e estratégias de retenção.

### Streaming and CDC Engineer

Projeta Kafka, Kafka Streams, Kafka Connect, Debezium e pipelines orientados a eventos.

### Distributed Systems SRE

Analisa disponibilidade, replicação, failover, métricas, incidentes e recuperação.

### Platform Security Reviewer

Revisa secrets, TLS, autenticação, imagens, redes e preparação para produção.

### Technical Knowledge Curator

Transforma repositórios, Compose e Markdown em inventários, relatórios e documentação confiável.

## 8. Conclusão

Os conhecimentos identificados permitem construir um conjunto de skills para um agente de **Data Platform Engineer**, capaz de analisar e operar arquiteturas distribuídas baseadas em Redis, Cassandra, ScyllaDB, Elasticsearch, Kafka, MySQL e Debezium.

A recomendação é começar pelas skills de arquitetura, NoSQL, Kafka, Redis e alta disponibilidade. Depois, adicionar observabilidade, performance, segurança e documentação. Essa evolução mantém cada skill focada, testável e reutilizável.
