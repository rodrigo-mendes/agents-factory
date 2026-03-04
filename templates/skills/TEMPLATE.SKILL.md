---
name: [skill-name]
description: [Brief description of what this skill implements]
---

## Function
Specialist in [SPECIALTY] for [TECHNOLOGY/FRAMEWORK] v[VERSION]

## Version Context

**Technology/Framework**: [TECHNOLOGY NAME]
**Target version**: v[VERSION]
**Release date**: [DATE]
**Support status**: Active

**Important changes in this version**:
- [Change 1]
- [Change 2]
- [Change 3]

**Deprecated**: [None or list deprecated]

⚠️ **CRITICAL - Agent warning**: 
This skill is specific to version v[VERSION]. 
Reject ANY patterns from versions <[VERSION].
Do not mix patterns from previous versions with v[VERSION].

---

## Plans and Guardrails

### ✅ Always

#### [Mandatory Pattern 1]
**Why it's mandatory**: [Explanation of importance]

```
# ✅ CORRECT: [Description of correct pattern] (v[VERSION])
# Generic example - adapt to specific language

# [Example of pseudocode or concept]
function correct_example():
    # Implementation following best practices
    # 1. [Step 1]
    # 2. [Step 2]
    # 3. [Step 3]
    pass
```

**Why it's mandatory**: [Detailed reason]
**Failure if omitted**: [Consequences of not implementing]
**Source**: [Link to official documentation]

#### [Mandatory Pattern 2]
**Why it's mandatory**: [Explanation of importance]

```
# ✅ CORRECT: [Description of correct pattern] (v[VERSION])
# Generic example - adapt to specific language

# [Example of pseudocode or concept]
function correct_example():
    # Implementation following best practices
    # 1. [Step 1]
    # 2. [Step 2]
    # 3. [Step 3]
    pass
```

**Why it's mandatory**: [Detailed reason]
**Failure if omitted**: [Consequences of not implementing]
**Source**: [Link to official documentation]

#### [Mandatory Pattern 3]
**Why it's mandatory**: [Explanation of importance]

```
# ✅ CORRECT: [Description of correct pattern] (v[VERSION])
# Generic example - adapt to specific language

# [Example of pseudocode or concept]
function correct_example():
    # Implementation following best practices
    # 1. [Step 1]
    # 2. [Step 2]
    # 3. [Step 3]
    pass
```

**Why it's mandatory**: [Detailed reason]
**Failure if omitted**: [Consequences of not implementing]
**Source**: [Link to official documentation]

### ⚠️ Ask First

#### [Decision Point 1]
**Decision point**: [Description of architectural decision]

**Available options**:

| Option | Optimizes for | Sacrifices | When to choose |
|--------|--------------|------------|----------------|
| [Option 1] | [Benefit] | [Cost] | [Scenario] |
| [Option 2] | [Benefit] | [Cost] | [Scenario] |

**Agent behavior**:
"Before implementing, ask:
'[Specific question for the user]'"

**Source**: [Link to documentation]

#### [Decision Point 2]
**Decision point**: [Description of architectural decision]

**Available options**:

| Option | Security | Complexity | Ideal when |
|--------|-----------|------------|-----------|
| [Option 1] | [Level] | [Level] | [Scenario] |
| [Option 2] | [Level] | [Level] | [Scenario] |

**Agent behavior**:
"Before configuring, ask:
'[Specific question for the user]'"

**Source**: [Link to documentation]

### 🚫 Never Do

#### [Anti-pattern 1]
**Anti-pattern**: [Description of anti-pattern]

```
# 🚫 INCORRECT: [Description of what not to do] (v[VERSION])
# Dangerous in [TECHNOLOGY] v[VERSION]: [Consequence]
# Generic example - adapt to specific language

function incorrect_example():
    # Problematic implementation
    # ❌ [Problem 1]
    # ❌ [Problem 2]
    # ❌ [Problem 3]
    pass
```

