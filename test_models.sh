#!/bin/bash
# =============================================================================
# OpenRouter Model Tester for cc2oc-bridge
# =============================================================================
# Tests various open source models to see which work best with the bridge.
# Uses OpenCode CLI in non-interactive mode.
#
# Usage: ./test_models.sh
# =============================================================================

set -e

# Configuration
RESULTS_DIR="test_results"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULTS_FILE="$RESULTS_DIR/model_test_$TIMESTAMP.md"
TIMEOUT_SECONDS=120

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

# =============================================================================
# OpenRouter Free/Open Source Models to Test
# =============================================================================
declare -a MODELS=(
    # Free tier models
    "meta-llama/llama-3.3-70b-instruct:free"
    "google/gemma-2-9b-it:free"
    "mistralai/devstral-2512:free"
    "nvidia/nemotron-3-nano-30b-a3b:free"
    "qwen/qwen-2.5-72b-instruct:free"
    "microsoft/phi-4:free"
    "deepseek/deepseek-chat-v3-0324:free"
    "google/gemini-2.0-flash-exp:free"
    
    # Open source (may have small cost)
    # "meta-llama/llama-3.1-70b-instruct"
    # "qwen/qwen-2.5-coder-32b-instruct"
    # "mistralai/mixtral-8x22b-instruct"
)

# Test prompts - simple to complex
declare -a TEST_PROMPTS=(
    "List the files in the current directory using bash"
    "Read the README.md file and summarize it in 2 sentences"
    "@cc2oc-bridge run greet"
)

# =============================================================================
# Setup
# =============================================================================
mkdir -p "$RESULTS_DIR"

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  cc2oc-bridge Model Compatibility Test${NC}"
echo -e "${CYAN}========================================${NC}"
echo ""
echo "Testing ${#MODELS[@]} models with ${#TEST_PROMPTS[@]} prompts each"
echo "Results will be saved to: $RESULTS_FILE"
echo ""

# Initialize results file
cat > "$RESULTS_FILE" << EOF
# Model Compatibility Test Results

**Date**: $(date)
**Bridge Version**: 1.0.0
**Test Location**: $(pwd)

## Summary

| Model | Test 1 (Bash) | Test 2 (Read) | Test 3 (Bridge) | Avg Time | Status |
|:------|:-------------:|:-------------:|:---------------:|:--------:|:------:|
EOF

# =============================================================================
# Test Functions
# =============================================================================

test_model() {
    local model="$1"
    local prompt="$2"
    local test_num="$3"
    
    echo -e "${BLUE}  Test $test_num:${NC} ${prompt:0:50}..."
    
    local start_time=$(date +%s.%N)
    local output_file=$(mktemp)
    local exit_code=0
    
    # Run OpenCode with timeout
    # Note: Adjust the command based on your OpenCode CLI syntax
    timeout "$TIMEOUT_SECONDS" opencode --model "$model" --prompt "$prompt" --non-interactive > "$output_file" 2>&1 || exit_code=$?
    
    local end_time=$(date +%s.%N)
    local duration=$(echo "$end_time - $start_time" | bc 2>/dev/null || echo "N/A")
    
    local result=""
    local output_preview=""
    
    if [ $exit_code -eq 0 ]; then
        # Check if output contains expected content
        if grep -qi "error\|failed\|cannot\|unable" "$output_file"; then
            result="⚠️"
            echo -e "${YELLOW}    Warning: Output contains error messages${NC}"
        else
            result="✅"
            echo -e "${GREEN}    Passed (${duration}s)${NC}"
        fi
        output_preview=$(head -c 200 "$output_file" | tr '\n' ' ')
    elif [ $exit_code -eq 124 ]; then
        result="⏰"
        echo -e "${YELLOW}    Timeout after ${TIMEOUT_SECONDS}s${NC}"
    else
        result="❌"
        echo -e "${RED}    Failed (exit code: $exit_code)${NC}"
    fi
    
    rm -f "$output_file"
    
    # Return result
    echo "$result|$duration"
}

