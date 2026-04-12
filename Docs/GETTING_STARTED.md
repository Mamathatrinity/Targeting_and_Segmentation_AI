# Getting Started - AI Testing Agent

## Quick Setup (5 minutes)

### 1. Install Dependencies

```powershell
# Create virtual environment
python -m venv .venv

# Activate virtual environment
.\.venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Azure GPT-4o

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Edit `.env` and add your Azure OpenAI credentials:

```bash
# Required
AZURE_OPENAI_API_KEY=your-actual-key-here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Optional - for monitoring
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
```

### 3. Run Your First Test

```powershell
# Simple example
python main.py --url https://www.google.com

# Your application
python main.py --url https://ce-ts-dev.trinitylifesciences.com/segments
```

## Understanding the Output

The system will:

1. **Extract UI** - Scans page for inputs, buttons, dropdowns
2. **Plan Scenarios** (AI) - Generates test scenarios
3. **Design Tests** (AI) - Creates executable test steps
4. **Execute Tests** (Playwright) - Runs tests
5. **Validate Results** (AI) - Analyzes failures

Example output:

```
==============================================================
STEP 1: UI EXTRACTION
==============================================================
✓ Extracted UI from: https://example.com
  - Title: Login Page
  - Elements: {'inputs': 2, 'buttons': 1}

==============================================================
STEP 2: SCENARIO PLANNING (AI)
==============================================================
✓ Generated scenarios:
  - Positive: 5
  - Edge cases: 3
  - Negative: 3

==============================================================
STEP 3: TEST DESIGN (AI)
==============================================================
✓ Designed 8 test cases

==============================================================
STEP 4: TEST EXECUTION (NO AI)
==============================================================
  Step 1: navigate https://example.com
  Step 2: fill Email
  Step 3: click Login
✓ Execution complete:
  - Total: 8
  - Passed: 7
  - Failed: 1
  - Pass Rate: 87.5%

==============================================================
STEP 5: RESULT VALIDATION (AI)
==============================================================
✓ Analysis complete:
  - Status: failures_detected
  - Confidence: high
  - Root causes: ['Selector not found for Email field']
  - Recommendations: ['Update selector strategy']
```

## Token Usage

The system is optimized for cost efficiency:

- **Planner**: ~300 tokens per run
- **Designer**: ~500 tokens per run
- **Validator**: ~200 tokens per run

**Total**: ~1000 tokens per workflow (approximately $0.01 with GPT-4o)

## Viewing Reports

Results are saved to `reports/` directory:

```
reports/
├── ai_test_results_20260403_203045.json
└── ai_test_results_20260403_204122.json
```

Each file contains:
- UI data extracted
- Scenarios generated
- Test cases designed
- Execution results
- AI analysis

## Langfuse Monitoring (Optional)

If you configured Langfuse, visit https://cloud.langfuse.com to see:

- All prompts sent to GPT-4o
- Token usage per agent
- Cost breakdown
- Execution traces

## Troubleshooting

### "AZURE_OPENAI_API_KEY not set"

Edit `.env` file and add your actual Azure OpenAI API key.

### "Import langchain could not be resolved"

Install dependencies:

```powershell
pip install -r requirements.txt
```

### "Playwright not installed"

Install Playwright browsers:

```powershell
playwright install chromium
```

### Tests failing with "Could not find element"

The AI-generated selectors may need refinement. Check:

1. Generated test steps in results JSON
2. Actual page structure
3. Update selector strategy in `executor.py` if needed

## Next Steps

1. **Test your application**: 
   ```powershell
   python main.py --url https://your-app.com/page
   ```

2. **Review generated tests**: 
   Check `reports/` directory

3. **Refine prompts**: 
   Edit agent files in `ai_agent/agents/`

4. **Add custom validation**: 
   Extend `executor.py` with API/DB checks

## Architecture Recap

```
User URL → UI Extractor → Planner (AI) → Designer (AI) → Executor → Validator (AI) → END
           (Playwright)   (GPT-4o)       (GPT-4o)       (No AI)    (GPT-4o)
```

**Key Principle**: AI plans and analyzes, Python executes. No loops!

---

Need help? Check [README.md](README.md) for detailed documentation.
