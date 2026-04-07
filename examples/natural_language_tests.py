"""
Natural Language Test Creation Example
Shows how non-technical users can create tests using plain English
"""
from ai_agent.utils.prompt_loader import load_prompt
from ai_agent.utils.prompt_formatter import format_prompt
from langchain_openai import AzureChatOpenAI
from ai_agent.config import AIConfig
import json


def create_tests_from_natural_language(user_input: str) -> dict:
    """
    User describes what they want to test in plain English
    AI converts it to detailed test scenarios
    
    Args:
        user_input: Plain English description
        
    Returns:
        Structured test scenarios
        
    Example:
        user_input = "I want to test creating a segment for cardiologists in California"
        
        Returns detailed scenarios with:
        - Positive: Create segment with filters
        - Edge cases: Maximum filters, special characters
        - Negative: SQL injection, invalid data
    """
    
    # Load planner prompt
    prompt_data = load_prompt("ai_agent/prompts/planner.yaml")
    
    # Format with natural language input (no UI data needed!)
    formatted_prompt = format_prompt(
        prompt_data,
        user_description=user_input,  # Natural language!
        domain_context="HCP Targeting & Segmentation: Medical specialties, NPI numbers, segments, filters",
        compliance_requirements="HIPAA compliance, PII masking, data privacy",
        ui_data=""  # Optional - AI will infer from description
    )
    
    # Initialize LLM
    llm = AzureChatOpenAI(
        azure_deployment=AIConfig.AZURE_OPENAI_DEPLOYMENT,
        openai_api_version=AIConfig.AZURE_OPENAI_API_VERSION,
        azure_endpoint=AIConfig.AZURE_OPENAI_ENDPOINT,
        api_key=AIConfig.AZURE_OPENAI_API_KEY,
        temperature=0.7
    )
    
    # Get scenarios
    response = llm.invoke(formatted_prompt)
    
    # Parse JSON
    content = response.content.strip()
    if content.startswith("```"):
        content = content.split("```")[1]
        if content.startswith("json"):
            content = content[4:]
    
    return json.loads(content)


# Example Usage
if __name__ == "__main__":
    print("="*80)
    print("NATURAL LANGUAGE TEST CREATION")
    print("="*80)
    
    # Example 1: Simple description
    print("\n📝 User Input (Plain English):")
    user_input_1 = "Test creating a segment for top cardiologists in California"
    print(f'   "{user_input_1}"')
    
    print("\n🤖 AI Generates:")
    scenarios_1 = create_tests_from_natural_language(user_input_1)
    print(json.dumps(scenarios_1, indent=2))
    
    print("\n" + "="*80)
    
    # Example 2: More complex description
    print("\n📝 User Input (More Details):")
    user_input_2 = """
    I need to test the HCP export functionality. 
    Users should be able to export segment data to CSV with NPI numbers, 
    specialty, and state. Make sure it handles large exports (100,000+ HCPs) 
    and checks for proper authorization.
    """
    print(f'   "{user_input_2.strip()}"')
    
    print("\n🤖 AI Generates:")
    scenarios_2 = create_tests_from_natural_language(user_input_2)
    print(json.dumps(scenarios_2, indent=2))
    
    print("\n" + "="*80)
    print("✅ Natural Language → Structured Test Scenarios")
    print("="*80)