test_model_full() {
    local model="$1"
    local model_short=$(echo "$model" | sed 's/:free$//' | sed 's/.*\///')
    
    echo -e "\n${CYAN}Testing: ${model}${NC}"
    echo "----------------------------------------"
    
    local test1_result=$(test_model "$model" "${TEST_PROMPTS[0]}" 1)
    local test2_result=$(test_model "$model" "${TEST_PROMPTS[1]}" 2)
    local test3_result=$(test_model "$model" "${TEST_PROMPTS[2]}" 3)
    
    # Parse results
    local t1_status=$(echo "$test1_result" | cut -d'|' -f1)
    local t1_time=$(echo "$test1_result" | cut -d'|' -f2)
    local t2_status=$(echo "$test2_result" | cut -d'|' -f1)
    local t2_time=$(echo "$test2_result" | cut -d'|' -f2)
    local t3_status=$(echo "$test3_result" | cut -d'|' -f1)
    local t3_time=$(echo "$test3_result" | cut -d'|' -f2)
    
    # Calculate average time
    local avg_time="N/A"
    if [[ "$t1_time" != "N/A" && "$t2_time" != "N/A" && "$t3_time" != "N/A" ]]; then
        avg_time=$(echo "scale=2; ($t1_time + $t2_time + $t3_time) / 3" | bc 2>/dev/null || echo "N/A")
    fi
    
    # Overall status
    local overall="❌"
    if [[ "$t1_status" == "✅" && "$t2_status" == "✅" && "$t3_status" == "✅" ]]; then
        overall="✅ Pass"
    elif [[ "$t1_status" == "✅" || "$t2_status" == "✅" || "$t3_status" == "✅" ]]; then
        overall="⚠️ Partial"
    fi
    
    # Append to results
    echo "| \`$model_short\` | $t1_status | $t2_status | $t3_status | ${avg_time}s | $overall |" >> "$RESULTS_FILE"
}

# =============================================================================
# Alternative: Direct API Test (if OpenCode CLI doesn't support --model flag)
# =============================================================================

test_model_api() {
    local model="$1"
    local prompt="$2"
    
    # Use curl to call OpenRouter directly
    local response=$(curl -s --max-time "$TIMEOUT_SECONDS" \
        -H "Authorization: Bearer $OPENROUTER_API_KEY" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"$model\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}],
            \"max_tokens\": 500
        }" \
        "https://openrouter.ai/api/v1/chat/completions" 2>/dev/null)
    
    if echo "$response" | grep -q '"content"'; then
        echo "✅"
    else
        echo "❌"
    fi
}

# =============================================================================
# Main Execution
# =============================================================================

# Check if OpenCode CLI exists
if ! command -v opencode &> /dev/null; then
    echo -e "${RED}Error: OpenCode CLI not found in PATH${NC}"
    echo ""
    echo "This script requires the OpenCode CLI to be installed."
    echo "Falling back to direct API testing..."
    echo ""
    
    # Check for API key
    if [ -z "$OPENROUTER_API_KEY" ]; then
        echo -e "${RED}Error: OPENROUTER_API_KEY not set${NC}"
        echo "Please set your OpenRouter API key:"
        echo "  export OPENROUTER_API_KEY=your-key-here"
        exit 1
    fi
    
    # Run API tests
    echo -e "${YELLOW}Running direct API tests...${NC}"
    echo ""
    
    for model in "${MODELS[@]}"; do
        model_short=$(echo "$model" | sed 's/:free$//' | sed 's/.*\///')
        echo -n "Testing $model_short... "
        
        result=$(test_model_api "$model" "Say hello in one word")
        echo "$result"
        
        # Add to results
        echo "| \`$model_short\` | $result | - | - | - | $result |" >> "$RESULTS_FILE"
    done
else
    # Run full OpenCode tests
    for model in "${MODELS[@]}"; do
        test_model_full "$model"
    done
fi

# =============================================================================
# Finish Report
# =============================================================================

cat >> "$RESULTS_FILE" << EOF

## Legend

- ✅ Passed - Model completed the task successfully
- ⚠️ Warning - Completed but with errors in output
- ❌ Failed - Model could not complete the task
- ⏰ Timeout - Model took too long (>${TIMEOUT_SECONDS}s)

## Test Prompts Used

1. **Bash Test**: "${TEST_PROMPTS[0]}"
2. **Read Test**: "${TEST_PROMPTS[1]}"
3. **Bridge Test**: "${TEST_PROMPTS[2]}"

## Recommendations

Models that passed all tests are recommended for use with cc2oc-bridge.
Models with partial passes may work for simple commands but struggle with complex workflows.

---
*Generated by cc2oc-bridge model tester*
EOF

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Testing Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Results saved to: $RESULTS_FILE"
echo ""
cat "$RESULTS_FILE"
