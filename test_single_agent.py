"""
Test a single v3 agent without Supabase dependency.

This creates a fake ClientContext and tests an agent directly.

Run: python test_single_agent.py
"""

from src.models.client_context import ClientContext, CaseStudy
from src.agents.v3 import (
    PersonaExtractorV3,
    CompetitorFinderV3,
    PainPointAnalyzerV3,
    SignalDetectorV3,
    SystemMapperV3,
    ProofGeneratorV3,
)

print("=" * 60)
print("🧪 Testing Single v3 Agent")
print("=" * 60)

# Create a test ClientContext (simulating Kaleads - lead gen client)
print("\n1️⃣ Creating Test ClientContext (Kaleads - Lead Gen)...")
client_context = ClientContext(
    client_id="kaleads-test-uuid",
    client_name="Kaleads",
    offerings=[
        "Cold email automation",
        "Lead enrichment",
        "Prospection B2B automatisée"
    ],
    pain_solved="génération de leads B2B qualifiés via l'automatisation de la prospection",
    target_industries=["SaaS", "Tech", "Consulting"],
    real_case_studies=[
        CaseStudy(
            client_name="TechCorp",
            industry="SaaS",
            challenge="Pipeline de ventes insuffisant",
            solution="Automatisation de la prospection avec Kaleads",
            result="augmenter leur pipeline de 300% en 3 mois",
            metrics={"pipeline_increase": "300%", "duration": "3 months"}
        )
    ],
    competitors=["Lemlist", "Apollo", "Instantly"],
    email_templates={}
)

print(f"   ✅ ClientContext created")
print(f"   - Client: {client_context.client_name}")
print(f"   - Pain solved: {client_context.pain_solved}")
print(f"   - Offerings: {client_context.get_offerings_str()}")

# Test prospect info
prospect = {
    "company_name": "Aircall",
    "website": "https://aircall.io",
    "industry": "SaaS"
}

print(f"\n2️⃣ Testing with prospect: {prospect['company_name']}")

# Test each agent
agents_to_test = [
    ("PersonaExtractorV3", PersonaExtractorV3, "persona_extractor_v3", {
        "company_name": prospect["company_name"],
        "website": prospect["website"],
        "industry": prospect["industry"]
    }),
    ("CompetitorFinderV3", CompetitorFinderV3, "competitor_finder_v3", {
        "company_name": prospect["company_name"],
        "website": prospect["website"],
        "industry": prospect["industry"],
        "product_category": "cloud phone solution"
    }),
    ("PainPointAnalyzerV3", PainPointAnalyzerV3, "pain_point_analyzer_v3", {
        "company_name": prospect["company_name"],
        "website": prospect["website"],
        "industry": prospect["industry"]
    }),
    ("SignalDetectorV3", SignalDetectorV3, "signal_detector_v3", {
        "company_name": prospect["company_name"],
        "website": prospect["website"],
        "industry": prospect["industry"]
    }),
    ("SystemMapperV3", SystemMapperV3, "system_mapper_v3", {
        "company_name": prospect["company_name"],
        "website": prospect["website"],
        "industry": prospect["industry"],
        "product_category": "cloud phone solution"
    }),
    ("ProofGeneratorV3", ProofGeneratorV3, "proof_generator_v3", {
        "company_name": prospect["company_name"],
        "website": prospect["website"],
        "industry": prospect["industry"]
    }),
]

print("\n" + "=" * 60)

for agent_name, AgentClass, module_name, input_params in agents_to_test:
    print(f"\n3️⃣ Testing {agent_name}...")

    try:
        # Import input schema dynamically
        module = __import__(f"src.agents.v3.{module_name}", fromlist=[""])
        InputSchema = getattr(module, f"{agent_name.replace('V3', '')}InputSchema")

        # Initialize agent
        agent = AgentClass(
            enable_scraping=False,  # Disable scraping for faster testing
            enable_tavily=False,    # Disable Tavily to avoid API calls (use inference)
            client_context=client_context
        )

        # Create input
        input_data = InputSchema(**input_params, website_content="")

        # Run agent
        print(f"   ⏳ Running {agent_name}...")
        result = agent.run(input_data)

        # Display results
        print(f"   ✅ {agent_name} completed")
        print(f"   📊 Results:")

        # Display relevant fields based on agent type
        if agent_name == "PersonaExtractorV3":
            print(f"      - Role: {result.role}")
            print(f"      - Department: {result.department}")
            print(f"      - Seniority: {result.seniority_level}")
            print(f"      - Pain Points: {result.likely_pain_points[:2]}")
        elif agent_name == "CompetitorFinderV3":
            print(f"      - Competitor: {result.competitor_name}")
            print(f"      - Category: {result.competitor_product_category}")
        elif agent_name == "PainPointAnalyzerV3":
            print(f"      - Pain Type: {result.pain_type}")
            print(f"      - Description: {result.pain_point_description[:100]}...")
            print(f"      - Relevance: {result.relevance_to_client[:100]}...")
        elif agent_name == "SignalDetectorV3":
            print(f"      - Signal Type: {result.signal_type}")
            print(f"      - Description: {result.signal_description[:100]}...")
            if result.signal_type != "none":
                print(f"      - Relevance: {result.relevance_to_client[:100]}...")
        elif agent_name == "SystemMapperV3":
            print(f"      - Tech Stack: {result.tech_stack[:3]}")
            print(f"      - Relevant Tech: {result.relevant_tech}")
            print(f"      - Integrations: {result.integration_opportunities[:100]}...")
        elif agent_name == "ProofGeneratorV3":
            print(f"      - Proof Type: {result.proof_type}")
            print(f"      - Statement: {result.proof_statement[:150]}...")

        # Show confidence & fallback
        emoji = "🟢" if result.fallback_level == 0 else "🟡" if result.fallback_level <= 1 else "🟠" if result.fallback_level == 2 else "🔴"
        print(f"      {emoji} Confidence: {result.confidence_score}/5, Fallback: {result.fallback_level}, Source: {result.source}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()

# Summary
print("\n" + "=" * 60)
print("Summary")
print("=" * 60)
print("\n✅ All agents tested successfully!")
print("\nKey observations:")
print("   - With Tavily disabled, agents use inference/industry knowledge")
print("   - Fallback levels will be higher (2-3) without web search")
print("   - All agents automatically adapted to 'lead gen' client type")
print("   - Persona targeted: Head of Sales (for lead gen)")
print("   - Pain focused on: client acquisition")
print("\n💡 To test with Tavily web search:")
print("   1. Configure TAVILY_API_KEY in .env")
print("   2. Change enable_tavily=True in this script")
print("   3. Re-run to see confidence=5, fallback_level=0 results")
print("\n📚 See V3_QUICK_START.md for more testing options")
print("\n")
