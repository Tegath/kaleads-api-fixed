"""
Script simple pour tester avec feedback via fichier.

Plus facile que le terminal - vous editez un fichier texte pour donner votre feedback!
"""

import os
import json
from datetime import datetime
from dotenv import load_dotenv
from src.orchestrator import CampaignOrchestrator
from src.schemas.campaign_schemas import CampaignRequest, Contact

load_dotenv()

if not os.getenv("OPENAI_API_KEY"):
    print("[ERROR] OPENAI_API_KEY not found in environment")
    exit(1)


def generate_email(contact_data=None, template_path=None, directives=""):
    """Genere un email simple."""

    # Contact par defaut ou personnalise
    if contact_data is None:
        contact = Contact(
            company_name="Aircall",
            first_name="Sophie",
            last_name="Durand",
            email="sophie@aircall.io",
            website="https://aircall.io",
            industry="SaaS"
        )
    else:
        contact = Contact(**contact_data)

    # Template
    if template_path is None:
        template_path = "data/templates/cold_email_template_example.md"

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read().split("---")[0].strip()

    # Orchestrateur
    orchestrator = CampaignOrchestrator(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        enable_cache=True
    )

    # Contexte
    context = {
        "client_name": "example-client",
        "directives": directives if directives else "Aucune directive specifique"
    }

    # Request
    request = CampaignRequest(
        template_content=template,
        contacts=[contact],
        context=context,
        batch_id=f"simple-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        enable_cache=True
    )

    # Generation
    print("\n[*] Generation en cours...")
    result = orchestrator.run(request)

    if result.emails_generated:
        return result.emails_generated[0]
    return None


