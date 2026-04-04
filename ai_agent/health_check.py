"""
System Health Check - Verify all components work
Run this before using the system to diagnose issues
"""
import os
import sys

def check_health():
    """Check system health"""
    print("\n🏥 AI Testing Agent - Health Check")
    print("="*60)
    
    issues = []
    warnings = []
    
    # 1. Check Azure credentials
    print("\n1. Azure GPT-4o Configuration")
    print("-" * 60)
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    
    if not api_key or api_key == "your_api_key_here":
        issues.append("AZURE_OPENAI_API_KEY not configured in .env")
        print("   ❌ API Key: Not configured")
    else:
        print(f"   ✅ API Key: Configured ({api_key[:10]}...)")
    
    if not endpoint or endpoint == "your_endpoint_here":
        issues.append("AZURE_OPENAI_ENDPOINT not configured in .env")
        print("   ❌ Endpoint: Not configured")
    else:
        print(f"   ✅ Endpoint: {endpoint}")
    
    # 2. Check prompt files
    print("\n2. Prompt Files")
    print("-" * 60)
    
    prompts = [
        "planner_prompt.txt",
        "designer_prompt.txt", 
        "validator_prompt.txt",
        "failure_analyzer_prompt.txt",
        "ui_automation_prompt.txt",
        "api_testing_prompt.txt",
        "data_validation_prompt.txt"
    ]
    
    for prompt in prompts:
        path = os.path.join("ai_agent", "prompts", prompt)
        if os.path.exists(path):
            size = os.path.getsize(path)
            print(f"   ✅ {prompt} ({size} bytes)")
        else:
            issues.append(f"Missing prompt file: {prompt}")
            print(f"   ❌ {prompt}")
    
    # 3. Check agent files
    print("\n3. Agent Files")
    print("-" * 60)
    
    agents = [
        "planner.py",
        "designer.py",
        "validator.py",
        "failure_analyzer.py",
        "ui_automation_agent.py",
        "api_testing_agent.py",
        "data_validation_agent.py"
    ]
    
    for agent in agents:
        path = os.path.join("ai_agent", "agents", agent)
        if os.path.exists(path):
            print(f"   ✅ {agent}")
        else:
            warnings.append(f"Optional agent missing: {agent}")
            print(f"   ⚠ {agent} (optional)")
    
    # 4. Check dependencies
    print("\n4. Python Dependencies")
    print("-" * 60)
    
    dependencies = [
        ("langchain", "LangChain"),
        ("langchain_openai", "LangChain OpenAI"),
        ("langgraph", "LangGraph"),
        ("playwright", "Playwright"),
        ("pyyaml", "PyYAML"),
        ("requests", "Requests"),
        ("python-dotenv", "python-dotenv")
    ]
    
    for module, name in dependencies:
        try:
            __import__(module)
            print(f"   ✅ {name}")
        except ImportError:
            issues.append(f"Missing dependency: {name}")
            print(f"   ❌ {name}")
    
    # 5. Check Langfuse (optional)
    print("\n5. Langfuse (Optional)")
    print("-" * 60)
    
    try:
        import langfuse
        langfuse_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
        if langfuse_key:
            print("   ✅ Langfuse installed and configured")
        else:
            warnings.append("Langfuse installed but not configured")
            print("   ⚠ Langfuse installed but not configured (optional)")
    except ImportError:
        print("   ⚠ Langfuse not installed (optional)")
    
    # 6. Check directories
    print("\n6. Directory Structure")
    print("-" * 60)
    
    directories = ["reports", "learning_data", "ai_agent/prompts", "ai_agent/agents"]
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"   ✅ {directory}/")
        else:
            warnings.append(f"Directory missing: {directory}")
            print(f"   ⚠ {directory}/ (will be created)")
            try:
                os.makedirs(directory, exist_ok=True)
            except:
                pass
    
    # 7. Check config files
    print("\n7. Configuration Files")
    print("-" * 60)
    
    configs = [
        (".env", "Environment variables"),
        ("config.yaml", "Multi-module config"),
        ("requirements.txt", "Dependencies list")
    ]
    
    for config_file, desc in configs:
        if os.path.exists(config_file):
            print(f"   ✅ {config_file} - {desc}")
        else:
            if config_file == ".env":
                issues.append(f"Missing {config_file}")
                print(f"   ❌ {config_file} - {desc}")
            else:
                warnings.append(f"Missing {config_file}")
                print(f"   ⚠ {config_file} - {desc} (optional)")
    
    # Summary
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    if issues:
        print(f"\n❌ {len(issues)} CRITICAL ISSUE(S) FOUND:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
        print("\n⚠️  System is NOT ready. Please fix the issues above.")
        return False
    elif warnings:
        print(f"\n⚠️  {len(warnings)} WARNING(S):")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
        print("\n✅ System is functional but has warnings.")
        print("   Optional components missing - system will work with reduced features.")
        return True
    else:
        print("\n✅ ALL CHECKS PASSED!")
        print("   System is ready to use.")
        print("\n🚀 Next step: python main.py --url 'https://example.com'")
        return True


if __name__ == "__main__":
    success = check_health()
    sys.exit(0 if success else 1)
