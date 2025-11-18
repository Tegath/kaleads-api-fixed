"""
LeadGenCoordinator Agent - Coordonne la génération de leads basée sur le contexte client

Analyse le ClientContext depuis Supabase et génère automatiquement:
- Stratégie optimale (Google Maps, JobSpy, LinkedIn, ou hybride)
- Mots-clés Google Maps adaptés à l'ICP
- Recherches JobSpy ciblées (job titles, locations, company sizes)
- Plan d'exécution avec estimations

Exemple:
    Client = Kaleads (lead gen B2B)
    → Stratégie: hybrid
    → Google Maps: ["agence marketing", "agence SaaS", "consulting"]
    → JobSpy: ["Head of Sales", "VP Marketing"] (hiring = need leads)
    → Estimation: 480 leads en 17 minutes
"""

from typing import List, Dict, Optional, Literal
from pydantic import Field, BaseModel
import os

try:
    from src.models.client_context import ClientContext
except ImportError:
    ClientContext = None

try:
    from src.utils.cities_helper import CitiesHelper
except ImportError:
    CitiesHelper = None


# ============================================
# Schemas
# ============================================

class CoordinatorInputSchema(BaseModel):
    """Input pour LeadGenCoordinator."""

    client_id: str = Field(description="UUID du client dans Supabase")
    target_count: int = Field(default=500, description="Nombre de leads souhaités")
    regions: Optional[List[str]] = Field(
        default=None,
        description="Régions ciblées (override du ClientContext)"
    )
    country: str = Field(default="France", description="Pays ciblé (France ou Belgique)")


class CoordinatorOutputSchema(BaseModel):
    """Output du LeadGenCoordinator."""

    pain_type: str = Field(description="Type de pain détecté")
    strategy: str = Field(description="Stratégie choisie")
    google_maps_searches: List[Dict] = Field(
        default_factory=list,
        description="Liste des recherches Google Maps à effectuer"
    )
    jobspy_searches: List[Dict] = Field(
        default_factory=list,
        description="Liste des recherches JobSpy à effectuer"
    )
    cities: List[str] = Field(default_factory=list, description="Liste des villes sélectionnées")
    estimated_leads: Dict[str, int] = Field(
        default_factory=dict,
        description="Estimation du nombre de leads par source"
    )
    execution_plan: Dict[str, str] = Field(
        default_factory=dict,
        description="Plan d'exécution avec étapes et temps estimés"
    )


# ============================================
# Helper Functions - Pain Type Classification
# ============================================

def classify_pain_type(pain_solved: str, offerings: List[str]) -> str:
    """
    Classifie le type de problème résolu par le client.

    Args:
        pain_solved: Description du problème résolu
        offerings: Liste des offres/services du client

    Returns:
        Pain type: "lead_generation", "local_services", "hr_recruitment",
                   "devops_infrastructure", "marketing_automation", "generic"

    Examples:
        >>> classify_pain_type("génération de leads B2B", ["prospecting"])
        "lead_generation"

        >>> classify_pain_type("livraison rapide", ["restaurant delivery"])
        "local_services"
    """
    pain_lower = pain_solved.lower()
    offerings_str = " ".join(offerings).lower()

    combined = f"{pain_lower} {offerings_str}"

    # Lead generation
    if any(kw in combined for kw in ["lead", "prospect", "acquisition client", "pipeline", "cold email"]):
        return "lead_generation"

    # Local services
    if any(kw in combined for kw in ["restaurant", "hôtel", "local", "commerce", "livraison", "boutique"]):
        return "local_services"

    # HR/Recruitment
    if any(kw in combined for kw in ["recrutement", "rh", "talent", "hiring", "candidat"]):
        return "hr_recruitment"

    # DevOps/Infrastructure
    if any(kw in combined for kw in ["devops", "infrastructure", "déploiement", "cloud", "sre"]):
        return "devops_infrastructure"

    # Marketing automation
    if any(kw in combined for kw in ["marketing", "automation", "email marketing", "campagne"]):
        return "marketing_automation"

    return "generic"


