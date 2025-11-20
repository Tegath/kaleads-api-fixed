"""
Leads Storage - Store and deduplicate leads in Supabase
Manages comprehensive lead database with intelligent deduplication
"""
import logging
from typing import List, Dict, Optional
from datetime import datetime
import hashlib
from .supabase_client import SupabaseClient

logger = logging.getLogger(__name__)


class LeadsStorage:
    """
    Store and manage leads in Supabase with deduplication.

    Table schema (create in Supabase):

    CREATE TABLE leads (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        lead_hash TEXT UNIQUE NOT NULL,  -- For deduplication
        company_name TEXT NOT NULL,
        city TEXT,
        country TEXT,
        address TEXT,
        phone TEXT,
        email TEXT,
        website TEXT,
        rating FLOAT,
        reviews_count INTEGER,
        place_id TEXT,
        search_query TEXT,
        source TEXT,  -- 'google_maps' or 'jobspy'
        raw_data JSONB,  -- Full API response
        client_id TEXT,  -- Which client this lead is for
        created_at TIMESTAMP DEFAULT NOW(),
        updated_at TIMESTAMP DEFAULT NOW()
    );

    CREATE INDEX idx_leads_hash ON leads(lead_hash);
    CREATE INDEX idx_leads_client ON leads(client_id);
    CREATE INDEX idx_leads_source ON leads(source);
    CREATE INDEX idx_leads_city ON leads(city);
    """

    def __init__(self, client_id: str = "kaleads"):
        self.supabase_client = SupabaseClient()
        self.client_id = client_id
        self.table_name = "leads"

    def _generate_lead_hash(self, lead: Dict) -> str:
        """
        Generate unique hash for deduplication.
        Based on: company_name + city + source
        """
        company = lead.get("company_name", "").lower().strip()
        city = lead.get("city", "").lower().strip()
        source = lead.get("source", "").lower().strip()

        # Create unique key
        key = f"{company}_{city}_{source}"

        # Hash it
        return hashlib.md5(key.encode()).hexdigest()

    def _prepare_lead_data(self, lead: Dict) -> Dict:
        """Prepare lead data for Supabase insertion"""
        return {
            "lead_hash": self._generate_lead_hash(lead),
            "company_name": lead.get("company_name") or lead.get("name"),
            "city": lead.get("city"),
            "country": lead.get("country"),
            "address": lead.get("address"),
            "phone": lead.get("phone"),
            "email": lead.get("email"),
            "website": lead.get("website"),
            "rating": lead.get("rating"),
            "reviews_count": lead.get("reviews_count"),
            "place_id": lead.get("place_id"),
            "search_query": lead.get("search_query"),
            "source": lead.get("source", "google_maps"),
            "raw_data": lead,
            "client_id": self.client_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

    def store_leads(self, leads: List[Dict], batch_size: int = 100) -> Dict[str, int]:
        """
        Store leads in Supabase with automatic deduplication.

        Args:
            leads: List of lead dictionaries
            batch_size: Number of leads to insert per batch

        Returns:
            Stats: {
                "total_leads": 1000,
                "new_leads": 850,
                "duplicates_skipped": 150,
                "errors": 0
            }
        """
        stats = {
            "total_leads": len(leads),
            "new_leads": 0,
            "duplicates_skipped": 0,
            "errors": 0
        }

        if not leads:
            logger.warning("No leads to store")
            return stats

        try:
            # Process in batches
            for i in range(0, len(leads), batch_size):
                batch = leads[i:i + batch_size]
                prepared_batch = []

                for lead in batch:
                    try:
                        prepared_lead = self._prepare_lead_data(lead)
                        prepared_batch.append(prepared_lead)
                    except Exception as e:
                        logger.error(f"Error preparing lead: {e}")
                        stats["errors"] += 1

                # Insert batch with upsert (on_conflict: do nothing)
                if prepared_batch:
                    try:
                        result = self.supabase_client.client.table(self.table_name).upsert(
                            prepared_batch,
                            on_conflict="lead_hash"  # Skip duplicates
                        ).execute()

                        # Count new vs duplicates
                        if result.data:
                            new_count = len(result.data)
                            stats["new_leads"] += new_count
                            stats["duplicates_skipped"] += len(batch) - new_count
                        else:
                            # All were duplicates
                            stats["duplicates_skipped"] += len(batch)

                        logger.info(f"Batch {i//batch_size + 1}: Stored {len(batch)} leads")

                    except Exception as e:
                        logger.error(f"Error inserting batch: {e}")
                        stats["errors"] += len(batch)

            logger.info(f"✅ Storage complete: {stats['new_leads']} new, {stats['duplicates_skipped']} duplicates, {stats['errors']} errors")
            return stats

        except Exception as e:
            logger.error(f"Error storing leads: {e}")
            stats["errors"] = len(leads)
            return stats

    def get_lead_count(self, source: Optional[str] = None) -> int:
        """Get total lead count, optionally filtered by source"""
        try:
            query = self.supabase_client.client.table(self.table_name).select("id", count="exact")

            if source:
                query = query.eq("source", source)

            query = query.eq("client_id", self.client_id)

            result = query.execute()
            return result.count or 0

        except Exception as e:
            logger.error(f"Error getting lead count: {e}")
            return 0

    def get_city_stats(self) -> List[Dict]:
        """Get lead count by city"""
        try:
            result = self.supabase_client.client.table(self.table_name).select(
                "city, count",
                count="exact"
            ).eq("client_id", self.client_id).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting city stats: {e}")
            return []

    def check_lead_exists(self, company_name: str, city: str, source: str = "google_maps") -> bool:
        """Check if a lead already exists"""
        lead_hash = self._generate_lead_hash({
            "company_name": company_name,
            "city": city,
            "source": source
        })

        try:
            result = self.supabase_client.client.table(self.table_name).select("id").eq(
                "lead_hash", lead_hash
            ).execute()

            return len(result.data) > 0

        except Exception as e:
            logger.error(f"Error checking lead existence: {e}")
            return False

    def get_leads_by_city(self, city: str, limit: int = 100) -> List[Dict]:
        """Get leads for a specific city"""
        try:
            result = self.supabase_client.client.table(self.table_name).select("*").eq(
                "city", city
            ).eq("client_id", self.client_id).limit(limit).execute()

            return result.data or []

        except Exception as e:
            logger.error(f"Error getting leads by city: {e}")
            return []
