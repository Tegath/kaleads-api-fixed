"""
Schemas pour les requêtes de campagne et résultats globaux.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional


class Contact(BaseModel):
    """Un contact à enrichir"""
    company_name: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    linkedin_url: Optional[str] = None
    industry: Optional[str] = None


class CampaignRequest(BaseModel):
    """Input pour l'orchestrateur de campagne"""
    template_content: str = Field(..., description="Contenu du template email avec variables {{variable_name}}")
    contacts: List[Contact] = Field(..., description="Liste des contacts à enrichir")
    context: Dict[str, str] = Field(
        ...,
        description="Contexte client (pci, personas, pain_points, etc.)"
    )
    batch_id: Optional[str] = Field(default=None, description="ID du batch pour tracking")
    enable_cache: bool = Field(default=True, description="Activer le cache pour les résultats")


class EmailVariables(BaseModel):
    """Variables générées pour un email"""
    # Variables de base
    first_name: Optional[str] = None
    company_name: str

    # Variables générées par les agents
    target_persona: str
    product_category: str
    competitor_name: str
    competitor_product_category: str
    problem_specific: str
    impact_measurable: str
    specific_signal_1: str
    specific_signal_2: str
    specific_target_1: str
    specific_target_2: str
    system_1: str
    system_2: str
    system_3: str
    case_study_result: str

    # Hook généré
    hook: Optional[str] = None


class EmailResult(BaseModel):
    """Résultat pour un email généré"""
    contact: Contact
    email_generated: str = Field(..., description="Email avec toutes les variables remplacées")
    variables: Dict[str, str] = Field(..., description="Toutes les variables générées")
    quality_score: int = Field(..., ge=0, le=100, description="Score de qualité global")

    # Métriques de fallback
    fallback_levels: Dict[str, int] = Field(
        ...,
        description="Niveau de fallback utilisé par chaque agent"
    )
    confidence_scores: Dict[str, int] = Field(
        ...,
        description="Scores de confiance par variable"
    )

    # Métriques de performance
    generation_time_ms: int = Field(..., description="Temps de génération en millisecondes")
    tokens_used: Optional[int] = Field(default=None, description="Tokens consommés")

    # Erreurs éventuelles
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class CampaignResult(BaseModel):
    """Output de l'orchestrateur de campagne"""
    batch_id: Optional[str] = None
    emails_generated: List[EmailResult]

    # Métriques globales
    total_contacts: int
    success_count: int
    success_rate: float = Field(..., ge=0, le=1, description="Taux de succès (0-1)")
    average_quality_score: float = Field(..., ge=0, le=100)

    # Performance
    total_execution_time_seconds: float
    average_time_per_email_seconds: float
    cache_hit_rate: float = Field(..., ge=0, le=1, description="Taux de cache hit (0-1)")
    total_tokens_used: Optional[int] = None
    estimated_cost_usd: Optional[float] = None

    # Logs et debug
    logs: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
