"""
V2 API - Generic, Client-Agnostic Endpoints.

This is the "Lego" API where:
- Client context is passed in the request (not hardcoded)
- Same endpoints serve all clients
- No code changes needed for new clients
- Perfect for n8n integration

Mounted at /v2 on main API. Endpoints:
- POST /v2/email/write - Write a personalized email
- POST /v2/email/write-sequence - Generate 4-email sequence
- POST /v2/enrich - Enrich prospect data
- POST /v2/qualify - Qualify a prospect
- POST /v2/pipeline - Full pipeline (enrich → qualify → email)
- GET /v2/clients/{client_id} - Load client context from Supabase
- GET /v2/templates/{client_id} - Load email templates
- GET /v2/campaigns/{client_id} - Get SmartLead campaign mapping
"""

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import time

from src.api.v2.schemas import (
    EmailWriteRequest,
    EmailWriteResponse,
    EnrichmentRequest,
    EnrichmentResponse,
    EnrichmentSource,
    QualificationRequest,
    QualificationResponse,
    PipelineRequest,
    PipelineResponse,
    ClientContext,
    EmailTemplate,
    ProspectData,
    # V2 Sequence schemas
    EmailTemplateDB,
    EmailSequenceRequest,
    EmailSequenceResponse,
    GeneratedEmail,
    ClientFromDB,
    CampaignMapping,
    CaseStudy
)
from src.agents.generic.email_writer_v2 import EmailWriterV2
from src.enrichers import enricher_factory
import os


# ============================================
# FastAPI App
# ============================================

app = FastAPI(
    title="Kaleads Atomic Agents V2 API",
    description="Generic, client-agnostic API for cold email campaigns. Pass client context at runtime.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# Lazy-initialized writers
# ============================================

_email_writer: Optional[EmailWriterV2] = None
_supabase_client = None


def get_email_writer() -> EmailWriterV2:
    """Get or create email writer instance."""
    global _email_writer
    if _email_writer is None:
        _email_writer = EmailWriterV2()
    return _email_writer


def get_supabase():
    """Get or create Supabase client."""
    global _supabase_client
    if _supabase_client is None:
        try:
            from supabase import create_client, Client
            url = os.getenv("SUPABASE_URL", "https://ckrspaktqohjenqfuuzl.supabase.co")
            key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_KEY")
            if not key:
                raise ValueError("SUPABASE_SERVICE_ROLE_KEY not configured")
            _supabase_client = create_client(url, key)
        except ImportError:
            raise HTTPException(
                status_code=500,
                detail="Supabase client not installed. Run: pip install supabase"
            )
    return _supabase_client


# ============================================
# Health Check
# ============================================

@app.get("/")
async def root():
    """API health check."""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "architecture": "client-agnostic",
        "endpoints": [
            "/email/write",
            "/email/write-sequence",
            "/enrich",
            "/qualify",
            "/pipeline",
            "/clients/{client_id}",
            "/templates/{client_id}",
            "/campaigns/{client_id}"
        ],
        "enrichers_available": enricher_factory.list_sources()
    }


@app.get("/health")
async def health():
    """Detailed health check."""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "enrichers": {
            source: {
                "available": True,
                "fields": enricher_factory.get(source).get_available_fields()
            }
            for source in enricher_factory.list_sources()
        }
    }


# ============================================
# Email Writing Endpoint
# ============================================

@app.post("/email/write", response_model=EmailWriteResponse)
async def write_email(request: EmailWriteRequest):
    """
    Write a personalized cold email.

    This endpoint accepts:
    - client: Your client context (who you are)
    - template: Email template with {variables}
    - prospect: Target prospect data

    n8n Usage:
    ```
    HTTP Request Node:
      Method: POST
      URL: http://localhost:8000/v2/email/write
      Body JSON: {
        "client": {
          "name": "HUPLA",
          "offering": "Rapport bancaire unique ESG",
          "pain_solved": "Multi-bancarisation chronophage",
          "tone": "direct et professionnel",
          "required_words": ["rapport UNIQUE", "BCE"],
          "forbidden_words": ["normes ESG"],
          "case_studies": [
            {
              "company_name": "Bouygues",
              "industry": "BTP",
              "problem": "4 banques différentes",
              "result": "4 semaines gagnées par an"
            }
          ]
        },
        "template": {
          "subject": "Question sur {company_name}",
          "body": "Bonjour {first_name},\\n\\n{hook}\\n\\n{pain}\\n\\n{proof}\\n\\n{cta}",
          "instructions": "Ton direct, max 70 mots",
          "max_words": 70
        },
        "prospect": {
          "first_name": "Pierre",
          "company_name": "Eiffage",
          "industry": "BTP",
          "signal": "3 banques détectées"
        }
      }
    ```
    """
    try:
        writer = get_email_writer()
        result = writer.write(request)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Email generation failed: {str(e)}")


