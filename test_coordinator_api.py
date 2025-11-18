"""
Test script for Lead Gen Coordinator API endpoints.

Tests:
1. POST /api/v2/coordinator/analyze - Analyze Kaleads context and get strategy
2. POST /api/v2/leads/google-maps - Execute Google Maps search (simulated)
3. POST /api/v2/leads/jobspy - Execute JobSpy search (simulated)
"""

import requests
import json
from typing import Dict, Any

# Configuration
API_BASE_URL = "http://localhost:8001"  # Change to http://92.112.193.183:20001 for production
API_KEY = "lL^nc2U%tU8f2!LH48!29!mW8"  # Actual API key from .env

HEADERS = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}


def print_section(title: str):
    """Print a formatted section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)


def print_json(data: Dict[str, Any], indent: int = 2):
    """Pretty print JSON data."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def test_coordinator_analyze():
    """Test the coordinator analyze endpoint."""
    print_section("TEST 1: Coordinator Analyze")

    request_data = {
        "client_id": "kaleads",
        "target_count": 500,
        "country": "France"
    }

    print("\n📤 Request:")
    print_json(request_data)

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v2/coordinator/analyze",
            headers=HEADERS,
            json=request_data,
            timeout=60
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print(f"\nClient: {result['client_name']}")
            print(f"Pain Type: {result['pain_type']}")
            print(f"Strategy: {result['strategy']}")
            print(f"\nGoogle Maps Searches ({len(result['google_maps_searches'])}):")
            for search in result['google_maps_searches'][:3]:  # Show first 3
                print(f"  - {search['query']}: {len(search['cities'])} cities")
            print(f"\nJobSpy Searches ({len(result['jobspy_searches'])}):")
            for search in result['jobspy_searches'][:3]:  # Show first 3
                print(f"  - {search['job_title']}: {search['location']}")
            print(f"\nEstimated Leads:")
            print_json(result['estimated_leads'])

            # Save full response for inspection
            with open("coordinator_response.json", "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print("\n💾 Full response saved to: coordinator_response.json")

            return result
        else:
            print(f"\n❌ ERROR: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
        return None


def test_google_maps_search():
    """Test the Google Maps search endpoint."""
    print_section("TEST 2: Google Maps Search")

    request_data = {
        "query": "agence marketing digital",
        "cities": ["Paris", "Lyon", "Marseille"],
        "max_results_per_city": 10  # Small number for testing
    }

    print("\n📤 Request:")
    print_json(request_data)

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v2/leads/google-maps",
            headers=HEADERS,
            json=request_data,
            timeout=120
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print(f"\nTotal Leads: {result['total_leads']}")
            print(f"Cities Searched: {', '.join(result['cities_searched'])}")
            print(f"Cost: ${result['cost_usd']:.4f}")

            if result['leads']:
                print(f"\n📊 Sample Lead:")
                sample = result['leads'][0]
                print_json(sample)

            return result
        else:
            print(f"\n❌ ERROR: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
        return None


def test_jobspy_search():
    """Test the JobSpy search endpoint."""
    print_section("TEST 3: JobSpy Search")

    request_data = {
        "job_title": "Head of Sales",
        "location": "France",
        "company_size": ["11-50", "51-200"],
        "industries": ["SaaS", "Tech"],
        "max_results": 20  # Small number for testing
    }

    print("\n📤 Request:")
    print_json(request_data)

    try:
        response = requests.post(
            f"{API_BASE_URL}/api/v2/leads/jobspy",
            headers=HEADERS,
            json=request_data,
            timeout=120
        )

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n✅ SUCCESS!")
            print(f"\nTotal Leads: {result['total_leads']}")
            print(f"Job Title Searched: {result['job_title_searched']}")
            print(f"Cost: ${result['cost_usd']:.4f}")

            if result['leads']:
                print(f"\n📊 Sample Lead:")
                sample = result['leads'][0]
                print_json(sample)

            return result
        else:
            print(f"\n❌ ERROR: {response.text}")
            return None

    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
        return None


def test_health():
    """Test the health endpoint."""
    print_section("TEST 0: Health Check")

    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=10)

        print(f"\n📥 Response Status: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("\n✅ API is healthy!")
            print_json(result)
            return True
        else:
            print(f"\n❌ ERROR: {response.text}")
            return False

    except requests.exceptions.RequestException as e:
        print(f"\n❌ REQUEST ERROR: {e}")
        print("\nMake sure the API is running:")
        print("  - Local: python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8001")
        print("  - Docker: docker-compose up")
        return False


def run_all_tests():
    """Run all tests sequentially."""
    print("\n" + "🚀 "*35)
    print("  COORDINATOR API TEST SUITE")
    print("🚀 "*35)

    # Test 0: Health check
    if not test_health():
        print("\n⚠️  API is not available. Stopping tests.")
        return

    # Test 1: Coordinator analyze (most important)
    coordinator_result = test_coordinator_analyze()

    # Test 2: Google Maps (optional, may fail if RapidAPI not configured)
    if coordinator_result and coordinator_result.get('google_maps_searches'):
        print("\n⚠️  Google Maps test requires RapidAPI key.")
        print("Skipping for now. Test manually with:")
        print(f"  curl -X POST {API_BASE_URL}/api/v2/leads/google-maps ...")

    # Test 3: JobSpy (optional, may fail if JobSpy not running)
    if coordinator_result and coordinator_result.get('jobspy_searches'):
        print("\n⚠️  JobSpy test requires JobSpy API running.")
        print("Skipping for now. Test manually with:")
        print(f"  curl -X POST {API_BASE_URL}/api/v2/leads/jobspy ...")

    # Summary
    print_section("SUMMARY")
    if coordinator_result:
        print("\n✅ Coordinator analyze: PASSED")
        print("\nYou can now use the coordinator in n8n:")
        print(f"  1. Call: POST {API_BASE_URL}/api/v2/coordinator/analyze")
        print("  2. Use the returned google_maps_searches and jobspy_searches")
        print("  3. Execute them in parallel in n8n")
        print("  4. Collect leads and feed them to email generation")
    else:
        print("\n❌ Coordinator analyze: FAILED")
        print("\nCheck:")
        print("  1. Is Supabase configured correctly?")
        print("  2. Does 'kaleads' client exist in Supabase?")
        print("  3. Is the cities database file present?")

    print("\n" + "="*70)


if __name__ == "__main__":
    # You can also run individual tests:
    # test_health()
    # test_coordinator_analyze()
    # test_google_maps_search()
    # test_jobspy_search()

    run_all_tests()
