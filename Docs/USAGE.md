# AI Testing Agent - Quick Start Guide

## 🚀 Quick Setup (5 Minutes)

### **Option 1: Automated Setup (Recommended)**

**Windows:**
```powershell
.\setup.ps1
```

**Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### **Option 2: Manual Setup**

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate
.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate    # Linux/Mac

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install Playwright browsers
playwright install chromium

# 5. Configure environment
cp .env.example .env
# Edit .env and add your Azure credentials
```

---

## ⚙️ Configuration

Edit `.env` file:

```env
# Required - Azure GPT-4o
AZURE_OPENAI_API_KEY=your_key_here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/

# Optional - Langfuse Observability
LANGFUSE_PUBLIC_KEY=pk_...
LANGFUSE_SECRET_KEY=sk_...
```

---

## 📖 Usage Examples

### **1. Test Single Page (UI Only)**

```bash
python main.py --url "https://example.com"
```

**Output:**
- Extracts UI elements
- Generates test scenarios (AI)
- Creates test steps (AI)
- Executes tests (Playwright)
- Analyzes failures (AI)
- Saves report to `reports/`

---

### **2. Test Multiple Modules**

Edit `config.yaml`:
```yaml
app:
  base_url: "https://myapp.com"

modules:
  - name: "login"
    url: "/login"
    enabled: true
  
  - name: "dashboard"
    url: "/dashboard"
    enabled: true
```

Run:
```bash
python main.py --config config.yaml
```

---

### **3. Full Stack Testing (UI + API + Data)**

```bash
python main.py \
  --url "https://example.com" \
  --api "https://api.example.com" \
  --data "postgresql://localhost/mydb" \
  --mode full
```

**Modes:**
- `ui_only` (default) - UI testing only
- `full` - UI + API + Data validation
- `api_only` - API testing only
- `data_only` - Data validation only

---

### **4. Test Specific Module**

```bash
python main.py --config config.yaml --single-module "login"
```

---

### **5. Disable Langfuse Tracking**

```bash
python main.py --url "https://example.com" --no-langfuse
```

---

## 📊 Understanding Results

### **Console Output**

```
STEP 1: UI EXTRACTION
✓ Extracted 15 elements from: https://example.com

STEP 2: SCENARIO PLANNING (AI)
✓ Generated 11 scenarios (5 positive, 3 edge, 3 negative)

STEP 3: TEST DESIGN (AI)
✓ Designed 10 test cases

STEP 4: TEST EXECUTION
✓ Execution complete:
  - Total: 10
  - Passed: 8
  - Failed: 2

STEP 5: RESULT VALIDATION (AI)
  Running AI Failure Analysis...
  Root Cause: Selectors changed in recent UI update
  Severity: high
  Confidence: high
```

---

### **JSON Report**

Location: `reports/ai_test_results_YYYYMMDD_HHMMSS.json`

```json
{
  "execution_results": {
    "total_tests": 10,
    "passed": 8,
    "failed": 2,
    "failure_groups": [
      {
        "error_type": "element_not_found",
        "count": 2,
        "recommendation": "Update selectors to use data-testid",
        "failed_tests": ["Login test", "Signup test"]
      }
    ]
  },
  "failure_analysis": {
    "root_cause": "Selectors changed in recent UI update",
    "severity": "high",
    "recommendations": [
      "Update selectors to use data-testid attributes"
    ]
  }
}
```

---

## 🧠 Advanced Features

### **1. View Failure History**

```python
from ai_agent.learning_layer import get_learning_layer

learning = get_learning_layer()

# Get summary
summary = learning.get_failure_summary()
print(summary)

