---
name: project-quality-improvements
description: Technology-agnostic quality analysis and improvement recommendations for GitHub Copilot agent projects (complementary to compatibility review)
argument-hint: project directory to analyze for quality improvements
---

# Project Quality Analysis & Improvement Tool

## Objective
Provide comprehensive quality analysis and improvement recommendations for GitHub Copilot agent projects, focusing on implementation quality, best practices, and optimization opportunities. **This tool complements compatibility reviews by analyzing quality rather than basic compliance.**

## Instructions for GitHub Copilot

Act as a **GitHub Copilot Project Quality Architect**. Focus on implementation quality, architectural patterns, and improvement opportunities rather than basic compatibility checks.

**Note**: This tool assumes basic compatibility has been verified. Use `/copilot-compatibility-review` first for compatibility validation.

### Step 1: Quality Framework Analysis

Load and analyze quality-focused documentation:

1. **Quality Standards Framework** - Implementation patterns and best practices
2. **Three-Tier Safety Architecture** - Security and reliability patterns
3. **Prompt First Implementation** - Strategic pattern analysis
4. **Skill Author Standards** - Quality criteria for technical skills

### Step 2: Quality-Focused Structural Analysis

Explore and analyze the project's implementation quality:

#### Quality Assessment Areas
- **Implementation Patterns**: How well patterns are implemented
- **Information Consistency**: Coherence across components
- **Security Implementation**: Three-tier safety architecture quality
- **Verification Quality**: Testability and validation effectiveness
- **Documentation Quality**: Completeness and usefulness
- **Maintainability**: Code organization and evolution readiness

#### Component Quality Analysis

##### AGENTS (.agent.md) - Implementation Quality
**Quality Assessment Criteria:**
- ✓ **Keyword Mapping Quality**: Comprehensive and accurate mapping
- ✓ **Prompt-First Strategy**: Implementation depth and effectiveness
- ✓ **Metadata Completeness**: Rich, useful metadata
- ✓ **Verification Checklist**: Thoroughness and practicality
- ✓ **Scope Definition**: Clear boundaries and capabilities

**Quality Indicators:**
- **Excellent**: Comprehensive keyword coverage, clear decision framework
- **Good**: Basic mapping present, some gaps in decision logic
- **Fair**: Minimal keywords, unclear prompt strategy
- **Poor**: Missing keywords, no prompt-first approach

##### INSTRUCTIONS (.instructions.md) - Integration Quality
**Quality Assessment Criteria:**
- ✓ **Prompt-First Implementation**: Depth of priority rules
- ✓ **Cross-Cutting Rules**: Comprehensiveness and clarity
- ✓ **Skill Mapping Quality**: Accuracy and completeness
- ✓ **Verification Requirements**: Practicality and coverage
- ✓ **Quality Standards**: Clear, actionable guidelines

**Quality Indicators:**
- **Excellent**: Comprehensive prompt-first rules, clear skill mapping
- **Good**: Basic prompt rules present, some mapping gaps
- **Fair**: Minimal prompt rules, incomplete mapping
- **Poor**: No prompt-first strategy, missing skill mapping

##### PROMPTS (.prompt.md) - Specialization Quality
**Quality Assessment Criteria:**
- ✓ **Role Specialization**: Clarity and domain expertise
- ✓ **Skill Loading Logic**: Conditional loading effectiveness
- ✓ **Workflow Structure**: Step-by-step clarity
- ✓ **Integration Patterns**: Quality of technology integration
- ✓ **Trigger Precision**: Keyword accuracy and coverage

**Quality Indicators:**
- **Excellent**: Highly specialized roles, sophisticated skill loading
- **Good**: Clear roles, basic conditional loading
- **Fair**: Vague roles, minimal skill logic
- **Poor**: Undefined roles, no skill loading strategy

