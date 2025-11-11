"""
API REST compatible avec Clay.

Clay peut appeler ces endpoints via HTTP Request enrichment.

Endpoints:
    POST /api/generate-email - Generate un email complet
    POST /api/extract-persona - Agent 1 seulement
    POST /api/find-competitor - Agent 2 seulement
    POST /api/identify-pain - Agent 3 seulement
    POST /api/generate-signals - Agent 4 seulement
    POST /api/build-systems - Agent 5 seulement
    POST /api/create-case-study - Agent 6 seulement
"""

from fastapi import FastAPI, HTTPException, Header, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import os
from dotenv import load_dotenv

from src.orchestrator import CampaignOrchestrator
from src.schemas.campaign_schemas import CampaignRequest, Contact
from src.agents.agents_v2 import (
    PersonaExtractorAgent,
    CompetitorFinderAgent,
    PainPointAgent,
    SignalGeneratorAgent,
    SystemBuilderAgent,
    CaseStudyAgent
)
from src.schemas.agent_schemas_v2 import (
    PersonaExtractorInputSchema,
    CompetitorFinderInputSchema,
    PainPointInputSchema,
    SignalGeneratorInputSchema,
    SystemBuilderInputSchema,
    CaseStudyInputSchema
)

load_dotenv()

app = FastAPI(
    title="Clay-Compatible Email Generation API",
    description="API pour generer des emails personnalises depuis Clay",
    version="1.0.0"
)

# CORS pour permettre les appels depuis Clay
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Authentication
# ============================================

def verify_api_key(x_api_key: str = Header(...)):
    """Verifie la cle API."""
    expected_key = os.getenv("API_KEY", "your-secure-api-key")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


# ============================================
# Schemas pour Clay
# ============================================

class ClayContactInput(BaseModel):
    """
    Input compatible avec les colonnes Clay.

    Dans Clay, vous mappez:
    - company_name → {{company_name}}
    - first_name → {{first_name}}
    - website → {{company_domain}}
    - etc.
    """
    company_name: str = Field(..., description="Nom de l'entreprise")
    first_name: str = Field(..., description="Prenom du contact")
    last_name: Optional[str] = Field(None, description="Nom de famille")
    email: Optional[str] = Field(None, description="Email du contact")
    website: str = Field(..., description="Site web de l'entreprise")
    industry: Optional[str] = Field(None, description="Industrie/secteur")
    company_size: Optional[str] = Field(None, description="Taille entreprise (ex: 50-200)")
    linkedin_url: Optional[str] = Field(None, description="URL LinkedIn")


class ClayEmailRequest(BaseModel):
    """Request pour generer un email complet."""
    contact: ClayContactInput
    template: Optional[str] = Field(
        None,
        description="Template custom (si None, utilise le template par defaut)"
    )
    directives: Optional[str] = Field(
        "Ton professionnel, focus ROI",
        description="Directives pour la generation"
    )
    model: Optional[str] = Field(
        "gpt-4o-mini",
        description="Modele OpenAI (gpt-4o-mini, gpt-4o, etc.)"
    )


class ClayEmailResponse(BaseModel):
    """Response avec l'email genere + variables."""
    success: bool
    email_content: str
    quality_score: int
    generation_time_ms: int

    # Variables individuelles (pour les mapper dans Clay)
    target_persona: str
    product_category: str
    competitor_name: str
    problem_specific: str
    impact_measurable: str
    case_study_result: str
    specific_signal_1: str
    specific_signal_2: str
    specific_target_1: str
    specific_target_2: str
    system_1: str
    system_2: str
    system_3: str

    # Metriques
    fallback_levels: Dict[str, int]
    confidence_scores: Dict[str, int]


class ClayAgentResponse(BaseModel):
    """Response pour un agent individuel."""
    success: bool
    data: Dict
    fallback_level: int
    confidence_score: int
    reasoning: str


# ============================================
# Endpoint principal: Email complet
# ============================================

