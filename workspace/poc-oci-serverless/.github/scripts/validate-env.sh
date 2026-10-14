#!/usr/bin/env bash
# validate-env.sh — Validates Java build environment for OCI Functions projects
# Usage: bash .github/scripts/validate-env.sh
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

EXPECTED_JAVA_MAJOR="21"
ERRORS=0

echo "=== OCI Functions Java Environment Validation ==="
echo ""

# 1. Check JAVA_HOME
echo -n "Checking JAVA_HOME... "
if [ -z "${JAVA_HOME:-}" ]; then
    echo -e "${YELLOW}WARNING: JAVA_HOME not set${NC}"
    echo "  Fix: export JAVA_HOME=\$(/usr/libexec/java_home -v ${EXPECTED_JAVA_MAJOR})"
    ERRORS=$((ERRORS + 1))
else
    echo -e "${GREEN}OK${NC} → ${JAVA_HOME}"
fi

# 2. Check java version
echo -n "Checking java -version... "
JAVA_VERSION=$(java -version 2>&1 | head -1 | grep -oE '"[^"]+"' | tr -d '"' | cut -d. -f1)
if [ "$JAVA_VERSION" = "$EXPECTED_JAVA_MAJOR" ]; then
    echo -e "${GREEN}OK${NC} → Java ${JAVA_VERSION}"
else
    echo -e "${RED}FAIL${NC} → Java ${JAVA_VERSION} (expected ${EXPECTED_JAVA_MAJOR})"
    ERRORS=$((ERRORS + 1))
fi

# 3. Check Maven Java version
echo -n "Checking Maven Java version... "
if command -v mvn &> /dev/null; then
    MVN_JAVA=$(mvn -version 2>&1 | grep -i "java version" | grep -oE '[0-9]+' | head -1)
    if [ "$MVN_JAVA" = "$EXPECTED_JAVA_MAJOR" ]; then
        echo -e "${GREEN}OK${NC} → Maven using Java ${MVN_JAVA}"
    else
        echo -e "${RED}FAIL${NC} → Maven using Java ${MVN_JAVA} (expected ${EXPECTED_JAVA_MAJOR})"
        echo "  Fix: export JAVA_HOME=\$(/usr/libexec/java_home -v ${EXPECTED_JAVA_MAJOR})"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo -e "${YELLOW}SKIP${NC} → Maven not found"
fi

# 4. Check for version mismatch between java and mvn
echo -n "Checking java/Maven JVM consistency... "
if [ "${JAVA_VERSION:-}" = "${MVN_JAVA:-}" ]; then
    echo -e "${GREEN}OK${NC} → Both use Java ${JAVA_VERSION}"
else
    echo -e "${RED}FAIL${NC} → java=${JAVA_VERSION:-?}, Maven=${MVN_JAVA:-?}"
    echo "  This WILL cause Mockito/ByteBuddy failures if Maven uses Java 25+"
    ERRORS=$((ERRORS + 1))
fi

# 5. Check for problematic dependencies in pom.xml (if in project dir)
if [ -f "pom.xml" ]; then
    echo ""
    echo "=== Dependency Checks (pom.xml) ==="

    echo -n "Checking for mockito-inline... "
    if grep -q "mockito-inline" pom.xml; then
        echo -e "${RED}FAIL${NC} → Remove mockito-inline (not needed in Mockito 5.x)"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}OK${NC}"
    fi

    echo -n "Checking for explicit byte-buddy... "
    if grep -q "<artifactId>byte-buddy</artifactId>" pom.xml; then
        echo -e "${YELLOW}WARNING${NC} → Explicit byte-buddy found (should be managed by Mockito)"
        ERRORS=$((ERRORS + 1))
    else
        echo -e "${GREEN}OK${NC}"
    fi

    echo -n "Checking JaCoCo version... "
    JACOCO_VERSION=$(grep -A1 "jacoco-maven-plugin" pom.xml | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    if [ -n "$JACOCO_VERSION" ]; then
        JACOCO_MINOR=$(echo "$JACOCO_VERSION" | cut -d. -f3)
        if [ "$JACOCO_MINOR" -ge 13 ]; then
            echo -e "${GREEN}OK${NC} → ${JACOCO_VERSION}"
        else
            echo -e "${YELLOW}WARNING${NC} → ${JACOCO_VERSION} (recommend 0.8.13+ for Java 22+ compatibility)"
        fi
    else
        echo -e "${YELLOW}SKIP${NC} → JaCoCo not found in pom.xml"
    fi
fi

# Summary
echo ""
echo "=== Summary ==="
if [ $ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ All checks passed — environment is ready for build/test${NC}"
    exit 0
else
    echo -e "${RED}❌ ${ERRORS} issue(s) found — fix before running mvn test${NC}"
    echo ""
    echo "Quick fix (macOS):"
    echo "  export JAVA_HOME=\$(/usr/libexec/java_home -v ${EXPECTED_JAVA_MAJOR})"
    echo "  mvn clean test"
    exit 1
fi