def generate_google_maps_keywords(
    target_industries: List[str],
    pain_type: str,
    offerings: List[str]
) -> List[str]:
    """
    Génère les mots-clés Google Maps en fonction de l'ICP et du pain type.

    Args:
        target_industries: Industries ciblées (ex: ["SaaS", "Tech", "Consulting"])
        pain_type: Type de pain résolu
        offerings: Offres du client

    Returns:
        Liste de mots-clés optimisés pour Google Maps

    Examples:
        >>> generate_google_maps_keywords(["SaaS", "Tech"], "lead_generation", ["prospecting"])
        ["agence marketing digital", "agence SaaS", "startup tech"]
    """

    # Mapping industry → keywords
    industry_keywords_map = {
        "SaaS": ["agence SaaS", "éditeur de logiciel", "startup SaaS", "scale-up SaaS"],
        "Tech": ["agence web", "startup tech", "scale-up technologique", "entreprise technologique"],
        "Consulting": ["cabinet de conseil", "consulting", "conseil stratégique", "cabinet conseil"],
        "E-commerce": ["boutique en ligne", "e-commerce", "site marchand", "commerce en ligne"],
        "Marketing": ["agence marketing", "agence digitale", "agence communication", "agence marketing digital"],
        "Restaurant": ["restaurant", "bistrot", "brasserie", "restaurant gastronomique"],
        "Hôtellerie": ["hôtel", "résidence hôtelière", "auberge", "chambre d'hôtes"],
        "Retail": ["boutique", "magasin", "commerce de détail", "enseigne"],
        "Santé": ["clinique", "cabinet médical", "centre de santé", "laboratoire médical"],
        "Finance": ["cabinet comptable", "conseiller financier", "banque", "assurance"],
        "Immobilier": ["agence immobilière", "promoteur immobilier", "syndic"],
        "BTP": ["entreprise construction", "maçonnerie", "rénovation", "artisan bâtiment"]
    }

    keywords = []

    # Strategy 1: Based on target industries
    for industry in target_industries:
        # Exact match
        if industry in industry_keywords_map:
            keywords.extend(industry_keywords_map[industry])
        # Partial match (case-insensitive)
        else:
            for key, values in industry_keywords_map.items():
                if industry.lower() in key.lower() or key.lower() in industry.lower():
                    keywords.extend(values)

    # Strategy 2: Based on pain type (if no industries matched)
    if not keywords:
        if pain_type == "lead_generation":
            keywords = ["agence marketing", "agence SaaS", "consulting", "startup"]
        elif pain_type == "local_services":
            keywords = ["restaurant", "hôtel", "commerce", "boutique"]
        elif pain_type == "hr_recruitment":
            keywords = ["startup", "scale-up", "entreprise", "société"]
        elif pain_type == "devops_infrastructure":
            keywords = ["startup tech", "scale-up", "entreprise technologique"]
        elif pain_type == "marketing_automation":
            keywords = ["agence marketing", "agence digitale", "e-commerce"]
        else:
            keywords = ["entreprise", "société", "startup"]

    # Remove duplicates and limit to top 5
    keywords = list(set(keywords))[:5]

    return keywords


