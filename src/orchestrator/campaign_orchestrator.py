"""
CampaignOrchestrator

Coordonne l'exécution des 6 agents pour générer des emails personnalisés.
"""

import asyncio
import time
import os
import re
from typing import Dict, List, Optional
from atomic_agents.agents.base_agent import BaseAgentConfig
from atomic_agents.lib.models.base_models import ChatMessage

from src.agents import (
    PersonaExtractorAgent,
    CompetitorFinderAgent,
    PainPointAgent,
    SignalGeneratorAgent,
    SystemBuilderAgent,
    CaseStudyAgent
)
from src.schemas.campaign_schemas import (
    CampaignRequest,
    CampaignResult,
    Contact,
    EmailResult
)
from src.schemas.agent_schemas import (
    PersonaExtractorInput,
    CompetitorFinderInput,
    PainPointInput,
    SignalGeneratorInput,
    SystemBuilderInput,
    CaseStudyInput
)
from src.context import (
    PCIContextProvider,
    PersonaContextProvider,
    PainPointContextProvider,
    CompetitorContextProvider,
    CaseStudyContextProvider
)


class CampaignOrchestrator:
    """
    Orchestrateur qui coordonne tous les agents pour générer une campagne d'emails.

    Workflow:
    1. Batch 1 (parallèle): Agents 1, 2, 3, 6
    2. Batch 2 (séquentiel): Agent 4 → Agent 5
    3. Assemblage de l'email final
    4. Validation qualité
    """

    def __init__(
        self,
        openai_api_key: Optional[str] = None,
        model: str = "gpt-4o-mini",
        enable_cache: bool = True,
        context_paths: Optional[Dict[str, str]] = None
    ):
        """
        Initialise l'orchestrateur et tous les agents.

        Args:
            openai_api_key: Clé API OpenAI (ou depuis env var OPENAI_API_KEY)
            model: Modèle à utiliser (défaut: gpt-4o-mini)
            enable_cache: Activer le cache pour les résultats (défaut: True)
            context_paths: Chemins vers les fichiers de contexte (pci, personas, etc.)
        """
        self.api_key = openai_api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.enable_cache = enable_cache
        self.cache: Dict[str, Dict] = {} if enable_cache else None

        # Initialiser les Context Providers
        context_paths = context_paths or {}
        self.pci_provider = PCIContextProvider(pci_file_path=context_paths.get("pci"))
        self.persona_provider = PersonaContextProvider(persona_file_path=context_paths.get("personas"))
        self.pain_provider = PainPointContextProvider(pain_file_path=context_paths.get("pain_points"))
        self.competitor_provider = CompetitorContextProvider(competitor_file_path=context_paths.get("competitors"))
        self.case_study_provider = CaseStudyContextProvider(case_study_file_path=context_paths.get("case_studies"))

        # Initialiser les agents
        self._init_agents()

    def _init_agents(self):
        """Initialise les 6 agents avec leur configuration."""

        # Configuration de base pour tous les agents
        base_config = BaseAgentConfig(
            client=None,  # Sera initialisé par BaseAgent avec api_key
            model=self.model,
            openai_api_key=self.api_key
        )

        # Agent 1: PersonaExtractorAgent
        persona_config = BaseAgentConfig(
            client=None,
            model=self.model,
            openai_api_key=self.api_key
        )
        persona_config.context_providers = [self.pci_provider, self.persona_provider]
        self.persona_agent = PersonaExtractorAgent(persona_config)

        # Agent 2: CompetitorFinderAgent
        competitor_config = BaseAgentConfig(
            client=None,
            model=self.model,
            openai_api_key=self.api_key
        )
        competitor_config.context_providers = [self.pci_provider, self.competitor_provider, self.case_study_provider]
        self.competitor_agent = CompetitorFinderAgent(competitor_config)

        # Agent 3: PainPointAgent
        pain_config = BaseAgentConfig(
            client=None,
            model=self.model,
            openai_api_key=self.api_key
        )
        pain_config.context_providers = [self.pci_provider, self.pain_provider, self.persona_provider]
        self.pain_agent = PainPointAgent(pain_config)

        # Agent 4: SignalGeneratorAgent
        signal_config = BaseAgentConfig(
            client=None,
            model=self.model,
            openai_api_key=self.api_key
        )
        signal_config.context_providers = [self.pci_provider, self.persona_provider, self.pain_provider]
        self.signal_agent = SignalGeneratorAgent(signal_config)

        # Agent 5: SystemBuilderAgent
        system_config = BaseAgentConfig(
            client=None,
            model=self.model,
            openai_api_key=self.api_key
        )
        system_config.context_providers = [self.pci_provider, self.persona_provider, self.pain_provider]
        self.system_agent = SystemBuilderAgent(system_config)

        # Agent 6: CaseStudyAgent
        case_study_config = BaseAgentConfig(
            client=None,
            model=self.model,
            openai_api_key=self.api_key
        )
        case_study_config.context_providers = [self.pci_provider, self.case_study_provider, self.pain_provider]
        self.case_study_agent = CaseStudyAgent(case_study_config)

    def run(self, request: CampaignRequest) -> CampaignResult:
        """
        Exécute la génération d'une campagne complète.

        Args:
            request: CampaignRequest avec template, contacts, et contexte

        Returns:
            CampaignResult avec tous les emails générés et les métriques
        """
        start_time = time.time()

        emails_generated: List[EmailResult] = []
        total_tokens = 0
        cache_hits = 0
        logs = []
        errors = []

        logs.append(f"🚀 Starting campaign generation for {len(request.contacts)} contacts")

        # Traiter chaque contact
        for idx, contact in enumerate(request.contacts, 1):
            try:
                logs.append(f"📧 Processing contact {idx}/{len(request.contacts)}: {contact.company_name}")

                # Générer l'email pour ce contact
                email_result = self._process_contact(
                    contact=contact,
                    template=request.template_content,
                    context=request.context
                )

                emails_generated.append(email_result)
                total_tokens += email_result.tokens_used or 0

                # Compter les cache hits
                for level in email_result.fallback_levels.values():
                    if level == 1:  # Niveau 1 = info trouvée (potentiellement depuis cache)
                        cache_hits += 1

                logs.append(f"✅ Completed {contact.company_name} (quality: {email_result.quality_score}/100)")

            except Exception as e:
                error_msg = f"❌ Error processing {contact.company_name}: {str(e)}"
                errors.append(error_msg)
                logs.append(error_msg)
                continue

        # Calculer les métriques globales
        end_time = time.time()
        total_time = end_time - start_time
        success_count = len(emails_generated)
        success_rate = success_count / len(request.contacts) if request.contacts else 0
        avg_quality = sum(e.quality_score for e in emails_generated) / success_count if success_count > 0 else 0
        avg_time_per_email = total_time / success_count if success_count > 0 else 0
        cache_hit_rate = cache_hits / (len(emails_generated) * 6) if emails_generated else 0  # 6 agents

        # Estimer le coût (exemple avec gpt-4o-mini: ~$0.15/1M input tokens, ~$0.60/1M output tokens)
        # Approximation: 50% input, 50% output
        estimated_cost = (total_tokens * 0.5 * 0.15 / 1_000_000) + (total_tokens * 0.5 * 0.60 / 1_000_000)

        logs.append(f"✨ Campaign generation completed in {total_time:.2f}s")
        logs.append(f"📊 Success rate: {success_rate*100:.1f}% ({success_count}/{len(request.contacts)})")
        logs.append(f"⭐ Average quality score: {avg_quality:.1f}/100")
        logs.append(f"💰 Estimated cost: ${estimated_cost:.4f}")

        return CampaignResult(
            batch_id=request.batch_id,
            emails_generated=emails_generated,
            total_contacts=len(request.contacts),
            success_count=success_count,
            success_rate=success_rate,
            average_quality_score=avg_quality,
            total_execution_time_seconds=total_time,
            average_time_per_email_seconds=avg_time_per_email,
            cache_hit_rate=cache_hit_rate,
            total_tokens_used=total_tokens,
            estimated_cost_usd=estimated_cost,
            logs=logs,
            errors=errors
        )

    def _process_contact(
        self,
        contact: Contact,
        template: str,
        context: Dict[str, str]
    ) -> EmailResult:
        """
        Traite un contact individuel et génère son email.

        Args:
            contact: Contact à traiter
            template: Template d'email avec variables
            context: Contexte client (PCI, etc.)

        Returns:
            EmailResult avec l'email généré et les métriques
        """
        start_time = time.time()

        # Vérifier le cache
        cache_key = f"{contact.company_name}_{contact.website}"
        if self.enable_cache and cache_key in self.cache:
            cached_data = self.cache[cache_key]
            # Utiliser les données du cache pour assembler l'email
            variables = cached_data["variables"]
        else:
            # Exécuter le workflow des agents
            variables, fallback_levels, confidence_scores, tokens = self._execute_agents_workflow(contact)

            # Sauvegarder dans le cache
            if self.enable_cache:
                self.cache[cache_key] = {
                    "variables": variables,
                    "fallback_levels": fallback_levels,
                    "confidence_scores": confidence_scores
                }

        # Assembler l'email final
        email_generated = self._assemble_email(template, variables)

        # Calculer le quality score
        quality_score = self._calculate_quality_score(
            email_generated,
            fallback_levels if not self.enable_cache or cache_key not in self.cache else self.cache[cache_key]["fallback_levels"],
            confidence_scores if not self.enable_cache or cache_key not in self.cache else self.cache[cache_key]["confidence_scores"]
        )

        end_time = time.time()
        generation_time_ms = int((end_time - start_time) * 1000)

        return EmailResult(
            contact=contact,
            email_generated=email_generated,
            variables=variables,
            quality_score=quality_score,
            fallback_levels=fallback_levels if not self.enable_cache or cache_key not in self.cache else self.cache[cache_key]["fallback_levels"],
            confidence_scores=confidence_scores if not self.enable_cache or cache_key not in self.cache else self.cache[cache_key]["confidence_scores"],
            generation_time_ms=generation_time_ms,
            tokens_used=tokens if not self.enable_cache or cache_key not in self.cache else 0,
            errors=[],
            warnings=[]
        )

    def _execute_agents_workflow(self, contact: Contact) -> tuple[Dict[str, str], Dict[str, int], Dict[str, int], int]:
        """
        Exécute le workflow des 6 agents.

        Batch 1 (parallèle): Agents 1, 2, 3, 6
        Batch 2 (séquentiel): Agent 4 → Agent 5

        Args:
            contact: Contact à enrichir

        Returns:
            Tuple (variables, fallback_levels, confidence_scores, total_tokens)
        """
        variables = {}
        fallback_levels = {}
        confidence_scores = {}
        total_tokens = 0

        # BATCH 1: Exécution parallèle (Agents 1, 2, 3, 6)
        # Note: Pour simplifier, on exécute de manière séquentielle ici
        # TODO: Implémenter avec asyncio pour vraie parallélisation si nécessaire

        # Agent 1: PersonaExtractorAgent
        persona_input = PersonaExtractorInput(
            company_name=contact.company_name,
            website=contact.website or "",
            industry=contact.industry or "",
            website_content=""  # TODO: Scraper le site si besoin
        )
        persona_output = self.persona_agent.run(persona_input)
        variables["target_persona"] = persona_output.target_persona
        variables["product_category"] = persona_output.product_category
        fallback_levels["persona_agent"] = persona_output.fallback_level
        confidence_scores["target_persona"] = persona_output.confidence_score
        # Approximation tokens: ~500 tokens par appel agent
        total_tokens += 500

        # Agent 2: CompetitorFinderAgent
        competitor_input = CompetitorFinderInput(
            company_name=contact.company_name,
            website=contact.website or "",
            industry=contact.industry or "",
            product_category=variables["product_category"]
        )
        competitor_output = self.competitor_agent.run(competitor_input)
        variables["competitor_name"] = competitor_output.competitor_name
        variables["competitor_product_category"] = competitor_output.competitor_product_category
        fallback_levels["competitor_agent"] = competitor_output.fallback_level
        confidence_scores["competitor_name"] = competitor_output.confidence_score
        total_tokens += 500

        # Agent 3: PainPointAgent
        pain_input = PainPointInput(
            company_name=contact.company_name,
            website=contact.website or "",
            industry=contact.industry or "",
            target_persona=variables["target_persona"],
            product_category=variables["product_category"]
        )
        pain_output = self.pain_agent.run(pain_input)
        variables["problem_specific"] = pain_output.problem_specific
        variables["impact_measurable"] = pain_output.impact_measurable
        fallback_levels["pain_agent"] = pain_output.fallback_level
        confidence_scores["problem_specific"] = pain_output.confidence_score
        total_tokens += 500

        # Agent 6: CaseStudyAgent
        case_study_input = CaseStudyInput(
            company_name=contact.company_name,
            industry=contact.industry or "",
            target_persona=variables["target_persona"],
            problem_specific=variables["problem_specific"]
        )
        case_study_output = self.case_study_agent.run(case_study_input)
        variables["case_study_result"] = case_study_output.case_study_result
        fallback_levels["case_study_agent"] = case_study_output.fallback_level
        confidence_scores["case_study_result"] = case_study_output.confidence_score
        total_tokens += 500

        # BATCH 2: Exécution séquentielle (Agent 4 → Agent 5)

        # Agent 4: SignalGeneratorAgent
        signal_input = SignalGeneratorInput(
            company_name=contact.company_name,
            website=contact.website or "",
            industry=contact.industry or "",
            product_category=variables["product_category"],
            target_persona=variables["target_persona"]
        )
        signal_output = self.signal_agent.run(signal_input)
        variables["specific_signal_1"] = signal_output.specific_signal_1
        variables["specific_signal_2"] = signal_output.specific_signal_2
        variables["specific_target_1"] = signal_output.specific_target_1
        variables["specific_target_2"] = signal_output.specific_target_2
        fallback_levels["signal_agent"] = signal_output.fallback_level
        confidence_scores["specific_signal_1"] = signal_output.confidence_score
        total_tokens += 600  # Agent le plus complexe

        # Agent 5: SystemBuilderAgent (dépend d'Agent 4)
        system_input = SystemBuilderInput(
            company_name=contact.company_name,
            target_persona=variables["target_persona"],
            specific_target_1=variables["specific_target_1"],
            specific_target_2=variables["specific_target_2"],
            problem_specific=variables["problem_specific"]
        )
        system_output = self.system_agent.run(system_input)
        variables["system_1"] = system_output.system_1
        variables["system_2"] = system_output.system_2
        variables["system_3"] = system_output.system_3
        fallback_levels["system_agent"] = system_output.fallback_level
        confidence_scores["system_1"] = system_output.confidence_score
        total_tokens += 500

        # Ajouter les variables de base
        variables["first_name"] = contact.first_name or ""
        variables["company_name"] = contact.company_name
        variables["hook"] = ""  # TODO: Implémenter hook generator si nécessaire

        return variables, fallback_levels, confidence_scores, total_tokens

    def _assemble_email(self, template: str, variables: Dict[str, str]) -> str:
        """
        Assemble l'email final en remplaçant les variables dans le template.

        Args:
            template: Template avec variables {{variable_name}}
            variables: Dict des variables générées

        Returns:
            Email avec toutes les variables remplacées
        """
        email = template

        # Remplacer toutes les variables {{variable_name}}
        for key, value in variables.items():
            placeholder = f"{{{{{key}}}}}"
            email = email.replace(placeholder, str(value))

        # Vérifier s'il reste des variables non remplacées
        remaining_vars = re.findall(r'\{\{(\w+)\}\}', email)
        if remaining_vars:
            # Remplacer par des fallbacks génériques
            for var in remaining_vars:
                email = email.replace(f"{{{{{var}}}}}", "[INFORMATION NON DISPONIBLE]")

        return email

    def _calculate_quality_score(
        self,
        email: str,
        fallback_levels: Dict[str, int],
        confidence_scores: Dict[str, int]
    ) -> int:
        """
        Calcule le quality score de l'email (0-100).

        Critères:
        - Longueur appropriée (180-220 mots): 20 points
        - Niveaux de fallback bas: 40 points
        - Scores de confiance élevés: 30 points
        - Pas de variables manquantes: 10 points

        Args:
            email: Email généré
            fallback_levels: Niveaux de fallback par agent
            confidence_scores: Scores de confiance par variable

        Returns:
            Score entre 0 et 100
        """
        score = 0

        # 1. Longueur appropriée (20 points)
        word_count = len(email.split())
        if 180 <= word_count <= 220:
            score += 20
        elif 150 <= word_count <= 250:
            score += 15
        elif 120 <= word_count <= 280:
            score += 10

        # 2. Niveaux de fallback (40 points)
        avg_fallback = sum(fallback_levels.values()) / len(fallback_levels) if fallback_levels else 4
        # Fallback 1 = 40 points, Fallback 4 = 10 points
        fallback_score = max(0, 40 - (avg_fallback - 1) * 10)
        score += int(fallback_score)

        # 3. Scores de confiance (30 points)
        avg_confidence = sum(confidence_scores.values()) / len(confidence_scores) if confidence_scores else 2
        # Confidence 5 = 30 points, Confidence 1 = 6 points
        confidence_score_points = (avg_confidence / 5) * 30
        score += int(confidence_score_points)

        # 4. Pas de variables manquantes (10 points)
        if "[INFORMATION NON DISPONIBLE]" not in email:
            score += 10

        return min(100, max(0, score))
