"""
Optimized n8n-compatible API with cost savings.

Cost optimizations:
- OpenRouter with cheap models (DeepSeek, Gemini Flash, GPT-4o-mini)
- Batch processing (50% cost reduction)
- Smart scraping (90% token reduction)
- PCI filtering (avoid generating emails for bad leads)
- Supabase context loading

Target: $0.0005 per email (vs $0.0012 current) = 58% savings
Generation time: <30 seconds
"""

import os
import asyncio
from typing import Optional, List, Dict, Any
from fastapi import FastAPI, HTTPException, Header, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from src.agents.v3 import (
    PersonaExtractorV3,
    CompetitorFinderV3,
    PainPointAnalyzerV3,
    SignalDetectorV3,
    SystemMapperV3,
    ProofGeneratorV3,
)
from src.agents.v3.persona_extractor_v3 import PersonaExtractorInputSchema, PersonaExtractorOutputSchema
from src.agents.v3.competitor_finder_v3 import CompetitorFinderInputSchema, CompetitorFinderOutputSchema
from src.agents.v3.pain_point_analyzer_v3 import PainPointAnalyzerInputSchema, PainPointAnalyzerOutputSchema
from src.agents.v3.signal_detector_v3 import SignalDetectorInputSchema, SignalDetectorOutputSchema
from src.agents.v3.system_mapper_v3 import SystemMapperInputSchema, SystemMapperOutputSchema
from src.agents.v3.proof_generator_v3 import ProofGeneratorInputSchema, ProofGeneratorOutputSchema

from src.agents.validator_agent import (
    EmailValidatorAgent,
    EmailValidationInputSchema,
)
from src.agents.pci_agent import PCIFilterAgent, batch_filter_contacts
from src.providers.supabase_client import SupabaseClient
from src.models.client_context import ClientContext

app = FastAPI(
    title="n8n Email Generation API v3.0",
    description="Context-aware multi-agent email generation with v3 agents (Tavily web search + ClientContext)",
    version="3.0.0"
)

# Feedback loop configuration
MAX_RETRIES = 3  # Maximum number of generation attempts
QUALITY_THRESHOLD = 95  # Minimum quality score to accept (0-100)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory batch storage (replace with Redis in production)
BATCH_JOBS: Dict[str, Dict[str, Any]] = {}


# ============================================
# Authentication
# ============================================

def verify_api_key(x_api_key: str = Header(...)):
    """Verify API key."""
    expected_key = os.getenv("API_KEY", "your-secure-api-key")
    if x_api_key != expected_key:
        raise HTTPException(status_code=401, detail="Invalid API Key")
    return x_api_key


# ============================================
# Schemas
# ============================================

class ContactInput(BaseModel):
    """Contact information for email generation."""
    company_name: str
    first_name: str
    last_name: Optional[str] = ""
    email: Optional[str] = ""
    website: str
    industry: Optional[str] = ""
    employees: Optional[int] = None
    revenue: Optional[float] = None
    region: Optional[str] = ""


class GenerateEmailRequest(BaseModel):
    """Request for generating a single email."""
    client_id: str = Field(..., description="Client UUID for loading context from Supabase")
    contact: ContactInput
    template_content: Optional[str] = Field(
        None,
        description="Email template with {{variables}}. Use \\n for line breaks. Example: 'Bonjour {{first_name}},\\n\\nJ\\'ai vu que {{company_name}}...'"
    )
    template_id: Optional[str] = Field(None, description="Template ID from Supabase (alternative to template_content)")

    # NEW: Inline instructions and example
    email_instructions: Optional[str] = Field(
        None,
        description="Instructions sur le ton/style de l'email (ex: 'Ton conversational, court (<100 mots), corriger tous les espaces/majuscules')"
    )
    example_email: Optional[str] = Field(
        None,
        description="Un exemple parfait d'email à imiter pour apprendre le ton/style"
    )

    options: Dict[str, Any] = Field(
        default_factory=lambda: {
            "model_preference": "balanced",  # cheap|balanced|quality (balanced par défaut pour meilleure qualité)
            "enable_scraping": True,
            "enable_pci_filter": True
        }
    )


