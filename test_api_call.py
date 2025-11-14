"""
Simple API call example for v3.0.

Usage: python test_api_call.py
"""

import requests
import json

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "your-secure-api-key-for-n8n"  # Doit matcher API_KEY dans .env

# ⚠️ IMPORTANT: Remplace par un vrai client_id de ta Supabase
CLIENT_ID = "ton-client-uuid-ici"

# Requête
payload = {
    "client_id": CLIENT_ID,
    "contact": {
        "company_name": "Aircall",
        "first_name": "Sophie",
        "last_name": "Martin",
        "email": "sophie@aircall.io",
        "website": "https://aircall.io",
        "industry": "SaaS"
    },
    "options": {
        "model_preference": "balanced",  # "cheap", "balanced", "quality"
        "enable_scraping": False,  # True pour scraper le site (plus lent)
        "enable_tavily": True,     # True pour web search (meilleure qualité)
        "enable_pci_filter": False # True pour filtrer par ICP
    }
}

print("🚀 Envoi de la requête à l'API v3.0...")
print(f"📍 URL: {API_URL}/api/v2/generate-email")
print(f"🏢 Prospect: {payload['contact']['company_name']}")
print(f"👤 Contact: {payload['contact']['first_name']} {payload['contact']['last_name']}")
print(f"⚙️  Options: Tavily={'ON' if payload['options']['enable_tavily'] else 'OFF'}")
print()

try:
    response = requests.post(
        f"{API_URL}/api/v2/generate-email",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": API_KEY
        },
        json=payload,
        timeout=60
    )

    if response.status_code == 200:
        result = response.json()

        print("✅ Email généré avec succès!")
        print("\n" + "="*60)
        print("📧 EMAIL GÉNÉRÉ")
        print("="*60)
        print(result["email_content"])

        print("\n" + "="*60)
        print("📊 MÉTADONNÉES")
        print("="*60)
        print(f"👔 Persona ciblée: {result['target_persona']}")
        print(f"🏆 Concurrent détecté: {result['competitor_name']}")
        print(f"💡 Pain point: {result['problem_specific'][:80]}...")
        print(f"📈 Signal: {result['specific_signal_1'][:80]}...")
        print(f"💻 Tech stack: {result['system_1']}, {result['system_2']}, {result['system_3']}")
        print(f"⭐ Quality score: {result.get('quality_score', 'N/A')}/100")
        print(f"💰 Coût: ${result['cost_usd']}")
        print(f"⏱️  Temps: {result['generation_time_seconds']:.1f}s")

        print("\n" + "="*60)
        print("🎯 FALLBACK LEVELS (0=best, 3=generic)")
        print("="*60)
        fallback = result['fallback_levels']
        for agent, level in fallback.items():
            emoji = "🟢" if level == 0 else "🟡" if level <= 1 else "🟠" if level == 2 else "🔴"
            print(f"{emoji} {agent:15} : {level}")

        # Sauvegarder le résultat
        with open("last_api_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        print("\n💾 Résultat sauvegardé dans: last_api_result.json")

    elif response.status_code == 401:
        print("❌ Erreur d'authentification")
        print("→ Vérifie que X-API-Key correspond à API_KEY dans .env")

    elif response.status_code == 500:
        print("❌ Erreur serveur")
        try:
            error = response.json()
            print(f"→ {error.get('detail', 'Erreur inconnue')}")
        except:
            print(f"→ {response.text}")
        print("\n💡 Causes possibles:")
        print("   - client_id invalide (client n'existe pas dans Supabase)")
        print("   - API keys manquantes dans .env")
        print("   - Supabase connexion échouée")

    else:
        print(f"❌ Erreur {response.status_code}")
        print(response.text)

except requests.exceptions.ConnectionError:
    print("❌ Impossible de se connecter à l'API")
    print("→ Vérifie que l'API tourne: python src/api/n8n_optimized_api.py")

except requests.exceptions.Timeout:
    print("❌ Timeout (> 60s)")
    print("→ L'API prend plus de temps que prévu")

except Exception as e:
    print(f"❌ Erreur: {e}")
    import traceback
    traceback.print_exc()
