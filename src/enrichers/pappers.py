"""
Pappers Enricher - French Company Registry Data.

Pappers (pappers.fr) provides access to French company data:
- SIREN/SIRET numbers
- CEO/Directors names
- Company financials
- Employee count
- Address
- Activity codes (NAF)

API Documentation: https://www.pappers.fr/api
"""

import os
import requests
from typing import Dict, Any, List, Optional
from .base import BaseEnricher, EnrichmentResult, enricher_factory


class PappersEnricher(BaseEnricher):
    """
    Enricher for Pappers.fr API.

    Requires PAPPERS_API_KEY environment variable.

    Available fields:
    - siren: SIREN number
    - siret: SIRET number (headquarters)
    - nom_complet: Full company name
    - dirigeants: List of directors/CEO
    - effectif: Employee count range
    - chiffre_affaires: Revenue
    - date_creation: Creation date
    - adresse: Headquarters address
    - code_naf: NAF activity code
    - forme_juridique: Legal form (SAS, SARL, etc.)
    """

    BASE_URL = "https://api.pappers.fr/v2"

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("PAPPERS_API_KEY")

    def get_source_name(self) -> str:
        return "pappers"

    def get_available_fields(self) -> List[str]:
        return [
            "siren",
            "siret",
            "nom_complet",
            "dirigeants",
            "effectif",
            "chiffre_affaires",
            "date_creation",
            "adresse",
            "code_naf",
            "forme_juridique",
            "capital_social",
            "statut_rcs"
        ]

    def enrich(
        self,
        company_name: str,
        fields: Optional[List[str]] = None,
        **kwargs
    ) -> EnrichmentResult:
        """
        Fetch company data from Pappers.

        Args:
            company_name: Company name to search
            fields: Specific fields to extract (None = all)
            siren: Optional SIREN to search directly
        """
        if not self.api_key:
            return EnrichmentResult(
                source="pappers",
                company_name=company_name,
                data={},
                success=False,
                error="PAPPERS_API_KEY not configured"
            )

        # Check for direct SIREN lookup
        siren = kwargs.get("siren")

        try:
            if siren:
                data, elapsed = self._timed_operation(self._fetch_by_siren, siren)
            else:
                data, elapsed = self._timed_operation(self._search_company, company_name)

            if not data:
                return EnrichmentResult(
                    source="pappers",
                    company_name=company_name,
                    data={},
                    success=False,
                    error="Company not found",
                    processing_time_ms=elapsed
                )

            # Filter fields if specified
            if fields:
                data = {k: v for k, v in data.items() if k in fields}

            return EnrichmentResult(
                source="pappers",
                company_name=company_name,
                data=data,
                success=True,
                processing_time_ms=elapsed
            )

        except Exception as e:
            return EnrichmentResult(
                source="pappers",
                company_name=company_name,
                data={},
                success=False,
                error=str(e)
            )

    def _search_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """Search for a company by name."""
        response = requests.get(
            f"{self.BASE_URL}/recherche",
            params={
                "api_token": self.api_key,
                "q": company_name,
                "par_page": 1
            },
            timeout=10
        )
        response.raise_for_status()

        results = response.json().get("resultats", [])
        if not results:
            return None

        # Get first result's SIREN and fetch full details
        siren = results[0].get("siren")
        if siren:
            return self._fetch_by_siren(siren)
        return results[0]

    def _fetch_by_siren(self, siren: str) -> Optional[Dict[str, Any]]:
        """Fetch company details by SIREN."""
        response = requests.get(
            f"{self.BASE_URL}/entreprise",
            params={
                "api_token": self.api_key,
                "siren": siren
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()

        # Extract and normalize relevant fields
        return self._normalize_data(data)

    def _normalize_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize Pappers response to standard format."""
        normalized = {
            "siren": raw_data.get("siren"),
            "siret": raw_data.get("siege", {}).get("siret"),
            "nom_complet": raw_data.get("nom_entreprise"),
            "date_creation": raw_data.get("date_creation"),
            "forme_juridique": raw_data.get("forme_juridique"),
            "capital_social": raw_data.get("capital"),
            "effectif": raw_data.get("effectif"),
            "chiffre_affaires": raw_data.get("finances", {}).get("chiffre_affaires") if raw_data.get("finances") else None,
            "code_naf": raw_data.get("code_naf"),
            "statut_rcs": raw_data.get("statut_rcs"),
        }

        # Extract address
        siege = raw_data.get("siege", {})
        if siege:
            normalized["adresse"] = {
                "rue": siege.get("adresse_ligne_1"),
                "code_postal": siege.get("code_postal"),
                "ville": siege.get("ville")
            }

        # Extract directors
        representants = raw_data.get("representants", [])
        if representants:
            normalized["dirigeants"] = [
                {
                    "nom": rep.get("nom_complet"),
                    "qualite": rep.get("qualite"),
                    "date_prise_poste": rep.get("date_prise_poste")
                }
                for rep in representants[:5]  # Limit to 5
            ]

            # Extract CEO specifically
            for rep in representants:
                qualite = rep.get("qualite", "").lower()
                if any(title in qualite for title in ["president", "directeur general", "gerant"]):
                    normalized["ceo_name"] = rep.get("nom_complet")
                    break

        return normalized


# Register with factory
enricher_factory.register("pappers", PappersEnricher())
