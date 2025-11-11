"""
Script interactif pour tester, corriger et regenerer des emails.

Workflow:
1. Configure ton email (template + contexte)
2. Genere l'email
3. Revise et donne du feedback
4. Regenere avec corrections
5. Compare avant/apres
"""

import os
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
    exit(1)


class EmailReviewer:
    """Systeme interactif de review et regeneration."""

    def __init__(self):
        self.orchestrator = CampaignOrchestrator(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            enable_cache=True
        )
        self.history = []
        self.current_email = None
        self.current_contact = None
        self.current_template = None

    def configure_campaign(self):
        """Etape 1: Configuration initiale par l'humain."""
        print("\n" + "=" * 60)
        print("CONFIGURATION DE LA CAMPAGNE")
        print("=" * 60)

        # 1. Choisir ou creer un contact
        print("\n[1] CONTACT")
        print("Voulez-vous utiliser le contact de test (Aircall) ? (O/n)")
        use_default = input("> ").strip().lower() or "o"

        if use_default == "o":
            self.current_contact = Contact(
                company_name="Aircall",
                first_name="Sophie",
                last_name="Durand",
                email="sophie@aircall.io",
                website="https://aircall.io",
                industry="SaaS"
            )
        else:
            print("\nEntrez les informations du contact:")
            self.current_contact = Contact(
                company_name=input("  Company name: "),
                first_name=input("  First name: "),
                last_name=input("  Last name: "),
                email=input("  Email: "),
                website=input("  Website: "),
                industry=input("  Industry: ")
            )

        print(f"\n[OK] Contact: {self.current_contact.company_name}")

        # 2. Choisir ou creer un template
        print("\n[2] TEMPLATE")
        print("Voulez-vous utiliser le template par defaut ? (O/n)")
        use_default_template = input("> ").strip().lower() or "o"

        if use_default_template == "o":
            template_path = "data/templates/cold_email_template_example.md"
            with open(template_path, "r", encoding="utf-8") as f:
                self.current_template = f.read().split("---")[0].strip()
        else:
            print("\nCollez votre template (finissez par une ligne vide):")
            lines = []
            while True:
                line = input()
                if line == "":
                    break
                lines.append(line)
            self.current_template = "\n".join(lines)

        print(f"\n[OK] Template charge ({len(self.current_template)} caracteres)")

        # 3. Contexte et directives
        print("\n[3] CONTEXTE ET DIRECTIVES")
        print("Ajoutez des directives specifiques pour cette campagne (optionnel):")
        print("(Ex: 'Insister sur la rapidite', 'Ton formel', 'Focus sur le ROI')")
        print("(Laissez vide pour continuer)")

        directives = input("> ").strip()

        context = {
            "client_name": "example-client",
            "directives": directives if directives else "Aucune directive specifique"
        }

        print(f"\n[OK] Configuration terminee!")
        return context

    def generate_email(self, context):
        """Etape 2: Generation de l'email."""
        print("\n" + "=" * 60)
        print("GENERATION DE L'EMAIL")
        print("=" * 60)

        request = CampaignRequest(
            template_content=self.current_template,
            contacts=[self.current_contact],
            context=context,
            batch_id=f"interactive-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            enable_cache=True
        )

        print("\n[*] Generation en cours...")
        result = self.orchestrator.run(request)

        if result.emails_generated:
            self.current_email = result.emails_generated[0]
            self.history.append({
                "timestamp": datetime.now().isoformat(),
                "email": self.current_email,
                "context": context,
                "feedback": None
            })
            print("[OK] Email genere!")
            return self.current_email
        else:
            print("[ERROR] Echec de la generation")
            return None

    def display_email(self, email):
        """Affiche l'email genere avec metriques."""
        print("\n" + "=" * 60)
        print("EMAIL GENERE")
        print("=" * 60)

        print(f"\nContact: {email.contact.company_name}")
        print(f"Quality Score: {email.quality_score}/100")
        print(f"Generation Time: {email.generation_time_ms}ms")

        print("\nFallback Levels:")
        for agent, level in email.fallback_levels.items():
            status = "[!]" if level >= 3 else "[OK]"
            print(f"  {status} {agent}: Level {level}")

        print("\nConfidence Scores:")
        for var, score in email.confidence_scores.items():
            status = "[!]" if score <= 2 else "[OK]"
            print(f"  {status} {var}: {score}/5")

        print("\n" + "-" * 60)
        print("CONTENU:")
        print("-" * 60)
        print(email.email_generated)
        print("-" * 60)

    def collect_feedback(self):
        """Etape 3: Collecte du feedback humain."""
        print("\n" + "=" * 60)
        print("FEEDBACK ET CORRECTIONS")
        print("=" * 60)

        print("\nQue pensez-vous de cet email?")
        print("1. Parfait - je le valide")
        print("2. Bon mais necessite des ajustements mineurs")
        print("3. Moyen - des corrections importantes necessaires")
        print("4. Mauvais - a regenerer completement")

        choice = input("\nVotre choix (1-4): ").strip()

        if choice == "1":
            print("\n[OK] Email valide!")
            return None

        # Collecte des corrections specifiques
        print("\n[*] Collecte des corrections...")
        print("\nQuels elements poser probleme? (separees par des virgules)")
        print("Ex: persona incorrect, pain point trop vague, ton trop formel")

        issues = input("\nProblemes identifies: ").strip()

        print("\nQue souhaitez-vous ameliorer?")
        print("(Soyez specifique, ex: 'Le persona devrait etre VP Sales pas Customer Support Manager')")

        improvements = []
        print("\nAjoutez vos corrections (ligne vide pour terminer):")
        while True:
            correction = input("> ").strip()
            if correction == "":
                break
            improvements.append(correction)

        feedback = {
            "rating": choice,
            "issues": issues,
            "improvements": improvements,
            "timestamp": datetime.now().isoformat()
        }

        # Sauvegarder dans l'historique
        if self.history:
            self.history[-1]["feedback"] = feedback

        return feedback

    def regenerate_with_feedback(self, feedback, context):
        """Etape 4: Regeneration avec le feedback."""
        print("\n" + "=" * 60)
        print("REGENERATION AVEC FEEDBACK")
        print("=" * 60)

        # Enrichir le contexte avec le feedback
        enhanced_context = context.copy()
        enhanced_context["feedback_corrections"] = "\n".join([
            f"- {improvement}" for improvement in feedback["improvements"]
        ])
        enhanced_context["issues_identified"] = feedback["issues"]

        # Note: Dans une implementation complete, on pourrait:
        # 1. Ajuster les prompts des agents specifiques
        # 2. Utiliser un agent "critic" pour valider
        # 3. Fine-tuner les parametres

        print(f"\n[*] Regeneration avec {len(feedback['improvements'])} corrections...")

        # Pour l'instant, on regenere simplement avec le contexte enrichi
        # L'orchestrateur pourrait utiliser ces infos pour ajuster
        new_email = self.generate_email(enhanced_context)

        return new_email

    def compare_versions(self, old_email, new_email):
        """Compare 2 versions d'email."""
        print("\n" + "=" * 60)
        print("COMPARAISON AVANT/APRES")
        print("=" * 60)

        print("\nQUALITY SCORES:")
        print(f"  Avant: {old_email.quality_score}/100")
        print(f"  Apres: {new_email.quality_score}/100")
        diff = new_email.quality_score - old_email.quality_score
        print(f"  Difference: {'+' if diff > 0 else ''}{diff}")

        print("\nFALLBACK LEVELS:")
        for agent in old_email.fallback_levels.keys():
            old_level = old_email.fallback_levels[agent]
            new_level = new_email.fallback_levels[agent]
            if old_level != new_level:
                print(f"  {agent}: {old_level} -> {new_level}")

        print("\nVARIABLES CHANGEES:")
        for key in old_email.variables.keys():
            if old_email.variables[key] != new_email.variables.get(key):
                print(f"  {key}:")
                print(f"    Avant: {old_email.variables[key]}")
                print(f"    Apres: {new_email.variables.get(key)}")

        print("\n" + "-" * 60)
        print("NOUVEAU CONTENU:")
        print("-" * 60)
        print(new_email.email_generated)
        print("-" * 60)

    def save_session(self):
        """Sauvegarde la session avec historique."""
        output_dir = "output/sessions"
        os.makedirs(output_dir, exist_ok=True)

        session_file = os.path.join(
            output_dir,
            f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}.json"
        )

        session_data = {
            "contact": {
                "company_name": self.current_contact.company_name,
                "first_name": self.current_contact.first_name,
                "website": self.current_contact.website
            },
            "template": self.current_template,
            "history": [
                {
                    "timestamp": entry["timestamp"],
                    "quality_score": entry["email"].quality_score,
                    "fallback_levels": entry["email"].fallback_levels,
                    "email_content": entry["email"].email_generated,
                    "variables": entry["email"].variables,
                    "feedback": entry["feedback"]
                }
                for entry in self.history
            ]
        }

        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_data, f, indent=2, ensure_ascii=False)

        print(f"\n[*] Session sauvegardee: {session_file}")

    def run(self):
        """Lance la session interactive complete."""
        print("=" * 60)
        print("SYSTEME INTERACTIF DE GENERATION D'EMAILS")
        print("=" * 60)

        # Etape 1: Configuration
        context = self.configure_campaign()

        # Etape 2: Generation initiale
        email = self.generate_email(context)
        if not email:
            return

        # Etape 3: Review
        self.display_email(email)

        # Boucle de feedback/regeneration
        while True:
            feedback = self.collect_feedback()

            if feedback is None:
                # Email valide
                break

            # Sauvegarder l'ancienne version
            old_email = email

            # Regenerer avec feedback
            email = self.regenerate_with_feedback(feedback, context)

            if email:
                self.compare_versions(old_email, email)

                print("\nVoulez-vous continuer a ameliorer? (o/N)")
                continue_choice = input("> ").strip().lower()
                if continue_choice != "o":
                    break

        # Sauvegarder la session
        self.save_session()

        print("\n" + "=" * 60)
        print("SESSION TERMINEE")
        print("=" * 60)
        print(f"Nombre d'iterations: {len(self.history)}")
        if self.current_email:
            print(f"Quality score final: {self.current_email.quality_score}/100")


if __name__ == "__main__":
    try:
        reviewer = EmailReviewer()
        reviewer.run()
    except KeyboardInterrupt:
        print("\n\n[WARN] Session interrompue par utilisateur")
    except Exception as e:
        print(f"\n\n[ERROR] ERREUR: {str(e)}")
        import traceback
        traceback.print_exc()
