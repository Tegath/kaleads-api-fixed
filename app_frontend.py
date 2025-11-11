"""
Frontend simple avec Streamlit pour generer et editer des emails.

Installation:
    pip install streamlit

Lancement:
    streamlit run app_frontend.py
"""

import streamlit as st
import os
import json
from datetime import datetime
from dotenv import load_dotenv
from src.orchestrator import CampaignOrchestrator
from src.schemas.campaign_schemas import CampaignRequest, Contact

load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Email Campaign Generator",
    page_icon="✉️",
    layout="wide"
)

# Style CSS
st.markdown("""
<style>
    .stAlert {
        padding: 1rem;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialise le state de la session."""
    if 'email_history' not in st.session_state:
        st.session_state.email_history = []
    if 'current_email' not in st.session_state:
        st.session_state.current_email = None
    if 'config' not in st.session_state:
        st.session_state.config = {
            'contact': {
                'company_name': 'Aircall',
                'first_name': 'Sophie',
                'last_name': 'Durand',
                'email': 'sophie@aircall.io',
                'website': 'https://aircall.io',
                'industry': 'SaaS'
            },
            'directives': 'Ton professionnel, focus sur le ROI mesurable',
            'model': 'gpt-4o-mini'
        }


def generate_email(contact_data, template, directives, model):
    """Genere un email."""

    contact = Contact(**contact_data)

    orchestrator = CampaignOrchestrator(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model=model,
        enable_cache=True
    )

    context = {
        "client_name": "example-client",
        "directives": directives
    }

    request = CampaignRequest(
        template_content=template,
        contacts=[contact],
        context=context,
        batch_id=f"frontend-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        enable_cache=True
    )

    with st.spinner("Génération en cours... (20-30s)"):
        result = orchestrator.run(request)

    if result.emails_generated:
        return result.emails_generated[0]
    return None


def display_email_metrics(email):
    """Affiche les metriques de l'email."""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Quality Score", f"{email.quality_score}/100")

    with col2:
        st.metric("Generation Time", f"{email.generation_time_ms/1000:.1f}s")

    with col3:
        # Calculer le fallback moyen
        avg_fallback = sum(email.fallback_levels.values()) / len(email.fallback_levels)
        st.metric("Avg Fallback", f"{avg_fallback:.1f}")

    with col4:
        # Calculer la confiance moyenne
        avg_confidence = sum(email.confidence_scores.values()) / len(email.confidence_scores)
        st.metric("Avg Confidence", f"{avg_confidence:.1f}/5")


def display_fallback_levels(email):
    """Affiche les niveaux de fallback."""

    st.subheader("📊 Fallback Levels par Agent")

    for agent, level in email.fallback_levels.items():
        # Couleur selon le niveau
        if level <= 2:
            color = "🟢"
        elif level == 3:
            color = "🟡"
        else:
            color = "🔴"

        st.write(f"{color} **{agent}**: Level {level}")


def display_confidence_scores(email):
    """Affiche les scores de confiance."""

    st.subheader("💯 Confidence Scores")

    for var, score in email.confidence_scores.items():
        # Progress bar
        progress = score / 5

        # Couleur selon le score
        if score >= 4:
            color = "🟢"
        elif score >= 3:
            color = "🟡"
        else:
            color = "🔴"

        col1, col2 = st.columns([3, 1])
        with col1:
            st.progress(progress)
        with col2:
            st.write(f"{color} {score}/5")

        st.caption(var)


def display_variables(email):
    """Affiche les variables generees."""

    st.subheader("🔧 Variables Générées")

    for key, value in email.variables.items():
        with st.expander(f"**{key}**"):
            st.write(value)


def main():
    init_session_state()

    st.title("✉️ Email Campaign Generator")
    st.markdown("---")

    # Sidebar: Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key check
        if not os.getenv("OPENAI_API_KEY"):
            st.error("⚠️ OPENAI_API_KEY non trouvée dans .env")
            st.stop()
        else:
            st.success("✅ API Key configurée")

        st.markdown("---")

        # Model selection
        model = st.selectbox(
            "Modèle",
            ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"],
            index=0,
            help="gpt-4o-mini est recommandé (rapide et économique)"
        )
        st.session_state.config['model'] = model

        st.markdown("---")

        # Contact
        st.subheader("👤 Contact")

        company_name = st.text_input("Company", st.session_state.config['contact']['company_name'])
        first_name = st.text_input("Prénom", st.session_state.config['contact']['first_name'])
        last_name = st.text_input("Nom", st.session_state.config['contact']['last_name'])
        email = st.text_input("Email", st.session_state.config['contact']['email'])
        website = st.text_input("Website", st.session_state.config['contact']['website'])
        industry = st.text_input("Industry", st.session_state.config['contact']['industry'])

        st.session_state.config['contact'] = {
            'company_name': company_name,
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'website': website,
            'industry': industry
        }

        st.markdown("---")

        # Directives
        st.subheader("📝 Directives")
        directives = st.text_area(
            "Directives spécifiques",
            st.session_state.config['directives'],
            height=100,
            help="Ex: Ton professionnel, focus ROI, éviter jargon"
        )
        st.session_state.config['directives'] = directives

    # Main area: Tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📧 Générer", "📊 Analyse", "📝 Historique", "📖 Guide"])

    # Tab 1: Generation
    with tab1:
        st.header("Génération d'Email")

        # Template
        st.subheader("📄 Template")

        template_choice = st.radio(
            "Choisir un template",
            ["Template par défaut", "Template personnalisé"],
            horizontal=True
        )

        if template_choice == "Template par défaut":
            template_path = "data/templates/cold_email_template_example.md"
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    template = f.read().split("---")[0].strip()
                st.text_area("Template", template, height=200, disabled=True)
            else:
                st.error("Template par défaut introuvable")
                template = ""
        else:
            template = st.text_area(
                "Collez votre template ici",
                height=200,
                placeholder="Bonjour {{first_name}},\n\nJ'ai remarqué que {{company_name}}..."
            )

        st.markdown("---")

        # Generate button
        col1, col2 = st.columns([1, 3])

        with col1:
            generate_btn = st.button("🚀 Générer l'Email", type="primary", use_container_width=True)

        if generate_btn:
            if not template:
                st.error("Veuillez fournir un template")
            else:
                email = generate_email(
                    st.session_state.config['contact'],
                    template,
                    st.session_state.config['directives'],
                    st.session_state.config['model']
                )

                if email:
                    st.session_state.current_email = email
                    st.session_state.email_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'email': email,
                        'config': st.session_state.config.copy()
                    })
                    st.success("✅ Email généré avec succès!")
                    st.rerun()
                else:
                    st.error("Échec de la génération")

        # Display current email
        if st.session_state.current_email:
            st.markdown("---")

            email = st.session_state.current_email

            # Metrics
            display_email_metrics(email)

            st.markdown("---")

            # Email content
            st.subheader("📧 Email Généré")

            # Editable email
            edited_email = st.text_area(
                "Contenu (éditable)",
                email.email_generated,
                height=400,
                help="Vous pouvez éditer l'email ici"
            )

            # Copy button
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("📋 Copier", use_container_width=True):
                    st.success("Email copié! (Ctrl+C depuis la zone de texte)")

            with col2:
                # Download button
                st.download_button(
                    "💾 Télécharger",
                    edited_email,
                    file_name=f"email_{email.contact.company_name}_{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt",
                    use_container_width=True
                )

    # Tab 2: Analysis
    with tab2:
        st.header("Analyse de l'Email")

        if st.session_state.current_email:
            email = st.session_state.current_email

            col1, col2 = st.columns(2)

            with col1:
                display_fallback_levels(email)

            with col2:
                display_confidence_scores(email)

            st.markdown("---")

            display_variables(email)

            st.markdown("---")

            # Feedback section
            st.subheader("💬 Feedback et Régénération")

            rating = st.select_slider(
                "Qualité de l'email",
                options=[1, 2, 3, 4],
                value=3,
                format_func=lambda x: {
                    1: "1 - Parfait",
                    2: "2 - Bon mais ajustements mineurs",
                    3: "3 - Corrections importantes",
                    4: "4 - À régénérer"
                }[x]
            )

            issues = st.text_input(
                "Problèmes identifiés (séparés par des virgules)",
                placeholder="Ex: persona incorrect, pain point vague"
            )

            corrections = st.text_area(
                "Corrections détaillées",
                height=150,
                placeholder="Ex:\n- Le persona devrait être VP Sales\n- Ajouter un chiffre ROI concret"
            )

            example_email = st.text_area(
                "Exemple d'email idéal (optionnel)",
                height=200,
                placeholder="Bonjour {{first_name}},\n\nJ'ai remarqué que..."
            )

            if st.button("🔄 Régénérer avec Feedback", type="primary"):
                # Enrichir les directives avec le feedback
                enhanced_directives = st.session_state.config['directives']
                enhanced_directives += f"\n\nCORRECTIONS À APPLIQUER:\n{corrections}"

                if example_email:
                    enhanced_directives += f"\n\nEXEMPLE D'EMAIL IDÉAL:\n{example_email}"

                # Regenerer
                if template_choice == "Template par défaut":
                    template_path = "data/templates/cold_email_template_example.md"
                    with open(template_path, "r", encoding="utf-8") as f:
                        template = f.read().split("---")[0].strip()

                new_email = generate_email(
                    st.session_state.config['contact'],
                    template,
                    enhanced_directives,
                    st.session_state.config['model']
                )

                if new_email:
                    st.session_state.current_email = new_email
                    st.session_state.email_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'email': new_email,
                        'config': st.session_state.config.copy(),
                        'feedback': {
                            'rating': rating,
                            'issues': issues,
                            'corrections': corrections,
                            'example': example_email
                        }
                    })
                    st.success("✅ Email régénéré!")
                    st.rerun()
        else:
            st.info("Générez d'abord un email dans l'onglet 'Générer'")

    # Tab 3: History
    with tab3:
        st.header("📝 Historique des Emails")

        if st.session_state.email_history:
            st.write(f"**{len(st.session_state.email_history)} emails générés**")

            for i, entry in enumerate(reversed(st.session_state.email_history), 1):
                with st.expander(f"Email #{len(st.session_state.email_history) - i + 1} - {entry['timestamp'][:19]}"):
                    email = entry['email']

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Quality", f"{email.quality_score}/100")
                    with col2:
                        st.metric("Time", f"{email.generation_time_ms/1000:.1f}s")
                    with col3:
                        avg_fallback = sum(email.fallback_levels.values()) / len(email.fallback_levels)
                        st.metric("Avg Fallback", f"{avg_fallback:.1f}")

                    st.text_area("Contenu", email.email_generated, height=200, key=f"history_{i}")

                    if 'feedback' in entry:
                        st.caption(f"Feedback: {entry['feedback'].get('issues', 'N/A')}")
        else:
            st.info("Aucun email généré pour le moment")

    # Tab 4: Guide
    with tab4:
        st.header("📖 Guide d'Utilisation")

        st.markdown("""
        ## Comment utiliser cette application

        ### 1️⃣ Configuration (Sidebar)

        - **Modèle**: Choisissez le modèle OpenAI (gpt-4o-mini recommandé)
        - **Contact**: Entrez les informations du contact cible
        - **Directives**: Spécifiez le ton, focus, style souhaité

        ### 2️⃣ Génération (Onglet Générer)

        1. Choisissez un template (défaut ou personnalisé)
        2. Cliquez sur "Générer l'Email"
        3. Attendez 20-30s
        4. Consultez l'email généré avec les métriques

        ### 3️⃣ Analyse (Onglet Analyse)

        - **Fallback Levels**: Vérifie la qualité des données
          - 🟢 Niveau 1-2: Bon
          - 🟡 Niveau 3: Moyen
          - 🔴 Niveau 4: Problématique

        - **Confidence Scores**: Confiance de l'AI dans chaque variable
          - 🟢 4-5/5: Très confiant
          - 🟡 3/5: Moyennement confiant
          - 🔴 1-2/5: Peu confiant

        - **Variables**: Toutes les variables générées par les agents

        ### 4️⃣ Feedback et Régénération

        1. Donnez un rating (1-4)
        2. Identifiez les problèmes
        3. Ajoutez des corrections détaillées
        4. (Optionnel) Collez un exemple d'email idéal
        5. Cliquez "Régénérer avec Feedback"
        6. Comparez l'ancien et le nouveau

        ### 5️⃣ Historique

        - Consultez tous les emails générés
        - Comparez les versions
        - Téléchargez les versions précédentes

        ## 📊 Métriques

        - **Quality Score**: Score global /100
          - > 75: Excellent
          - 60-75: Bon
          - < 60: À améliorer

        - **Fallback Level**: Niveau de fallback moyen
          - < 2.0: Excellent
          - 2.0-3.0: Bon
          - > 3.0: À améliorer

        - **Confidence**: Confiance moyenne /5
          - > 4: Excellent
          - 3-4: Bon
          - < 3: À améliorer

        ## 💡 Conseils

        1. **Soyez spécifique** dans les directives
        2. **Testez plusieurs versions** avec différentes directives
        3. **Comparez l'historique** pour voir l'évolution
        4. **Utilisez des exemples** pour guider l'AI
        """)


if __name__ == "__main__":
    main()