##### SKILLS (SKILL.md) - Technical Quality
**Quality Assessment Criteria:**
- ✓ **Three-Tier Implementation**: Completeness and accuracy
- ✓ **Code Example Quality**: Practical, well-commented examples
- ✓ **Verification Effectiveness**: Commands work as expected
- ✓ **Integration Completeness**: Thorough integration patterns
- ✓ **Version Specificity**: Accurate version locking and context

**Three-Tier Quality Analysis:**
- **✅ Always Do Quality**: Mandatory pattern completeness
- **⚠️ Ask First Quality**: Decision framework effectiveness
- **🚫 Never Do Quality**: Anti-pattern coverage and alternatives

### Step 3: Quality Metrics Evaluation

#### Implementation Quality Metrics
- **Pattern Consistency**: How consistently patterns are applied
- **Security Coverage**: Three-tier safety implementation depth
- **Verification Reliability**: Test effectiveness and coverage
- **Documentation Quality**: Completeness and usefulness
- **Maintainability Score**: Ease of evolution and updates

#### Architectural Quality Assessment
- **Coherence**: How well components work together
- **Scalability**: Ability to handle growth and complexity
- **Modularity**: Component independence and reusability
- **Extensibility**: Ease of adding new capabilities
- **Robustness**: Error handling and edge case coverage

### Step 4: Generate Quality Analysis Report

Create a file `PROJECT_QUALITY_ANALYSIS.md` with:

