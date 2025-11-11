"""
Script de test end-to-end pour valider le système complet.

Ce script:
1. Charge un template et des contacts
2. Initialise l'orchestrateur
3. Génère une campagne
4. Affiche les résultats
"""

import os
from dotenv import load_dotenv
from src.orchestrator import CampaignOrchestrator
from src.schemas.campaign_schemas import CampaignRequest, Contact

# Load env vars
load_dotenv()

# Vérifier que la clé API est configurée
if not os.getenv("OPENAI_API_KEY"):
    print("OPENAI_API_KEY not found in environment")
    print("Please add it to your .env file")
    exit(1)


def test_campaign_generation():
    """Test complet de génération de campagne."""

    print("=" * 60)
    print("TEST: Campaign Generation End-to-End (Atomic Agents v2)")
    print("=" * 60)

    # 1. Charger le template
    print("\n[*] Loading email template...")
    template_path = "data/templates/cold_email_template_example.md"
    if not os.path.exists(template_path):
        print(f"[ERROR] Template not found: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read()
        # Extraire juste le template, pas les instructions
        template_content = template_content.split("---")[0].strip()

    print(f"[OK] Template loaded ({len(template_content)} characters)")

    # 2. Créer des contacts de test
    print("\n[*] Creating test contacts...")
    contacts = [
        Contact(
            company_name="Aircall",
            first_name="Sophie",
            last_name="Durand",
            email="sophie@aircall.io",
            website="https://aircall.io",
            industry="SaaS"
        )
    ]
    print(f"[OK] {len(contacts)} contacts created")

    # 3. Préparer le contexte
    print("\n[*] Preparing context...")
    data_dir = os.getenv("DATA_DIR", "./data")
    client_name = "example-client"

    context = {
        "client_name": client_name
    }

    context_paths = {
        "pci": os.path.join(data_dir, "clients", client_name, "pci.md"),
        "personas": os.path.join(data_dir, "clients", client_name, "personas.md"),
        "pain_points": os.path.join(data_dir, "clients", client_name, "pain_points.md"),
        "competitors": os.path.join(data_dir, "clients", client_name, "competitors.md"),
        "case_studies": os.path.join(data_dir, "clients", client_name, "case_studies.md")
    }

    # Vérifier que les fichiers existent
    existing_files = []
    for key, path in context_paths.items():
        if os.path.exists(path):
            existing_files.append(key)
            print(f"  [OK] {key}: {path}")
        else:
            print(f"  [WARN] {key}: {path} (not found, will use fallbacks)")

    # 4. Créer la requête
    print("\n[*] Creating campaign request...")
    request = CampaignRequest(
        template_content=template_content,
        contacts=contacts,
        context=context,
        batch_id="test-batch-001",
        enable_cache=True
    )
    print("[OK] Campaign request created")

    # 5. Initialiser l'orchestrateur
    print("\n[*] Initializing orchestrator (Atomic Agents v2)...")
    orchestrator = CampaignOrchestrator(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        enable_cache=True
    )
    print("[OK] Orchestrator initialized")

    # 6. Exécuter la génération
    print("\n[*] Starting campaign generation...")
    print("This may take 30-60 seconds depending on the model...")
    print("-" * 60)

    result = orchestrator.run(request)

    print("-" * 60)
    print("[OK] Campaign generation completed!")

    # 7. Afficher les résultats
    print("\n[*] RESULTS:")
    print("=" * 60)
    print(f"Total contacts: {result.total_contacts}")
    print(f"Success count: {result.success_count}")
    print(f"Success rate: {result.success_rate * 100:.1f}%")
    print(f"Average quality score: {result.average_quality_score:.1f}/100")
    print(f"Total execution time: {result.total_execution_time_seconds:.2f}s")
    print(f"Average time per email: {result.average_time_per_email_seconds:.2f}s")
    print(f"Cache hit rate: {result.cache_hit_rate * 100:.1f}%")
    print(f"Total tokens used: {result.total_tokens_used}")
    print(f"Estimated cost: ${result.estimated_cost_usd:.4f}")

    # 8. Afficher le premier email généré
    if result.emails_generated:
        print("\n[*] FIRST EMAIL GENERATED:")
        print("=" * 60)
        email = result.emails_generated[0]
        print(f"Contact: {email.contact.company_name}")
        print(f"Quality score: {email.quality_score}/100")
        print(f"Generation time: {email.generation_time_ms}ms")
        print(f"\nFallback levels:")
        for agent, level in email.fallback_levels.items():
            print(f"  - {agent}: Level {level}")
        print(f"\nConfidence scores:")
        for var, score in email.confidence_scores.items():
            print(f"  - {var}: {score}/5")
        print("\n" + "-" * 60)
        print("EMAIL CONTENT:")
        print("-" * 60)
        print(email.email_generated)
        print("-" * 60)

        # Afficher les variables
        print("\n[*] VARIABLES USED:")
        print("=" * 60)
        for key, value in email.variables.items():
            print(f"{key}: {value}")

    # 9. Afficher les logs
    if result.logs:
        print("\n[*] LOGS:")
        print("=" * 60)
        for log in result.logs:
            print(f"  {log}")

    # 10. Afficher les erreurs
    if result.errors:
        print("\n[ERROR] ERRORS:")
        print("=" * 60)
        for error in result.errors:
            print(f"  {error}")

    print("\n" + "=" * 60)
    print("[OK] TEST COMPLETED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_campaign_generation()
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrupted by user")
    except Exception as e:
        print(f"\n\n[ERROR] ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
