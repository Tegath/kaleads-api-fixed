#!/usr/bin/env python3
"""
Script pour uploader des contacts depuis CSV vers Supabase.

Usage:
    python upload_contacts.py contacts.csv --client "Acme Inc" --template "Cold Email V1"

Le script:
1. Lit le fichier CSV
2. Récupère le client_id et template_id depuis Supabase
3. Génère un batch_id unique
4. Insère tous les contacts dans la table contacts_to_enrich
5. Affiche un résumé

CSV Format attendu:
    company_name,first_name,last_name,email,website,linkedin_url,industry
    Aircall,Sophie,Durand,sophie@aircall.io,https://aircall.io,,SaaS
"""

import csv
import uuid
import sys
import argparse
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Service role pour bypass RLS

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in .env")
    sys.exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def upload_contacts(csv_path: str, client_name: str, template_name: str) -> str:
    """
    Upload contacts from CSV to Supabase.

    Args:
        csv_path: Path to CSV file
        client_name: Name of the client (must exist in clients table)
        template_name: Name of the template (must exist in templates table)

    Returns:
        batch_id: UUID of the batch created
    """
    print(f"\\n🚀 Starting upload...")
    print(f"📁 CSV file: {csv_path}")
    print(f"🏢 Client: {client_name}")
    print(f"📧 Template: {template_name}")
    print()

    # 1. Get client_id
    print("🔍 Looking up client...")
    client_result = supabase.table('clients').select('id').eq('client_name', client_name).execute()

    if not client_result.data or len(client_result.data) == 0:
        print(f"❌ Client '{client_name}' not found in database")
        print("   Available clients:")
        all_clients = supabase.table('clients').select('client_name').execute()
        for c in all_clients.data:
            print(f"   - {c['client_name']}")
        sys.exit(1)

    client_id = client_result.data[0]['id']
    print(f"✅ Client found: {client_id}")

    # 2. Get template_id
    print("🔍 Looking up template...")
    template_result = supabase.table('templates').select('id').eq('template_name', template_name).execute()

    if not template_result.data or len(template_result.data) == 0:
        print(f"❌ Template '{template_name}' not found in database")
        print("   Available templates:")
        all_templates = supabase.table('templates').select('template_name').execute()
        for t in all_templates.data:
            print(f"   - {t['template_name']}")
        sys.exit(1)

    template_id = template_result.data[0]['id']
    print(f"✅ Template found: {template_id}")

    # 3. Generate batch_id
    batch_id = str(uuid.uuid4())
    print(f"📦 Generated batch_id: {batch_id}")

    # 4. Read CSV and prepare records
    print(f"📖 Reading CSV file...")
    contacts = []

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Validate required field
                if not row.get('company_name'):
                    print(f"⚠️  Skipping row: missing company_name")
                    continue

                contacts.append({
                    'client_id': client_id,
                    'template_id': template_id,
                    'batch_id': batch_id,
                    'first_name': row.get('first_name', '').strip() or None,
                    'last_name': row.get('last_name', '').strip() or None,
                    'email': row.get('email', '').strip() or None,
                    'company_name': row['company_name'].strip(),
                    'website': row.get('website', '').strip() or None,
                    'linkedin_url': row.get('linkedin_url', '').strip() or None,
                    'industry': row.get('industry', '').strip() or None,
                    'status': 'pending'
                })

    except FileNotFoundError:
        print(f"❌ File not found: {csv_path}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading CSV: {str(e)}")
        sys.exit(1)

    if not contacts:
        print("❌ No valid contacts found in CSV")
        sys.exit(1)

    print(f"✅ Loaded {len(contacts)} contacts from CSV")

    # 5. Bulk insert
    print(f"💾 Inserting contacts into Supabase...")

    try:
        result = supabase.table('contacts_to_enrich').insert(contacts).execute()
        print(f"✅ Successfully inserted {len(contacts)} contacts")

    except Exception as e:
        print(f"❌ Error inserting contacts: {str(e)}")
        sys.exit(1)

    # 6. Summary
    print()
    print("="*60)
    print("✅ UPLOAD COMPLETE")
    print("="*60)
    print(f"📦 Batch ID: {batch_id}")
    print(f"🏢 Client: {client_name}")
    print(f"📧 Template: {template_name}")
    print(f"📊 Contacts uploaded: {len(contacts)}")
    print()
    print("Next steps:")
    print("1. Trigger n8n workflow with this batch_id")
    print("2. Or call API: POST /campaigns/generate")
    print(f"   Body: {{ \"batch_id\": \"{batch_id}\" }}")
    print()

    return batch_id


def main():
    parser = argparse.ArgumentParser(
        description="Upload contacts from CSV to Supabase",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python upload_contacts.py data/contacts.csv --client "Acme Inc" --template "Cold Email V1"

  python upload_contacts.py contacts.csv \\
    --client "Test Client" \\
    --template "LinkedIn Outreach"

CSV Format:
  company_name,first_name,last_name,email,website,linkedin_url,industry
  Aircall,Sophie,Durand,sophie@aircall.io,https://aircall.io,,SaaS
        """
    )

    parser.add_argument('csv_file', help='Path to CSV file with contacts')
    parser.add_argument('--client', required=True, help='Client name (must exist in clients table)')
    parser.add_argument('--template', required=True, help='Template name (must exist in templates table)')

    args = parser.parse_args()

    # Upload contacts
    batch_id = upload_contacts(args.csv_file, args.client, args.template)

    sys.exit(0)


if __name__ == "__main__":
    main()
