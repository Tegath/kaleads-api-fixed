"""
V2 Schemas - Flexible, Client-Agnostic Data Structures.

These schemas enable a "Lego-like" architecture where:
- Client context is DATA, not CODE
- Templates are passed at runtime
- Same API serves multiple clients
- No code changes needed for new clients
"""

from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


# ============================================
# Client Context (WHO we are)
# ============================================

class CaseStudy(BaseModel):
    """A client success story for social proof."""
    company_name: str = Field(..., description="Client company name")
    industry: str = Field(..., description="Client industry")
    problem: str = Field(..., description="Problem they had")
    result: str = Field(..., description="Quantified result achieved")
    
    def to_proof_string(self) -> str:
        return f"{self.company_name} ({self.industry}): {self.result}"


class ClientContext(BaseModel):
    """
    Client configuration - passed at runtime, not hardcoded.
    Same API, different client context = different behavior.
    """
    name: str = Field(..., description="Client/Agency name")
    offering: str = Field(..., description="What we sell")
    pain_solved: str = Field(..., description="Main pain point we address")
    unique_value: Optional[str] = Field(None, description="What makes us different")
    case_studies: List[CaseStudy] = Field(default_factory=list)
    required_words: List[str] = Field(default_factory=list)
    forbidden_words: List[str] = Field(default_factory=list)
    tone: str = Field("direct et conversationnel", description="Writing tone")
    ideal_industries: List[str] = Field(default_factory=list)
    min_employee_count: Optional[int] = None
    
    def get_best_case_study(self, industry: Optional[str] = None) -> Optional[CaseStudy]:
        if not self.case_studies:
            return None
        if industry:
            for cs in self.case_studies:
                if cs.industry.lower() == industry.lower():
                    return cs
        return self.case_studies[0]


class EmailTemplate(BaseModel):
    """Email template with {variables}."""
    subject: str = Field(..., description="Email subject with {variables}")
    body: str = Field(..., description="Email body with {variables}")
    instructions: str = Field("Ton direct. Pas de flatterie.", description="Style instructions")
    example_output: Optional[str] = Field(None, description="Example email")
    max_words: int = Field(70, description="Maximum word count")
    
    def get_variables(self) -> List[str]:
        import re
        pattern = r"\{(\w+)\}"
        subject_vars = re.findall(pattern, self.subject)
        body_vars = re.findall(pattern, self.body)
        return list(set(subject_vars + body_vars))