```markdown
# Project Quality Analysis & Improvement Report

---

## EXECUTIVE SUMMARY

### Quality Score: [X/10]
- **Agent Structure Quality**: [X/2.5] - Agent definition and metadata
- **Instructions Quality**: [X/2.5] - Integration rules and prompt-first
- **Prompts Quality**: [X/2] - Specialized prompts effectiveness
- **Skills Quality**: [X/2] - Technical skills implementation
- **Documentation Quality**: [X/1] - Overall documentation

### Overall Quality Level: [EXCELLENT | GOOD | FAIR | POOR | CRITICAL]

### Agent Type: [Identified agent specialization]
### Component Count: [Number of agents, instructions, prompts, skills]
### Compatibility Status: [✅ VERIFIED | ⚠️ NEEDS REVIEW | ❌ ISSUES FOUND]
**Note**: Run `/copilot-compatibility-review` for detailed compatibility analysis

---

## QUALITY IMPROVEMENT PRIORITIES

### CRITICAL Quality Issues (Impact functionality)
1. **[Component]**: [Critical quality issue]
   - **Quality Impact**: [How it affects implementation]
   - **Effort**: [High/Medium/Low]
   - **Best Practice**: [Reference standard]

### HIGH Priority (Significant quality improvement)
1. **[Component]**: [Major quality gap]
   - **Quality Impact**: [Improvement benefit]
   - **Effort**: [High/Medium/Low]
   - **Best Practice**: [Reference standard]

### MEDIUM Priority (Enhancement opportunities)
1. **[Component]**: [Quality enhancement]
   - **Quality Impact**: [What improves]
   - **Effort**: [High/Medium/Low]

### LOW Priority (Refinement)
1. **[Component]**: [Quality refinement]
   - **Quality Impact**: [What refines]
   - **Effort**: [Low]

---

## DETAILED QUALITY ANALYSIS

## Agent Structure Quality Assessment

### Pattern Implementation Consistency
- **Prompt-First Strategy**: [Quality assessment]
- **Three-Tier Safety**: [Implementation depth]
- **Metadata Completeness**: [Version locking, maintainer info]
- **Keyword Mapping**: [Coverage and accuracy]

### Component Coherence Analysis
- **Component Integration**: [How well components work together]
- **Consistency Score**: [X/10]
- **Integration Issues**: [List of coherence problems]

---

## AGENTS (.agent.md) - Quality Analysis

### Files Analyzed
- [List of .agent.md files]

### Quality Assessment Matrix
| Agent | Keyword Quality | Prompt-First | Metadata | Verification | Overall Score |
|-------|-----------------|--------------|-----------|--------------|---------------|
| [name] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [X/10] |

### Quality Issues Identified
- ❌ **Keyword Mapping**: [Specific quality issues]
- ❌ **Prompt-First Strategy**: [Implementation gaps]
- ❌ **Metadata Quality**: [Missing or incomplete]
- ❌ **Verification Effectiveness**: [Practicality issues]

### Improvement Recommendations
1. **[Specific Improvement]**: [Detailed recommendation]
   - **Quality Impact**: [How it improves]
   

---

## INSTRUCTIONS (.instructions.md) - Quality Analysis

### Files Analyzed
- [List of .instructions.md files]

### Quality Assessment Matrix
| Instruction | Prompt-First | Cross-Cutting | Skill Mapping | Verification | Score |
|-------------|--------------|---------------|--------------|---------------|-------|
| [name] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [X/10] |

### Quality Issues Identified
- ❌ **Prompt-First Implementation**: [Depth and effectiveness issues]
- ❌ **Cross-Cutting Rules**: [Comprehensiveness gaps]
- ❌ **Skill Mapping Quality**: [Accuracy and completeness]
- ❌ **Verification Requirements**: [Practicality issues]

### Improvement Recommendations
1. **[Specific Improvement]**: [Detailed recommendation]
   - **Quality Impact**: [How it improves]

---

## PROMPTS (.prompt.md) - Quality Analysis

### Files Analyzed
- [List of .prompt.md files]

### Quality Assessment Matrix
| Prompt | Role Quality | Skill Logic | Workflow | Integration | Score |
|--------|-------------|-------------|----------|-------------|-------|
| [name] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [X/10] |

### Quality Issues Identified
- ❌ **Role Specialization**: [Clarity and expertise issues]
- ❌ **Skill Loading Logic**: [Conditional loading effectiveness]
- ❌ **Workflow Structure**: [Step-by-step clarity]
- ❌ **Integration Quality**: [Technology integration depth]

### Improvement Recommendations
1. **[Specific Improvement]**: [Detailed recommendation]
   - **Quality Impact**: [How it improves]

---

## SKILLS (SKILL.md) - Quality Analysis

### Skills Analyzed
- [List of skills with directories]

### Quality Assessment Matrix
| Skill | Three-Tier | Code Quality | Verification | Integration | Score |
|-------|------------|--------------|--------------|-------------|-------|
| [name] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [E/G/F/P] | [X/10] |

### Three-Tier Quality Analysis

#### [Skill Name]
- **✅ Always Do Quality**: [Implementation completeness]
  - Code Examples: [Quality assessment]
  - Rationale Clarity: [Assessment]
  - Practicality: [Assessment]
  
- **⚠️ Ask First Quality**: [Decision framework effectiveness]
  - Tradeoff Matrix: [Quality assessment]
  - Decision Guidance: [Clarity assessment]
  - User Choice: [Effectiveness assessment]
  
- **🚫 Never Do Quality**: [Anti-pattern coverage]
  - Pattern Identification: [Accuracy assessment]
  - Alternative Quality: [Solution effectiveness]
  - Impact Documentation: [Clarity assessment]

### Quality Issues Identified
- ❌ **Three-Tier Implementation**: [Completeness and accuracy]
- ❌ **Code Example Quality**: [Practicality and commenting]
- ❌ **Verification Effectiveness**: [Command reliability]
- ❌ **Integration Completeness**: [Pattern thoroughness]

### Improvement Recommendations
1. **[Specific Improvement]**: [Detailed recommendation]
   - **Quality Impact**: [How it improves]
   

---

## QUALITY PATTERNS ANALYSIS

### Prompt First Implementation Quality
- **Keyword Coverage**: [X%] - [Assessment]
- **Decision Framework**: [Quality assessment]
- **Prompt Recommendation**: [Effectiveness assessment]
- **Multiple Prompt Handling**: [Sophistication assessment]

### Three-Tier Safety Architecture Quality
- **Always Do Coverage**: [X/10] - [Implementation depth]
- **Ask First Effectiveness**: [X/10] - [Decision quality]
- **Never Do Completeness**: [X/10] - [Anti-pattern coverage]

### Verification Quality Assessment
- **Command Reliability**: [X/10] - [Commands work as expected]
- **Expected Output Accuracy**: [X/10] - [Outputs match expectations]
- **Troubleshooting Coverage**: [X/10] - [Problem resolution guidance]

### Documentation Quality Assessment
- **Completeness**: [X/10] - [All necessary information present]
- **Clarity**: [X/10] - [Easy to understand and follow]
- **Practicality**: [X/10] - [Real-world applicable]

---
### Quality Improvement Templates

#### Enhanced Agent Template
```yaml
---
name: [domain]-[purpose]
description: Clear, comprehensive description with keyword triggers
tools: ['read', 'edit', 'search', 'execute']
metadata:
  version: "1.0.0"
  maintainer: "[Team Name]"
  specialization: "[Domain]"
  frameworks: ["[Framework1]", "[Framework2]"]
  compatibility: ["VSCode", "GitHub Copilot"]
  last_updated: "YYYY-MM-DD"
  quality_version: "1.0"
