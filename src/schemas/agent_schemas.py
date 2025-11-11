"""
Schemas pour les inputs/outputs de tous les agents spécialisés.
"""

from pydantic import BaseModel, Field
from typing import Literal, Optional


# ============================================
# Agent 1: PersonaExtractorAgent
# ============================================

class PersonaExtractorInput(BaseModel):
    """Input pour PersonaExtractorAgent"""
    company_name: str = Field(..., description="Nom de l'entreprise cible")
    website: str = Field(..., description="URL du site web")
    industry: str = Field(default="", description="Secteur d'activité")
    website_content: str = Field(default="", description="Contenu pré-scrapé du site (optionnel)")


class PersonaExtractorOutput(BaseModel):
    """Output de PersonaExtractorAgent"""
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

class CompetitorFinderInput(BaseModel):
    """Input pour CompetitorFinderAgent"""
    company_name: str
    website: str
    industry: str = ""
    product_category: str = ""  # Vient de PersonaExtractorAgent


class CompetitorFinderOutput(BaseModel):
    """Output de CompetitorFinderAgent"""
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
    confidence_score: int = Field(..., ge=1, le=5)
    fallback_level: Literal[1, 2, 3, 4]
    reasoning: str


# ============================================
# Agent 3: PainPointAgent
# ============================================

class PainPointInput(BaseModel):
    """Input pour PainPointAgent"""
    company_name: str
    website: str
    industry: str = ""
    target_persona: str = ""  # Vient de PersonaExtractorAgent
    product_category: str = ""


class PainPointOutput(BaseModel):
    """Output de PainPointAgent"""
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
    confidence_score: int = Field(..., ge=1, le=5)
    fallback_level: Literal[1, 2, 3, 4]
    reasoning: str


# ============================================
# Agent 4: SignalGeneratorAgent
# ============================================

class SignalGeneratorInput(BaseModel):
    """Input pour SignalGeneratorAgent"""
    company_name: str
    website: str
    industry: str = ""
    product_category: str  # Vient de PersonaExtractorAgent
    target_persona: str    # Vient de PersonaExtractorAgent


class SignalGeneratorOutput(BaseModel):
    """Output de SignalGeneratorAgent"""
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
    confidence_score: int = Field(..., ge=1, le=5)
    fallback_level: Literal[1, 2, 3, 4]
    reasoning: str


# ============================================
# Agent 5: SystemBuilderAgent
# ============================================

class SystemBuilderInput(BaseModel):
    """Input pour SystemBuilderAgent"""
    company_name: str
    target_persona: str  # Vient d'Agent 1
    specific_target_1: str  # Vient d'Agent 4
    specific_target_2: str  # Vient d'Agent 4
    problem_specific: str  # Vient d'Agent 3


class SystemBuilderOutput(BaseModel):
    """Output de SystemBuilderAgent"""
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
    confidence_score: int = Field(..., ge=1, le=5)
    fallback_level: Literal[1, 2, 3, 4]
    reasoning: str


# ============================================
# Agent 6: CaseStudyAgent
# ============================================

class CaseStudyInput(BaseModel):
    """Input pour CaseStudyAgent"""
    company_name: str
    industry: str = ""
    target_persona: str = ""
    problem_specific: str = ""


class CaseStudyOutput(BaseModel):
    """Output de CaseStudyAgent"""
    case_study_result: str = Field(
        ...,
        description="Résultat mesurable du case study",
        max_length=200
    )
    confidence_score: int = Field(..., ge=1, le=5)
    fallback_level: Literal[1, 2, 3, 4]
    reasoning: str
