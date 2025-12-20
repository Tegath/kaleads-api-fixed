"""
Email Writer V2 - Generic, Context-Driven Email Generation.

Key Features:
- Client context passed at runtime (not hardcoded)
- Template-based with flexible variables
- Supports example-guided generation
- Quality and spam scoring
- Vocabulary enforcement

This is the core of the 'Lego' architecture - same code,
different context = different emails for different clients.
"""

import os
import re
import json
import time
from typing import Dict, Any, Optional, List
from openai import OpenAI

from src.api.v2.schemas import (
    EmailWriteRequest,
    EmailWriteResponse,
    ClientContext,
    EmailTemplate,
    ProspectData,
    CaseStudy
)


class EmailWriterV2:
    """
    Generic email writer that accepts context at runtime.

    Usage:
        writer = EmailWriterV2()
        response = writer.write(EmailWriteRequest(
            client=ClientContext(...),
            template=EmailTemplate(...),
            prospect=ProspectData(...)
        ))
    """

    def __init__(
        self,
        model: str = "gpt-4o",
        temperature: float = 0.4,
        api_key: Optional[str] = None
    ):
        self.model = model
        self.temperature = temperature
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self._client = None

    @property
    def openai_client(self) -> OpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            self._client = OpenAI(api_key=self.api_key)
        return self._client

    def write(self, request: EmailWriteRequest) -> EmailWriteResponse:
        """
        Write a personalized email based on the request.

        Args:
            request: Complete email write request with client, template, prospect

        Returns:
            EmailWriteResponse with generated email and metrics
        """
        start_time = time.time()

        # Build the prompt
        prompt = self._build_prompt(request)

        # Call LLM
        response = self.openai_client.chat.completions.create(
            model=self.model,
            messages=[
                {
                    "role": "system",
                    "content": "Tu es un expert en cold emailing B2B. Tu reponds UNIQUEMENT en JSON valide."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=self.temperature,
            response_format={"type": "json_object"}
        )

        # Parse response
        content = response.choices[0].message.content
        result = json.loads(content)

        # Extract subject and body
        subject = result.get("subject", "")
        body = result.get("body", "")

        # Calculate metrics
        word_count = len(body.split())
        quality_score = self._calculate_quality_score(body, request)
        spam_score = self._calculate_spam_score(body, subject)

        # Check vocabulary
        forbidden_found = self._check_forbidden_words(body, request.client.forbidden_words)
        required_missing = self._check_required_words(body, request.client.required_words)

        # Calculate cost
        usage = response.usage
        cost = self._calculate_cost(usage.prompt_tokens, usage.completion_tokens)

        processing_time = int((time.time() - start_time) * 1000)

        return EmailWriteResponse(
            subject=subject,
            body=body,
            word_count=word_count,
            quality_score=quality_score,
            spam_score=spam_score,
            forbidden_words_found=forbidden_found,
            required_words_missing=required_missing,
            variables_used=result.get("variables_used", {}),
            processing_time_ms=processing_time,
            model_used=self.model,
            cost_usd=cost
        )

    def _build_prompt(self, request: EmailWriteRequest) -> str:
        """Build the LLM prompt with all context."""

        # Get best case study for proof
        case_study = request.client.get_best_case_study(request.prospect.industry)
        proof_text = case_study.to_proof_string() if case_study else ""
        if request.override_proof:
            proof_text = request.override_proof

        # Build variable context
        available_vars = {
            "first_name": request.prospect.first_name or "[Prenom]",
            "last_name": request.prospect.last_name or "",
            "company_name": request.prospect.company_name,
            "industry": request.prospect.industry or "[Industrie]",
            "role": request.prospect.role or "",
            "signal": request.prospect.signal or "",
            "proof": proof_text,
            "pain": request.override_pain or request.client.pain_solved,
            "offering": request.client.offering,
        }

        # Add custom vars from prospect
        available_vars.update(request.prospect.custom_vars)

        # Build vocabulary strings
        forbidden_str = ", ".join(request.client.forbidden_words) if request.client.forbidden_words else "Aucun"
        required_str = ", ".join(request.client.required_words) if request.client.required_words else "Aucun"

        # Case studies info
        case_studies_str = ""
        if request.client.case_studies:
            case_studies_str = "\n## CASE STUDIES DISPONIBLES\n"
            for cs in request.client.case_studies:
                case_studies_str += f"- {cs.company_name} ({cs.industry}): {cs.result}\n"

        prompt = f"""# CONTEXTE CLIENT
Entreprise: {request.client.name}
Offre: {request.client.offering}
Pain resolu: {request.client.pain_solved}
Ce qui nous differencie: {request.client.unique_value or "Non specifie"}
Ton: {request.client.tone}
{case_studies_str}

# TEMPLATE A PERSONNALISER

## Sujet
{request.template.subject}

## Corps
{request.template.body}

# INSTRUCTIONS DE STYLE
{request.template.instructions}

# CONTRAINTES STRICTES
- Maximum {request.template.max_words} mots dans le corps
- Mots INTERDITS (NE PAS utiliser): {forbidden_str}
- Mots REQUIS (DOIT apparaitre): {required_str}
- Remplacer les {{variables}} par les valeurs du prospect

# VARIABLES DISPONIBLES
{json.dumps(available_vars, indent=2, ensure_ascii=False)}

# PROSPECT CIBLE
Prenom: {request.prospect.first_name or "[Non fourni]"}
Nom: {request.prospect.last_name or "[Non fourni]"}
Entreprise: {request.prospect.company_name}
Industrie: {request.prospect.industry or "Non specifie"}
Role: {request.prospect.role or "Non specifie"}
Signal/Trigger: {request.prospect.signal or "Aucun signal specifique"}
"""

        # Add custom variables if any
        if request.prospect.custom_vars:
            prompt += "\n# VARIABLES PERSONNALISEES\n"
            for key, value in request.prospect.custom_vars.items():
                prompt += f"{key}: {value}\n"

        # Add example if provided
        if request.template.example_output:
            prompt += f"""
# EXEMPLE DE RESULTAT ATTENDU
Utilise ce style et cette structure:
---
{request.template.example_output}
---
"""

        prompt += """
# FORMAT DE SORTIE (JSON STRICT)
{
  "subject": "Le sujet de l'email personnalise",
  "body": "Le corps de l'email personnalise (max X mots)",
  "variables_used": {"variable": "valeur utilisee", ...}
}

Genere maintenant l'email en respectant TOUTES les contraintes."""

        return prompt

    def _calculate_quality_score(self, body: str, request: EmailWriteRequest) -> float:
        """Calculate email quality score (0-10)."""
        score = 5.0
        body_lower = body.lower()

        # Length check (+1 if under limit, -2 if over)
        word_count = len(body.split())
        if word_count <= request.template.max_words:
            score += 1.0
        else:
            score -= 2.0

        # Company name personalization (+1)
        if request.prospect.company_name.lower() in body_lower:
            score += 1.0

        # First name personalization (+0.5)
        if request.prospect.first_name and request.prospect.first_name.lower() in body_lower:
            score += 0.5

        # Case study mention (+1)
        if any(cs.company_name.lower() in body_lower for cs in request.client.case_studies):
            score += 1.0

        # Required words present (+1 proportional)
        if request.client.required_words:
            required_present = sum(1 for w in request.client.required_words if w.lower() in body_lower)
            score += (required_present / len(request.client.required_words)) * 1.0

        # Forbidden words penalty (-0.5 each)
        forbidden_present = sum(1 for w in request.client.forbidden_words if w.lower() in body_lower)
        score -= forbidden_present * 0.5

        # CTA question present (+0.5)
        if "?" in body:
            score += 0.5

        return max(0.0, min(10.0, score))

    def _calculate_spam_score(self, body: str, subject: str) -> float:
        """Calculate spam score (0-10, lower is better)."""
        spam_triggers = [
            "gratuit", "free", "offre speciale", "promotion", "urgent",
            "cliquez ici", "click", "ne manquez pas", "exclusif", "garanti",
            "meilleur prix", "economisez", "!!!", "100%", "winner"
        ]

        score = 0.0
        text_lower = (body + " " + subject).lower()

        # Spam words (+1 each)
        for trigger in spam_triggers:
            if trigger in text_lower:
                score += 1.0

        # Excessive caps (+2)
        caps_ratio = sum(1 for c in body if c.isupper()) / len(body) if body else 0
        if caps_ratio > 0.1:
            score += 2.0

        # Multiple exclamation marks (+1 each after first)
        exclaim_count = body.count("!")
        if exclaim_count > 1:
            score += (exclaim_count - 1) * 1.0

        return min(10.0, score)

    def _check_forbidden_words(self, body: str, forbidden: List[str]) -> List[str]:
        """Check which forbidden words appear in body."""
        body_lower = body.lower()
        return [w for w in forbidden if w.lower() in body_lower]

    def _check_required_words(self, body: str, required: List[str]) -> List[str]:
        """Check which required words are missing from body."""
        body_lower = body.lower()
        return [w for w in required if w.lower() not in body_lower]

    def _calculate_cost(self, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost in USD (GPT-4o pricing)."""
        input_cost = input_tokens * 2.50 / 1_000_000
        output_cost = output_tokens * 10.0 / 1_000_000
        return round(input_cost + output_cost, 6)
