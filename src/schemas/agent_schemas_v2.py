"""
Schemas pour les inputs/outputs de tous les agents spécialisés (Atomic Agents v2).
"""

from atomic_agents import BaseIOSchema
from pydantic import Field
from typing import Literal


# ============================================
# Agent 1: PersonaExtractorAgent
# ============================================

class PersonaExtractorInputSchema(BaseIOSchema):
    """
    Input pour PersonaExtractorAgent.

    Contient les informations de base sur l'entreprise à analyser pour identifier
    le persona cible et la catégorie de produit.
    """
    company_name: str = Field(..., description="Nom de l'entreprise cible")
    website: str = Field(..., description="URL du site web")
    industry: str = Field(default="", description="Secteur d'activité")
    website_content: str = Field(default="", description="Contenu pré-scrapé du site (optionnel)")


class PersonaExtractorOutputSchema(BaseIOSchema):
    """
    Output de PersonaExtractorAgent.

    Contient le persona cible identifié et la catégorie de produit avec métadonnées
    de confiance et raisonnement.
    """
    target_persona: str = Field(
        ...,
        description="Persona cible identifié (ex: 'vP Sales')",
        max_length=50
    )
    product_category: str = Field(
        ...,
        description="Catégorie de produit (ex: 'solution de téléphonie cloud')",
        max_length=100
    )
    confidence_score: int = Field(
        ...,
        ge=1,
        le=5,
        description="Score de confiance (1=générique, 5=trouvé sur site)"
    )
    fallback_level: Literal[1, 2, 3, 4] = Field(
        ...,
        description="Niveau de fallback utilisé"
    )
    reasoning: str = Field(
        ...,
        description="Raisonnement (chain-of-thought)"
    )


# ============================================
# Agent 2: CompetitorFinderAgent
# ============================================

class CompetitorFinderInputSchema(BaseIOSchema):
    """
    Input pour CompetitorFinderAgent.

    Informations sur l'entreprise pour identifier son concurrent principal.
    """
    company_name: str = Field(..., description="Nom de l'entreprise")
    website: str = Field(..., description="URL du site web")
    industry: str = Field(default="", description="Secteur d'activité")
    product_category: str = Field(default="", description="Catégorie de produit (vient de PersonaExtractorAgent)")
    website_content: str = Field(default="", description="Contenu pré-scrapé du site (optionnel)")


class CompetitorFinderOutputSchema(BaseIOSchema):
    """
    Output de CompetitorFinderAgent.

    Concurrent identifié avec sa catégorie de produit.
    """
    competitor_name: str = Field(
        ...,
        description="Nom du concurrent identifié",
        max_length=50
    )
    competitor_product_category: str = Field(
        ...,
        description="Catégorie du produit concurrent",
        max_length=100
    )
    confidence_score: int = Field(..., ge=1, le=5, description="Score de confiance")
    fallback_level: Literal[1, 2, 3, 4] = Field(..., description="Niveau de fallback")
    reasoning: str = Field(..., description="Raisonnement")


# ============================================
# Agent 3: PainPointAgent
# ============================================

class PainPointInputSchema(BaseIOSchema):
    """
    Input pour PainPointAgent.

    Informations pour identifier le pain point spécifique de l'entreprise.
    """
    company_name: str = Field(..., description="Nom de l'entreprise")
    website: str = Field(..., description="URL du site web")
    industry: str = Field(default="", description="Secteur d'activité")
    target_persona: str = Field(default="", description="Persona cible (vient de PersonaExtractorAgent)")
    product_category: str = Field(default="", description="Catégorie de produit")
    website_content: str = Field(default="", description="Contenu pré-scrapé du site (optionnel)")


class PainPointOutputSchema(BaseIOSchema):
    """
    Output de PainPointAgent.

    Pain point spécifique identifié avec son impact mesurable.
    """
    problem_specific: str = Field(
        ...,
        description="Pain point spécifique identifié",
        max_length=200
    )
    impact_measurable: str = Field(
        ...,
        description="Impact mesurable du pain point",
        max_length=150
    )
    confidence_score: int = Field(..., ge=1, le=5, description="Score de confiance")
    fallback_level: Literal[1, 2, 3, 4] = Field(..., description="Niveau de fallback")
    reasoning: str = Field(..., description="Raisonnement")


