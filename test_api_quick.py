"""
Test rapide de l'API Coordinator
Vérifie que l'API fonctionne et charge bien les données Kaleads depuis Supabase
"""

import requests
import json
import sys

# Configuration
API_URL = "http://localhost:8001"
API_KEY = "lL^nc2U%tU8f2!LH48!29!mW8"

headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

def print_section(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def test_health():
    """Test 1: Health check"""
    print_section("TEST 1: Health Check")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ API is healthy!")
            print(f"   - Status: {data.get('status')}")
            print(f"   - Supabase: {'✅' if data.get('supabase_configured') else '❌'}")
            print(f"   - OpenRouter: {'✅' if data.get('openrouter_key_configured') else '❌'}")
            print(f"   - Version: {data.get('version')}")
            return True
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("\n❌ ERREUR: Impossible de se connecter à l'API")
        print("   → Vérifier que l'API tourne sur http://localhost:8001")
        print("   → Lancer avec: .\\start_api.ps1")
        return False
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def test_coordinator():
    """Test 2: Coordinator analyze"""
    print_section("TEST 2: Coordinator Analyze (Kaleads)")
    
    print("\n📤 Request:")
    request_data = {
        "client_id": "kaleads",
        "target_count": 500,
        "country": "France"
    }
    print(json.dumps(request_data, indent=2))
    
    try:
        response = requests.post(
            f"{API_URL}/api/v2/coordinator/analyze",
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("\n📥 Response:")
            print(f"\n✅ SUCCESS!")
            print(f"   - Client: {result['client_name']}")
            print(f"   - Pain Type: {result['pain_type']}")
            print(f"   - Strategy: {result['strategy']}")
            
            # Google Maps searches
            gmaps = result.get('google_maps_searches', [])
            print(f"\n   📍 Google Maps Searches: {len(gmaps)}")
            for i, search in enumerate(gmaps[:3], 1):
                print(f"      {i}. \"{search['query']}\" dans {len(search['cities'])} villes")
            if len(gmaps) > 3:
                print(f"      ... et {len(gmaps) - 3} autres")
            
            # JobSpy searches
            jobspy = result.get('jobspy_searches', [])
            print(f"\n   💼 JobSpy Searches: {len(jobspy)}")
            for i, search in enumerate(jobspy[:3], 1):
                print(f"      {i}. \"{search['job_title']}\" - {search['location']}")
            if len(jobspy) > 3:
                print(f"      ... et {len(jobspy) - 3} autres")
            
            # Estimated leads
            estimated = result.get('estimated_leads', {})
            print(f"\n   📊 Estimated Leads:")
            print(f"      - Google Maps: {estimated.get('google_maps', 0)}")
            print(f"      - JobSpy: {estimated.get('jobspy', 0)}")
            print(f"      - Total: {estimated.get('total', 0)}")
            
            # Save full response
            filename = "test_coordinator_result.json"
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            
            print(f"\n   💾 Résultat complet sauvegardé: {filename}")
            
            # Check if using mock data
            if result['client_name'] == "Mock Client (v3)":
                print("\n   ⚠️  WARNING: Utilise des données MOCK")
                print("      → Vérifier la connexion Supabase")
                print("      → Vérifier que SUPABASE_SERVICE_ROLE_KEY est définie")
                return False
            
            return True
            
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def test_google_maps_demo():
    """Test 3: Google Maps (Demo mode)"""
    print_section("TEST 3: Google Maps Search (Demo)")
    
    print("\n📤 Request:")
    request_data = {
        "query": "agence SaaS",
        "cities": ["Paris", "Lyon"],
        "max_results_per_city": 5
    }
    print(json.dumps(request_data, indent=2))
    
    print("\n⚠️  Note: Mode démo (RapidAPI key non configurée)")
    print("   → Retournera des données simulées")
    
    try:
        response = requests.post(
            f"{API_URL}/api/v2/leads/google-maps",
            headers=headers,
            json=request_data,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Response reçue")
            print(f"   - Total leads: {result.get('total_leads', 0)}")
            print(f"   - Cities searched: {', '.join(result.get('cities_searched', []))}")
            
            if result.get('leads'):
                print(f"\n   📊 Sample lead:")
                lead = result['leads'][0]
                print(f"      - Company: {lead.get('company_name', 'N/A')}")
                print(f"      - Phone: {lead.get('phone', 'N/A')}")
                print(f"      - Website: {lead.get('website', 'N/A')}")
                print(f"      - City: {lead.get('city', 'N/A')}")
            
            return True
        else:
            print(f"\n❌ Error: Status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        return False


def main():
    print("\n" + "🚀 " * 35)
    print("  TEST RAPIDE API COORDINATOR")
    print("🚀 " * 35)
    
    # Test 1: Health
    health_ok = test_health()
    if not health_ok:
        print("\n❌ API non disponible. Arrêt des tests.")
        sys.exit(1)
    
    # Test 2: Coordinator (le plus important)
    coordinator_ok = test_coordinator()
    
    # Test 3: Google Maps (optionnel, mode démo)
    # test_google_maps_demo()
    
    # Summary
    print_section("RÉSUMÉ")
    
    if coordinator_ok:
        print("\n✅ TOUS LES TESTS PASSÉS")
        print("\n   Prochaines étapes:")
        print("   1. ✅ L'API fonctionne correctement")
        print("   2. ✅ Les données Kaleads sont chargées depuis Supabase")
        print("   3. 🎯 Prêt pour n8n!")
        print("\n   → Consulter: QUICK_START_N8N.md pour setup n8n")
        print("   → Workflow n8n: n8n_workflows/lead_generation_master.json")
    else:
        print("\n⚠️  TESTS PARTIELS")
        print("\n   À vérifier:")
        print("   - Connexion Supabase (SUPABASE_SERVICE_ROLE_KEY)")
        print("   - Client 'kaleads' existe dans Supabase")
        print("   - Variables d'environnement bien définies")
    
    print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()