# ============================================
# Enrichment Endpoint
# ============================================

@app.post("/enrich", response_model=EnrichmentResponse)
async def enrich_prospect(request: EnrichmentRequest):
    """
    Enrich prospect/company data from external sources.

    Available sources:
    - pappers: French company registry (SIREN, CEO, revenue, etc.)
    - google: Web search (news, funding, description)

    n8n Usage:
    ```
    HTTP Request Node:
      Method: POST
      URL: http://localhost:8000/v2/enrich
      Body JSON: {
        "company_name": "Eiffage Construction",
        "source": "pappers",
        "fields_to_fetch": ["ceo_name", "effectif", "chiffre_affaires"]
      }
    ```
    """
    try:
        enricher = enricher_factory.get(request.source.value)
        if not enricher:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown enrichment source: {request.source}"
            )

        result = enricher.enrich(
            company_name=request.company_name,
            fields=request.fields_to_fetch
        )

        return EnrichmentResponse(
            company_name=request.company_name,
            source=request.source.value,
            data=result.data,
            success=result.success,
            error=result.error,
            processing_time_ms=result.processing_time_ms
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enrichment failed: {str(e)}")


# ============================================
# Qualification Endpoint
# ============================================

@app.post("/qualify", response_model=QualificationResponse)
async def qualify_prospect(request: QualificationRequest):
    """
    Qualify a prospect based on client criteria.

    Uses client.ideal_industries and client.min_employee_count
    to determine if prospect is a good fit.

    n8n Usage:
    ```
    HTTP Request Node:
      Method: POST
      URL: http://localhost:8000/v2/qualify
      Body JSON: {
        "client": {
          "name": "HUPLA",
          "offering": "...",
          "pain_solved": "...",
          "ideal_industries": ["BTP", "Construction", "Transport"],
          "min_employee_count": 50
        },
        "prospect": {
          "company_name": "Eiffage",
          "industry": "BTP",
          "company_size": "5000+"
        }
      }
    ```
    """
    start_time = time.time()

    try:
        score = 0.0
        reasons = []
        disqualification_reasons = []

        # Industry match
        if request.client.ideal_industries:
            if request.prospect.industry:
                industry_lower = request.prospect.industry.lower()
                for ideal in request.client.ideal_industries:
                    if ideal.lower() in industry_lower or industry_lower in ideal.lower():
                        score += 40
                        reasons.append(f"Industry match: {request.prospect.industry}")
                        break
                else:
                    disqualification_reasons.append(
                        f"Industry '{request.prospect.industry}' not in ideal list"
                    )
            else:
                score += 20  # Unknown industry, partial score
                reasons.append("Industry unknown, assuming potential fit")

        # Company size check
        if request.client.min_employee_count:
            size_str = request.prospect.company_size or ""
            # Try to extract number from size string
            import re
            numbers = re.findall(r'\d+', size_str.replace(",", "").replace(" ", ""))
            if numbers:
                max_size = max(int(n) for n in numbers)
                if max_size >= request.client.min_employee_count:
                    score += 30
                    reasons.append(f"Company size ({size_str}) meets minimum")
                else:
                    disqualification_reasons.append(
                        f"Company size ({size_str}) below minimum ({request.client.min_employee_count})"
                    )
            else:
                score += 15  # Unknown size, partial score
                reasons.append("Company size unknown")

        # Has signal/trigger
        if request.prospect.signal:
            score += 30
            reasons.append(f"Has trigger signal: {request.prospect.signal[:50]}...")

        # Clamp score
        score = min(100, max(0, score))
        qualified = score >= 50 and len(disqualification_reasons) == 0

        processing_time = int((time.time() - start_time) * 1000)

        return QualificationResponse(
            qualified=qualified,
            score=score,
            reasons=reasons,
            disqualification_reasons=disqualification_reasons,
            processing_time_ms=processing_time
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Qualification failed: {str(e)}")


# ============================================
# Full Pipeline Endpoint
# ============================================

@app.post("/pipeline", response_model=PipelineResponse)
async def run_pipeline(request: PipelineRequest):
    """
    Run full pipeline: Enrich → Qualify → Write Email.

    This is the most complete endpoint that:
    1. Enriches prospect data from specified sources
    2. Qualifies the prospect
    3. Generates a personalized email

    n8n Usage:
    ```
    HTTP Request Node:
      Method: POST
      URL: http://localhost:8000/v2/pipeline
      Body JSON: {
        "client": { ... },
        "template": { ... },
        "prospect": {
          "company_name": "Eiffage",
          "first_name": "Pierre"
        },
        "enrichment_sources": ["pappers"],
        "skip_qualification": false
      }
    ```
    """
    start_time = time.time()
    total_cost = 0.0
    errors = []

    # Start with original prospect data
    enriched_prospect = request.prospect.model_copy(deep=True)

    # Step 1: Enrichment (optional)
    if request.enrichment_sources:
        for source in request.enrichment_sources:
            try:
                enricher = enricher_factory.get(source.value)
                if enricher:
                    result = enricher.enrich(request.prospect.company_name)
                    if result.success:
                        # Merge enriched data into custom_vars
                        enriched_prospect.custom_vars.update(result.data)
                        # Update standard fields if found
                        if result.data.get("ceo_name") and not enriched_prospect.first_name:
                            enriched_prospect.first_name = result.data["ceo_name"].split()[0]
            except Exception as e:
                errors.append(f"Enrichment ({source.value}) failed: {str(e)}")

    # Step 2: Qualification (optional)
    qualification_result = None
    if not request.skip_qualification:
        try:
            qual_request = QualificationRequest(
                client=request.client,
                prospect=enriched_prospect
            )
            qualification_result = await qualify_prospect(qual_request)

            # Stop pipeline if not qualified
            if not qualification_result.qualified:
                return PipelineResponse(
                    prospect_enriched=enriched_prospect,
                    qualification=qualification_result,
                    email=None,
                    pipeline_success=False,
                    total_processing_time_ms=int((time.time() - start_time) * 1000),
                    total_cost_usd=total_cost,
                    errors=["Prospect not qualified"] + errors
                )
        except Exception as e:
            errors.append(f"Qualification failed: {str(e)}")

    # Step 3: Email Generation
    email_result = None
    try:
        email_request = EmailWriteRequest(
            client=request.client,
            template=request.template,
            prospect=enriched_prospect
        )
        email_result = await write_email(email_request)
        total_cost += email_result.cost_usd
    except Exception as e:
        errors.append(f"Email generation failed: {str(e)}")

    total_time = int((time.time() - start_time) * 1000)

    return PipelineResponse(
        prospect_enriched=enriched_prospect,
        qualification=qualification_result,
        email=email_result,
        pipeline_success=email_result is not None and len(errors) == 0,
        total_processing_time_ms=total_time,
        total_cost_usd=total_cost,
        errors=errors
    )


# ============================================
# V2 Endpoints - Supabase Integration
# ============================================

@app.get("/clients/{client_id}", response_model=ClientFromDB)
async def get_client(client_id: str):
    """
    Get client context from Supabase.

    n8n Usage:
    ```
    HTTP Request Node:
      Method: GET
      URL: http://localhost:8001/v2/clients/hupla
    ```

    Returns the full client configuration including:
    - Client name and offering
    - Email templates (JSONB)
    - Case studies
    - Qualification criteria
    """
    try:
        supabase = get_supabase()

        # Query clients table
        result = supabase.table("clients").select("*").eq("client_name", client_id).execute()

        if not result.data or len(result.data) == 0:
            # Try with client_id field if it exists
            result = supabase.table("clients").select("*").eq("client_id", client_id).execute()

        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail=f"Client '{client_id}' not found")

        client_data = result.data[0]
        return ClientFromDB(**client_data)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch client: {str(e)}")


@app.get("/templates/{client_id}", response_model=List[EmailTemplateDB])
async def get_templates(
    client_id: str,
    signal_type: Optional[str] = None,
    sequence: bool = True
):
    """
    Get email templates for a client from Supabase.

    Args:
        client_id: Client identifier
        signal_type: Optional signal to filter templates (e.g., 'MULTI_BANQUE')
        sequence: If True, returns all 4 emails in sequence

    n8n Usage:
    ```
    HTTP Request Node:
      Method: GET
      URL: http://localhost:8001/v2/templates/hupla?signal_type=MULTI_BANQUE&sequence=true
    ```
    """
    try:
        supabase = get_supabase()

        # Build query
        query = supabase.table("email_templates").select("*").eq("client_id", client_id).eq("active", True)

        if signal_type:
            # Get templates matching signal OR default (NULL signal)
            query = query.or_(f"signal_type.eq.{signal_type},signal_type.is.null")

        if sequence:
            query = query.order("sequence_position", desc=False)

        result = query.execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"No templates found for client '{client_id}'"
            )

        # Sort by specificity (signal match first, then default)
        templates = sorted(
            result.data,
            key=lambda t: (
                0 if t.get("signal_type") == signal_type else 1,
                t.get("sequence_position", 1)
            )
        )

        # If we have templates for the specific signal, filter out defaults
        if signal_type and any(t.get("signal_type") == signal_type for t in templates):
            templates = [t for t in templates if t.get("signal_type") == signal_type]

        return [EmailTemplateDB(**t) for t in templates]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch templates: {str(e)}")


