"""
Supabase client for loading client context.

This module provides both v2.x and v3.0 context loading methods:
- load_client_context() : Legacy v2.x format
- load_client_context_v3() : New v3.0 standardized format (recommended)
"""
import os
from typing import Optional, Dict, List, Any
from pydantic import BaseModel
from datetime import datetime

# v3.0 imports
try:
    from src.models.client_context import (
        ClientContext as ClientContextV3,
        CaseStudy,
        TemplateContext,
        TemplateExample
    )
    V3_AVAILABLE = True
except ImportError:
    V3_AVAILABLE = False

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
        self.supabase_key = supabase_key or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

        print(f"DEBUG: SupabaseClient init - URL present: {bool(self.supabase_url)}, Key present: {bool(self.supabase_key)}")

        try:
            from supabase import create_client, Client
            if not self.supabase_url or not self.supabase_key:
                print(f"DEBUG: Missing credentials - setting enabled=False")
                raise ValueError("Supabase credentials required.")
            self.client: Client = create_client(self.supabase_url, self.supabase_key)
            self.enabled = True
            print(f"DEBUG: Supabase client created successfully - enabled=True")
        except ImportError as e:
            print(f"DEBUG: Import error: {e}")
            self.client = None
            self.enabled = False
        except Exception as e:
            print(f"DEBUG: Error creating Supabase client: {e}")
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

    # ============================================
    # v3.0 Methods
    # ============================================

    def load_client_context_v3(self, client_id: str) -> "ClientContextV3":
        """
        Load client context in v3.0 standardized format.

        This method loads ALL client information from Supabase and returns
        a standardized ClientContextV3 object that agents can use.

        Args:
            client_id: UUID of the client

        Returns:
            ClientContextV3 with all client information

        Raises:
            ValueError: If V3 models not available or client not found

        Example:
            >>> supabase = SupabaseClient()
            >>> context = supabase.load_client_context_v3("kaleads-uuid")
            >>> print(context.client_name)
            "Kaleads"
            >>> print(context.get_offerings_str())
            "lead generation B2B, prospecting automation"
        """
        if not V3_AVAILABLE:
            raise ImportError(
                "v3.0 models not available. Install with: pip install -e ."
            )

        if not self.enabled:
            return self._get_mock_context_v3(client_id)

        try:
            # Step 1: Load main client data from client_contexts table
            print(f"DEBUG: Querying Supabase for client_id: {client_id}")
            response = self.client.table("client_contexts").select("*").eq("client_id", client_id).execute()
            print(f"DEBUG: Response data count: {len(response.data) if response.data else 0}")

            if not response.data or len(response.data) == 0:
                print(f"DEBUG: Client {client_id} not found in client_contexts table")
                raise ValueError(f"Client {client_id} not found in client_contexts")

            data = response.data[0]
            print(f"DEBUG: Found client: {data.get('client_name', 'Unknown')}")

            # Step 2: Extract basic info
            client_name = data.get("client_name", "Unknown Client")

            # Step 3: Extract from company_profile (PRIMARY SOURCE)
            company_profile = data.get("company_profile", {})

            # Offerings from company_profile (not from personas!)
            offerings = company_profile.get("offerings", [])

            # Pain solved from company_profile
            pain_solved = company_profile.get("pain_solved", "")

            # Target industries from company_profile
            target_industries = company_profile.get("target_industries", [])

            # Step 4: Extract personas
            personas = data.get("personas", [])

            # Step 5: Extract value proposition (if exists)
            value_proposition = company_profile.get("value_proposition", "")

            # Fallback for pain_solved if not in company_profile
            if not pain_solved:
                pain_solved = self._extract_pain_solved(data, personas)

            # Step 6: Extract ICP from segments (company sizes, regions)
            target_company_sizes = []
            target_regions = []

            segments = data.get("segments", [])
            if segments and len(segments) > 0:
                first_seg = segments[0]
                firmographics = first_seg.get("firmographics", {})

                # Industries (only if not already set from company_profile)
                if not target_industries:
                    target_industries = firmographics.get("industries", [])

                # Company sizes
                employee_count = firmographics.get("employee_count", {})
                if isinstance(employee_count, dict):
                    min_size = employee_count.get("min")
                    max_size = employee_count.get("max")
                    if min_size is not None and max_size is not None:
                        target_company_sizes.append(f"{min_size}-{max_size}")

                # Regions
                target_regions = firmographics.get("geographies", [])

            # Step 8: Load case studies (if table exists)
            real_case_studies = []
            try:
                cs_response = self.client.table("case_studies").select("*").eq("client_id", client_id).execute()
                if cs_response.data:
                    for cs_data in cs_response.data:
                        try:
                            case_study = CaseStudy(
                                company=cs_data.get("company", ""),
                                industry=cs_data.get("industry", ""),
                                result=cs_data.get("result", ""),
                                metric=cs_data.get("metric"),
                                persona=cs_data.get("persona"),
                                description=cs_data.get("description")
                            )
                            real_case_studies.append(case_study)
                        except Exception as e:
                            # Skip invalid case studies
                            print(f"Warning: Skipping invalid case study: {e}")
                            continue
            except Exception as e:
                # Table doesn't exist yet or other error
                print(f"Warning: Could not load case studies: {e}")

                # Fallback: try to use reference_clients from client_contexts
                reference_clients = data.get("reference_clients", [])
                for ref in reference_clients:
                    try:
                        case_study = CaseStudy(
                            company=ref.get("name", ref.get("company", "")),
                            industry=ref.get("industry", ""),
                            result=ref.get("result", ref.get("outcome", "")),
                            metric=ref.get("metric"),
                            persona=ref.get("persona")
                        )
                        if case_study.company and case_study.result:
                            real_case_studies.append(case_study)
                    except Exception:
                        continue

            # Step 9: Extract competitors
            competitors = []
            competitors_data = data.get("competitors", [])
            for comp in competitors_data:
                if isinstance(comp, str):
                    competitors.append(comp)
                elif isinstance(comp, dict):
                    comp_name = comp.get("name", comp.get("company", ""))
                    if comp_name:
                        competitors.append(comp_name)

            # Step 10: Load email templates (if table exists)
            email_templates = {}
            try:
                templates_response = self.client.table("email_templates").select("*").eq("client_id", client_id).eq("is_active", True).execute()
                if templates_response.data:
                    for tmpl_data in templates_response.data:
                        template_name = tmpl_data.get("template_name", "")
                        if not template_name:
                            continue

                        # Build template dict
                        template_dict = {
                            "template_content": tmpl_data.get("template_content", ""),
                            "required_variables": tmpl_data.get("required_variables", []),
                            "recommended_pipeline": tmpl_data.get("recommended_pipeline", "basic"),
                            "description": tmpl_data.get("description", "")
                        }

                        # Parse context (JSONB)
                        context_data = tmpl_data.get("context", {})
                        if context_data and isinstance(context_data, dict):
                            try:
                                template_dict["context"] = TemplateContext(
                                    intention=context_data.get("intention", ""),
                                    tone=context_data.get("tone", ""),
                                    approach=context_data.get("approach", ""),
                                    style=context_data.get("style", ""),
                                    dos=context_data.get("dos", []),
                                    donts=context_data.get("donts", [])
                                )
                            except Exception as e:
                                print(f"Warning: Could not parse template context: {e}")

                        # Parse example (JSONB)
                        example_data = tmpl_data.get("example", {})
                        if example_data and isinstance(example_data, dict):
                            try:
                                template_dict["example"] = TemplateExample(
                                    for_contact=example_data.get("for_contact", {}),
                                    perfect_email=example_data.get("perfect_email", ""),
                                    why_it_works=example_data.get("why_it_works", "")
                                )
                            except Exception as e:
                                print(f"Warning: Could not parse template example: {e}")

                        email_templates[template_name] = template_dict
            except Exception as e:
                # Table doesn't exist yet or other error
                print(f"Warning: Could not load email templates: {e}")

            # Step 11: Build ClientContextV3
            return ClientContextV3(
                client_id=client_id,
                client_name=client_name,
                offerings=offerings,
                personas=personas,
                pain_solved=pain_solved,
                value_proposition=value_proposition,
                target_industries=target_industries,
                target_company_sizes=target_company_sizes,
                target_regions=target_regions,
                real_case_studies=real_case_studies,
                competitors=competitors,
                email_templates=email_templates,
                created_at=data.get("created_at"),
                updated_at=data.get("updated_at")
            )

        except Exception as e:
            import traceback
            print(f"ERROR loading client context v3 for {client_id}: {e}")
            print(f"Full traceback:\n{traceback.format_exc()}")
            return self._get_mock_context_v3(client_id)

    def _extract_pain_solved(self, data: Dict[str, Any], personas: List[Dict[str, Any]]) -> str:
        """
        Extract pain_solved from client data.

        Priority:
        1. Explicit pain_solved field
        2. First persona's pain_point_solved or value_proposition
        3. Infer from client name

        Args:
            data: Client data from Supabase
            personas: List of personas

        Returns:
            String describing the problem the client solves
        """
        # Try explicit field
        pain_solved = data.get("pain_solved", "")
        if pain_solved:
            return pain_solved

        # Try from personas
        if personas and len(personas) > 0:
            first_persona = personas[0]
            pain_solved = first_persona.get("pain_point_solved", "") or first_persona.get("value_proposition", "")
            if pain_solved:
                return pain_solved

        # Infer from client name
        client_name = data.get("client_name", "").lower()
        return self._infer_pain_solved(client_name)

    def _infer_pain_solved(self, client_name: str) -> str:
        """
        Infer pain_solved from client name.

        Args:
            client_name: Name of the client (lowercase)

        Returns:
            Best guess for pain_solved
        """
        if "kaleads" in client_name or "lead" in client_name:
            return "génération de leads B2B qualifiés via l'automatisation"
        elif "sales" in client_name or "vente" in client_name or "commercial" in client_name:
            return "optimisation des processus de vente et augmentation du pipeline"
        elif "talent" in client_name or "recruit" in client_name or "rh" in client_name or "hr" in client_name:
            return "recrutement et gestion RH efficace"
        elif "devops" in client_name or "cloud" in client_name or "infra" in client_name:
            return "déploiements rapides et infrastructure scalable"
        elif "marketing" in client_name or "martech" in client_name:
            return "automatisation marketing et génération de demande"
        else:
            return "amélioration de l'efficacité opérationnelle"

    def _get_mock_context_v3(self, client_id: str) -> "ClientContextV3":
        """
        Get mock ClientContextV3 for testing.

        Args:
            client_id: Client ID

        Returns:
            Mock ClientContextV3
        """
        return ClientContextV3(
            client_id=client_id,
            client_name="Mock Client (v3)",
            offerings=["service A", "service B"],
            personas=[{"title": "VP Sales", "description": "Decision maker for sales tools"}],
            pain_solved="amélioration de l'efficacité opérationnelle",
            value_proposition="On aide les entreprises à scaler",
            target_industries=["SaaS", "Tech"],
            target_company_sizes=["50-200", "200-1000"],
            target_regions=["France", "Europe"],
            real_case_studies=[
                CaseStudy(
                    company="Client A",
                    industry="SaaS",
                    result="augmenter son pipeline de 200%",
                    metric="200% pipeline increase",
                    persona="VP Sales"
                )
            ],
            competitors=["Competitor A", "Competitor B"],
            email_templates={},
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
