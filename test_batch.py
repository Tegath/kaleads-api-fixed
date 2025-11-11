"""
Script de test avec plusieurs contacts et feedback detaille.

Ce script permet de:
1. Tester avec plusieurs contacts (CSV ou hardcodes)
2. Exporter les resultats en CSV pour feedback
3. Analyser les emails generes
4. Identifier les problemes rapidement
"""

import os
import csv
import json
from datetime import datetime
from dotenv import load_dotenv
from src.orchestrator import CampaignOrchestrator
from src.schemas.campaign_schemas import CampaignRequest, Contact

# Load env vars
load_dotenv()

# Verifier que la cle API est configuree
if not os.getenv("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY not found in environment")
    print("Please add it to your .env file")
    exit(1)


def load_contacts_from_csv(csv_path: str) -> list[Contact]:
    """Charge les contacts depuis un fichier CSV."""
    contacts = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            contacts.append(Contact(
                company_name=row.get("company_name", ""),
                first_name=row.get("first_name", ""),
                last_name=row.get("last_name", ""),
                email=row.get("email", ""),
                website=row.get("website", ""),
                industry=row.get("industry", "")
            ))

    return contacts


def get_default_contacts() -> list[Contact]:
    """Retourne une liste de contacts de test par defaut."""
    return [
        Contact(
            company_name="Aircall",
            first_name="Sophie",
            last_name="Durand",
            email="sophie@aircall.io",
            website="https://aircall.io",
            industry="SaaS"
        ),
        Contact(
            company_name="Stripe",
            first_name="Jean",
            last_name="Martin",
            email="jean@stripe.com",
            website="https://stripe.com",
            industry="FinTech"
        ),
        Contact(
            company_name="Notion",
            first_name="Marie",
            last_name="Dubois",
            email="marie@notion.so",
            website="https://notion.so",
            industry="Productivity"
        ),
        Contact(
            company_name="Figma",
            first_name="Pierre",
            last_name="Bernard",
            email="pierre@figma.com",
            website="https://figma.com",
            industry="Design"
        ),
        Contact(
            company_name="Doctolib",
            first_name="Claire",
            last_name="Petit",
            email="claire@doctolib.fr",
            website="https://doctolib.fr",
            industry="HealthTech"
        )
    ]


def export_results_to_csv(result, output_path: str):
    """Exporte les resultats en CSV pour analyse et feedback."""

    with open(output_path, "w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "company_name",
            "first_name",
            "quality_score",
            "generation_time_ms",
            "target_persona",
            "problem_specific",
            "competitor_name",
            "case_study_result",
            "fallback_persona",
            "fallback_competitor",
            "fallback_pain",
            "fallback_signal",
            "fallback_system",
            "fallback_case_study",
            "confidence_persona",
            "confidence_competitor",
            "confidence_pain",
            "feedback",  # Colonne vide pour que vous ajoutiez vos commentaires
            "email_content"
        ]

        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for email in result.emails_generated:
            writer.writerow({
                "company_name": email.contact.company_name,
                "first_name": email.contact.first_name,
                "quality_score": email.quality_score,
                "generation_time_ms": email.generation_time_ms,
                "target_persona": email.variables.get("target_persona", ""),
                "problem_specific": email.variables.get("problem_specific", ""),
                "competitor_name": email.variables.get("competitor_name", ""),
                "case_study_result": email.variables.get("case_study_result", ""),
                "fallback_persona": email.fallback_levels.get("persona_agent", 0),
                "fallback_competitor": email.fallback_levels.get("competitor_agent", 0),
                "fallback_pain": email.fallback_levels.get("pain_agent", 0),
                "fallback_signal": email.fallback_levels.get("signal_agent", 0),
                "fallback_system": email.fallback_levels.get("system_agent", 0),
                "fallback_case_study": email.fallback_levels.get("case_study_agent", 0),
                "confidence_persona": email.confidence_scores.get("target_persona", 0),
                "confidence_competitor": email.confidence_scores.get("competitor_name", 0),
                "confidence_pain": email.confidence_scores.get("problem_specific", 0),
                "feedback": "",  # A remplir manuellement
                "email_content": email.email_generated.replace("\n", " | ")
            })


def analyze_results(result):
    """Analyse les resultats et identifie les problemes."""

    print("\n" + "=" * 60)
    print("ANALYSE DES RESULTATS")
    print("=" * 60)

    # 1. Problemes de qualite
    low_quality = [e for e in result.emails_generated if e.quality_score < 70]
    if low_quality:
        print(f"\n[WARN] {len(low_quality)} emails avec qualite < 70:")
        for email in low_quality:
            print(f"  - {email.contact.company_name}: {email.quality_score}/100")

    # 2. Fallbacks eleves (niveau 3-4)
    high_fallbacks = []
    for email in result.emails_generated:
        for agent, level in email.fallback_levels.items():
            if level >= 3:
                high_fallbacks.append((email.contact.company_name, agent, level))

    if high_fallbacks:
        print(f"\n[WARN] {len(high_fallbacks)} agents ont utilise des fallbacks eleves:")
        for company, agent, level in high_fallbacks:
            print(f"  - {company}: {agent} = Level {level}")

    # 3. Variables manquantes
    missing_vars = []
    for email in result.emails_generated:
        if "[INFORMATION NON DISPONIBLE]" in email.email_generated:
            missing_vars.append(email.contact.company_name)

    if missing_vars:
        print(f"\n[ERROR] {len(missing_vars)} emails avec variables manquantes:")
        for company in missing_vars:
            print(f"  - {company}")

    # 4. Performance
    slow_emails = [e for e in result.emails_generated if e.generation_time_ms > 30000]
    if slow_emails:
        print(f"\n[WARN] {len(slow_emails)} emails generes lentement (>30s):")
        for email in slow_emails:
            print(f"  - {email.contact.company_name}: {email.generation_time_ms/1000:.1f}s")

    # 5. Resume des problemes par agent
    print("\n" + "-" * 60)
    print("PROBLEMES PAR AGENT:")
    print("-" * 60)

    agent_issues = {}
    for email in result.emails_generated:
        for agent, level in email.fallback_levels.items():
            if agent not in agent_issues:
                agent_issues[agent] = {"total": 0, "level_3_4": 0}
            agent_issues[agent]["total"] += 1
            if level >= 3:
                agent_issues[agent]["level_3_4"] += 1

    for agent, stats in agent_issues.items():
        pct = (stats["level_3_4"] / stats["total"]) * 100 if stats["total"] > 0 else 0
        if pct > 20:
            print(f"  [!] {agent}: {pct:.0f}% fallback eleve ({stats['level_3_4']}/{stats['total']})")
        else:
            print(f"  [OK] {agent}: {pct:.0f}% fallback eleve")