@app.get("/campaigns/{client_id}", response_model=CampaignMapping)
async def get_campaign_mapping(
    client_id: str,
    signal_type: Optional[str] = None
):
    """
    Get SmartLead campaign mapping for a client/signal.

    n8n Usage:
    ```
    HTTP Request Node:
      Method: GET
      URL: http://localhost:8001/v2/campaigns/hupla?signal_type=MULTI_BANQUE
    ```
    """
    try:
        supabase = get_supabase()

        # Build query
        query = supabase.table("campaign_mappings").select("*").eq("client_id", client_id).eq("active", True)

        if signal_type:
            query = query.or_(f"signal_type.eq.{signal_type},signal_type.is.null")
        else:
            query = query.is_("signal_type", "null")

        result = query.order("priority", desc=True).limit(1).execute()

        if not result.data:
            raise HTTPException(
                status_code=404,
                detail=f"No campaign mapping found for client '{client_id}'"
            )

        return CampaignMapping(**result.data[0])

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch campaign: {str(e)}")


@app.post("/email/write-sequence", response_model=EmailSequenceResponse)
async def write_email_sequence(request: EmailSequenceRequest):
    """
    Generate a complete email sequence (4 emails).

    This endpoint generates all emails in a sequence:
    1. Initial email (personalized with signal)
    2. Follow-up 1 (value-add)
    3. Follow-up 2 (case study)
    4. Break-up email

    Returns SmartLead-ready custom fields for direct push.

    n8n Usage:
    ```
    HTTP Request Node:
      Method: POST
      URL: http://localhost:8001/v2/email/write-sequence
      Body JSON: {
        "client": { ... },
        "templates": [ ... 4 templates ... ],
        "prospect": { ... }
      }
    ```
    """
    start_time = time.time()
    total_cost = 0.0
    generated_emails = []

    try:
        writer = get_email_writer()

        for template_db in sorted(request.templates, key=lambda t: t.sequence_position):
            email_start = time.time()

            # Convert DB template to API template
            template = EmailTemplate(
                subject=template_db.subject,
                body=template_db.body,
                instructions=template_db.instructions or "Ton direct et professionnel.",
                max_words=template_db.max_words,
                example_output=template_db.example_output
            )

            # Generate email
            email_request = EmailWriteRequest(
                client=request.client,
                template=template,
                prospect=request.prospect
            )

            result = writer.write(email_request)
            total_cost += result.cost_usd

            email_time = int((time.time() - email_start) * 1000)

            generated_emails.append(GeneratedEmail(
                sequence_position=template_db.sequence_position,
                delay_days=template_db.delay_days,
                subject=result.subject,
                body=result.body,
                word_count=result.word_count,
                quality_score=result.quality_score,
                processing_time_ms=email_time
            ))

        # Calculate totals
        total_time = int((time.time() - start_time) * 1000)
        total_words = sum(e.word_count for e in generated_emails)
        avg_quality = sum(e.quality_score for e in generated_emails) / len(generated_emails)

        # Build SmartLead custom fields
        smartlead_fields = {}
        for email in generated_emails:
            pos = email.sequence_position
            smartlead_fields[f"email_subject_{pos}"] = email.subject
            smartlead_fields[f"email_body_{pos}"] = email.body

        return EmailSequenceResponse(
            emails=generated_emails,
            total_emails=len(generated_emails),
            total_word_count=total_words,
            average_quality_score=round(avg_quality, 2),
            total_processing_time_ms=total_time,
            total_cost_usd=round(total_cost, 6),
            model_used="gpt-4o-mini",
            smartlead_custom_fields=smartlead_fields
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sequence generation failed: {str(e)}")


# ============================================
# Run Server
# ============================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
