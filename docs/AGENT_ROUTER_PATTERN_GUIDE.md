# Agent Router Pattern - Implementation Guide

## Overview

The Agent Router Pattern is a sophisticated architectural pattern for GitHub Copilot agents that enables **minimal routing logic with maximum delegation**. This pattern separates concerns by creating a lightweight router agent that delegates all implementation work to specialized instructions and prompts.

## Core Principles

### 1. Router Puro, Instrucciones Ricas (Pure Router, Rich Instructions)
- **Router Agent**: Contains only routing logic, no implementation details
- **Instructions**: Rich, detailed implementation guides
- **Prompts**: Specialized sub-agents for specific domains
- **Skills**: Technical knowledge units for libraries and frameworks

### 2. Three-Tier Architecture
```
┌─────────────────┐
│   Router Agent  │ ← Traffic controller
├─────────────────┤
│  Instructions   │ ← Persistent memory
├─────────────────┤
│   Prompts +     │ ← Specialized experts
│    Skills       │ ← Technical knowledge
└─────────────────┘
```

### 3. Separation of Concerns
- **Routing**: What to do with a request
- **Implementation**: How to do it
- **Knowledge**: Technical details and patterns

---

## Component Architecture

### 1. Router Agent (`*.agent.md`)

**Purpose**: Traffic controller that classifies intent and routes to appropriate handlers.

**Key Characteristics**:
- **Lightweight**: Contains only routing tables and decision logic
- **No Implementation**: Never contains code examples or technical details
- **Intent Classification**: Maps user keywords to specialized prompts
- **Conflict Resolution**: Handles requests that span multiple domains

**Structure**:
```yaml
---
name: python-eci
description: Router especializado para desarrollo Python ECI que dirige solicitudes a instrucciones especializadas
tools: ['read', 'edit', 'search', 'execute']
metadata:
  version: "2.0.0"
  maintainer: "ECI Development Team"
  specialization: "Python Development Router"
  instructions_anchor: ".github/instructions"
  compatibility: ["VSCode", "GitHub Copilot", "IntelliJ IDEA", "Eclipse"]
  last_updated: "2026-02-23"
---
```

**Core Sections**:
- **🎯 Responsabilidad Principal**: Pure router role definition
- **📋 Enrutamiento de Instrucciones**: Mapping of request types to instructions
- **🔄 Flujo de Trabajo del Router**: Step-by-step routing process
- **🚫 Lo Que NO Haces**: Clear boundaries of what the router doesn't do
- **✅ Lo Que SÍ Haces**: Explicit responsibilities
- **📚 Referencia de Instrucciones**: Documentation of available instructions

### 2. Instructions (`*.instructions.md`)

**Purpose**: Persistent memory that's automatically injected into conversations. Three types:

#### A. Skills Management Instructions
- **File**: `{agent}-skills.instructions.md`
- **Purpose**: Maps keywords to skills and manages prompt routing
- **ApplyTo**: `"**/*"` (always active)
- **Key Features**:
  - Prompt-first routing logic
  - Skill directory mapping
  - Cross-cutting rules
  - Prompt recommendation examples

#### B. Code Standards Instructions
- **File**: `{agent}-standards.instructions.md`
- **Purpose**: Enforces coding standards and quality rules
- **ApplyTo**: Source file patterns (`"**/*.py"`, `"**/*.js"`, etc.)
- **Key Features**:
  - Mandatory coding standards
  - Forbidden patterns
  - Code structure requirements
  - Verification checklists

#### C. Project Configuration Instructions
- **File**: `{agent}-config.instructions.md`
- **Purpose**: Manages project structure and dependencies
- **ApplyTo**: Configuration file patterns
- **Key Features**:
  - Standard project structure
  - Dependency management rules
  - Environment configuration
  - Definition of done

### 3. Prompts (`*.prompt.md`)

**Purpose**: Specialized sub-agents for specific domains. Each prompt is an expert in one narrow area.

**Characteristics**:
- **Domain-Specific**: Expert in one technology or domain
- **Three-Tier Guardrails**: Always Do, Ask First, Never Do
- **Skill Loading**: Loads relevant skills on demand
- **Implementation Focus**: Generates actual code and solutions

**Structure**:
```yaml
---
name: python-eci-auth
description: 'Create JWT authentication systems with security standards for Python ECI projects'
agent: python-eci
tools: ['read', 'edit', 'search', 'execute', 'github/*']
argument-hint: 'Choose pattern: stateless or refresh-tokens'
---
```

