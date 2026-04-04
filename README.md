# Targeting and Segmentation AI - Multi-Agent Testing System

**Modern AI-powered test automation using LangChain + LangGraph + Langfuse**

## 🎯 Architecture Overview

This is a **controlled multi-agent AI system** that generates and executes tests intelligently without autonomous loops.

```
┌─────────────────────────────────────────────────────────────┐
│                    Multi-Agent Workflow                      │
│  Planner → Designer → Executor → Validator → STOP           │
└─────────────────────────────────────────────────────────────┘
```

### Components

1. **Planner Agent** (LLM) - Analyzes UI and generates test scenarios
2. **Designer Agent** (LLM) - Converts scenarios to executable YAML test steps
3. **Executor** (NO AI) - Runs tests using Playwright + API + DB validation
4. **Validator Agent** (LLM) - Analyzes results and identifies root causes

## 🧠 Tech Stack

- **LangChain** - Prompt templates, structured output
- **LangGraph** - Workflow control (prevents loops)
- **Langfuse** - Observability, token tracking, cost monitoring
- **Azure GPT-4o** - LLM brain
- **Playwright** - UI automation
- **Python** - Execution engine

## 🚀 Quick Start

### 1. Install Dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Configure Azure GPT-4o

Create `.env` file:

```bash
# Azure OpenAI
AZURE_OPENAI_API_KEY=your-key-here
AZURE_OPENAI_ENDPOINT=https://your-endpoint.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Application URL
APP_URL=https://ce-ts-dev.trinitylifesciences.com

# Database (optional)
DB_HOST=mysql-customerengagement-dev.mysql.database.azure.com
DB_USER=hcp_targetandsegment_user
DB_PASSWORD=your-password
DB_NAME=mysql_hcp_targetandsegmentation_dev
```

### 3. Run AI Agent

**Single URL Mode:**
```powershell
python main.py --url https://your-app-url.com/segments
```

**Multi-Module Mode (using config file):**
```powershell
# Edit config.yaml first to define modules
python main.py --config config.yaml

# Or use default config.yaml
python main.py
```

**Config File Example (`config.yaml`):**
```yaml
app:
  base_url: "https://your-app.com"

modules:
  - name: "login"
    url: "/login"
    enabled: true
    
  - name: "dashboard"
    url: "/dashboard"
    enabled: true
```

## 📁 Project Structure

```
Targeting_and_Segmentation_AI/
├── ai_agent/
│   ├── agents/           # LLM agents (Planner, Designer, Validator)
│   ├── tools/            # UI extractor, Executor
│   ├── graph/            # LangGraph workflow
│   ├── prompts/          # Prompt templates (easy to modify)
│   └── config.py         # Azure GPT-4o configuration
├── tests/                # Generated test files
├── reports/              # Test execution reports
├── main.py               # Entry point
├── requirements.txt      # Dependencies
└── .env                  # Configuration (not committed)
```

## 🔥 Key Features

### ✅ Token Efficiency
- Planner: 300 tokens max
- Designer: 500 tokens max
- Validator: 200 tokens max

### ✅ No Autonomous Loops
- Fixed workflow with END condition
- No retry chains
- Deterministic execution

### ✅ Tri-Layer Validation
- UI validation (Playwright)
- API validation (REST)
- DB validation (MySQL)

### ✅ Observability
- Langfuse tracks all prompts
- Token usage monitoring
- Cost tracking per agent

## 🎯 How It Works

```
1. User provides URL
   ↓
2. UI Extractor (Playwright) scans page
   ↓
3. Planner Agent (GPT-4o) generates scenarios
   ↓
4. Designer Agent (GPT-4o) creates YAML test steps
   ↓
5. Executor runs tests (NO AI - deterministic)
   ↓
6. Validator Agent (GPT-4o) analyzes results
   ↓
7. Report generated + Langfuse logs
```

## 🚨 Critical Rules

❌ **NEVER DO:**
- Autonomous agent loops
- Self-calling agents
- "Retry until success"
- Unlimited LLM calls

✅ **ALWAYS DO:**
- Use structured output (JSON/YAML)
- Set token limits
- Define MAX_TESTS
- Control workflow with LangGraph

## 💬 Demo Explanation

*"We use a multi-agent AI architecture where each agent has a defined responsibility. LangGraph controls execution flow, LangChain standardizes prompts, and Langfuse provides observability."*

## 📊 Monitoring

Access Langfuse dashboard to see:
- All prompts used
- LLM responses
- Token usage per agent
- Cost breakdown
- Execution traces

## 🛠 Development

### Adding New Agents

1. Create agent in `ai_agent/agents/`
2. Add to workflow in `ai_agent/graph/workflow.py`
3. Update token limits in `ai_agent/config.py`

### Modifying Prompts

Edit prompt templates in agent files:
- `agents/planner.py`
- `agents/designer.py`
- `agents/validator.py`

## 📝 License

Internal project for Trinity Life Sciences

---

**Built with controlled AI - No autonomous loops, full observability**