**Why it's prohibited**: [Detailed reason]
**Real impact**: [Negative consequences]
**Source**: [Link to documentation]

```
# ✅ CORRECT: [Description of correct solution] (v[VERSION])
# Generic example - adapt to specific language

function correct_example():
    # Safe implementation
    # ✅ [Solution 1]
    # ✅ [Solution 2]
    # ✅ [Solution 3]
    pass
```

#### [Anti-pattern 2]
**Anti-pattern**: [Description of anti-pattern]

```
# 🚫 INCORRECT: [Description of what not to do] (v[VERSION])
# Dangerous in [TECHNOLOGY] v[VERSION]: [Consequence]
# Generic example - adapt to specific language

function incorrect_example():
    # Problematic implementation
    # ❌ [Problem 1]
    # ❌ [Problem 2]
    # ❌ [Problem 3]
    pass
```

**Why it's prohibited**: [Detailed reason]
**Real impact**: [Negative consequences]
**Source**: [Link to documentation]

```
# ✅ CORRECT: [Description of correct solution] (v[VERSION])
# Generic example - adapt to specific language

function correct_example():
    # Safe implementation
    # ✅ [Solution 1]
    # ✅ [Solution 2]
    # ✅ [Solution 3]
    pass
```

---

## Integration Patterns

### [TECHNOLOGY] ↔ [RELATED TECHNOLOGY]
**Library/Framework**: `[library_name]==[VERSION]`
**Compatibility**:
- [TECHNOLOGY]: v[VERSION]
- [RELATED TECHNOLOGY]: Latest version
- Languages: [e.g., Python, JavaScript, Java, Go, Rust, etc.]

**Installation**:
```
# Generic example - adapt to specific package manager
# npm/pip/maven/cargo/gem/etc.
install [library_name]==[VERSION]
```

**Integration pattern**:
```
# Complete [TECHNOLOGY] + [RELATED TECHNOLOGY] integration
# Generic example - adapt to specific language

# Configuration
config = {
    # Configuration parameters
    "parameter1": "value1",
    "parameter2": "value2"
}

# Implementation
function integration_example():
    # Integration example
    # 1. [Step 1]
    # 2. [Step 2]
    # 3. [Step 3]
    pass
```

**Common problems**:
- **Problem**: [Problem description]
  **Cause**: [Root cause]
  **Solution**: [How to solve]

**Source**: [Link to documentation]

---

## Verification Loop

The agent MUST execute after each code generation:

### 1. Installation
```
# Generic example - adapt to specific package manager
install [library_name]==[VERSION]
```
**Expected result**: [library]-[VERSION] installed successfully.
**Exit code**: 0

### 2. Installation verification
```
# Generic example - adapt to specific language
run_verification_command
```
**Expected result**: Version information displayed.
**Exit code**: 0

### 3. Basic test
```
# Generic example - adapt to specific language
test_basic_functionality
```
**Expected result**: Success message.
**Exit code**: 0

### 4. Main pattern test
```
# Generic example - adapt to specific language
test_main_pattern
```
**Expected result**: Main pattern test successful.
**Exit code**: 0.

**Troubleshooting**:
- [Error 1] → [Solution]
- [Error 2] → [Solution]
- [Error 3] → [Solution]

---

## Quick Reference

**Most used commands**:
```
# Generic example - adapt to specific package manager
install [library_name]==[VERSION]
verify_installation
```

**Essential patterns**:
```
# Basic pattern - adapt to specific language
basic_pattern_example

# Advanced pattern - adapt to specific language
advanced_pattern_example

# Configuration pattern - adapt to specific language
configuration_pattern_example
```

---

## External Resources

### Official documentation
- [Link to main documentation]
- [Link to official repository]
- [Link to distribution page]

### Security and best practices
- [Link to security guide]
- [Link to best practices]
- [Link to integration guide]

### Multi-language support
- [Link to documentation by language]
- [Link to examples in different languages]
- [Link to migration guides]