def main():
    print("=" * 60)
    print("TEST BATCH: Generation de Campagne avec Feedback")
    print("=" * 60)

    # 1. Choisir la source des contacts
    csv_path = "contacts_test.csv"

    if os.path.exists(csv_path):
        print(f"\n[*] Chargement des contacts depuis {csv_path}...")
        contacts = load_contacts_from_csv(csv_path)
    else:
        print(f"\n[*] Fichier {csv_path} non trouve")
        print("[*] Utilisation des contacts de test par defaut...")
        contacts = get_default_contacts()

    print(f"[OK] {len(contacts)} contacts charges")

    # 2. Charger le template
    print("\n[*] Chargement du template...")
    template_path = "data/templates/cold_email_template_example.md"

    if not os.path.exists(template_path):
        print(f"[ERROR] Template non trouve: {template_path}")
        return

    with open(template_path, "r", encoding="utf-8") as f:
        template_content = f.read().split("---")[0].strip()

    print(f"[OK] Template charge ({len(template_content)} caracteres)")

    # 3. Creer la requete
    print("\n[*] Creation de la requete...")
    batch_id = f"batch-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    request = CampaignRequest(
        template_content=template_content,
        contacts=contacts,
        context={"client_name": "example-client"},
        batch_id=batch_id,
        enable_cache=True
    )
    print(f"[OK] Requete creee (batch_id: {batch_id})")

    # 4. Initialiser l'orchestrateur
    print("\n[*] Initialisation de l'orchestrateur...")
    orchestrator = CampaignOrchestrator(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        enable_cache=True
    )
    print("[OK] Orchestrateur initialise")

    # 5. Executer la generation
    print("\n[*] Generation de la campagne...")
    print(f"Cela peut prendre {len(contacts) * 20}s environ...")
    print("-" * 60)

    result = orchestrator.run(request)

    print("-" * 60)
    print("[OK] Generation terminee!")

    # 6. Afficher les metriques globales
    print("\n" + "=" * 60)
    print("METRIQUES GLOBALES")
    print("=" * 60)
    print(f"Total contacts: {result.total_contacts}")
    print(f"Success: {result.success_count}/{result.total_contacts} ({result.success_rate*100:.1f}%)")
    print(f"Quality moyenne: {result.average_quality_score:.1f}/100")
    print(f"Temps total: {result.total_execution_time_seconds:.1f}s")
    print(f"Temps/email: {result.average_time_per_email_seconds:.1f}s")
    print(f"Cache hit rate: {result.cache_hit_rate*100:.1f}%")
    print(f"Tokens: {result.total_tokens_used}")
    print(f"Cout estime: ${result.estimated_cost_usd:.4f}")

    # 7. Analyser les resultats
    analyze_results(result)

    # 8. Exporter les resultats
    output_dir = "output"
    os.makedirs(output_dir, exist_ok=True)

    csv_output = os.path.join(output_dir, f"{batch_id}_results.csv")
    export_results_to_csv(result, csv_output)
    print(f"\n[*] Resultats exportes vers: {csv_output}")

    # 9. Sauvegarder les emails individuels
    for i, email in enumerate(result.emails_generated, 1):
        email_file = os.path.join(output_dir, f"{batch_id}_{i}_{email.contact.company_name}.txt")
        with open(email_file, "w", encoding="utf-8") as f:
            f.write(f"Contact: {email.contact.company_name}\n")
            f.write(f"Quality: {email.quality_score}/100\n")
            f.write(f"Time: {email.generation_time_ms}ms\n")
            f.write("\n" + "=" * 60 + "\n")
            f.write(email.email_generated)
            f.write("\n\n" + "=" * 60 + "\n")
            f.write("VARIABLES:\n")
            for key, value in email.variables.items():
                f.write(f"  {key}: {value}\n")

    print(f"[*] {len(result.emails_generated)} emails sauvegardes dans {output_dir}/")

    print("\n" + "=" * 60)
    print("PROCHAINES ETAPES:")
    print("=" * 60)
    print(f"1. Ouvrez {csv_output} dans Excel")
    print("2. Ajoutez vos commentaires dans la colonne 'feedback'")
    print("3. Identifiez les patterns de problemes")
    print(f"4. Lisez les emails individuels dans {output_dir}/")
    print("=" * 60)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[WARN] Test interrompu par utilisateur")
    except Exception as e:
        print(f"\n\n[ERROR] ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