@app.post("/api/generate-email", response_model=ClayEmailResponse)
async def generate_email_for_clay(
    request: ClayEmailRequest
    # NOTE: Authentication désactivée pour tests locaux
    # Pour activer: ajouter → , api_key: str = Depends(verify_api_key)
):
    """
    Genere un email complet pour un contact Clay.

    Dans Clay, utilisez HTTP Request enrichment:
    - Method: POST
    - URL: https://votre-api.com/api/generate-email
    - Headers: {"X-API-Key": "your-key"}
    - Body: JSON avec contact, template, directives

    Exemple body:
    {
        "contact": {
            "company_name": "{{company_name}}",
            "first_name": "{{first_name}}",
            "website": "{{company_domain}}",
            "industry": "{{industry}}"
        },
        "directives": "Ton professionnel, focus ROI"
    }
    """

    try:
        # Convertir le contact Clay en Contact interne
        contact = Contact(
            company_name=request.contact.company_name,
            first_name=request.contact.first_name,
            last_name=request.contact.last_name or "",
            email=request.contact.email or "",
            website=request.contact.website,
            industry=request.contact.industry or ""
        )

        # Template
        if request.template:
            template = request.template
        else:
            # Template par defaut
            template_path = "data/templates/cold_email_template_example.md"
            if os.path.exists(template_path):
                with open(template_path, "r", encoding="utf-8") as f:
                    template = f.read().split("---")[0].strip()
            else:
                raise HTTPException(status_code=500, detail="Template par defaut introuvable")

        # Orchestrateur
        orchestrator = CampaignOrchestrator(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=request.model,
            enable_cache=True
        )

        # Request
        campaign_request = CampaignRequest(
            template_content=template,
            contacts=[contact],
            context={
                "client_name": "clay-client",
                "directives": request.directives
            },
            batch_id=f"clay-{contact.company_name}",
            enable_cache=True
        )

        # Generer
        result = orchestrator.run(campaign_request)

        if not result.emails_generated:
            raise HTTPException(status_code=500, detail="Echec generation email")

        email = result.emails_generated[0]

        # Response compatible Clay
        return ClayEmailResponse(
            success=True,
            email_content=email.email_generated,
            quality_score=email.quality_score,
            generation_time_ms=email.generation_time_ms,

            # Variables (Clay peut les mapper dans des colonnes separees)
            target_persona=email.variables.get("target_persona", ""),
            product_category=email.variables.get("product_category", ""),
            competitor_name=email.variables.get("competitor_name", ""),
            problem_specific=email.variables.get("problem_specific", ""),
            impact_measurable=email.variables.get("impact_measurable", ""),
            case_study_result=email.variables.get("case_study_result", ""),
            specific_signal_1=email.variables.get("specific_signal_1", ""),
            specific_signal_2=email.variables.get("specific_signal_2", ""),
            specific_target_1=email.variables.get("specific_target_1", ""),
            specific_target_2=email.variables.get("specific_target_2", ""),
            system_1=email.variables.get("system_1", ""),
            system_2=email.variables.get("system_2", ""),
            system_3=email.variables.get("system_3", ""),

            fallback_levels=email.fallback_levels,
            confidence_scores=email.confidence_scores
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Endpoints par agent (pour usage avancé)
# ============================================

@app.post("/api/extract-persona", response_model=ClayAgentResponse)
async def extract_persona(
    contact: ClayContactInput,
    api_key: str = Depends(verify_api_key)
):
    """
    Agent 1: Extrait le persona cible.

    Dans Clay:
    - Appelez cet endpoint pour JUSTE le persona
    - Mappez la reponse → colonnes: target_persona, product_category
    """

    try:
        agent = PersonaExtractorAgent(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini"
        )

        input_data = PersonaExtractorInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            website_content=""
        )

        result = agent.run(input_data)

        return ClayAgentResponse(
            success=True,
            data={
                "target_persona": result.target_persona,
                "product_category": result.product_category
            },
            fallback_level=result.fallback_level,
            confidence_score=result.confidence_score,
            reasoning=result.reasoning
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/find-competitor", response_model=ClayAgentResponse)
async def find_competitor(
    contact: ClayContactInput,
    product_category: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Agent 2: Trouve le concurrent principal.

    Dans Clay:
    - Prerequis: avoir le product_category (depuis extract-persona)
    - Appelez cet endpoint
    - Mappez → colonnes: competitor_name, competitor_product_category
    """

    try:
        agent = CompetitorFinderAgent(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini"
        )

        input_data = CompetitorFinderInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            product_category=product_category,
            website_content=""
        )

        result = agent.run(input_data)

        return ClayAgentResponse(
            success=True,
            data={
                "competitor_name": result.competitor_name,
                "competitor_product_category": result.competitor_product_category
            },
            fallback_level=result.fallback_level,
            confidence_score=result.confidence_score,
            reasoning=result.reasoning
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/identify-pain", response_model=ClayAgentResponse)
async def identify_pain(
    contact: ClayContactInput,
    target_persona: str,
    product_category: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Agent 3: Identifie le pain point.

    Dans Clay:
    - Prerequis: target_persona, product_category
    - Appelez cet endpoint
    - Mappez → colonnes: problem_specific, impact_measurable
    """

    try:
        agent = PainPointAgent(
            api_key=os.getenv("OPENAI_API_KEY"),
            model="gpt-4o-mini"
        )

        input_data = PainPointInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            target_persona=target_persona,
            product_category=product_category,
            website_content=""
        )

        result = agent.run(input_data)

        return ClayAgentResponse(
            success=True,
            data={
                "problem_specific": result.problem_specific,
                "impact_measurable": result.impact_measurable
            },
            fallback_level=result.fallback_level,
            confidence_score=result.confidence_score,
            reasoning=result.reasoning
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Health check
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "openai_key_configured": bool(os.getenv("OPENAI_API_KEY")),
        "api_key_configured": bool(os.getenv("API_KEY"))
    }


@app.get("/")
async def root():
    """Root endpoint avec documentation."""
    return {
        "message": "Clay-Compatible Email Generation API",
        "version": "1.0.0",
        "endpoints": {
            "generate_email": "POST /api/generate-email (email complet)",
            "extract_persona": "POST /api/extract-persona (agent 1)",
            "find_competitor": "POST /api/find-competitor (agent 2)",
            "identify_pain": "POST /api/identify-pain (agent 3)",
            "health": "GET /health"
        },
        "docs": "/docs (Swagger UI)",
        "redoc": "/redoc (ReDoc)"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000))
    )
