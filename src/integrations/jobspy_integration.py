"""
JobSpy Lead Generator Integration

Wrapper pour générer des leads depuis JobSpy (offres d'emploi).
Détecte les entreprises qui recrutent = signaux d'achat potentiels.
"""

import requests
import logging
from typing import List, Dict, Optional
import os

logger = logging.getLogger(__name__)


class JobSpyLeadGenerator:
    """
    Génère des leads depuis JobSpy (offres d'emploi).

    Logic:
    - Entreprise recrute "Head of Sales" = besoin de leads
    - Entreprise recrute "DevOps Engineer" = besoin d'infrastructure
    - Entreprise recrute (en général) = croissance = opportunité

    Usage:
        generator = JobSpyLeadGenerator(api_url="http://localhost:8000")
        leads = generator.search_jobs(
            job_title="Head of Sales",
            location="France",
            company_size=["11-50", "51-200"],
            max_results=100
        )
    """

    def __init__(self, jobspy_api_url: Optional[str] = None):
        """
        Initialize JobSpy Lead Generator.

        Args:
            jobspy_api_url: JobSpy API URL (default: http://localhost:8000)
        """
        self.api_url = jobspy_api_url or os.getenv(
            "JOBSPY_API_URL",
            "http://localhost:8000"
        )
        logger.info(f"JobSpy API URL: {self.api_url}")

    def search_jobs(
        self,
        job_title: str,
        location: str,
        company_size: Optional[List[str]] = None,
        industries: Optional[List[str]] = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Search job postings and extract companies.

        Args:
            job_title: "Head of Sales", "DevOps Engineer", "" for all jobs
            location: "France", "Ile-de-France", "Paris"
            company_size: ["11-50", "51-200", "201-500"]
            industries: ["SaaS", "Tech"] (optional filter)
            max_results: Maximum number of jobs to fetch

        Returns:
            List of leads with company info + hiring signal

        Example output:
            [
                {
                    "company_name": "Aircall",
                    "job_title": "Head of Sales France",
                    "location": "Paris",
                    "company_size": "51-200",
                    "company_website": "https://aircall.io",
                    "hiring_signal": "Recruiting for Head of Sales",
                    "job_posted_date": "2025-01-10",
                    "job_url": "https://...",
                    "source": "jobspy"
                },
                ...
            ]
        """
        try:
            # Call JobSpy API to execute workflow
            # Note: Adapt this based on actual JobSpy API endpoints

            # Option 1: Create and execute workflow
            workflow_name = f"search_{job_title}_{location}".replace(" ", "_").lower()

            logger.info(f"Creating JobSpy workflow: {workflow_name}")

            # Create workflow (if needed)
            create_response = requests.post(
                f"{self.api_url}/api/workflows",
                json={
                    "name": workflow_name,
                    "search_terms": [job_title] if job_title else [""],
                    "locations": [location],
                    "results_wanted": max_results,
                    "hours_old": 720,  # Last 30 days
                    "country_indeed": "france" if "france" in location.lower() else "worldwide"
                },
                timeout=30
            )

            if create_response.status_code in [200, 201, 409]:  # 409 = already exists
                logger.info(f"Workflow created or already exists")

                # Execute workflow
                execute_response = requests.post(
                    f"{self.api_url}/api/workflows/{workflow_name}/execute",
                    timeout=300  # 5 minutes max
                )

                if execute_response.status_code == 200:
                    execution_data = execute_response.json()

                    # Get results
                    execution_id = execution_data.get("execution_id")
                    if execution_id:
                        results_response = requests.get(
                            f"{self.api_url}/api/executions/{execution_id}/results",
                            timeout=30
                        )

                        if results_response.status_code == 200:
                            jobs = results_response.json().get("results", [])
                            logger.info(f"Found {len(jobs)} jobs")

                            # Extract unique companies
                            return self._extract_companies_from_jobs(
                                jobs,
                                job_title,
                                company_size,
                                industries
                            )

            logger.warning("Could not fetch jobs from JobSpy API")
            return []

        except requests.exceptions.RequestException as e:
            logger.error(f"JobSpy API error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return []

    def _extract_companies_from_jobs(
        self,
        jobs: List[Dict],
        job_title_searched: str,
        company_size_filter: Optional[List[str]] = None,
        industries_filter: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Extract unique companies from job postings.

        Args:
            jobs: Raw job data from JobSpy
            job_title_searched: The job title that was searched
            company_size_filter: Filter by company size
            industries_filter: Filter by industries

        Returns:
            List of unique companies with metadata
        """
        companies = {}

        for job in jobs:
            company_name = job.get("company_name") or job.get("company")
            if not company_name:
                continue

            # Skip if company already processed
            if company_name in companies:
                continue

            # Apply filters
            if company_size_filter:
                job_company_size = job.get("company_size", "")
                # Simple matching (can be improved)
                if not any(size in job_company_size for size in company_size_filter):
                    continue

            if industries_filter:
                job_industry = job.get("industry", "")
                if not any(ind.lower() in job_industry.lower() for ind in industries_filter):
                    continue

            # Extract company info
            companies[company_name] = {
                "company_name": company_name,
                "job_title": job.get("title") or job.get("job_title"),
                "location": job.get("location"),
                "company_size": job.get("company_size"),
                "company_website": job.get("company_url") or job.get("company_website"),
                "hiring_signal": f"Recruiting for {job_title_searched}" if job_title_searched else "Currently hiring",
                "job_posted_date": job.get("date_posted") or job.get("posted_date"),
                "job_url": job.get("job_url"),
                "industry": job.get("industry"),
                "source": "jobspy"
            }

        logger.info(f"Extracted {len(companies)} unique companies from {len(jobs)} jobs")
        return list(companies.values())

    def search_multiple_titles(
        self,
        job_titles: List[str],
        location: str,
        company_size: Optional[List[str]] = None,
        max_results_per_title: int = 50
    ) -> List[Dict]:
        """
        Search multiple job titles in parallel.

        Args:
            job_titles: ["Head of Sales", "VP Marketing", "Business Developer"]
            location: "France"
            company_size: ["11-50", "51-200"]
            max_results_per_title: 50

        Returns:
            Aggregated list of unique companies (deduplicated)
        """
        all_companies = {}

        for job_title in job_titles:
            logger.info(f"Searching jobs for: {job_title}")

            companies = self.search_jobs(
                job_title=job_title,
                location=location,
                company_size=company_size,
                max_results=max_results_per_title
            )

            # Deduplicate by company_name
            for company in companies:
                company_name = company["company_name"]
                if company_name not in all_companies:
                    all_companies[company_name] = company

        logger.info(f"Total unique companies: {len(all_companies)}")
        return list(all_companies.values())


if __name__ == "__main__":
    """Test JobSpy integration."""

    import logging
    logging.basicConfig(level=logging.INFO)

    # Test with JobSpy API (must be running locally)
    generator = JobSpyLeadGenerator(jobspy_api_url="http://localhost:8000")

    print("="*60)
    print("💼 Testing JobSpy Lead Generator")
    print("="*60)

    # Test: Search for companies hiring sales roles
    leads = generator.search_multiple_titles(
        job_titles=["Head of Sales", "VP Marketing"],
        location="France",
        company_size=["11-50", "51-200"],
        max_results_per_title=20
    )

    print(f"\n✅ Found {len(leads)} unique companies")

    if leads:
        print(f"\n📊 Sample lead:")
        sample = leads[0]
        print(f"  - Company: {sample.get('company_name')}")
        print(f"  - Job Title: {sample.get('job_title')}")
        print(f"  - Location: {sample.get('location')}")
        print(f"  - Company Size: {sample.get('company_size')}")
        print(f"  - Website: {sample.get('company_website')}")
        print(f"  - Hiring Signal: {sample.get('hiring_signal')}")
        print(f"  - Posted: {sample.get('job_posted_date')}")

    print("\n" + "="*60)