class ProspectData(BaseModel):
    """Prospect information."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    company_name: str
    industry: Optional[str] = None
    role: Optional[str] = None
    company_size: Optional[str] = None
    revenue: Optional[str] = None
    website: Optional[str] = None
    signal: Optional[str] = Field(None, description="Trigger for outreach")
    custom_vars: Dict[str, Any] = Field(default_factory=dict)
    
    def get_variable(self, var_name: str) -> Optional[str]:
        if hasattr(self, var_name):
            value = getattr(self, var_name)
            if value is not None:
                return str(value)
        if var_name in self.custom_vars:
            return str(self.custom_vars[var_name])
        return None


class EmailWriteRequest(BaseModel):
    """Complete request to write an email."""
    client: ClientContext
    template: EmailTemplate
    prospect: ProspectData
    override_proof: Optional[str] = None
    override_pain: Optional[str] = None


class EmailWriteResponse(BaseModel):
    """Response from email writer."""
    subject: str
    body: str
    word_count: int
    quality_score: float = Field(..., ge=0, le=10)
    spam_score: float = Field(..., ge=0, le=10)
    forbidden_words_found: List[str] = Field(default_factory=list)
    required_words_missing: List[str] = Field(default_factory=list)
    variables_used: Dict[str, str] = Field(default_factory=dict)
    processing_time_ms: int
    model_used: str
    cost_usd: float


class EnrichmentSource(str, Enum):
    PAPPERS = "pappers"
    SOCIETE_COM = "societe_com"
    LINKEDIN = "linkedin"
    GOOGLE_SEARCH = "google"
    CRUNCHBASE = "crunchbase"
    CUSTOM_API = "custom"


class EnrichmentRequest(BaseModel):
    company_name: str
    source: EnrichmentSource
    fields_to_fetch: List[str] = Field(default_factory=lambda: ["ceo", "employee_count"])
    custom_endpoint: Optional[str] = None
    custom_headers: Optional[Dict[str, str]] = None


class EnrichmentResponse(BaseModel):
    company_name: str
    source: str
    data: Dict[str, Any]
    success: bool
    error: Optional[str] = None
    processing_time_ms: int


class QualificationRequest(BaseModel):
    client: ClientContext
    prospect: ProspectData
    custom_criteria: Optional[Dict[str, Any]] = None


class QualificationResponse(BaseModel):
    qualified: bool
    score: float = Field(..., ge=0, le=100)
    reasons: List[str]
    disqualification_reasons: List[str] = Field(default_factory=list)
    processing_time_ms: int


class PipelineRequest(BaseModel):
    client: ClientContext
    template: EmailTemplate
    prospect: ProspectData
    skip_qualification: bool = False
    enrichment_sources: List[EnrichmentSource] = Field(default_factory=list)


class PipelineResponse(BaseModel):
    prospect_enriched: ProspectData
    qualification: Optional[QualificationResponse]
    email: Optional[EmailWriteResponse]
    pipeline_success: bool
    total_processing_time_ms: int
    total_cost_usd: float
    errors: List[str] = Field(default_factory=list)


# ============================================
# Email Sequence Schemas (V2 - 4 emails)
# ============================================

class EmailTemplateDB(BaseModel):
    """Email template from database with sequence support."""
    id: Optional[str] = None
    client_id: str
    template_name: str
    signal_type: Optional[str] = None
    subject: str
    body: str
    instructions: Optional[str] = None
    max_words: int = 70
    example_output: Optional[str] = None
    sequence_position: int = 1  # 1=initial, 2=follow-up 1, 3=follow-up 2, 4=break-up
    delay_days: int = 0
    active: bool = True


class EmailSequenceRequest(BaseModel):
    """Request to generate a complete email sequence (4 emails)."""
    client: ClientContext
    templates: List[EmailTemplateDB]  # 4 templates for the sequence
    prospect: ProspectData


class GeneratedEmail(BaseModel):
    """A single generated email in a sequence."""
    sequence_position: int
    delay_days: int
    subject: str
    body: str
    word_count: int
    quality_score: float = Field(..., ge=0, le=10)
    processing_time_ms: int


class EmailSequenceResponse(BaseModel):
    """Response with all 4 generated emails."""
    emails: List[GeneratedEmail]
    total_emails: int
    total_word_count: int
    average_quality_score: float
    total_processing_time_ms: int
    total_cost_usd: float
    model_used: str

    # SmartLead-ready custom fields
    smartlead_custom_fields: Dict[str, str] = Field(default_factory=dict)


class ClientFromDB(BaseModel):
    """Client data as stored in Supabase."""
    id: Optional[str] = None
    client_name: str
    email_templates: Optional[Dict[str, Any]] = None
    pci_file_path: Optional[str] = None
    personas_file_path: Optional[str] = None
    pain_points_file_path: Optional[str] = None
    competitors_file_path: Optional[str] = None
    case_studies_folder_path: Optional[str] = None
    active: bool = True

    # Extended fields for V2
    offering: Optional[str] = None
    pain_solved: Optional[str] = None
    tone: Optional[str] = None
    required_words: Optional[List[str]] = None
    forbidden_words: Optional[List[str]] = None
    case_studies: Optional[List[Dict[str, Any]]] = None
    ideal_industries: Optional[List[str]] = None
    min_employee_count: Optional[int] = None
    smartlead_campaign_id: Optional[str] = None

    def to_client_context(self) -> ClientContext:
        """Convert DB record to ClientContext for API use."""
        case_studies_list = []
        if self.case_studies:
            for cs in self.case_studies:
                case_studies_list.append(CaseStudy(
                    company_name=cs.get("company_name", ""),
                    industry=cs.get("industry", ""),
                    problem=cs.get("problem", ""),
                    result=cs.get("result", "")
                ))

        return ClientContext(
            name=self.client_name,
            offering=self.offering or "",
            pain_solved=self.pain_solved or "",
            tone=self.tone or "direct et professionnel",
            required_words=self.required_words or [],
            forbidden_words=self.forbidden_words or [],
            case_studies=case_studies_list,
            ideal_industries=self.ideal_industries or [],
            min_employee_count=self.min_employee_count
        )


class CampaignMapping(BaseModel):
    """Campaign mapping from database."""
    id: Optional[str] = None
    client_id: str
    signal_type: Optional[str] = None
    smartlead_campaign_id: str
    smartlead_campaign_name: Optional[str] = None
    email_account_id: Optional[str] = None
    active: bool = True
