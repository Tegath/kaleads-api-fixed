"""
Quick test script to verify v3.0 setup.

Run: python test_v3_setup.py
"""

import os
from dotenv import load_dotenv

# Load environment
load_dotenv()

print("=" * 60)
print("🧪 Testing v3.0 Setup")
print("=" * 60)

# 1. Check environment variables
print("\n1️⃣ Checking Environment Variables...")
env_vars = {
    "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY"),
    "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY"),
    "SUPABASE_URL": os.getenv("SUPABASE_URL"),
    "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
}

for var, value in env_vars.items():
    if value:
        print(f"   ✅ {var}: Configured")
    else:
        print(f"   ❌ {var}: Missing")

# 2. Check imports
print("\n2️⃣ Checking v3 Imports...")
try:
    from src.agents.v3 import (
        PersonaExtractorV3,
        CompetitorFinderV3,
        PainPointAnalyzerV3,
        SignalDetectorV3,
        SystemMapperV3,
        ProofGeneratorV3,
    )
    print("   ✅ All v3 agents import successfully")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    exit(1)

# 3. Check ClientContext
print("\n3️⃣ Checking ClientContext...")
try:
    from src.models.client_context import ClientContext, CaseStudy
    print("   ✅ ClientContext model available")
except ImportError as e:
    print(f"   ❌ Import error: {e}")
    exit(1)

# 4. Check Tavily
print("\n4️⃣ Checking Tavily...")
try:
    from src.providers.tavily_client import get_tavily_client
    tavily = get_tavily_client()
    if tavily.enabled:
        print("   ✅ Tavily configured and enabled")

        # Quick test search
        try:
            results = tavily.search("test", max_results=1)
            print("   ✅ Tavily API working (test search successful)")
        except Exception as e:
            print(f"   ⚠️ Tavily API error: {e}")
    else:
        print("   ⚠️ Tavily not configured (will use fallback)")
except ImportError as e:
    print(f"   ❌ Import error: {e}")

# 5. Check Supabase
print("\n5️⃣ Checking Supabase...")
try:
    from src.providers.supabase_client import SupabaseClient
    supabase = SupabaseClient()
    print("   ✅ SupabaseClient initialized")

    # Try to load a client context (will fail if no client exists, but that's ok)
    # We're just checking the method exists
    if hasattr(supabase, 'load_client_context_v3'):
        print("   ✅ load_client_context_v3() method available")
    else:
        print("   ❌ load_client_context_v3() method missing")
except Exception as e:
    print(f"   ❌ Supabase error: {e}")

# 6. Test individual agent initialization
print("\n6️⃣ Testing Agent Initialization...")

# Create a minimal ClientContext for testing
test_context = ClientContext(
    client_id="test-uuid",
    client_name="Test Company",
    offerings=["Test Offering"],
    pain_solved="test pain solved",
    target_industries=["SaaS"],
    real_case_studies=[],
    competitors=["Competitor A"],
    email_templates={}
)

agents_to_test = [
    ("PersonaExtractorV3", PersonaExtractorV3),
    ("CompetitorFinderV3", CompetitorFinderV3),
    ("PainPointAnalyzerV3", PainPointAnalyzerV3),
    ("SignalDetectorV3", SignalDetectorV3),
    ("SystemMapperV3", SystemMapperV3),
    ("ProofGeneratorV3", ProofGeneratorV3),
]

for agent_name, AgentClass in agents_to_test:
    try:
        agent = AgentClass(
            enable_scraping=False,
            enable_tavily=False,  # Disable to avoid API calls
            client_context=test_context
        )
        print(f"   ✅ {agent_name} initialized successfully")
    except Exception as e:
        print(f"   ❌ {agent_name} error: {e}")

# Summary
print("\n" + "=" * 60)
print("✅ Setup test complete!")
print("=" * 60)
print("\nNext steps:")
print("1. Fix any ❌ errors above")
print("2. Run individual agent tests: python src/agents/v3/persona_extractor_v3.py")
print("3. Start API: python src/api/n8n_optimized_api.py")
print("4. Test API endpoint: see test_v3_api.py")
print("\n")
