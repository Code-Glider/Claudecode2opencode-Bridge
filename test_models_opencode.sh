#!/bin/bash
# =============================================================================
# OpenCode Model Tester for cc2oc-bridge
# =============================================================================
# Tests OpenRouter free models through OpenCode to see which work best
# with the cc2oc-bridge.
#
# Usage: ./test_models_opencode.sh
# =============================================================================

set -e

# Configuration
RESULTS_DIR="test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_FILE="$RESULTS_DIR/opencode_test_$TIMESTAMP.md"
TIMEOUT_SECONDS=60

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# Fetch Current Free Models from OpenRouter
# =============================================================================

echo -e "${CYAN}Fetching free models from OpenRouter...${NC}"

MODELS=$(curl -s https://openrouter.ai/api/v1/models | python3 -c "
import json, sys
data = json.load(sys.stdin)
models = data.get('data', [])
free_models = [m['id'] for m in models if m.get('pricing', {}).get('prompt') == '0']
print('\n'.join(free_models[:15]))  # First 15 free models
")

if [ -z "$MODELS" ]; then
    echo -e "${RED}Error: Could not fetch models from OpenRouter${NC}"
    exit 1
fi

# Convert to array (compatible with bash 3.2)
IFS=$'\n' read -d '' -r -a MODEL_ARRAY <<< "$MODELS" || true

echo -e "${GREEN}Found ${#MODEL_ARRAY[@]} free models to test${NC}"
echo ""

# =============================================================================
# Test Prompts
# =============================================================================
TEST_PROMPT_SIMPLE="List the files in the current directory using the bash tool"
TEST_PROMPT_READ="Read README.md and tell me what this project does in one sentence"
TEST_PROMPT_BRIDGE="@cc2oc-bridge run greet"

# =============================================================================
# Setup
# =============================================================================
mkdir -p "$RESULTS_DIR"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  OpenCode Model Compatibility Test${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo "Testing ${#MODEL_ARRAY[@]} models with 3 test prompts each"
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Initialize results file
cat > "$RESULTS_FILE" << EOF
# OpenCode Model Compatibility Test

**Date**: $(date)
**OpenCode Version**: $(opencode --version 2>/dev/null || echo "unknown")
**Test Location**: $(pwd)

## Summary

| Model | Simple Bash | Read File | Bridge Command | Avg Time | Rating |
|:------|:-----------:|:---------:|:--------------:|:--------:|:------:|
EOF

# =============================================================================
# Test Function
# =============================================================================

test_model_with_prompt() {
    local model="$1"
    local prompt="$2"
    local test_name="$3"
    
    echo -e "${BLUE}    $test_name:${NC} Testing..."
    
    local start_time=$(date +%s)
    local output_file=$(mktemp)
    local exit_code=0
    
    # Run OpenCode with the model
    timeout "$TIMEOUT_SECONDS" opencode -m "openrouter/$model" --prompt "$prompt" > "$output_file" 2>&1 || exit_code=$?
    
    local end_time=$(date +%s)
    local duration=$((end_time - start_time))
    
    local result=""
    
    if [ $exit_code -eq 0 ]; then
        # Check output quality
        local output=$(cat "$output_file")
        if echo "$output" | grep -qi "error\|failed\|cannot\|unable\|sorry"; then
            result="⚠️"
            echo -e "${YELLOW}      Completed with warnings (${duration}s)${NC}"
        else
            result="✅"
            echo -e "${GREEN}      Success (${duration}s)${NC}"
        fi
    elif [ $exit_code -eq 124 ]; then
        result="⏰"
        duration="$TIMEOUT_SECONDS+"
        echo -e "${YELLOW}      Timeout${NC}"
    else
        result="❌"
        echo -e "${RED}      Failed (exit $exit_code, ${duration}s)${NC}"
    fi
    
    rm -f "$output_file"
    
    # Return result and duration
    echo "$result|$duration"
}

test_single_model() {
    local model="$1"
    local model_short=$(echo "$model" | sed 's/.*\///' | sed 's/:free$//')
    
    echo ""
    echo -e "${CYAN}Testing: ${model}${NC}"
    echo "----------------------------------------"
    
    # Test 1: Simple bash
    local test1=$(test_model_with_prompt "$model" "$TEST_PROMPT_SIMPLE" "Simple Bash")
    local t1_result=$(echo "$test1" | cut -d'|' -f1)
    local t1_time=$(echo "$test1" | cut -d'|' -f2)
    
    # Test 2: Read file
    local test2=$(test_model_with_prompt "$model" "$TEST_PROMPT_READ" "Read File")
    local t2_result=$(echo "$test2" | cut -d'|' -f1)
    local t2_time=$(echo "$test2" | cut -d'|' -f2)
    
    # Test 3: Bridge command
    local test3=$(test_model_with_prompt "$model" "$TEST_PROMPT_BRIDGE" "Bridge Command")
    local t3_result=$(echo "$test3" | cut -d'|' -f1)
    local t3_time=$(echo "$test3" | cut -d'|' -f2)
    
    # Calculate average
    local avg_time="N/A"
    if [[ "$t1_time" =~ ^[0-9]+$ ]] && [[ "$t2_time" =~ ^[0-9]+$ ]] && [[ "$t3_time" =~ ^[0-9]+$ ]]; then
        avg_time=$(( (t1_time + t2_time + t3_time) / 3 ))
        avg_time="${avg_time}s"
    fi
    
    # Overall rating
    local rating="❌ Poor"
    local pass_count=0
    [[ "$t1_result" == "✅" ]] && pass_count=$((pass_count + 1))
    [[ "$t2_result" == "✅" ]] && pass_count=$((pass_count + 1))
    [[ "$t3_result" == "✅" ]] && pass_count=$((pass_count + 1))
    
    if [ $pass_count -eq 3 ]; then
        rating="✅ Excellent"
    elif [ $pass_count -eq 2 ]; then
        rating="⚠️ Good"
    elif [ $pass_count -eq 1 ]; then
        rating="⚠️ Fair"
    fi
    
    # Write to results
    echo "| \`$model_short\` | $t1_result | $t2_result | $t3_result | $avg_time | $rating |" >> "$RESULTS_FILE"
    
    echo -e "${CYAN}  Result: $rating${NC}"
}

# =============================================================================
# Main Test Loop
# =============================================================================

for model in "${MODEL_ARRAY[@]}"; do
    test_single_model "$model"
done

# =============================================================================
# Finish Report
# =============================================================================

cat >> "$RESULTS_FILE" << EOF

## Test Details

### Prompts Used

1. **Simple Bash**: "$TEST_PROMPT_SIMPLE"
2. **Read File**: "$TEST_PROMPT_READ"
3. **Bridge Command**: "$TEST_PROMPT_BRIDGE"

### Legend

- ✅ Success - Model completed the task correctly
- ⚠️ Warning - Partial success or completion with errors
- ❌ Failed - Model could not complete the task
- ⏰ Timeout - Model took longer than ${TIMEOUT_SECONDS}s

### Ratings

- **✅ Excellent** - Passed all 3 tests (recommended for production)
- **⚠️ Good** - Passed 2/3 tests (suitable for most tasks)
- **⚠️ Fair** - Passed 1/3 tests (limited compatibility)
- **❌ Poor** - Failed all tests (not recommended)

## Recommendations

Models rated "Excellent" are recommended for use with cc2oc-bridge.
Models rated "Good" may work well for simpler commands but could struggle with complex workflows.

---
*Generated by cc2oc-bridge OpenCode model tester*
*Test duration: approximately $((${#MODEL_ARRAY[@]} * 3 * TIMEOUT_SECONDS / 60)) minutes (if all timeout)*
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Testing Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""
echo "Summary:"
cat "$RESULTS_FILE" | grep -A 100 "## Summary"
