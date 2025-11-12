"""
Dashboard Streamlit pour monitoring de la qualité des emails

Lance avec: streamlit run dashboard/email_quality_dashboard.py
"""

import streamlit as st
import pandas as pd
import json
from glob import glob
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

st.set_page_config(page_title="Kaleads Email Quality Dashboard", page_icon="📊", layout="wide")

st.title("📊 Kaleads Email Quality Dashboard")
st.markdown("Monitoring en temps réel de la qualité des emails générés")

# Configuration
LOGS_DIR = Path("./logs")

# Load logs
@st.cache_data(ttl=60)  # Cache for 60 seconds
def load_validation_logs():
    """Charge tous les logs de validation"""
    validations = []
    log_files = list(LOGS_DIR.glob("validations_*.jsonl"))

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    validations.append(json.loads(line))
        except Exception as e:
            st.error(f"Error loading {log_file}: {e}")

    return pd.DataFrame(validations) if validations else pd.DataFrame()

@st.cache_data(ttl=60)
def load_email_logs():
    """Charge tous les logs d'emails"""
    emails = []
    log_files = list(LOGS_DIR.glob("emails_*.jsonl"))

    for log_file in log_files:
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    emails.append(json.loads(line))
        except Exception as e:
            st.error(f"Error loading {log_file}: {e}")

    return pd.DataFrame(emails) if emails else pd.DataFrame()

# Load data
df_validations = load_validation_logs()
df_emails = load_email_logs()

if df_validations.empty and df_emails.empty:
    st.warning("⚠️ Aucun log trouvé. Générez des emails pour voir les statistiques.")
    st.info(f"Dossier de logs: {LOGS_DIR.absolute()}")
    st.stop()

# === Métriques Principales ===
st.header("📈 Métriques Globales")

col1, col2, col3, col4 = st.columns(4)

if not df_emails.empty:
    with col1:
        avg_quality = df_emails["final_quality_score"].mean()
        st.metric("Quality Score Moyen", f"{avg_quality:.1f}%")

    with col2:
        success_rate = (df_emails["success"].sum() / len(df_emails) * 100) if len(df_emails) > 0 else 0
        st.metric("Taux de Validation", f"{success_rate:.1f}%")

    with col3:
        avg_attempts = df_emails["attempts"].mean()
        st.metric("Tentatives Moyennes", f"{avg_attempts:.1f}")

    with col4:
        total_cost = df_emails["cost_usd"].sum()
        st.metric("Coût Total", f"${total_cost:.4f}")

# === Quality Score Evolution ===
st.header("📊 Évolution de la Qualité")

if not df_validations.empty:
    df_validations['timestamp'] = pd.to_datetime(df_validations['timestamp'])
    df_validations = df_validations.sort_values('timestamp')

    fig = px.line(
        df_validations,
        x='timestamp',
        y='quality_score',
        title="Quality Score au fil du temps",
        labels={'quality_score': 'Quality Score (%)', 'timestamp': 'Date/Heure'}
    )
    fig.add_hline(y=95, line_dash="dash", line_color="green", annotation_text="Seuil (95%)")
    st.plotly_chart(fig, use_container_width=True)

# === Distribution des Scores ===
col1, col2 = st.columns(2)

with col1:
    if not df_validations.empty:
        st.subheader("Distribution des Quality Scores")
        fig = px.histogram(
            df_validations,
            x='quality_score',
            nbins=20,
            title="",
            labels={'quality_score': 'Quality Score (%)'}
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if not df_emails.empty:
        st.subheader("Tentatives par Email")
        attempts_counts = df_emails['attempts'].value_counts().sort_index()
        fig = px.bar(
            x=attempts_counts.index,
            y=attempts_counts.values,
            title="",
            labels={'x': 'Nombre de tentatives', 'y': 'Nombre d\'emails'}
        )
        st.plotly_chart(fig, use_container_width=True)

# === Top Problèmes ===
st.header("🔴 Top Problèmes Détectés")

if not df_validations.empty and 'issues' in df_validations.columns:
    # Extraire tous les issues
    all_issues = []
    for issues in df_validations['issues']:
        if isinstance(issues, list):
            all_issues.extend(issues)

    if all_issues:
        issue_counts = pd.Series(all_issues).value_counts().head(10)

        fig = px.bar(
            x=issue_counts.values,
            y=issue_counts.index,
            orientation='h',
            title="",
            labels={'x': 'Nombre d\'occurrences', 'y': 'Problème'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.success("✅ Aucun problème détecté!")

# === Derniers Emails ===
st.header("📧 Derniers Emails Générés")

if not df_emails.empty:
    df_display = df_emails[['timestamp', 'contact_company', 'final_quality_score', 'attempts', 'success', 'cost_usd']].copy()
    df_display['timestamp'] = pd.to_datetime(df_display['timestamp'])
    df_display = df_display.sort_values('timestamp', ascending=False).head(20)

    # Color code success
    def color_success(val):
        color = 'green' if val else 'red'
        return f'color: {color}'

    st.dataframe(
        df_display.style.applymap(color_success, subset=['success']),
        use_container_width=True
    )

# === Filtres et Détails ===
with st.expander("🔍 Filtres et Détails"):
    if not df_validations.empty:
        st.subheader("Filtrer par Quality Score")
        min_score, max_score = st.slider(
            "Range de Quality Score",
            0, 100, (0, 100)
        )

        filtered = df_validations[
            (df_validations['quality_score'] >= min_score) &
            (df_validations['quality_score'] <= max_score)
        ]

        st.write(f"**{len(filtered)}** validations dans ce range")

        if not filtered.empty:
            st.dataframe(filtered[['timestamp', 'email_id', 'quality_score', 'is_valid', 'issues']].head(20))

# === Statistiques Avancées ===
with st.expander("📊 Statistiques Avancées"):
    if not df_emails.empty:
        col1, col2 = st.columns(2)

        with col1:
            st.metric("Temps Moyen de Génération", f"{df_emails['generation_time_seconds'].mean():.1f}s")
            st.metric("Coût Moyen par Email", f"${df_emails['cost_usd'].mean():.4f}")

        with col2:
            st.metric("Temps Minimum", f"{df_emails['generation_time_seconds'].min():.1f}s")
            st.metric("Temps Maximum", f"{df_emails['generation_time_seconds'].max():.1f}s")

# === Bouton de Refresh ===
if st.button("🔄 Rafraîchir les données"):
    st.cache_data.clear()
    st.rerun()

# === Footer ===
st.markdown("---")
st.caption("Dashboard généré avec Streamlit | Données en temps réel depuis ./logs/")
