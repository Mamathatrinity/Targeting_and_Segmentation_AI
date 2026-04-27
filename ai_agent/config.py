"""
Azure GPT-4o Configuration
Token-efficient settings for AI agent system
"""
import os
from dotenv import load_dotenv

load_dotenv()


class AIConfig:
    """Configuration for AI agent system"""
    
    # Azure OpenAI Settings
    AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY", "")
    AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
    
    # Token Limits
    MAX_TOKENS_PLANNER   = 8000
    MAX_TOKENS_DESIGNER  = 16000  # bumped: 30 scenarios x ~10 steps x ~30 tokens = ~9000
    MAX_TOKENS_VALIDATOR = 8000   # bumped: 30 failures x detailed root cause

    # Temperature
    TEMPERATURE = 0  # Deterministic output

    # Caching
    ENABLE_PROMPT_CACHING = True
    CACHE_TTL_SECONDS     = 300   # 5 minutes

    # Workflow Safeguards
    MAX_TESTS               = 100  # hard cap on test cases sent to execution
    MAX_ITERATIONS          = 1    # max retry iterations
    MAX_FAILURES_TO_ANALYZE = 20   # max failed tests sent to validator LLM (top by priority)
    DESIGNER_BATCH_SIZE     = 10   # scenarios per designer LLM call (prevents token overflow)
    TIMEOUT_MINUTES         = 60
    ENABLE_LIFECYCLE_LOOP   = False
    ENABLE_LEARNING_LAYER   = True
    
    # Langfuse Settings (Optional - for observability)
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # ── Domain / prompt content (single source of truth — not in YAML) ──────
    DOMAIN_CONTEXT: str = os.getenv(
        "DOMAIN_CONTEXT",
        "HCP Targeting & Segmentation: medical specialties, segments, filters, "
        "NPI numbers, universe summaries, target lists, HIPAA compliance",
    )

    COMPLIANCE_REQUIREMENTS: str = os.getenv(
        "COMPLIANCE_REQUIREMENTS",
        "HIPAA compliance, PII masking, data privacy, no real patient data in tests, audit logging",
    )

    # Few-shot examples shown to the LLM — can be overridden via env var or
    # replaced with domain-specific examples loaded from a JSON/YAML config file.
    FEW_SHOT_EXAMPLES: str = os.getenv(
        "FEW_SHOT_EXAMPLES",
        (
            "  - module: Login\n"
            "    positive: 'User logs in with valid HCP credentials and sees Dashboard'\n"
            "    edge:     'User enters max-length username (254 chars) and valid password'\n"
            "    negative: 'User enters SQL injection in email field; system blocks and shows error'\n"
            "  - module: Segment Filter\n"
            "    positive: 'User applies Specialty=Oncology filter; result count updates correctly'\n"
            "    edge:     'User applies all filters simultaneously; combined result displays'\n"
            "    negative: 'User tries to save segment without required name; validation error shows'\n"
        ),
    )

    # Designer few-shot examples (depth: deep shown — lighter depths will use fewer layers)
    DESIGNER_FEW_SHOT_EXAMPLES: str = os.getenv(
        "DESIGNER_FEW_SHOT_EXAMPLES",
        (
            "  - scenario: 'User logs in with email user@co.com and password Pass123! and sees Dashboard'\n"
            "    depth: deep\n"
            "    steps:\n"
            "      - {action: navigate,    target: url,      value: 'https://app/login',        expected: 'Login page loads',           layer: UI}\n"
            "      - {action: fill,        target: Email,    value: 'user@co.com',               expected: 'Field populated',            layer: UI}\n"
            "      - {action: fill,        target: Password, value: 'Pass123!',                  expected: 'Field populated',            layer: UI}\n"
            "      - {action: click,       target: Login,    value: '',                           expected: 'Form submitted',             layer: UI}\n"
            "      - {action: verify_text, target: '',       value: '',                           expected: 'Dashboard visible',          layer: UI}\n"
            "      - {action: verify_api,  endpoint: /api/auth/session, expected_status: 200,     expected: 'Session active with token',  layer: API}\n"
            "      - {action: verify_db,   table: users, column: last_login, condition: 'IS NOT NULL WHERE email=\\'user@co.com\\'', expected: 'Login timestamp recorded', layer: DB}\n"
            "  - scenario: 'User applies Specialty filter Oncology and result count updates'\n"
            "    depth: medium\n"
            "    steps:\n"
            "      - {action: navigate,    target: url,       value: 'https://app/segments',      expected: 'Segment page loads',         layer: UI}\n"
            "      - {action: select,      target: Specialty, value: 'Oncology',                  expected: 'Filter selected',            layer: UI}\n"
            "      - {action: click,       target: Apply,     value: '',                           expected: 'Results refresh',            layer: UI}\n"
            "      - {action: verify_text, target: '',        value: '',                           expected: 'Result count > 0 visible',   layer: UI}\n"
            "      - {action: verify_api,  endpoint: /api/segments/filter, expected_status: 200,  expected: 'API returns filtered HCPs',  layer: API}\n"
        ),
    )

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEY not set in environment")
        if not cls.AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_ENDPOINT not set in environment")
        return True