---

## ⚠️ CRITICAL: Always Check for Prompts First!
[Comprehensive keyword mapping with quality examples]
```

#### Enhanced Skill Template
```markdown
---
name: [skill-name]
description: Use this when the user needs to [action] [object] with [technology] v[version]
---

## Version Context
**Technology**: [Technology Name]
**Target Version**: v[X.Y.Z]
**Release Date**: [Date]
**Support Status**: [Status]
**Quality Lock**: This skill is version-specific to v[X.Y.Z]

## Three-Tier Safety Architecture

### ✅ Always Do
**[Pattern Name]**: [Comprehensive rationale]

```[language]
# ✅ CORRECT: Detailed explanation of why each line is critical
# [Version-specific context and quality considerations]
[production-ready code with extensive comments]
```
**Why it's mandatory**: [Official reason with quality implications]
**Quality Impact**: [What happens to quality if omitted]
**Source**: [Official documentation link]

### ⚠️ Ask First
**Decision Point**: [Architectural choice with quality implications]

**Available Options**:

| Option | Optimizes For | Sacrifices | Quality Impact | Choose When |
|--------|--------------|-----------|----------------|-------------|
| A | [benefit] | [cost] | [quality effect] | [scenario] |
| B | [benefit] | [cost] | [quality effect] | [scenario] |

**Agent Behavior**: "Before implementing, ask the user: '[quality-focused question]'"

### 🚫 Never Do
**Anti-Pattern**: [What NOT to do with quality consequences]

