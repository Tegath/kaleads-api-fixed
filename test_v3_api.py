"""
Test v3.0 API with a real request.

Prerequisites:
1. Start API server: python src/api/n8n_optimized_api.py
2. Configure .env with API keys
3. Have a client in Supabase

Run: python test_v3_api.py
"""

import requests
import json
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_URL = "http://localhost:8001"
API_KEY = os.getenv("API_KEY", "your-secure-api-key-for-n8n")

print("=" * 60)
print("🧪 Testing v3.0 API")
print("=" * 60)

# 1. Health Check
print("\n1️⃣ Testing Health Check...")
try:
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        health = response.json()
        print(f"   ✅ API is healthy")
        print(f"   - OpenRouter: {'✅' if health.get('openrouter_key_configured') else '❌'}")
        print(f"   - Supabase: {'✅' if health.get('supabase_configured') else '❌'}")
        print(f"   - Tavily: {'✅' if health.get('tavily_configured') else '❌'}")
        print(f"   - Version: {health.get('version')}")
    else:
        print(f"   ❌ Health check failed: {response.status_code}")
        exit(1)
except requests.exceptions.ConnectionError:
    print("   ❌ Cannot connect to API. Make sure it's running:")
    print("      python src/api/n8n_optimized_api.py")
    exit(1)

# 2. Root Endpoint
print("\n2️⃣ Testing Root Endpoint...")
try:
    response = requests.get(f"{API_URL}/")
    if response.status_code == 200:
        root = response.json()
        print(f"   ✅ Root endpoint working")
        print(f"   - Message: {root.get('message')}")
        print(f"   - Agents: {', '.join(root.get('agents', []))}")
    else:
        print(f"   ❌ Root endpoint failed: {response.status_code}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# 3. Generate Email (TEST MODE - No real client needed)
print("\n3️⃣ Testing Email Generation (with test client)...")
print("   ⚠️ This will fail if you don't have a real client in Supabase")
print("   ⚠️ Replace 'test-client-uuid' with a real client_id from your Supabase")

# Test request
test_request = {
    "client_id": "test-client-uuid",  # ⚠️ REPLACE with real client_id
    "contact": {
        "company_name": "Aircall",
        "first_name": "Sophie",
        "last_name": "Martin",
        "email": "sophie@aircall.io",
        "website": "https://aircall.io",
        "industry": "SaaS"
    },
    "options": {
        "model_preference": "balanced",
        "enable_scraping": False,  # Disable for faster testing
        "enable_tavily": True,
        "enable_pci_filter": False  # Disable PCI filter for testing
    }
}

print("\n   Request payload:")
print(json.dumps(test_request, indent=2))

try:
    print("\n   Sending request (this may take 20-30 seconds)...")
    response = requests.post(
        f"{API_URL}/api/v2/generate-email",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json=test_request,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()
        print("\n   ✅ Email generated successfully!")
        print("\n" + "=" * 60)
        print("Generated Email:")
        print("=" * 60)
        print(result.get("email_content", "No email content"))
        print("\n" + "=" * 60)
        print("Metadata:")
        print("=" * 60)
        print(f"   - Target Persona: {result.get('target_persona')}")
        print(f"   - Competitor: {result.get('competitor_name')}")
        print(f"   - Pain Point: {result.get('problem_specific')}")
        print(f"   - Signal: {result.get('specific_signal_1')}")
        print(f"   - Tech Stack: {result.get('system_1')}, {result.get('system_2')}, {result.get('system_3')}")
        print(f"   - Quality Score: {result.get('quality_score')}/100")
        print(f"   - Cost: ${result.get('cost_usd')}")
        print(f"   - Time: {result.get('generation_time_seconds')}s")

        print("\n" + "=" * 60)
        print("Fallback Levels (0=best, 3=generic):")
        print("=" * 60)
        fallback_levels = result.get('fallback_levels', {})
        for agent, level in fallback_levels.items():
            emoji = "🟢" if level == 0 else "🟡" if level <= 1 else "🟠" if level == 2 else "🔴"
            print(f"   {emoji} {agent}: {level}")

    elif response.status_code == 401:
        print("   ❌ Authentication failed. Check API_KEY in .env")
    elif response.status_code == 500:
        error = response.json()
        print(f"   ❌ Server error: {error.get('detail', 'Unknown error')}")
        print("\n   Common causes:")
        print("   - Invalid client_id (client not found in Supabase)")
        print("   - Missing API keys in .env")
        print("   - Supabase connection issue")
    else:
        print(f"   ❌ Unexpected status: {response.status_code}")
        print(f"   Response: {response.text}")

except requests.exceptions.Timeout:
    print("   ❌ Request timeout (took > 60s)")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Summary
print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("\n✅ If you see a generated email above, v3.0 is working!")
print("\n❌ If you got errors:")
print("   1. Make sure API is running: python src/api/n8n_optimized_api.py")
print("   2. Replace 'test-client-uuid' with real client_id from Supabase")
print("   3. Check .env has all required keys")
print("   4. Run: python test_v3_setup.py to debug setup")
print("\n📚 See V3_QUICK_START.md for more testing options")
print("\n")