class GenerateEmailResponse(BaseModel):
    """Response with generated email."""
    success: bool
    email_content: str
    cost_usd: float
    generation_time_seconds: float
    model_used: str

    # Variables
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

    # Metadata
    pci_filtered: bool = False
    quality_score: int
    fallback_levels: Dict[str, int]

    # Validation metadata (new in v2.1)
    validation_passed: Optional[bool] = None
    validation_issues: Optional[List[str]] = None
    attempts: int = 1
    validation_attempts: List[Dict[str, Any]] = []
    validation_error: Optional[str] = None


class PCIFilterRequest(BaseModel):
    """Request for PCI filtering."""
    client_id: str
    contacts: List[ContactInput]


class PCIFilterResponse(BaseModel):
    """Response from PCI filtering."""
    matches: List[Dict[str, Any]]
    filtered_out: List[Dict[str, Any]]
    cost_usd: float
    processing_time_seconds: float


class BatchRequest(BaseModel):
    """Request for batch processing."""
    client_id: str
    contacts: List[ContactInput]
    template_content: Optional[str] = Field(None, description="Email template with {{variables}}")
    batch_size: int = Field(20, description="Process N contacts at a time")
    webhook_url: Optional[str] = Field(None, description="Webhook to call when complete")
    options: Dict[str, Any] = Field(default_factory=dict)


class BatchResponse(BaseModel):
    """Response for batch job creation."""
    batch_id: str
    status: str  # "queued", "processing", "completed", "failed"
    total_contacts: int
    estimated_time_seconds: int
    webhook_url: Optional[str] = None


class BatchStatusResponse(BaseModel):
    """Response for batch status check."""
    batch_id: str
    status: str
    processed_count: int
    total_count: int
    success_count: int
    error_count: int
    cost_usd: float
    results: Optional[List[Dict[str, Any]]] = None


# ============================================
# Helper Functions
# ============================================

def estimate_cost(model_preference: str, num_contacts: int = 1) -> float:
    """
    Estimate cost based on model preference.

    Args:
        model_preference: "cheap", "balanced", or "quality"
        num_contacts: Number of contacts

    Returns:
        Estimated cost in USD
    """
    cost_per_email = {
        "cheap": 0.0005,      # DeepSeek + Gemini Flash
        "balanced": 0.0010,   # Mix of cheap + GPT-4o-mini
        "quality": 0.0030     # GPT-4o-mini + Claude Sonnet
    }

    return cost_per_email.get(model_preference, 0.0010) * num_contacts


def render_template(template: str, variables: Dict[str, Any]) -> str:
    """
    Replace {{variables}} in template with actual values.

    Args:
        template: Template string with {{variable_name}}
        variables: Dict mapping variable names to values

    Returns:
        Rendered template

    Example:
        >>> template = "Bonjour {{first_name}},\\n\\nJ'ai vu {{company_name}}..."
        >>> variables = {"first_name": "Sophie", "company_name": "Aircall"}
        >>> render_template(template, variables)
        "Bonjour Sophie,\n\nJ'ai vu Aircall..."
    """
    rendered = template

    for key, value in variables.items():
        placeholder = f"{{{{{key}}}}}"  # {{key}}
        rendered = rendered.replace(placeholder, str(value))

    return rendered


