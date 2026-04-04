"""
End-to-End Test Script
Tests the complete system with a real website
"""
import subprocess
import sys
import os
import json

def run_test(url: str, description: str):
    """Run a test and display results"""
    print("\n" + "="*60)
    print(f"TEST: {description}")
    print("="*60)
    print(f"URL: {url}\n")
    
    # Run the test
    try:
        result = subprocess.run(
            ["python", "main.py", "--url", url, "--no-langfuse"],
            capture_output=True,
            text=True,
            timeout=120  # 2 minute timeout
        )
        
        # Print output
        print(result.stdout)
        
        if result.stderr:
            print("STDERR:", result.stderr)
        
        # Check exit code
        if result.returncode == 0:
            print("\n✅ TEST PASSED")
            return True
        else:
            print(f"\n❌ TEST FAILED (exit code: {result.returncode})")
            return False
    
    except subprocess.TimeoutExpired:
        print("\n❌ TEST TIMEOUT (exceeded 2 minutes)")
        return False
    
    except Exception as e:
        print(f"\n❌ TEST ERROR: {e}")
        return False


def main():
    """Run end-to-end tests"""
    print("\n" + "="*60)
    print("AI TESTING AGENT - END-TO-END TESTS")
    print("="*60)
    
    # Check if .env is configured
    if not os.path.exists(".env"):
        print("\n❌ .env file not found")
        print("Run setup script first: setup.ps1 (Windows) or setup.sh (Linux/Mac)")
        return 1
    
    # Load .env and check credentials
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "")
    if not api_key or api_key == "your_api_key_here":
        print("\n❌ Azure credentials not configured in .env")
        print("Edit .env file and add your AZURE_OPENAI_API_KEY")
        return 1
    
    print("\n✓ Configuration check passed")
    
    # Run health check first
    print("\n" + "="*60)
    print("Running Health Check...")
    print("="*60)
    
    health_result = subprocess.run(
        ["python", "-m", "ai_agent.health_check"],
        capture_output=True,
        text=True
    )
    
    print(health_result.stdout)
    
    if health_result.returncode != 0:
        print("\n❌ Health check failed")
        print("Fix the issues above before running tests")
        return 1
    
    # Run tests
    tests = [
        {
            "url": "https://www.google.com",
            "description": "Test with Google homepage (simple UI)"
        },
        {
            "url": "https://www.wikipedia.org",
            "description": "Test with Wikipedia (complex UI)"
        }
    ]
    
    results = []
    for test in tests:
        success = run_test(test["url"], test["description"])
        results.append({
            "url": test["url"],
            "description": test["description"],
            "passed": success
        })
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    
    print(f"\nTotal Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    for i, result in enumerate(results, 1):
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"\n{i}. {status} - {result['description']}")
        print(f"   URL: {result['url']}")
    
    # Check reports directory
    if os.path.exists("reports"):
        reports = [f for f in os.listdir("reports") if f.endswith(".json")]
        if reports:
            print(f"\n📁 {len(reports)} report(s) generated in reports/")
            latest = max(reports)
            print(f"   Latest: {latest}")
    
    # Final result
    print("\n" + "="*60)
    if failed == 0:
        print("✅ ALL TESTS PASSED!")
        print("="*60)
        print("\n🎉 System is working correctly!")
        print("\nNext steps:")
        print("  1. Test with your own application URL")
        print("  2. Configure multi-module testing in config.yaml")
        print("  3. Review generated reports in reports/")
        return 0
    else:
        print("❌ SOME TESTS FAILED")
        print("="*60)
        print("\n⚠️  Please review the errors above")
        print("   Check .env configuration and network connectivity")
        return 1


if __name__ == "__main__":
    sys.exit(main())