def save_email_for_review(email, output_file="output/current_email.txt"):
    """Sauvegarde l'email pour review."""
    os.makedirs(os.path.dirname(output_file), exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("EMAIL GENERE - A REVIEWER\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Contact: {email.contact.company_name}\n")
        f.write(f"Quality Score: {email.quality_score}/100\n")
        f.write(f"Generation Time: {email.generation_time_ms}ms\n\n")

        f.write("Fallback Levels:\n")
        for agent, level in email.fallback_levels.items():
            status = "[!]" if level >= 3 else "[OK]"
            f.write(f"  {status} {agent}: Level {level}\n")

        f.write("\nConfidence Scores:\n")
        for var, score in email.confidence_scores.items():
            status = "[!]" if score <= 2 else "[OK]"
            f.write(f"  {status} {var}: {score}/5\n")

        f.write("\n" + "-" * 60 + "\n")
        f.write("CONTENU:\n")
        f.write("-" * 60 + "\n\n")
        f.write(email.email_generated)
        f.write("\n\n" + "-" * 60 + "\n")

        f.write("\nVARIABLES:\n")
        f.write("-" * 60 + "\n")
        for key, value in email.variables.items():
            f.write(f"{key}: {value}\n")

        f.write("\n\n")
        f.write("=" * 60 + "\n")
        f.write("FEEDBACK (A REMPLIR)\n")
        f.write("=" * 60 + "\n\n")
        f.write("RATING (1-4):\n")
        f.write("1 = Parfait\n")
        f.write("2 = Bon mais ajustements mineurs\n")
        f.write("3 = Moyen, corrections importantes\n")
        f.write("4 = Mauvais, a regenerer\n\n")
        f.write("Votre rating: [ECRIVEZ ICI]\n\n")

        f.write("PROBLEMES IDENTIFIES:\n")
        f.write("[ECRIVEZ ICI - Ex: persona incorrect, pain point vague]\n\n\n")

        f.write("CORRECTIONS DETAILLEES:\n")
        f.write("[ECRIVEZ ICI - Soyez specifique]\n")
        f.write("Ex:\n")
        f.write("- Le persona devrait etre VP Sales pas Customer Support Manager\n")
        f.write("- Le pain point devrait mentionner la perte de temps concrete\n")
        f.write("- Le ton doit etre plus formel\n\n\n")

        f.write("EXEMPLE D'EMAIL IDEAL (optionnel):\n")
        f.write("[COLLEZ ICI votre exemple si vous avez une vision precise]\n\n\n")

    print(f"[OK] Email sauvegarde: {output_file}")
    print(f"\n[*] PROCHAINE ETAPE:")
    print(f"1. Ouvrez {output_file} dans votre editeur de texte")
    print(f"2. Ajoutez votre feedback a la fin du fichier")
    print(f"3. Sauvegardez")
    print(f"4. Relancez: python test_simple.py --regenerate")


def load_feedback(feedback_file="output/current_email.txt"):
    """Charge le feedback depuis le fichier."""
    if not os.path.exists(feedback_file):
        return None

    with open(feedback_file, "r", encoding="utf-8") as f:
        content = f.read()

    # Parser le feedback
    feedback = {
        "rating": None,
        "issues": "",
        "improvements": [],
        "example_email": ""
    }

    # Extraire le rating
    if "Votre rating:" in content:
        parts = content.split("Votre rating:")
        if len(parts) > 1:
            rating_section = parts[1].split("\n")[0].strip()
            # Chercher un chiffre 1-4
            for char in rating_section:
                if char in "1234":
                    feedback["rating"] = char
                    break

    # Extraire problemes identifies
    if "PROBLEMES IDENTIFIES:" in content:
        parts = content.split("PROBLEMES IDENTIFIES:")
        if len(parts) > 1:
            issues_section = parts[1].split("CORRECTIONS DETAILLEES:")[0].strip()
            lines = [l.strip() for l in issues_section.split("\n") if l.strip() and not l.startswith("[")]
            if lines:
                feedback["issues"] = lines[0]

    # Extraire corrections
    if "CORRECTIONS DETAILLEES:" in content:
        parts = content.split("CORRECTIONS DETAILLEES:")
        if len(parts) > 1:
            corrections_section = parts[1].split("EXEMPLE D'EMAIL IDEAL")[0].strip()
            lines = [l.strip() for l in corrections_section.split("\n")
                    if l.strip() and not l.startswith("[") and not l.startswith("Ex:")]
            feedback["improvements"] = [l.lstrip("- ") for l in lines if l.startswith("-")]

    # Extraire exemple email
    if "EXEMPLE D'EMAIL IDEAL" in content:
        parts = content.split("EXEMPLE D'EMAIL IDEAL")
        if len(parts) > 1:
            example_section = parts[1].strip()
            lines = [l for l in example_section.split("\n")
                    if l.strip() and not l.startswith("[")]
            if lines:
                feedback["example_email"] = "\n".join(lines)

    # Verifier si du feedback a ete donne
    if feedback["rating"] or feedback["improvements"] or feedback["example_email"]:
        return feedback

    return None


def regenerate_with_feedback(contact_data, template_path, directives, feedback):
    """Regenere avec le feedback."""

    print("\n[*] Regeneration avec feedback...")
    print(f"  Rating: {feedback['rating']}/4")
    print(f"  Problemes: {feedback['issues']}")
    print(f"  Nombre de corrections: {len(feedback['improvements'])}")

    # Enrichir les directives avec le feedback
    enhanced_directives = directives + "\n\nCORRECTIONS A APPLIQUER:\n"
    for improvement in feedback['improvements']:
        enhanced_directives += f"- {improvement}\n"

    if feedback['example_email']:
        enhanced_directives += f"\n\nEXEMPLE D'EMAIL IDEAL A SUIVRE:\n{feedback['example_email']}"

    # Regenerer
    email = generate_email(contact_data, template_path, enhanced_directives)

    return email


def compare_emails(old_file, new_file):
    """Compare deux emails."""
    print("\n" + "=" * 60)
    print("COMPARAISON AVANT/APRES")
    print("=" * 60)
    print(f"\nEmail AVANT: {old_file}")
    print(f"Email APRES: {new_file}")
    print("\nOuvrez les 2 fichiers cote a cote pour comparer!")


def main():
    import sys

    # Fichiers de config optionnels
    config_file = "config_email.json"

    # Charger config si existe
    if os.path.exists(config_file):
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        contact_data = config.get("contact")
        template_path = config.get("template_path")
        directives = config.get("directives", "")
    else:
        # Valeurs par defaut
        contact_data = None
        template_path = None
        directives = ""

        # Creer config par defaut
        default_config = {
            "contact": {
                "company_name": "Aircall",
                "first_name": "Sophie",
                "last_name": "Durand",
                "email": "sophie@aircall.io",
                "website": "https://aircall.io",
                "industry": "SaaS"
            },
            "template_path": "data/templates/cold_email_template_example.md",
            "directives": "Ton professionnel, focus sur le ROI mesurable"
        }
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(default_config, f, indent=2, ensure_ascii=False)
        print(f"[OK] Fichier de config cree: {config_file}")
        print("[*] Vous pouvez l'editer pour personnaliser le contact et les directives")

    # Mode regeneration?
    if "--regenerate" in sys.argv or "-r" in sys.argv:
        # Charger le feedback
        feedback = load_feedback()

        if feedback is None:
            print("[ERROR] Aucun feedback trouve dans output/current_email.txt")
            print("[*] Ajoutez votre feedback a la fin du fichier et relancez")
            return

        print("[OK] Feedback charge:")
        print(f"  Rating: {feedback['rating']}")
        print(f"  Problemes: {feedback['issues']}")
        print(f"  Corrections: {len(feedback['improvements'])}")

        # Archiver l'ancien email
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        old_file = f"output/email_v1_{timestamp}.txt"
        os.rename("output/current_email.txt", old_file)
        print(f"[*] Ancien email archive: {old_file}")

        # Regenerer
        new_email = regenerate_with_feedback(contact_data, template_path, directives, feedback)

        if new_email:
            new_file = "output/current_email.txt"
            save_email_for_review(new_email, new_file)
            compare_emails(old_file, new_file)
    else:
        # Generation initiale
        print("=" * 60)
        print("GENERATION D'EMAIL SIMPLE")
        print("=" * 60)

        email = generate_email(contact_data, template_path, directives)

        if email:
            save_email_for_review(email)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[WARN] Interrompu par utilisateur")
    except Exception as e:
        print(f"\n[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
