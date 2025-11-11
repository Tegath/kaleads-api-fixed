"""
API FastAPI principale pour le système de génération de campagnes emails.

Endpoints:
- POST /campaigns/generate : Génère une campagne complète
- GET /campaigns/{job_id} : Récupère le statut d'un job
- GET /health : Health check
"""

from fastapi import FastAPI, HTTPException, Header, BackgroundTasks, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn
import uuid
import time
import os
from dotenv import load_dotenv

from src.schemas import CampaignRequest, CampaignResult
from src.orchestrator import CampaignOrchestrator

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="Kaleads Atomic Agents API",
    description="API pour générer des campagnes d'emails ultra-personnalisés via Atomic Agents",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production: limiter aux domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key pour sécuriser l'accès
API_KEY = os.getenv("API_KEY", "your-secure-api-key")

# Storage pour les jobs (en production: utiliser Redis ou DB)
jobs_storage = {}


# ============================================
# Security: API Key Validation
# ============================================

def verify_api_key(x_api_key: Optional[str] = Header(None)):
    """Vérifie que la clé API est valide"""
    if x_api_key != API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid API Key"
        )
    return x_api_key


# ============================================
# Routes
# ============================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0"
    }


@app.post("/campaigns/generate", dependencies=[Depends(verify_api_key)])
async def generate_campaign(
    request: CampaignRequest,
    background_tasks: BackgroundTasks
):
    """
    Génère une campagne d'emails complète.

    Flow:
    1. Crée un job_id
    2. Lance la génération en arrière-plan
    3. Retourne immédiatement le job_id
    4. Client peut poll /campaigns/{job_id} pour récupérer le résultat

    Args:
        request: CampaignRequest avec template, contacts, context

    Returns:
        {
            "job_id": "uuid",
            "status": "processing",
            "message": "Campaign generation started"
        }
    """
    # Génère un job_id unique
    job_id = request.batch_id or str(uuid.uuid4())

    # Initialise le job dans le storage
    jobs_storage[job_id] = {
        "job_id": job_id,
        "status": "processing",
        "created_at": time.time(),
        "result": None,
        "error": None
    }

    # Lance la génération en arrière-plan
    background_tasks.add_task(process_campaign, job_id, request)

    return {
        "job_id": job_id,
        "status": "processing",
        "message": f"Campaign generation started for {len(request.contacts)} contacts",
        "poll_url": f"/campaigns/{job_id}"
    }


@app.get("/campaigns/{job_id}")
async def get_campaign_status(job_id: str):
    """
    Récupère le statut et résultat d'un job de campagne.

    Returns:
        {
            "job_id": "uuid",
            "status": "processing" | "completed" | "failed",
            "result": CampaignResult (si completed),
            "error": str (si failed)
        }
    """
    if job_id not in jobs_storage:
        raise HTTPException(status_code=404, detail="Job not found")

    job = jobs_storage[job_id]

    return {
        "job_id": job["job_id"],
        "status": job["status"],
        "created_at": job["created_at"],
        "result": job["result"],
        "error": job["error"]
    }


@app.delete("/campaigns/{job_id}", dependencies=[Depends(verify_api_key)])
async def delete_campaign_job(job_id: str):
    """Supprime un job du storage (cleanup)"""
    if job_id in jobs_storage:
        del jobs_storage[job_id]
        return {"message": f"Job {job_id} deleted"}
    else:
        raise HTTPException(status_code=404, detail="Job not found")


# ============================================
# Background Task: Campaign Processing
# ============================================

async def process_campaign(job_id: str, request: CampaignRequest):
    """
    Traite une campagne en arrière-plan.

    Cette fonction:
    1. Initialise l'orchestrateur
    2. Charge les Context Providers
    3. Exécute la génération
    4. Update le job storage avec le résultat
    """
    try:
        print(f"[{job_id}] Starting campaign generation for {len(request.contacts)} contacts...")

        # Récupérer les chemins des fichiers de contexte depuis l'env
        data_dir = os.getenv("DATA_DIR", "./data")
        client_name = request.context.get("client_name", "example-client")

        context_paths = {
            "pci": os.path.join(data_dir, "clients", client_name, "pci.md"),
            "personas": os.path.join(data_dir, "clients", client_name, "personas.md"),
            "pain_points": os.path.join(data_dir, "clients", client_name, "pain_points.md"),
            "competitors": os.path.join(data_dir, "clients", client_name, "competitors.md"),
            "case_studies": os.path.join(data_dir, "clients", client_name, "case_studies.md")
        }

        # Initialiser l'orchestrateur
        orchestrator = CampaignOrchestrator(
            openai_api_key=os.getenv("OPENAI_API_KEY"),
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            enable_cache=request.enable_cache,
            context_paths=context_paths
        )

        # Exécuter la génération
        result = orchestrator.run(request)

        # Convert Pydantic model to dict for JSON serialization
        result_dict = result.model_dump()

        # Update job storage
        jobs_storage[job_id]["status"] = "completed"
        jobs_storage[job_id]["result"] = result_dict
        jobs_storage[job_id]["completed_at"] = time.time()

        print(f"[{job_id}] ✅ Campaign generation completed!")
        print(f"[{job_id}] Success rate: {result.success_rate*100:.1f}%")
        print(f"[{job_id}] Average quality: {result.average_quality_score:.1f}/100")

    except Exception as e:
        print(f"[{job_id}] ❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        jobs_storage[job_id]["status"] = "failed"
        jobs_storage[job_id]["error"] = str(e)
        jobs_storage[job_id]["completed_at"] = time.time()


# ============================================
# Startup & Shutdown Events
# ============================================

@app.on_event("startup")
async def startup_event():
    """Actions à effectuer au démarrage"""
    print("🚀 Kaleads Atomic Agents API starting...")
    print(f"📁 Data directory: {os.getenv('DATA_DIR', './data')}")
    print(f"🔐 API secured with API Key")
    print(f"📊 Cache enabled: {os.getenv('ENABLE_CACHE', 'true')}")


@app.on_event("shutdown")
async def shutdown_event():
    """Actions à effectuer à l'arrêt"""
    print("👋 Kaleads Atomic Agents API shutting down...")


# ============================================
# Run Server (Development)
# ============================================

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", 8000)),
        reload=True,
        log_level="info"
    )
