# Manual Model Testing Checklist

Test each model manually in OpenCode to see which work best with cc2oc-bridge.

## Test Procedure

For each model:
1. Switch to the model in OpenCode
2. Run the test command: `@cc2oc-bridge run greet`
3. Check if it works correctly
4. Record the result below

## Free OpenRouter Models to Test

### ✅ Recommended (Based on Specs)

- [ ] **Qwen 3 Coder** (`qwen/qwen3-coder:free`) - 262K context
- [ ] **DeepSeek R1** (`deepseek/deepseek-r1-0528:free`) - 163K context
- [ ] **Mistral Devstral** (`mistralai/devstral-2512:free`) - 262K context
- [ ] **Nvidia Nemotron Nano 30B** (`nvidia/nemotron-3-nano-30b-a3b:free`) - 256K context

### ⚠️ Worth Testing

- [ ] **GLM 4.5 Air** (`z-ai/glm-4.5-air:free`) - 131K context ✅ *Known working with similar model*
- [ ] **Kimi K2** (`moonshotai/kimi-k2:free`) - 32K context
- [ ] **OpenAI GPT OSS 120B** (`openai/gpt-oss-120b:free`) - 131K context
- [ ] **Xiaomi Mimo v2 Flash** (`xiaomi/mimo-v2-flash:free`) - 262K context

### ❓ Experimental

- [ ] **Dolphin Mistral Venice** (`cognitivecomputations/dolphin-mistral-24b-venice-edition:free`)
- [ ] **Gemma 3N E4B** (`google/gemma-3n-e4b-it:free`) - 8K context (small)
- [ ] **Nvidia Nemotron Nano 9B** (`nvidia/nemotron-nano-9b-v2:free`) - 128K context

## Test Commands

```bash
# Simple test
@cc2oc-bridge run greet

# More complex test
@cc2oc-bridge run count-files md

# Advanced test
@cc2oc-bridge run create-agent test-reviewer "Code quality expert"
```

## Results Template

For each working model, record:

| Model | Simple | Complex | Advanced | Notes |
|:------|:------:|:-------:|:--------:|:------|
| Example | ✅ | ✅ | ⚠️ | Works but slow |

## Quick Test Script

If you want to test just the top 3 models, run:

```bash
#!/bin/bash
echo "Testing top 3 models..."
echo ""

for model in \
  "qwen/qwen3-coder:free" \
  "deepseek/deepseek-r1-0528:free" \
  "mistralai/devstral-2512:free"
do
  echo "Test: $model"
  echo "Switch to this model in OpenCode and run: @cc2oc-bridge run greet"
  read -p "Did it work? (y/n): " result
  echo "$model: $result" >> test_results/manual_test.txt
  echo ""
done

echo "Results saved to test_results/manual_test.txt"
```

## Expected Behavior

A working model should:
1. Find the `greet` command in `plugins/test-plugin/.claude/commands/`
2. Read the command definition
3. Execute the bash commands inside
4. Output the greeting with current time and directory

## Known Working

- ✅ **glm-4.7** (tested and confirmed)
- ✅ **Claude Sonnet 4.5** (excellent)
- ✅ **Gemini 2.5 Pro** (very good)

## Troubleshooting

If a model doesn't work:
- Check if it understands tool use
- Try a simpler command first
- Check if it's following the instructions in the agent definition

---

*Update this file as you test models*