**Three-Tier Guardrail System**:
```
✅ Always Do    — Mandatory patterns. No exceptions.
⚠️ Ask First   — Architectural decisions requiring user choice.
🚫 Never Do    — Anti-patterns to avoid completely.
```

### 4. Skills (`SKILL.md`)

**Purpose**: Deep knowledge documents about specific libraries, frameworks, or tools at specific versions.

**Structure**:
```
.github/skills/
├── fastapi-web-framework/
│   └── SKILL.md
├── psycopg-postgresql/
│   └── SKILL.md
└── pyjwt-authentication/
    └── SKILL.md
```

**Key Features**:
- **Version-Specific**: Each skill targets a specific version
- **Three-Tier Patterns**: Always Do, Ask First, Never Do
- **Integration Patterns**: How to combine with other technologies
- **Verification Loop**: Commands to verify correct implementation

---

## Routing Flow

### 1. User Request Analysis
```
User: "Crear API FastAPI con autenticación JWT"
```

### 2. Router Classification
The router analyzes keywords:
- "API", "FastAPI" → Web API domain
- "autenticación", "JWT" → Authentication domain

### 3. Conflict Resolution
Multiple domains detected → Sequential execution:
1. `/python-eci-web-api` (create API structure)
2. `/python-eci-auth` (add authentication)

### 4. Prompt Execution
Each prompt:
- Loads relevant skills
- Asks clarifying questions (⚠️ Ask First)
- Generates implementation
- Enforces patterns (✅ Always Do, 🚫 Never Do)

### 5. Skill Integration
Prompts load skills like:
- `fastapi-web-framework/SKILL.md`
- `pyjwt-authentication/SKILL.md`
- `pytest-testing-framework/SKILL.md`

---

## Implementation Guidelines

### 1. Router Agent Development

**DO**:
- Keep routing logic simple and clear
- Use keyword-based classification
- Provide clear examples of routing decisions
- Document all available instructions

**DON'T**:
- Include implementation details
- Generate code examples
- Store technical knowledge
- Handle specific domain logic

### 2. Instructions Design

**Skills Management Instructions**:
- Prioritize prompts over direct skill loading
- Provide clear keyword mappings
- Include prompt recommendation examples
- Define cross-cutting rules

**Code Standards Instructions**:
- Define mandatory standards
- List forbidden patterns
- Provide verification checklists
- Include quality commands

**Project Configuration Instructions**:
- Define standard structure
- Specify dependency rules
- Include environment templates
- Define "done" criteria

### 3. Prompt Development

**Three-Tier Guardrails**:
```
✅ Always Do
- Pattern name and why it's mandatory
- Code example with explanations
- Consequences of omission
- Source documentation

⚠️ Ask First  
- Decision point description
- Options table with trade-offs
- Specific question for user
- Source documentation

🚫 Never Do
- Anti-pattern description
- Wrong and right code examples
- Why it's prohibited
- Source documentation
```

**Trigger Keywords**:
- List all user phrases that should trigger this prompt
- Include synonyms and variations
- Align with router keyword mapping

### 4. Skill Creation

**Version Specificity**:
- Target exact versions (e.g., "FastAPI v0.129.0")
- Reject patterns from other versions
- Document important changes

**Integration Patterns**:
- How to combine with other technologies
- Common problems and solutions
- Verification commands

---

## Directory Structure

### Complete Agent Project Structure
```
.github/
├── agents/
│   └── python-eci.agent.md              ← Router agent
├── instructions/
│   ├── python-eci-skills.instructions.md ← Skills management
│   ├── python-eci-standards.instructions.md ← Code standards
│   └── python-eci-config.instructions.md ← Project config
├── prompts/
│   ├── python-eci-auth.prompt.md        ← Authentication expert
│   ├── python-eci-database.prompt.md    ← Database expert
│   ├── python-eci-web-api.prompt.md     ← Web API expert
│   ├── python-eci-testing.prompt.md     ← Testing expert
│   ├── python-eci-kafka.prompt.md        ← Messaging expert
│   ├── agent-router-pattern-validator.prompt.md ← Architecture validator
│   └── copilot-compatibility-review.prompt.md ← Format validator
├── skills/
│   ├── fastapi-web-framework/
│   │   └── SKILL.md
│   ├── psycopg-postgresql/
│   │   └── SKILL.md
│   ├── pyjwt-authentication/
│   │   └── SKILL.md
│   ├── pytest-testing-framework/
│   │   └── SKILL.md
│   └── confluent-kafka/
│       └── SKILL.md
└── README.md
```

