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
    
    # Token Limits (TESTING MODE - No limits, measure actual usage)
    MAX_TOKENS_PLANNER = 4000    # Unlimited for testing
    MAX_TOKENS_DESIGNER = 4000   # Unlimited for testing
    MAX_TOKENS_VALIDATOR = 4000  # Unlimited for testing (includes root cause + self-healing)
    
    # Temperature Settings
    TEMPERATURE = 0  # Deterministic output
    
    # Prompt Caching (reduces costs for repeated prompts)
    ENABLE_PROMPT_CACHING = True  # Cache system prompts
    CACHE_TTL_SECONDS = 300  # Cache validity: 5 minutes
    
    # Workflow Safeguards (TESTING MODE - Generous limits)
    MAX_TESTS = 100  # Allow up to 100 tests to see full potential
    MAX_ITERATIONS = 1  # Maximum feedback loop iterations (SAFE: only 1 retry allowed)
    TIMEOUT_MINUTES = 60  # 1 hour maximum for comprehensive testing
    ENABLE_LIFECYCLE_LOOP = False  # Enable safe lifecycle loop (max 1 retry)
    ENABLE_LEARNING_LAYER = True  # Enable failure history tracking
    
    # Langfuse Settings (Optional - for observability)
    LANGFUSE_PUBLIC_KEY = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    LANGFUSE_SECRET_KEY = os.getenv("LANGFUSE_SECRET_KEY", "")
    LANGFUSE_HOST = os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    @classmethod
    def validate(cls):
        """Validate required configuration"""
        if not cls.AZURE_OPENAI_API_KEY:
            raise ValueError("AZURE_OPENAI_API_KEY not set in environment")
        if not cls.AZURE_OPENAI_ENDPOINT:
            raise ValueError("AZURE_OPENAI_ENDPOINT not set in environment")
        return True