```[language]
# 🚫 WRONG: [Quality problem explanation]
# [Context of quality degradation]
[problematic code]

# ✅ RIGHT: [Quality solution explanation]
# [Version where quality pattern was introduced]
[high-quality code]
```
**Why it's prohibited**: [Quality and security reasons]
**Quality Impact**: [What degrades in production]
**Source**: [Official documentation with quality focus]
```

---

## QUALITY VERIFICATION CHECKLIST

### Pre-Implementation Quality Checks
- [ ] **Compatibility Verified**: `/copilot-compatibility-review` passed
- [ ] **Quality Standards Loaded**: Latest quality patterns reviewed
- [ ] **Technology Stack Identified**: Quality criteria adapted
- [ ] **Quality Goals Defined**: Success metrics established

### Implementation Quality Checks
- [ ] **Pattern Consistency**: All patterns applied consistently
- [ ] **Three-Tier Completeness**: All three levels implemented
- [ ] **Code Quality**: Examples are production-ready
- [ ] **Verification Reliability**: All commands tested and working

### Post-Implementation Quality Checks
- [ ] **Quality Score**: Target quality achieved
- [ ] **Documentation Quality**: Complete and clear
- [ ] **Maintainability**: Easy to evolve and update
- [ ] **User Experience**: Smooth and effective

---

## QUALITY METRICS & KPIs

### Current Quality Metrics
- **Overall Quality Score**: [X/10]
- **Implementation Consistency**: [X%]
- **Security Coverage**: [X%]
- **Verification Reliability**: [X%]
- **Documentation Completeness**: [X%]

### Target Quality Metrics
- **Overall Quality Score**: [Target/10]
- **Implementation Consistency**: [Target%]
- **Security Coverage**: [Target%]
- **Verification Reliability**: [Target%]
- **Documentation Completeness**: [Target%]

---

## NEXT STEPS & RECOMMENDATIONS

### Immediate Actions (This Week)
1. **Run Compatibility Check**: `/copilot-compatibility-review` first
2. **Address Critical Issues**: Fix blocking quality problems
3. **Establish Quality Baseline**: Document current state

### Short-term Actions 
1. **Implement Quality Improvements**: Follow roadmap
2. **Enhance Verification**: Improve command reliability
3. **Documentation Enhancement**: Improve clarity and completeness

### Long-term Actions 
1. **Quality Maintenance**: Establish ongoing quality checks
2. **Pattern Evolution**: Update patterns as needed
3. **Team Training**: Ensure team understands quality standards

---

## QUALITY REFERENCES

### Quality Framework Documentation
- [Custom GitHub Copilot Agents Guide](docs/custom-github-copilot-agents-guide.md)
- [Quality Standards Framework](docs/quality-standards.md)
- [Three-Tier Safety Architecture](docs/safety-architecture.md)

### Complementary Tools
- **Compatibility Review**: `/copilot-compatibility-review` - Basic compliance validation
- **Quality Analysis**: `/project-quality-improvements` - Implementation quality assessment
- **Skill Author**: `/skill-author-specialist` - Skill creation standards

### Official Documentation
- [GitHub Copilot Agent Skills](https://docs.github.com/en/copilot/building-copilot-extensions/building-a-copilot-agent-for-your-copilot-extension/about-agent-skills)
- [Custom Agents Configuration](https://docs.github.com/en/reference/custom-agents-configuration)
- [Quality Best Practices](https://docs.github.com/en/copilot/best-practices/quality)
```

### Step 5: Quality Evaluation Criteria

For each component, evaluate quality dimensions:
- **IMPLEMENTATION DEPTH**: How thoroughly patterns are implemented
- **CONSISTENCY**: How consistently quality standards are applied
- **EFFECTIVENESS**: How well the implementation achieves its goals
- **MAINTAINABILITY**: Ease of evolution and updates
- **USER EXPERIENCE**: Quality of end-user interaction

### Step 6: Complementary Usage

This tool is designed to complement `/copilot-compatibility-review`:

1. **First**: Run `/copilot-compatibility-review` for basic compliance
2. **Then**: Run `/project-quality-improvements` for quality analysis
3. **Result**: Complete picture of both compatibility and quality

---

## Usage Instructions

**Recommended Workflow:**
```bash
# Step 1: Check basic compatibility
/copilot-compatibility-review [project-path]

# Step 2: Analyze implementation quality
/project-quality-improvements [project-path]

# Step 3: Review both reports together
# Focus on critical issues from both reports
```

**Quality-Focused Analysis:**
```bash
# Direct quality analysis (assuming compatibility verified)
/project-quality-improvements /path/to/project

# Analyze current workspace quality
@workspace analyze project quality using /project-quality-improvements
```

---

**Note**: This quality analysis tool complements compatibility reviews by focusing on implementation quality, architectural patterns, and improvement opportunities rather than basic structural compliance.
