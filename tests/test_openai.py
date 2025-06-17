import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_openai_basic():
    """Basic OpenAI test without making API calls"""
    
    # Step 1: Check API key
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"1. API Key loaded: {'✅' if api_key else '❌'}")
    
    if api_key:
        print(f"   Key starts with sk-: {'✅' if api_key.startswith('sk-') else '❌'}")
        print(f"   Key length: {len(api_key)}")
        print(f"   Key preview: {api_key[:10]}...{api_key[-4:]}")
    
    # Step 2: Test import
    try:
        import openai
        print("2. OpenAI library import: ✅")
        print(f"   OpenAI version: {openai.__version__}")
    except Exception as e:
        print(f"2. Import failed: ❌ {e}")
        return
    
    print("\n🎯 Basic setup is working! API connection issue might be:")
    print("   - Network connectivity")
    print("   - API key permissions")
    print("   - OpenAI service status")

if __name__ == "__main__":
    test_openai_basic()
