"""
Scraping Job Manager - Background jobs with resume capability
Manages long-running scraping jobs with continuous saving and progress tracking
"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from src.providers.supabase_client import SupabaseClient
from src.providers.leads_storage import LeadsStorage
from src.integrations.google_maps_integration import GoogleMapsLeadGenerator
from src.helpers.city_strategy import get_strategy_manager

logger = logging.getLogger(__name__)


class ScrapingJobManager:
    """
    Manages background scraping jobs with:
    - Continuous saving (every 100 leads)
    - Progress tracking in database
    - Resume capability after interruption
    - Error handling and retry logic
    """

    def __init__(self, client_id: str = "kaleads"):
        self.supabase_client = SupabaseClient()
        self.leads_storage = LeadsStorage(client_id=client_id)
        self.gmaps = GoogleMapsLeadGenerator()
        self.strategy_manager = get_strategy_manager(min_population=5000)
        self.client_id = client_id

    def create_job(
        self,
        query: str,
        country: str = "France",
        min_population: int = 5000,
        max_priority: int = 3,
        job_type: str = "google_maps"
    ) -> str:
        """
        Create a new scraping job.

        Args:
            query: Search query
            country: Country to scrape
            min_population: Minimum city population
            max_priority: Max priority to include (1-3)
            job_type: 'google_maps' or 'jobspy'

        Returns:
            Job ID (UUID)
        """
        job_id = str(uuid.uuid4())

        # Get cities with strategy
        from src.helpers.cities_loader import get_cities_loader
        cities_loader = get_cities_loader()
        all_cities = cities_loader.get_all_cities(country=country)

        # Filter by strategy
        cities_with_strategy = self.strategy_manager.filter_cities_by_strategy(
            all_cities,
            min_priority=max_priority
        )

        # Estimate cost
        cost_estimate = self.strategy_manager.estimate_scraping_cost(cities_with_strategy)

        # Create job record
        job_data = {
            "id": job_id,
            "job_type": job_type,
            "status": "pending",
            "client_id": self.client_id,
            "query": query,
            "country": country,
            "search_params": {
                "min_population": min_population,
                "max_priority": max_priority
            },
            "total_cities": len(cities_with_strategy),
            "cities_remaining": [c['city'] for c in cities_with_strategy],
            "total_leads_found": 0,
            "total_api_calls": 0,
            "estimated_cost_usd": cost_estimate['estimated_cost_usd'],
            "errors": [],
            "last_checkpoint": {
                "cities_strategy": cities_with_strategy
            },
            "created_at": datetime.utcnow().isoformat()
        }

        # Insert into database
        self.supabase_client.client.table("scraping_jobs").insert(job_data).execute()

        logger.info(f"Created job {job_id}: {query} in {country}")
        logger.info(f"  Cities to scrape: {len(cities_with_strategy)}")
        logger.info(f"  Estimated cost: ${cost_estimate['estimated_cost_usd']}")
        logger.info(f"  Estimated time: {cost_estimate['estimated_time_minutes']} minutes")

        return job_id

    async def run_job(self, job_id: str):
        """
        Run a scraping job in background.

        This method:
        1. Loads job from database
        2. Scrapes cities one by one
        3. Saves leads continuously (every 100 leads)
        4. Updates progress in database
        5. Handles errors gracefully
        """
        try:
            # Load job
            job = self._get_job(job_id)
            if not job:
                logger.error(f"Job {job_id} not found")
                return

            # Mark as running
            self._update_job_status(job_id, "running", started_at=datetime.utcnow().isoformat())

            query = job['query']
            country = job.get('country', 'France')
            cities_strategy = job['last_checkpoint']['cities_strategy']
            cities_remaining = job.get('cities_remaining', [])

            logger.info(f"Starting job {job_id}: {query}")
            logger.info(f"  Remaining cities: {len(cities_remaining)}")

            # Scrape cities one by one
            leads_batch = []
            cities_completed = job.get('cities_completed', 0)
            total_leads = job.get('total_leads_found', 0)
            total_api_calls = job.get('total_api_calls', 0)

            for idx, city_strat in enumerate(cities_strategy):
                city_name = city_strat['city']

                # Skip if already completed
                if city_name not in cities_remaining:
                    continue

                try:
                    logger.info(f"[{idx+1}/{len(cities_strategy)}] Scraping {city_name}...")

                    # Update current city
                    self._update_job(job_id, current_city=city_name)

                    # Scrape with strategy limits
                    city_leads = self.gmaps.search_city_with_pagination(
                        query=query,
                        city=city_name,
                        country=country,
                        max_results=city_strat['max_pages'] * 20,  # ~20 results per page
                        language="fr"
                    )

                    # Add to batch
                    leads_batch.extend(city_leads)
                    total_leads += len(city_leads)
                    total_api_calls += city_strat['max_pages']

                    # Mark city as completed
                    cities_remaining.remove(city_name)
                    cities_completed += 1

                    # Save batch if >= 100 leads
                    if len(leads_batch) >= 100:
                        stats = self.leads_storage.store_leads(leads_batch)
                        logger.info(f"Saved batch: {stats['new_leads']} new leads")
                        leads_batch = []  # Clear batch

                    # Update progress
                    self._update_job(
                        job_id,
                        cities_completed=cities_completed,
                        cities_remaining=cities_remaining,
                        total_leads_found=total_leads,
                        total_api_calls=total_api_calls
                    )

                    # Rate limiting
                    await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"Error scraping {city_name}: {e}")
                    self._add_job_error(job_id, city_name, str(e))
                    continue

            # Save remaining leads
            if leads_batch:
                stats = self.leads_storage.store_leads(leads_batch)
                logger.info(f"Saved final batch: {stats['new_leads']} new leads")

            # Mark as completed
            self._update_job_status(
                job_id,
                "completed",
                completed_at=datetime.utcnow().isoformat()
            )

            logger.info(f"✅ Job {job_id} completed!")
            logger.info(f"  Total leads: {total_leads}")
            logger.info(f"  Cities scraped: {cities_completed}")

        except Exception as e:
            logger.error(f"Job {job_id} failed: {e}")
            self._update_job_status(job_id, "failed", last_error=str(e))

    def _get_job(self, job_id: str) -> Optional[Dict]:
        """Get job from database"""
        result = self.supabase_client.client.table("scraping_jobs").select("*").eq(
            "id", job_id
        ).execute()

        if result.data:
            return result.data[0]
        return None

    def _update_job_status(self, job_id: str, status: str, **kwargs):
        """Update job status"""
        update_data = {"status": status, "updated_at": datetime.utcnow().isoformat()}
        update_data.update(kwargs)

        self.supabase_client.client.table("scraping_jobs").update(update_data).eq(
            "id", job_id
        ).execute()

    def _update_job(self, job_id: str, **kwargs):
        """Update job fields"""
        update_data = {"updated_at": datetime.utcnow().isoformat()}
        update_data.update(kwargs)

        self.supabase_client.client.table("scraping_jobs").update(update_data).eq(
            "id", job_id
        ).execute()

    def _add_job_error(self, job_id: str, city: str, error: str):
        """Add error to job"""
        job = self._get_job(job_id)
        if job:
            errors = job.get('errors', [])
            errors.append({
                "city": city,
                "error": error,
                "timestamp": datetime.utcnow().isoformat()
            })

            self.supabase_client.client.table("scraping_jobs").update({
                "errors": errors,
                "last_error": error,
                "retry_count": job.get('retry_count', 0) + 1
            }).eq("id", job_id).execute()

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """Get current job status"""
        job = self._get_job(job_id)
        if not job:
            return None

        # Calculate progress
        total = job.get('total_cities', 1)
        completed = job.get('cities_completed', 0)
        progress_pct = round((completed / total) * 100, 2) if total > 0 else 0

        return {
            "job_id": job_id,
            "status": job['status'],
            "query": job['query'],
            "progress_pct": progress_pct,
            "cities_completed": completed,
            "total_cities": total,
            "total_leads_found": job.get('total_leads_found', 0),
            "estimated_cost_usd": job.get('estimated_cost_usd', 0),
            "current_city": job.get('current_city'),
            "errors_count": len(job.get('errors', [])),
            "created_at": job.get('created_at'),
            "started_at": job.get('started_at'),
            "completed_at": job.get('completed_at')
        }

    def resume_job(self, job_id: str):
        """Resume a paused or failed job"""
        job = self._get_job(job_id)

        if not job:
            logger.error(f"Job {job_id} not found")
            return

        if job['status'] not in ['paused', 'failed']:
            logger.warning(f"Job {job_id} cannot be resumed (status: {job['status']})")
            return

        if not job.get('can_resume', True):
            logger.error(f"Job {job_id} cannot be resumed")
            return

        logger.info(f"Resuming job {job_id}...")
        self._update_job_status(job_id, "pending")

        # Run in background
        asyncio.create_task(self.run_job(job_id))

    def list_jobs(self, status: str = None, limit: int = 50) -> List[Dict]:
        """List jobs, optionally filtered by status"""
        query = self.supabase_client.client.table("scraping_jobs").select("*")

        if status:
            query = query.eq("status", status)

        result = query.order("created_at", desc=True).limit(limit).execute()

        return result.data or []