def generate_jobspy_searches(
    target_industries: List[str],
    pain_type: str,
    location: str
) -> List[Dict]:
    """
    Génère les recherches JobSpy en fonction de l'ICP et du pain type.

    Logic:
    - "lead_generation": Chercher Sales/Marketing roles (= besoin de leads)
    - "hr_recruitment": Chercher tous les postes (= entreprises qui recrutent)
    - "devops_infrastructure": Chercher DevOps/SRE roles (= besoin d'infra)

    Args:
        target_industries: Industries ciblées
        pain_type: Type de pain résolu
        location: Location (ex: "France", "Belgique")

    Returns:
        Liste de JobSpySearchParams (as dicts)
    """

    searches = []

    if pain_type == "lead_generation":
        # Entreprises qui recrutent en Sales/Marketing = besoin de leads
        searches.extend([
            {
                "job_title": "Head of Sales",
                "location": location,
                "company_size": ["11-50", "51-200", "201-500"],
                "industries": target_industries,
                "max_results": 100
            },
            {
                "job_title": "VP Marketing",
                "location": location,
                "company_size": ["11-50", "51-200", "201-500"],
                "industries": target_industries,
                "max_results": 100
            },
            {
                "job_title": "Business Developer",
                "location": location,
                "company_size": ["11-50", "51-200"],
                "industries": target_industries,
                "max_results": 100
            }
        ])

    elif pain_type == "hr_recruitment":
        # Toutes les entreprises qui recrutent
        searches.append({
            "job_title": "",  # All jobs
            "location": location,
            "company_size": ["11-50", "51-200", "201-500"],
            "industries": target_industries,
            "max_results": 200
        })

    elif pain_type == "devops_infrastructure":
        # Entreprises qui recrutent DevOps = besoin d'infra
        searches.extend([
            {
                "job_title": "DevOps Engineer",
                "location": location,
                "company_size": ["11-50", "51-200"],
                "industries": target_industries,
                "max_results": 100
            },
            {
                "job_title": "SRE",
                "location": location,
                "company_size": ["51-200", "201-500"],
                "industries": target_industries,
                "max_results": 100
            }
        ])

    elif pain_type == "marketing_automation":
        # Entreprises qui recrutent Marketing = besoin automation
        searches.extend([
            {
                "job_title": "Marketing Manager",
                "location": location,
                "company_size": ["11-50", "51-200"],
                "industries": target_industries,
                "max_results": 100
            },
            {
                "job_title": "Growth Marketing",
                "location": location,
                "company_size": ["11-50", "51-200"],
                "industries": target_industries,
                "max_results": 100
            }
        ])

    return searches


def determine_strategy(
    pain_type: str,
    target_count: int,
    target_industries: List[str]
) -> str:
    """
    Détermine la stratégie optimale en fonction du contexte.

    Args:
        pain_type: Type de pain résolu
        target_count: Nombre de leads souhaités
        target_industries: Industries ciblées

    Returns:
        "google_maps_only", "jobspy_only", "hybrid", ou "linkedin_primary"
    """

    # Local services → Google Maps only (commerces locaux)
    if pain_type == "local_services":
        return "google_maps_only"

    # HR recruitment → JobSpy primary (focus on hiring companies)
    if pain_type == "hr_recruitment":
        return "jobspy_only"

    # Lead generation + B2B industries → Hybrid (best coverage)
    if pain_type == "lead_generation" and target_industries:
        return "hybrid"

    # DevOps/Infrastructure → Hybrid (Google Maps for agencies + JobSpy for tech companies)
    if pain_type == "devops_infrastructure":
        return "hybrid"

    # Default: hybrid for flexibility
    return "hybrid"


# ============================================
# LeadGenCoordinator Agent
# ============================================

