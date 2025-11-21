"""
Test script to verify that scraping and saving to Supabase works
"""
import os
import sys
from dotenv import load_dotenv

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Import our modules
from src.integrations.google_maps_integration import GoogleMapsLeadGenerator
from src.providers.leads_storage import LeadsStorage
from supabase import create_client

print("=" * 80)
print("TEST: Scraping 1 ville (Paris) et sauvegarde dans Supabase")
print("=" * 80)
print()

# Step 1: Check Supabase before
print("1. Comptage initial des leads dans Supabase...")
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(supabase_url, supabase_key)

before_count = supabase.table("leads").select("id", count="exact").eq("client_id", "kaleads").execute().count
print(f"   Leads avant: {before_count}")
print()

# Step 2: Scrape Paris
print("2. Scraping 'agence web' a Paris (1 page = ~20 leads)...")
gmaps = GoogleMapsLeadGenerator()

try:
    leads = gmaps.search_city_with_pagination(
        query="agence web",
        city="Paris",
        country="France",
        max_results=20,  # Just 1 page
        language="fr"
    )
    print(f"   Resultats trouves: {len(leads)} leads")

    if len(leads) == 0:
        print("   ERREUR: Aucun lead trouve!")
        sys.exit(1)

    # Show sample
    print(f"   Exemple: {leads[0].get('company_name', 'N/A')} - {leads[0].get('city', 'N/A')}")
    print()

except Exception as e:
    print(f"   ERREUR lors du scraping: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 3: Save to Supabase
print("3. Sauvegarde dans Supabase...")
storage = LeadsStorage(client_id="kaleads")

try:
    stats = storage.store_leads(leads)
    print(f"   Resultats:")
    print(f"   - Total: {stats['total_leads']}")
    print(f"   - Nouveaux: {stats['new_leads']}")
    print(f"   - Duplicats: {stats['duplicates_skipped']}")
    print(f"   - Erreurs: {stats['errors']}")
    print()

    if stats['errors'] > 0:
        print("   ERREUR: Des erreurs se sont produites lors de la sauvegarde!")
        sys.exit(1)

except Exception as e:
    print(f"   ERREUR lors de la sauvegarde: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Step 4: Verify in Supabase
print("4. Verification dans Supabase...")
after_count = supabase.table("leads").select("id", count="exact").eq("client_id", "kaleads").execute().count
print(f"   Leads apres: {after_count}")
print(f"   Difference: +{after_count - before_count}")
print()

# Step 5: Get sample from DB
print("5. Sample des leads sauvegardes:")
sample = supabase.table("leads").select("company_name, city, phone, website").eq("client_id", "kaleads").limit(3).execute()
for i, lead in enumerate(sample.data, 1):
    print(f"   {i}. {lead['company_name']} ({lead['city']})")
    print(f"      Tel: {lead.get('phone', 'N/A')}")
    print(f"      Web: {lead.get('website', 'N/A')}")
print()

# Final verdict
if after_count > before_count:
    print("=" * 80)
    print("SUCCES! La sauvegarde fonctionne correctement!")
    print("=" * 80)
    sys.exit(0)
else:
    print("=" * 80)
    print("ECHEC! Aucun lead n'a ete sauvegarde!")
    print("=" * 80)
    sys.exit(1)