# ============================================
# Agent 4: SignalGeneratorAgent
# ============================================

class SignalGeneratorInputSchema(BaseIOSchema):
    """
    Input pour SignalGeneratorAgent.

    Informations pour générer des signaux d'intention personnalisés.
    """
    company_name: str = Field(..., description="Nom de l'entreprise")
    website: str = Field(..., description="URL du site web")
    industry: str = Field(default="", description="Secteur d'activité")
    product_category: str = Field(default="", description="Catégorie de produit (vient de PersonaExtractorAgent)")
    target_persona: str = Field(default="", description="Persona cible (vient de PersonaExtractorAgent)")
    website_content: str = Field(default="", description="Contenu pré-scrapé du site (optionnel)")


class SignalGeneratorOutputSchema(BaseIOSchema):
    """
    Output de SignalGeneratorAgent.

    Quatre signaux personnalisés (2 signaux d'intention + 2 ciblages).
    """
    specific_signal_1: str = Field(
        ...,
        description="Premier signal d'intention (volume élevé)",
        max_length=150
    )
    specific_signal_2: str = Field(
        ...,
        description="Deuxième signal d'intention (niche)",
        max_length=150
    )
    specific_target_1: str = Field(
        ...,
        description="Premier ciblage spécifique",
        max_length=150
    )
    specific_target_2: str = Field(
        ...,
        description="Deuxième ciblage spécifique",
        max_length=150
    )
    confidence_score: int = Field(..., ge=1, le=5, description="Score de confiance")
    fallback_level: Literal[1, 2, 3, 4] = Field(..., description="Niveau de fallback")
    reasoning: str = Field(..., description="Raisonnement")


# ============================================
# Agent 5: SystemBuilderAgent
# ============================================

class SystemBuilderInputSchema(BaseIOSchema):
    """
    Input pour SystemBuilderAgent.

    Informations pour identifier les systèmes/processus de l'entreprise.
    """
    company_name: str = Field(..., description="Nom de l'entreprise")
    website: str = Field(default="", description="URL du site web")
    target_persona: str = Field(default="", description="Persona cible (vient d'Agent 1)")
    specific_target_1: str = Field(default="", description="Premier ciblage (vient d'Agent 4)")
    specific_target_2: str = Field(default="", description="Deuxième ciblage (vient d'Agent 4)")
    problem_specific: str = Field(default="", description="Pain point (vient d'Agent 3)")
    website_content: str = Field(default="", description="Contenu pré-scrapé du site (optionnel)")


class SystemBuilderOutputSchema(BaseIOSchema):
    """
    Output de SystemBuilderAgent.

    Trois systèmes/processus identifiés dans l'entreprise.
    """
    system_1: str = Field(
        ...,
        description="Premier système/process identifié",
        max_length=100
    )
    system_2: str = Field(
        ...,
        description="Deuxième système/process identifié",
        max_length=100
    )
    system_3: str = Field(
        ...,
        description="Troisième système/process identifié",
        max_length=100
    )
    confidence_score: int = Field(..., ge=1, le=5, description="Score de confiance")
    fallback_level: Literal[1, 2, 3, 4] = Field(..., description="Niveau de fallback")
    reasoning: str = Field(..., description="Raisonnement")


# ============================================
# Agent 6: CaseStudyAgent
# ============================================

class CaseStudyInputSchema(BaseIOSchema):
    """
    Input pour CaseStudyAgent.

    Informations pour générer un résultat de case study pertinent.
    """
    company_name: str = Field(..., description="Nom de l'entreprise")
    website: str = Field(default="", description="URL du site web")
    industry: str = Field(default="", description="Secteur d'activité")
    target_persona: str = Field(default="", description="Persona cible")
    problem_specific: str = Field(default="", description="Pain point spécifique")
    website_content: str = Field(default="", description="Contenu pré-scrapé du site (optionnel)")


class CaseStudyOutputSchema(BaseIOSchema):
    """
    Output de CaseStudyAgent.

    Résultat mesurable d'un case study.
    """
    case_study_result: str = Field(
        ...,
        description="Résultat mesurable du case study",
        max_length=200
    )
    confidence_score: int = Field(..., ge=1, le=5, description="Score de confiance")
    fallback_level: Literal[1, 2, 3, 4] = Field(..., description="Niveau de fallback")
    reasoning: str = Field(..., description="Raisonnement")