class LeadGenCoordinatorAgent:
    """
    LeadGenCoordinator Agent - Intelligent lead generation strategist.

    Analyzes ClientContext and generates optimized search strategies for:
    - Google Maps (local businesses)
    - JobSpy (hiring signals)
    - LinkedIn (future)

    Returns structured parameters for n8n workflows.
    """

    def __init__(
        self,
        client_context: Optional["ClientContext"] = None
    ):
        """
        Initialize LeadGenCoordinator.

        Args:
            client_context: Client context from Supabase
        """
        self.client_context = client_context

        # Initialize CitiesHelper if available
        self.cities_helper = None
        if CitiesHelper:
            try:
                self.cities_helper = CitiesHelper()
            except Exception as e:
                print(f"Warning: Could not initialize CitiesHelper: {e}")

    def run(self, input_data: CoordinatorInputSchema) -> CoordinatorOutputSchema:
        """
        Analyze client context and generate lead generation strategy.

        Args:
            input_data: Coordinator input with client_id, target_count, etc.

        Returns:
            CoordinatorOutputSchema with strategy and search parameters
        """
        # Extract context data
        if not self.client_context:
            raise ValueError("ClientContext is required")

        pain_solved = self.client_context.pain_solved
        offerings = self.client_context.offerings
        target_industries = self.client_context.target_industries or []

        # Get ICP data (may not exist on older contexts)
        icp = getattr(self.client_context, 'icp', {}) or {}

        # Classify pain type
        pain_type = classify_pain_type(pain_solved, offerings)

        # Determine strategy
        strategy = determine_strategy(pain_type, input_data.target_count, target_industries)

        # Select cities using CitiesHelper
        cities = []
        if self.cities_helper:
            cities = self.cities_helper.optimize_city_selection(
                target_count=input_data.target_count,
                pain_type=pain_type,
                target_industries=target_industries,
                country=input_data.country
            )
        else:
            # Fallback: use top 10 cities
            cities = ["Paris", "Lyon", "Marseille", "Toulouse", "Nice", "Nantes",
                     "Bordeaux", "Lille", "Rennes", "Strasbourg"]

        # Generate Google Maps searches
        google_maps_searches = []
        if strategy in ["google_maps_only", "hybrid"]:
            keywords = generate_google_maps_keywords(target_industries, pain_type, offerings)

            for keyword in keywords:
                google_maps_searches.append({
                    "query": keyword,
                    "cities": cities,
                    "max_results_per_city": 50
                })

        # Generate JobSpy searches
        jobspy_searches = []
        if strategy in ["jobspy_only", "hybrid"]:
            jobspy_searches = generate_jobspy_searches(
                target_industries=target_industries,
                pain_type=pain_type,
                location=input_data.country
            )

        # Estimate leads
        estimated_gmaps = len(google_maps_searches) * len(cities) * 50
        estimated_jobspy = sum([s.get("max_results", 100) for s in jobspy_searches])

        estimated_leads = {
            "google_maps": estimated_gmaps,
            "jobspy": estimated_jobspy,
            "total": estimated_gmaps + estimated_jobspy
        }

        # Execution plan
        execution_plan = {
            "step_1": f"Execute {len(google_maps_searches)} Google Maps searches in parallel",
            "step_2": f"Execute {len(jobspy_searches)} JobSpy searches in parallel",
            "step_3": "Merge and deduplicate leads by company_name",
            "step_4": "Feed qualified leads to email generation pipeline",
            "estimated_time": f"{(estimated_gmaps + estimated_jobspy) // 60} minutes"
        }

        return CoordinatorOutputSchema(
            pain_type=pain_type,
            strategy=strategy,
            google_maps_searches=google_maps_searches,
            jobspy_searches=jobspy_searches,
            cities=cities,
            estimated_leads=estimated_leads,
            execution_plan=execution_plan
        )


if __name__ == "__main__":
    """Test LeadGenCoordinator with mock ClientContext."""

    from src.models.client_context import ClientContext

    # Mock ClientContext for Kaleads
    mock_context = ClientContext(
        client_id="kaleads",
        client_name="Kaleads",
        offerings=["lead generation B2B", "prospecting automation", "cold email"],
        pain_solved="génération de leads B2B qualifiés via l'automatisation",
        target_industries=["SaaS", "Tech", "Consulting", "Marketing"],
        icp={
            "company_size": ["11-50", "51-200"],
            "regions": ["France"]
        }
    )

    agent = LeadGenCoordinatorAgent(client_context=mock_context)

    result = agent.run(CoordinatorInputSchema(
        client_id="kaleads",
        target_count=500,
        country="France"
    ))

    print("="*60)
    print("🎯 LEAD GENERATION STRATEGY")
    print("="*60)
    print(f"\nPain Type: {result.pain_type}")
    print(f"Strategy: {result.strategy}")

    print(f"\n📍 Google Maps Searches ({len(result.google_maps_searches)}):")
    for search in result.google_maps_searches:
        print(f"  - {search['query']} in {len(search['cities'])} cities")

    print(f"\n💼 JobSpy Searches ({len(result.jobspy_searches)}):")
    for search in result.jobspy_searches:
        print(f"  - {search['job_title']} in {search['location']}")

    print(f"\n📊 Estimated Leads:")
    for key, value in result.estimated_leads.items():
        print(f"  - {key}: {value}")

    print(f"\n📋 Execution Plan:")
    for step, desc in result.execution_plan.items():
        print(f"  {step}: {desc}")

    print("\n" + "="*60)
