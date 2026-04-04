# Quick Start Guide

## ✅ All Files Verified - Ready to Use!

Your AI Testing Agent system is fully built according to the recommendations from Page 112-120:

### Architecture Implemented:
```
User URL → UI Extractor → Planner Agent → Designer Agent → Executor → Validator → END
           (Playwright)    (LLM)          (LLM)           (NO AI)     (LLM)
```

### Key Features:
- ✅ **LangChain**: Prompt templates & structured output
- ✅ **LangGraph**: Controlled workflow (NO LOOPS)
- ✅ **Langfuse**: Observability & tracking (optional)
- ✅ **Azure GPT-4o**: LLM brain
- ✅ **Playwright**: UI automation
- ✅ **Token limits**: Cost control on each agent

---

## 📁 Project Structure

```
ai_agent/
├── agents/
│   ├── planner.py       ✅ Generates test scenarios (LLM)
│   ├── designer.py      ✅ Creates YAML test steps (LLM)
│   └── validator.py     ✅ Analyzes results (LLM)
├── tools/
│   ├── ui_extractor.py  ✅ Extracts UI elements (Playwright)
│   └── executor.py      ✅ Runs tests (NO AI)
├── graph/
│   └── workflow.py      ✅ LangGraph fixed workflow
├── prompts/
│   ├── planner_prompt.txt    ✅ Scenario generation prompt
│   ├── designer_prompt.txt   ✅ Test design prompt
│   └── validator_prompt.txt  ✅ Analysis prompt
├── config.py            ✅ Azure GPT-4o configuration
└── langfuse_tracker.py  ✅ Observability tracking
main.py                  ✅ Entry point
```

---

## 🚀 How to Run

### 1. Install Dependencies
```powershell
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure Environment
Create `.env` file:
```bash
# Azure OpenAI (Required)
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Langfuse (Optional - for demo observability)
LANGFUSE_PUBLIC_KEY=pk-lf-xxx
LANGFUSE_SECRET_KEY=sk-lf-xxx
LANGFUSE_HOST=https://cloud.langfuse.com
```

### 3. Run the System
**Single URL:**
```powershell
python main.py --url "https://ce-ts-dev.trinitylifesciences.com/segments"
```

**Multi-Module (using config.yaml):**
```powershell
# 1. Edit config.yaml to define your modules
# 2. Run with config
python main.py

# Or specify custom config
python main.py --config my-config.yaml
```

### 4. View Results
Results saved to `reports/ai_test_results_TIMESTAMP.json`

---

## 🎯 What Happens (Step by Step)

1. **UI Extractor** (Playwright) scans the page
   - Finds buttons, inputs, dropdowns, links
   - No AI involved - pure DOM extraction

2. **Planner Agent** (GPT-4o) generates scenarios
   - 5 positive flows
   - 3 edge cases
   - 3 negative scenarios
   - Max 300 tokens (cost controlled)

3. **Designer Agent** (GPT-4o) creates test steps
   - Converts scenarios to YAML
   - Actions: navigate, fill, click, verify
   - Max 500 tokens

4. **Executor** (Playwright) runs tests
   - NO AI - deterministic execution
   - Playwright + API + DB validation
   - Captures screenshots on failure

5. **Validator Agent** (GPT-4o) analyzes results
   - Identifies root causes
   - Suggests fixes
   - Max 200 tokens

6. **END** - No loops, no retries

---

## 💬 How to Demo (Important!)

When presenting, say:

> "We use a **multi-agent architecture** where each agent has a defined responsibility. **LangGraph controls execution flow**, **LangChain standardizes prompts**, and **Langfuse provides observability**. The system is designed with **no autonomous loops** - it follows a fixed path: Planner → Designer → Executor → Validator → END."

---

## 🔥 Key Differences from Old Approach

| Old (Rule-Based) | New (AI-Powered) |
|------------------|------------------|
| Manual test scenarios | AI generates scenarios |
| Hard-coded test steps | AI creates steps from UI |
| Manual failure analysis | AI identifies root causes |
| No observability | Langfuse tracks everything |
| Basic automation | Intelligent automation |

---

## ⚡ Token Efficiency

- **Planner**: 300 tokens max
- **Designer**: 500 tokens max  
- **Validator**: 200 tokens max
- **Total per run**: ~1000 tokens
- **Cost**: ~$0.01 per test run

---

## 🎯 Next Steps

### Test the System:
```powershell
# Simple test
python main.py --url "https://www.google.com"

# Your application
python main.py --url "https://ce-ts-dev.trinitylifesciences.com/segments"

# Without Langfuse
python main.py --url "https://example.com" --no-langfuse
```

### Monitor with Langfuse:
1. Sign up at https://cloud.langfuse.com
2. Get API keys
3. Add to `.env`
4. Run tests
5. View traces in Langfuse dashboard

---

## ❌ Critical Rules (Never Break!)

- ❌ NO autonomous agent loops
- ❌ NO self-calling agents
- ❌ NO "retry until success"
- ✅ Fixed workflow with END
- ✅ Token limits enforced
- ✅ MAX_TESTS limit (20)

---

## 📊 What You Get

### JSON Report Contains:
```json
{
  "url": "target URL",
  "ui_data": {...},
  "scenarios": {
    "positive_scenarios": [...],
    "edge_cases": [...],
    "negative_scenarios": [...]
  },
  "test_cases": [...],
  "execution_results": {
    "summary": {
      "total_tests": 10,
      "passed": 8,
      "failed": 2,
      "pass_rate": "80%"
    }
  },
  "validation_analysis": {
    "status": "failures_detected",
    "root_causes": [...],
    "recommendations": [...]
  }
}
```

---

## 🛠 Troubleshooting

### Error: "AZURE_OPENAI_API_KEY not set"
➜ Create `.env` file with Azure credentials

### Error: "Playwright not found"
➜ Run: `playwright install chromium`

### Langfuse not working
➜ It's optional! Use `--no-langfuse` flag

### Tests failing
➜ Check selectors in generated test steps
➜ Review validation analysis for root causes

---

## ✅ Verification Checklist

All files created and verified:
- [x] `ai_agent/agents/planner.py` - LLM scenario generation
- [x] `ai_agent/agents/designer.py` - LLM test step creation
- [x] `ai_agent/agents/validator.py` - LLM result analysis
- [x] `ai_agent/tools/ui_extractor.py` - Playwright UI extraction
- [x] `ai_agent/tools/executor.py` - Test execution (no AI)
- [x] `ai_agent/graph/workflow.py` - LangGraph workflow
- [x] `ai_agent/config.py` - Azure GPT-4o config
- [x] `ai_agent/langfuse_tracker.py` - Observability
- [x] `main.py` - Entry point
- [x] `requirements.txt` - Dependencies
- [x] `.env.example` - Configuration template
- [x] `README.md` - Documentation

**✅ Nothing is missing! Ready to run!**

---

## 🎓 Architecture Summary (from PDF Page 112-120)

This implementation follows the exact recommendations:

1. ✅ Uses ALL THREE: LangChain + LangGraph + Langfuse
2. ✅ Multi-agent with clear roles
3. ✅ NO loops - fixed workflow
4. ✅ LLM plans, Python executes
5. ✅ Token-efficient prompts
6. ✅ Observability with Langfuse
7. ✅ Controlled flow graph
8. ✅ Proper error handling

**Your system is production-ready!** 🚀