async def generate_email_with_agents(
    contact: ContactInput,
    client_id: str,
    template_content: Optional[str] = None,
    enable_scraping: bool = True,
    model_preference: str = "cheap",
    email_instructions: Optional[str] = None,
    example_email: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate email using optimized agents.

    Args:
        contact: Contact information
        client_id: Client UUID
        template_content: Custom email template with {{variables}} (optional)
        enable_scraping: Enable website scraping
        model_preference: Model preference (cheap/balanced/quality)

    Returns:
        Dict with email and variables
    """
    start_time = datetime.now()

    # LOAD CLIENT CONTEXT V3
    supabase_client = SupabaseClient()
    client_context = supabase_client.load_client_context_v3(client_id)

    # V3: Initialize agents with ClientContext (much simpler!)
    # All v3 agents accept ClientContext and automatically adapt
    persona_agent = PersonaExtractorV3(
        enable_scraping=enable_scraping,
        enable_tavily=True,
        client_context=client_context
    )
    competitor_agent = CompetitorFinderV3(
        enable_scraping=enable_scraping,
        enable_tavily=True,
        client_context=client_context
    )
    pain_agent = PainPointAnalyzerV3(
        enable_scraping=enable_scraping,
        enable_tavily=True,
        client_context=client_context
    )
    signal_agent = SignalDetectorV3(
        enable_scraping=enable_scraping,
        enable_tavily=True,
        client_context=client_context
    )
    system_agent = SystemMapperV3(
        enable_scraping=enable_scraping,
        enable_tavily=True,
        client_context=client_context
    )
    proof_agent = ProofGeneratorV3(
        enable_scraping=enable_scraping,
        enable_tavily=True,
        client_context=client_context
    )

    # V3 Agent 1: Persona
    persona_result = persona_agent.run(
        PersonaExtractorInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            website_content=""
        )
    )

    # V3 Agent 2: Competitor
    competitor_result = competitor_agent.run(
        CompetitorFinderInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            product_category=f"{persona_result.role} in {persona_result.department}",  # Infer from persona
            website_content=""
        )
    )

    # V3 Agent 3: Pain Point (automatically adapts to client type!)
    pain_result = pain_agent.run(
        PainPointAnalyzerInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            website_content=""
        )
    )

    # V3 Agent 4: Signals
    signal_result = signal_agent.run(
        SignalDetectorInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            website_content=""
        )
    )

    # V3 Agent 5: Tech Stack
    system_result = system_agent.run(
        SystemMapperInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            product_category=f"{persona_result.role} tools",
            website_content=""
        )
    )

    # V3 Agent 6: Proof (renamed from CaseStudy)
    proof_result = proof_agent.run(
        ProofGeneratorInputSchema(
            company_name=contact.company_name,
            website=contact.website,
            industry=contact.industry or "",
            website_content=""
        )
    )

    # Prepare all variables for template rendering
    # V3: Map new output fields to old variable names for backward compatibility
    variables = {
        # Contact info
        "first_name": contact.first_name,
        "last_name": contact.last_name,
        "company_name": contact.company_name,
        "website": contact.website,
        "industry": contact.industry or "",

        # Agent results (mapped from v3 outputs)
        "target_persona": persona_result.role,  # v3: role instead of target_persona
        "product_category": f"{persona_result.department} - {persona_result.seniority_level}",  # v3: constructed from role/department
        "competitor_name": competitor_result.competitor_name,  # Same
        "competitor_product_category": competitor_result.competitor_product_category,  # Same
        "problem_specific": pain_result.problem_specific,  # v3: problem_specific (correct field name)
        "impact_measurable": pain_result.impact_measurable,  # v3: impact_measurable (correct field name)
        "case_study_result": proof_result.case_study_result,  # v3: case_study_result (same as v2)
        "specific_signal_1": signal_result.signal_description if signal_result.signal_type != "none" else "est en phase de croissance",  # v3: signal_description
        "specific_signal_2": signal_result.relevance_to_client if signal_result.signal_type != "none" else "",  # v3: relevance
        "specific_target_1": ", ".join(persona_result.likely_pain_points[:1]) if persona_result.likely_pain_points else "",  # v3: from persona
        "specific_target_2": ", ".join(persona_result.likely_pain_points[1:2]) if len(persona_result.likely_pain_points) > 1 else "",  # v3: from persona
        "system_1": system_result.relevant_tech[0] if system_result.relevant_tech else system_result.tech_stack[0] if system_result.tech_stack else "CRM",  # v3: from tech_stack
        "system_2": system_result.relevant_tech[1] if len(system_result.relevant_tech) > 1 else system_result.tech_stack[1] if len(system_result.tech_stack) > 1 else "Email platform",
        "system_3": system_result.relevant_tech[2] if len(system_result.relevant_tech) > 2 else system_result.tech_stack[2] if len(system_result.tech_stack) > 2 else "Analytics tool",
    }

    # Build email - use custom template if provided, otherwise use default
    if template_content:
        email_content = render_template(template_content, variables)
    else:
        # V3: Default template with ClientContext
        client_name = client_context.client_name
        client_offerings_str = client_context.get_offerings_str(limit=2)  # v3: method on ClientContext

        email_content = f"""Bonjour {contact.first_name},

Je travaille chez {client_name}, spécialisé en {client_offerings_str}.

J'ai remarqué que {contact.company_name} {variables['specific_signal_1']}.

{variables['case_study_result']}

Seriez-vous ouvert(e) à un échange rapide?

Cordialement,
L'équipe {client_name}"""

    generation_time = (datetime.now() - start_time).total_seconds()

    return {
        "email_content": email_content,
        # V3: Return variables using the mapped values
        "target_persona": variables["target_persona"],
        "product_category": variables["product_category"],
        "competitor_name": variables["competitor_name"],
        "problem_specific": variables["problem_specific"],
        "impact_measurable": variables["impact_measurable"],
        "case_study_result": variables["case_study_result"],
        "specific_signal_1": variables["specific_signal_1"],
        "specific_signal_2": variables["specific_signal_2"],
        "specific_target_1": variables["specific_target_1"],
        "specific_target_2": variables["specific_target_2"],
        "system_1": variables["system_1"],
        "system_2": variables["system_2"],
        "system_3": variables["system_3"],
        "generation_time_seconds": generation_time,
        "cost_usd": estimate_cost(model_preference),
        "fallback_levels": {
            "persona": persona_result.fallback_level,
            "competitor": competitor_result.fallback_level,
            "pain": pain_result.fallback_level,
            "signal": signal_result.fallback_level,
            "system": system_result.fallback_level,
            "proof": proof_result.fallback_level  # v3: renamed from case_study
        }
    }


# ============================================
# Endpoints
# ============================================

@app.post("/api/v2/generate-email", response_model=GenerateEmailResponse)
async def generate_email(request: GenerateEmailRequest):
    """
    Generate a single email with all agents.

    Best for: n8n workflows processing 1 contact at a time.
    Cost: ~$0.0005 with cheap models.
    Time: ~20-30 seconds with scraping.
    """
    try:
        # PCI filtering (optional)
        if request.options.get("enable_pci_filter", True):
            supabase = SupabaseClient()
            pci_result = supabase.filter_by_pci(
                contact=request.contact.dict(),
                client_id=request.client_id
            )

            if not pci_result["match"]:
                # Contact doesn't match ICP - return minimal response
                return GenerateEmailResponse(
                    success=False,
                    email_content="",
                    cost_usd=0.0001,  # Just PCI filter cost
                    generation_time_seconds=0.5,
                    model_used="pci_filter",
                    pci_filtered=True,
                    quality_score=0,
                    target_persona="",
                    product_category="",
                    competitor_name="",
                    problem_specific="",
                    impact_measurable="",
                    case_study_result="",
                    specific_signal_1="",
                    specific_signal_2="",
                    specific_target_1="",
                    specific_target_2="",
                    system_1="",
                    system_2="",
                    system_3="",
                    fallback_levels={}
                )

        # Generate email with feedback loop
        model_pref = request.options.get("model_preference", "balanced")  # Default to balanced for quality
        enable_scraping = request.options.get("enable_scraping", True)
        enable_validation = request.options.get("enable_validation", True)  # New option

        # Initialize validator
        validator = EmailValidatorAgent() if enable_validation else None

        best_result = None
        best_quality_score = 0
        validation_attempts = []

        for attempt in range(1, MAX_RETRIES + 1):
            # Generate email
            result = await generate_email_with_agents(
                contact=request.contact,
                client_id=request.client_id,
                template_content=request.template_content,
                enable_scraping=enable_scraping,
                model_preference=model_pref
            )

            # Validate if enabled
            if validator:
                try:
                    # Load client context for validation (v3)
                    supabase_client = SupabaseClient()
                    client_context = supabase_client.load_client_context_v3(request.client_id)
                    client_offerings_str = client_context.get_offerings_str(limit=2)

                    # NEW: Scrape prospect website for validation (to detect hallucinations)
                    scraped_content_for_validation = ""
                    if enable_scraping and request.contact.website:
                        try:
                            from src.services.crawl4ai_service import scrape_for_agent_sync, preprocess_scraped_content
                            scraped = scrape_for_agent_sync("validation", request.contact.website)
                            # Combine relevant pages for validation
                            content_parts = [
                                scraped.get("/", ""),
                                scraped.get("/blog", ""),
                                scraped.get("/news", ""),
                                scraped.get("/actualites", ""),
                                scraped.get("/press", ""),
                                scraped.get("/careers", ""),
                                scraped.get("/about", ""),
                            ]
                            combined = "\n\n".join([c for c in content_parts if c])
                            scraped_content_for_validation = preprocess_scraped_content(combined, max_tokens=8000)
                        except Exception as e:
                            # If scraping fails, continue without it
                            scraped_content_for_validation = ""

                    # Validate
                    validation = validator.run(EmailValidationInputSchema(
                        email_content=result["email_content"],
                        contact_company=request.contact.company_name,
                        client_name=client_context.client_name,
                        client_offering=client_offerings_str,
                        scraped_content=scraped_content_for_validation,  # NOW PASSING REAL CONTENT
                        email_instructions=request.email_instructions or "",  # NEW: Pass instructions
                        example_email=request.example_email or ""  # NEW: Pass example
                    ))

                    # USE CORRECTED EMAIL (auto-fix from validator)
                    result["email_content"] = validation.corrected_email

                    quality_score = validation.quality_score
                    validation_attempts.append({
                        "attempt": attempt,
                        "quality_score": quality_score,
                        "issues": validation.issues,
                        "suggestions": validation.suggestions
                    })

                    # Track best result
                    if quality_score > best_quality_score:
                        best_quality_score = quality_score
                        best_result = result
                        best_result["quality_score"] = quality_score
                        best_result["validation_passed"] = validation.is_valid
                        best_result["validation_issues"] = validation.issues

                    # If quality is good enough, stop trying
                    if quality_score >= QUALITY_THRESHOLD:
                        best_result["attempts"] = attempt
                        best_result["validation_attempts"] = validation_attempts
                        break

                except Exception as e:
                    # If validation fails, use fallback quality score
                    avg_fallback = sum(result["fallback_levels"].values()) / len(result["fallback_levels"])
                    quality_score = max(0, min(100, int(100 - (avg_fallback * 15))))
                    result["quality_score"] = quality_score
                    result["validation_error"] = str(e)
                    best_result = result
                    break
            else:
                # No validation, use fallback quality score
                avg_fallback = sum(result["fallback_levels"].values()) / len(result["fallback_levels"])
                quality_score = max(0, min(100, int(100 - (avg_fallback * 15))))
                result["quality_score"] = quality_score
                best_result = result
                break

        # Add validation metadata
        if best_result is None:
            best_result = result
            best_result["quality_score"] = 0

        best_result["attempts"] = attempt if "attempts" not in best_result else best_result["attempts"]
        best_result["validation_attempts"] = validation_attempts if validation_attempts else []

        # Extract fields that are passed explicitly to avoid duplicate keyword arguments
        quality_score = best_result.pop("quality_score", 0)
        validation_passed = best_result.pop("validation_passed", None)
        validation_issues = best_result.pop("validation_issues", None)
        attempts = best_result.pop("attempts", 1)
        validation_attempts_list = best_result.pop("validation_attempts", [])
        validation_error = best_result.pop("validation_error", None)

        return GenerateEmailResponse(
            success=True,
            quality_score=quality_score,
            model_used=model_pref,
            validation_passed=validation_passed,
            validation_issues=validation_issues,
            attempts=attempts,
            validation_attempts=validation_attempts_list,
            validation_error=validation_error,
            **best_result
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/pci-filter", response_model=PCIFilterResponse)
async def pci_filter(request: PCIFilterRequest):
    """
    Filter contacts by Profil Client Ideal.

    Best for: Pre-filtering large lists before email generation.
    Cost: ~$0.0001 per contact.
    Time: <1 second per contact.
    """
    start_time = datetime.now()

    try:
        contacts_dict = [c.dict() for c in request.contacts]
        filtered = batch_filter_contacts(contacts_dict, request.client_id)

        matches = [c for c in filtered if c["pci_result"]["match"]]
        filtered_out = [c for c in filtered if not c["pci_result"]["match"]]

        processing_time = (datetime.now() - start_time).total_seconds()
        cost = len(request.contacts) * 0.0001

        return PCIFilterResponse(
            matches=matches,
            filtered_out=filtered_out,
            cost_usd=cost,
            processing_time_seconds=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v2/batch", response_model=BatchResponse)
async def create_batch(request: BatchRequest, background_tasks: BackgroundTasks):
    """
    Create a batch job for processing multiple contacts.

    Best for: Large lists (100+ contacts) in n8n.
    Processing: Async with webhook callback.
    Cost: Same as individual, but faster processing.
    """
    batch_id = str(uuid.uuid4())

    # Store job
    BATCH_JOBS[batch_id] = {
        "status": "queued",
        "client_id": request.client_id,
        "contacts": [c.dict() for c in request.contacts],
        "template_content": request.template_content,
        "batch_size": request.batch_size,
        "webhook_url": request.webhook_url,
        "options": request.options,
        "created_at": datetime.now(),
        "results": [],
        "processed_count": 0,
        "total_count": len(request.contacts),
        "cost_usd": 0.0
    }

    # Process in background
    background_tasks.add_task(process_batch, batch_id)

    # Estimate time
    estimated_time = (len(request.contacts) // request.batch_size) * 30

    return BatchResponse(
        batch_id=batch_id,
        status="queued",
        total_contacts=len(request.contacts),
        estimated_time_seconds=estimated_time,
        webhook_url=request.webhook_url
    )


@app.get("/api/v2/batch/{batch_id}", response_model=BatchStatusResponse)
async def get_batch_status(batch_id: str):
    """Get status of a batch job."""
    if batch_id not in BATCH_JOBS:
        raise HTTPException(status_code=404, detail="Batch not found")

    job = BATCH_JOBS[batch_id]

    return BatchStatusResponse(
        batch_id=batch_id,
        status=job["status"],
        processed_count=job["processed_count"],
        total_count=job["total_count"],
        success_count=len([r for r in job["results"] if r.get("success")]),
        error_count=len([r for r in job["results"] if not r.get("success")]),
        cost_usd=job["cost_usd"],
        results=job["results"] if job["status"] == "completed" else None
    )


async def process_batch(batch_id: str):
    """Background task to process batch."""
    job = BATCH_JOBS[batch_id]
    job["status"] = "processing"

    contacts = job["contacts"]
    batch_size = job["batch_size"]
    client_id = job["client_id"]
    template_content = job.get("template_content")
    options = job["options"]

    for i in range(0, len(contacts), batch_size):
        batch = contacts[i:i + batch_size]

        for contact_dict in batch:
            try:
                contact = ContactInput(**contact_dict)
                result = await generate_email_with_agents(
                    contact=contact,
                    client_id=client_id,
                    template_content=template_content,
                    enable_scraping=options.get("enable_scraping", True),
                    model_preference=options.get("model_preference", "cheap")
                )

                result["success"] = True
                result["contact"] = contact_dict
                job["results"].append(result)
                job["cost_usd"] += result["cost_usd"]

            except Exception as e:
                job["results"].append({
                    "success": False,
                    "contact": contact_dict,
                    "error": str(e)
                })

            job["processed_count"] += 1

    job["status"] = "completed"

    # TODO: Call webhook if provided
    # if job["webhook_url"]:
    #     requests.post(job["webhook_url"], json={"batch_id": batch_id, "status": "completed"})


@app.get("/health")
async def health_check():
    """Health check."""
    return {
        "status": "healthy",
        "openrouter_key_configured": bool(os.getenv("OPENROUTER_API_KEY")),
        "supabase_configured": bool(os.getenv("SUPABASE_URL")),
        "tavily_configured": bool(os.getenv("TAVILY_API_KEY")),
        "version": "3.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "n8n Email Generation API v3.0",
        "version": "3.0.0",
        "features": [
            "Context-aware agents with ClientContext",
            "Tavily web search for real data",
            "Automatic adaptation to client type",
            "6 specialized v3 agents",
            "Email validation loop"
        ],
        "agents": [
            "PersonaExtractorV3",
            "CompetitorFinderV3",
            "PainPointAnalyzerV3",
            "SignalDetectorV3",
            "SystemMapperV3",
            "ProofGeneratorV3"
        ],
        "endpoints": {
            "generate_email": "POST /api/v2/generate-email",
            "pci_filter": "POST /api/v2/pci-filter",
            "batch": "POST /api/v2/batch",
            "batch_status": "GET /api/v2/batch/{batch_id}"
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8001))
    )
