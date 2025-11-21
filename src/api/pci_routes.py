"""
PCI Qualification API Routes
Endpoints for qualifying leads against client's Ideal Customer Profile
"""
import logging
from fastapi import APIRouter, HTTPException
from typing import Optional

from src.agents.pci_qualifier_agent import (
    PCIQualifierAgent,
    PCIQualificationRequest,
    PCIQualificationResult
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v2/pci", tags=["PCI Qualification"])


@router.post("/qualify", response_model=PCIQualificationResult)
async def qualify_lead(
    request: PCIQualificationRequest
):
    """
    Qualify a lead against client's Ideal Customer Profile (PCI).

    This endpoint:
    1. Analyzes lead information (company name, website, content)
    2. Scores the lead 0-100 based on PCI match
    3. Returns qualification stage and recommended action

    **Usage in n8n:**
    ```
    POST http://92.112.193.183:20001/api/v2/pci/qualify
    Headers:
      X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8
      Content-Type: application/json

    Body:
    {
      "company_name": "Acme Corp",
      "website": "https://acme.com",
      "website_content": "<scraped content from Jina.ai>",
      "city": "Paris",
      "rating": 4.5,
      "client_id": "kaleads"
    }
    ```

    **Response:**
    ```json
    {
      "score": 85,
      "stage": "qualified_high",
      "match": true,
      "reasons": [
        "Industry match: SaaS, Tech",
        "Tech stack detected: React, Node.js, AWS",
        "Company size: 10-50 employees"
      ],
      "recommended_action": "enrich",
      "tech_stack": ["React", "Node.js", "AWS"],
      "estimated_company_size": "10-50",
      "industry_match": true
    }
    ```

    **Stages:**
    - `qualified_high` (score >= 70): Excellent match, enrich immediately
    - `qualified_medium` (score >= 50): Good match, watch for signals
    - `qualified_low` (score >= 30): Poor match, skip for now
    - `disqualified` (score < 30): Not a good fit
    - `no_site`: No website found, cannot qualify

    **Recommended Actions:**
    - `enrich`: Qualify for enrichment (find decision makers, emails)
    - `watch`: Keep in watchlist, may enrich later
    - `skip`: Skip this lead, not a good fit

    **Example n8n Workflow:**
    1. Get leads from Supabase (stage='new', limit=50)
    2. Loop through each lead
    3. IF website exists → Scrape with Jina.ai
    4. Call this endpoint to qualify
    5. Update lead in Supabase with score/stage

    **Cost:** ~$0.001 per lead (virtually free with simple heuristics)
    """
    try:
        logger.info(f"Qualifying lead: {request.company_name}")

        # Initialize agent
        agent = PCIQualifierAgent(client_id=request.client_id)

        # Qualify
        result = agent.qualify(request)

        logger.info(f"Qualified {request.company_name}: score={result.score}, stage={result.stage}")

        return result

    except Exception as e:
        logger.error(f"Error qualifying lead {request.company_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Qualification error: {str(e)}")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "pci-qualification"}