---

## Best Practices

### 1. Router Design
- **Minimal Logic**: Keep routing tables simple and readable
- **Clear Boundaries**: Document what the router doesn't do
- **Consistent Naming**: Use kebab-case for all names
- **Version Management**: Track agent version in metadata

### 2. Instructions Management
- **ApplyTo Patterns**: Be specific about when instructions activate
- **Cross-Cutting Rules**: Define standards that apply across all domains
- **Verification Commands**: Include commands to validate compliance

### 3. Prompt Engineering
- **Domain Focus**: Each prompt should have one clear domain
- **Guardrail Completeness**: All three tiers must be present
- **Skill Dependencies**: Clearly indicate which skills are needed

### 4. Skill Development
- **Version Locking**: Always specify exact versions
- **Pattern Documentation**: Explain why each pattern matters
- **Integration Testing**: Include verification commands

---

## Migration Guide

### From Monolithic Agent to Router Pattern

**Step 1: Extract Routing Logic**
- Identify keyword patterns in existing agent
- Create routing table in new agent file
- Remove implementation details from router

**Step 2: Create Instructions**
- Extract persistent rules into instructions files
- Separate concerns (skills, standards, config)
- Define applyTo patterns

**Step 3: Develop Prompts**
- Create domain-specific prompts
- Implement three-tier guardrails
- Map to relevant skills

**Step 4: Build Skills**
- Extract technical knowledge into skill files
- Version-specific documentation
- Integration patterns

**Step 5: Validation**
- Use agent-router-pattern-validator prompt
- Use copilot-compatibility-review prompt
- Test routing logic

---

## Troubleshooting

### Common Issues

**1. Router Not Routing Correctly**
- Check keyword matching in routing table
- Verify instruction file names match router references
- Ensure applyTo patterns are correct

**2. Instructions Not Applying**
- Verify applyTo glob patterns match file paths
- Check frontmatter syntax
- Ensure files are in correct directory

**3. Prompts Not Loading Skills**
- Verify skill directory paths
- Check skill file naming (SKILL.md uppercase)
- Ensure skill frontmatter is correct

**4. Guardrails Not Working**
- Verify all three tiers are present
- Check emoji formatting (✅ ⚠️ 🚫)
- Ensure proper markdown structure

### Debug Commands

```bash
# Validate agent router pattern
/agent-router-pattern-validator

# Check Copilot compatibility
/copilot-compatibility-review

# Test specific prompt routing
/python-eci-auth stateless
```

---

## Example: Python ECI Agent

### Router Agent (`python-eci.agent.md`)
Routes requests to three main instructions:
- **Project Config**: Structure, dependencies, environment
- **Code Standards**: Quality, style, async patterns  
- **Skills Management**: Prompt routing and technology integration

### Instructions
- **python-eci-skills.instructions.md**: Maps keywords to prompts
- **python-eci-standards.instructions.md**: Python coding standards
- **python-eci-config.instructions.md**: Project configuration rules

### Prompts
- **python-eci-auth.prompt.md**: JWT authentication expert
- **python-eci-database.prompt.md**: PostgreSQL operations expert
- **python-eci-web-api.prompt.md**: FastAPI endpoints expert
- **python-eci-testing.prompt.md**: Pytest testing expert
- **python-eci-kafka.prompt.md**: Event streaming expert

### Skills
- **fastapi-web-framework/SKILL.md**: FastAPI v0.129.0 patterns
- **psycopg-postgresql/SKILL.md**: PostgreSQL v3.3.2 patterns
- **pyjwt-authentication/SKILL.md**: JWT v2.11.0 patterns
- **pytest-testing-framework/SKILL.md**: Pytest v9.0.2 patterns
- **confluent-kafka/SKILL.md**: Kafka v2.13.0 patterns

---

## Conclusion

The Agent Router Pattern provides a scalable, maintainable architecture for GitHub Copilot agents by:

1. **Separating Concerns**: Clear boundaries between routing, implementation, and knowledge
2. **Enabling Specialization**: Each prompt focuses on one domain
3. **Ensuring Consistency**: Three-tier guardrails enforce standards
4. **Facilitating Maintenance**: Modular structure allows easy updates
5. **Supporting Growth**: New domains can be added as new prompts

This pattern transforms monolithic agents into organized, specialist teams that can handle complex development tasks while maintaining high quality and consistency.

---

*For implementation templates and examples, see the `agents-factory/templates/` directory.*
