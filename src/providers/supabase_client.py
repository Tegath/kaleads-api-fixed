"""
Supabase client for loading client context.
"""
import os
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from datetime import datetime

class ClientPCI(BaseModel):
    """Profil Client Ideal (Ideal Customer Profile)."""
    industry: List[str] = []
    company_size_min: Optional[int] = None
    company_size_max: Optional[int] = None
    revenue_min: Optional[float] = None
    revenue_max: Optional[float] = None
    technologies: List[str] = []
    exclude_industries: List[str] = []
    geographic_regions: List[str] = []

class ClientContext(BaseModel):
    """Complete client context from Supabase."""
    client_id: str
    client_name: str
    pci: ClientPCI
    personas: List[Dict[str, Any]] = []
    competitors: List[Dict[str, Any]] = []
    case_studies: List[Dict[str, Any]] = []

class SupabaseClient:
    def __init__(self, supabase_url: Optional[str] = None, supabase_key: Optional[str] = None):
        self.supabase_url = supabase_url or os.getenv("SUPABASE_URL")
        self.supabase_key = supabase_key or os.getenv("SUPABASE_KEY")
        
        try:
            from supabase import create_client, Client
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase credentials required.")
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            self.enabled = True
        except ImportError:
            self.client = None
            self.enabled = False

    def load_client_context(self, client_id: str) -> ClientContext:
        if not self.enabled:
            return self._get_mock_context(client_id)
        
        try:
            # Query client_contexts table
            response = self.client.table("client_contexts").select("*").eq("client_id", client_id).execute()
            
            if not response.data:
                raise ValueError(f"Client {client_id} not found")
            
            data = response.data[0]
            
            # Extract from JSONB columns
            personas = data.get("personas", [])
            competitors = data.get("competitors", [])
            case_studies = data.get("reference_clients", [])
            
            # Build PCI from segments
            segments = data.get("segments", [])
            if segments:
                first_seg = segments[0]
                firm = first_seg.get("firmographics", {})
                pci = ClientPCI(
                    industry=firm.get("industries", []),
                    company_size_min=firm.get("employee_count", {}).get("min") if isinstance(firm.get("employee_count"), dict) else None,
                    company_size_max=firm.get("employee_count", {}).get("max") if isinstance(firm.get("employee_count"), dict) else None,
                    geographic_regions=firm.get("geographies", [])
                )
            else:
                pci = ClientPCI()
            
            return ClientContext(
                client_id=client_id,
                client_name=data.get("client_name", "Unknown"),
                pci=pci,
                personas=personas,
                competitors=competitors,
                case_studies=case_studies
            )
        except Exception as e:
            return self._get_mock_context(client_id)
    
    def _get_mock_context(self, client_id: str) -> ClientContext:
        return ClientContext(
            client_id=client_id,
            client_name="Mock Client",
            pci=ClientPCI(industry=["SaaS"], company_size_min=50, company_size_max=500),
            personas=[{"title": "VP Sales"}],
            competitors=[{"name": "Competitor A"}],
            case_studies=[{"result": "3x growth"}]
        )

    def filter_by_pci(self, contact: Dict[str, Any], client_id: str) -> Dict[str, Any]:
        return {"match": True, "score": 1.0, "reason": "Always match for now"}