# Output:
# {
#   "total_failures": 45,
#   "total_runs": 12,
#   "patterns": [
#     {"type": "element_not_found", "count": 23},
#     {"type": "timeout", "count": 12}
#   ]
# }
```

---

### **2. Enable Lifecycle Loop (Safe Retry)**

Edit `ai_agent/config.py`:

```python
ENABLE_LIFECYCLE_LOOP = True  # Enable 1-retry on failure
```

**Safe because:**
- Max 1 retry only
- Hard timeout limits
- No infinite loops

---

### **3. Customize Prompts**

Edit prompt files in `ai_agent/prompts/`:
- `planner_prompt.txt` - Scenario generation
- `designer_prompt.txt` - Test step creation
- `validator_prompt.txt` - Result analysis

**Example:** To generate more edge cases, edit `planner_prompt.txt`:
```
Generate:
- 5 positive (happy path)
- 5 edge cases  ← Changed from 3
- 3 negative (errors/security)
```

---

## 🏥 Health Check

Run before testing to verify setup:

```bash
python -m ai_agent.health_check
```

**Checks:**
- ✅ Azure credentials configured
- ✅ All prompt files exist
- ✅ All agents available
- ✅ Dependencies installed
- ✅ Directories created

---

## 🐛 Troubleshooting

### **Issue: "AZURE_OPENAI_API_KEY not set"**
**Fix:** Edit `.env` file and add your Azure credentials

### **Issue: "playwright not installed"**
**Fix:** Run `pip install playwright` then `playwright install`

### **Issue: "No module named 'langchain'"**
**Fix:** Run `pip install -r requirements.txt`

### **Issue: Tests failing with "element not found"**
**Cause:** Selectors changed or page structure different  
**Fix:** Check failure analysis recommendations in the report

### **Issue: "Connection timeout"**
**Cause:** Network issues or wrong endpoint  
**Fix:** Verify `AZURE_OPENAI_ENDPOINT` in `.env`

---

## 📁 Project Structure

```
Targeting_and_Segmentation_AI/
├── main.py                    # Entry point
├── setup.ps1 / setup.sh       # Setup scripts
├── config.yaml                # Multi-module config
├── .env                       # Environment variables
├── requirements.txt           # Dependencies
│
├── ai_agent/
│   ├── agents/                # AI agents
│   │   ├── planner.py
│   │   ├── designer.py
│   │   ├── validator.py
│   │   └── failure_analyzer.py
│   │
│   ├── prompts/               # Prompt templates
│   │   ├── planner_prompt.txt
│   │   ├── designer_prompt.txt
│   │   └── validator_prompt.txt
│   │
│   ├── tools/                 # Tools & executors
│   │   ├── ui_extractor.py
│   │   └── executor.py
│   │
│   ├── graph/                 # Workflow
│   │   └── workflow.py
│   │
│   ├── config.py              # Configuration
│   ├── health_check.py        # System health check
│   └── learning_layer.py      # Failure tracking
│
├── reports/                   # Test reports (auto-created)
├── learning_data/             # Failure history (auto-created)
└── examples/                  # Sample configs/reports
```

---

## 🎯 Common Workflows

### **Daily Testing**
```bash
# Test main flows
python main.py --config config.yaml

# Review results
cat reports/ai_test_results_*.json | jq .
```

### **Debugging Failures**
```bash
# Run specific module
python main.py --config config.yaml --single-module "login"

# Check AI analysis
python -c "
from ai_agent.learning_layer import get_learning_layer
print(get_learning_layer().get_failure_summary())
"
```

### **CI/CD Integration**
```bash
# Run and exit with failure code if tests fail
python main.py --url "https://staging.example.com"
EXIT_CODE=$?

if [ $EXIT_CODE -ne 0 ]; then
    echo "Tests failed!"
    exit 1
fi
```

---

## 💡 Tips & Best Practices

1. **Start Small** - Test one page first, then expand
2. **Review AI Analysis** - Check `failure_analysis` in reports
3. **Use Stable Selectors** - Prefer `data-testid` over classes
4. **Monitor Costs** - Check token usage in Langfuse dashboard
5. **Update Prompts** - Customize for your specific needs
6. **Track History** - Learning layer improves over time

---

## 🚀 Next Steps

1. ✅ Run health check: `python -m ai_agent.health_check`
2. ✅ Test with real URL: `python main.py --url "https://yourapp.com"`
3. ✅ Review results in `reports/`
4. ✅ Check AI failure analysis
5. ✅ Customize prompts if needed

---

## 📞 Support

- Health Check: `python -m ai_agent.health_check`
- View Config: `cat .env` (check credentials)
- Test Prompts: Check `ai_agent/prompts/`
- View Reports: `ls reports/`
- Failure History: Run learning layer script

---

**System is production-ready! 🎉**
