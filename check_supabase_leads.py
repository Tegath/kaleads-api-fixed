"""
Script to check how many leads are actually in Supabase
"""
import os
import sys
from dotenv import load_dotenv
from supabase import create_client

# Fix Windows encoding
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Connect to Supabase
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(supabase_url, supabase_key)

# Count total leads
print("Checking Supabase for leads...")
print()

# Total count
result = client.table("leads").select("id", count="exact").eq("client_id", "kaleads").execute()
total_count = result.count

print(f">>> TOTAL LEADS IN DATABASE: {total_count}")
print()

# Count by source
gmaps_result = client.table("leads").select("id", count="exact").eq("client_id", "kaleads").eq("source", "google_maps").execute()
gmaps_count = gmaps_result.count

print(f"Google Maps leads: {gmaps_count}")
print()

# Get sample of 5 leads to show
sample = client.table("leads").select("company_name, city, phone, email, website, rating").eq("client_id", "kaleads").limit(10).execute()

print("Sample de leads recuperes:")
print("-" * 80)
for i, lead in enumerate(sample.data, 1):
    print(f"{i}. {lead['company_name']}")
    print(f"   Ville: {lead['city']}")
    print(f"   Tel: {lead.get('phone', 'N/A')}")
    print(f"   Email: {lead.get('email', 'N/A')}")
    print(f"   Site: {lead.get('website', 'N/A')}")
    print(f"   Note: {lead.get('rating', 'N/A')}/5")
    print()

# Count by city (top 10)
print("Top 10 villes avec le plus de leads:")
print("-" * 80)

# Get all leads and group by city manually (Supabase doesn't support GROUP BY easily)
all_leads = client.table("leads").select("city").eq("client_id", "kaleads").execute()
cities = {}
for lead in all_leads.data:
    city = lead.get('city', 'Unknown')
    cities[city] = cities.get(city, 0) + 1

# Sort and display top 10
sorted_cities = sorted(cities.items(), key=lambda x: x[1], reverse=True)[:10]
for i, (city, count) in enumerate(sorted_cities, 1):
    print(f"{i}. {city}: {count} leads")
