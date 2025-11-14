# Plan d'Action v3.0 - Refonte Architecturale

**Date** : 14 novembre 2025
**Objectif** : Transformer le système d'agents spécifiques Kaleads en agents fondamentaux réutilisables
**Durée estimée** : 8 semaines

---

## 🎯 Problèmes Actuels Identifiés

### 1. Contexte Client Incohérent

**Problème** :
```python
# Certains agents reçoivent un STRING
persona_agent = PersonaExtractorAgent(client_context="🎯 CRITICAL CONTEXT - YOUR ROLE:\n- You work FOR: Kaleads\n...")

# D'autres reçoivent un DICT
pain_agent = PainPointAgent(client_context={
    "client_name": "Kaleads",
    "offerings": [...],
    "pain_solved": "...",
})
```

**Impact** :
- Code difficile à maintenir
- Impossible de standardiser les prompts
- Bugs quand on ajoute un nouveau champ

**Solution** :
- Créer une classe `ClientContext` standard (Pydantic)
- Tous les agents utilisent le même format

---

### 2. Agent CaseStudy : Double Personnalité

**Problème** :
L'agent `CaseStudyAgent` a deux usages contradictoires :

```python
# Usage 1 : Scraper les case studies DU PROSPECT
# → "Aircall a aidé TechCo à améliorer leur productivité"
case_agent.run(scrape_prospect_website=True)

# Usage 2 : Utiliser les case studies DU CLIENT
# → "On a aidé Salesforce France à augmenter son pipeline de 300%"
case_agent.run(use_client_case_studies=True)
```

**Impact** :
- Confusion sur ce que l'agent fait
- Résultats incohérents
- Impossible de prédire le comportement

**Solution** :
- Renommer l'agent en `ProofGenerator`
- Mode explicite : `mode="client_case_studies"` ou `mode="prospect_achievements"`
- Par défaut : utiliser les vraies case studies du client

---

### 3. Agents Trop Spécifiques à Kaleads

**Problème** :
```python
# PainPointAgent a des instructions hardcodées pour lead generation
background = [
    "Focus on CLIENT ACQUISITION, LEAD GENERATION, SALES GROWTH",
    "NEVER about internal HR/tech problems",
]
```

**Impact** :
- Impossible d'utiliser pour un client qui vend des solutions RH
- Impossible d'utiliser pour un client DevOps
- Fonctionne uniquement pour Kaleads (lead gen)

**Solution** :
- Retirer les instructions spécifiques du code de l'agent
- Générer les instructions dynamiquement depuis `client_context.pain_solved`

---

### 4. Templates Hardcodés

**Problème** :
```python
# Template hardcodé dans le code
email_content = f"""Bonjour {contact.first_name},

Je travaille chez {client_name}, spécialisé en {client_personas_str}.
..."""
```

**Impact** :
- Impossible de changer le template sans redeployer
- Chaque client doit avoir le même format d'email
- Pas de A/B testing possible

**Solution** :
- Stocker les templates dans Supabase
- Les clients peuvent créer/éditer leurs templates
- L'API charge le template à la volée

---

## 🚀 Plan de Migration (8 semaines)

### Phase 1 : Standardisation du Contexte (Semaine 1-2)

**Objectif** : Tous les agents utilisent `ClientContext`

#### Actions

**1.1 Créer le modèle ClientContext**

Fichier : `src/models/client_context.py`

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class CaseStudy(BaseModel):
    """Une case study réelle du client."""
    company: str = Field(..., description="Nom de l'entreprise aidée")
    industry: str = Field(..., description="Secteur (ex: 'SaaS', 'Finance')")
    result: str = Field(..., description="Résultat mesurable (ex: 'augmenter son pipeline de 300%')")
    metric: Optional[str] = Field(None, description="Métrique quantifiée (ex: '300% pipeline increase')")
    persona: Optional[str] = Field(None, description="Persona aidé (ex: 'VP Sales')")


class ClientContext(BaseModel):
    """
    Contexte client standardisé.

    Ce contexte contient TOUTES les informations sur le client qui prospecte,
    et permet aux agents de personnaliser leur comportement.
    """

    # Identité
    client_id: str = Field(..., description="UUID du client dans Supabase")
    client_name: str = Field(..., description="Nom du client (ex: 'Kaleads')")

    # Offres
    offerings: List[str] = Field(
        default_factory=list,
        description="Liste des offres/services du client"
    )

    personas: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Liste des personas cibles (format Supabase)"
    )

    # Value Proposition
    pain_solved: str = Field(
        default="",
        description="Quel problème le client résout"
    )

    value_proposition: str = Field(
        default="",
        description="Proposition de valeur du client"
    )

    # ICP
    target_industries: List[str] = Field(
        default_factory=list,
        description="Industries cibles"
    )

    target_company_sizes: List[str] = Field(
        default_factory=list,
        description="Tailles d'entreprises cibles"
    )

    # Preuves sociales
    real_case_studies: List[CaseStudy] = Field(
        default_factory=list,
        description="Vraies case studies du client"
    )

    # Concurrence
    competitors: List[str] = Field(
        default_factory=list,
        description="Liste des concurrents du client"
    )

    # Templates
    email_templates: Dict[str, str] = Field(
        default_factory=dict,
        description="Templates d'emails par type"
    )

    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def get_offerings_str(self, limit: int = 3) -> str:
        """Retourne les offres sous forme de string."""
        return ", ".join(self.offerings[:limit]) if self.offerings else "nos solutions"

    def get_target_industries_str(self) -> str:
        """Retourne les industries cibles sous forme de string."""
        return ", ".join(self.target_industries) if self.target_industries else "B2B companies"

    def has_real_case_studies(self) -> bool:
        """Vérifie si le client a des case studies réelles."""
        return len(self.real_case_studies) > 0

    def find_case_study_by_industry(self, industry: str) -> Optional[CaseStudy]:
        """
        Trouve une case study pour une industrie donnée.

        Args:
            industry: Secteur du prospect (ex: "SaaS", "Finance")

        Returns:
            CaseStudy si trouvée, None sinon
        """
        # Exact match
        for cs in self.real_case_studies:
            if cs.industry.lower() == industry.lower():
                return cs

        # Partial match
        for cs in self.real_case_studies:
            if industry.lower() in cs.industry.lower() or cs.industry.lower() in industry.lower():
                return cs

        return None
```

**1.2 Mettre à jour SupabaseClient**

Fichier : `src/providers/supabase_client.py`

```python
from src.models.client_context import ClientContext, CaseStudy

class SupabaseClient:
    # ... existing code

    def load_client_context_v3(self, client_id: str) -> ClientContext:
        """
        Charge le contexte client depuis Supabase (format v3.0).

        Args:
            client_id: UUID du client

        Returns:
            ClientContext standardisé
        """
        # Charger le client
        client_data = self.client.table("clients").select("*").eq("id", client_id).execute()

        if not client_data.data or len(client_data.data) == 0:
            raise ValueError(f"Client {client_id} not found")

        client = client_data.data[0]

        # Charger les personas
        personas_data = self.client.table("personas").select("*").eq("client_id", client_id).execute()
        personas = personas_data.data if personas_data.data else []

        # Extraire les offres des personas
        offerings = [p.get("title", "") for p in personas if p.get("title")]

        # Extraire pain_solved
        pain_solved = ""
        if personas and len(personas) > 0:
            pain_solved = personas[0].get("pain_point_solved", "") or personas[0].get("value_proposition", "")

        if not pain_solved:
            # Fallback : deviner depuis le nom du client
            pain_solved = self._infer_pain_solved(client.get("name", ""))

        # Charger les case studies (si table existe)
        case_studies = []
        try:
            cs_data = self.client.table("case_studies").select("*").eq("client_id", client_id).execute()
            if cs_data.data:
                case_studies = [
                    CaseStudy(
                        company=cs.get("company", ""),
                        industry=cs.get("industry", ""),
                        result=cs.get("result", ""),
                        metric=cs.get("metric"),
                        persona=cs.get("persona")
                    )
                    for cs in cs_data.data
                ]
        except Exception:
            # Table n'existe pas encore
            pass

        # Charger les templates (si table existe)
        email_templates = {}
        try:
            templates_data = self.client.table("email_templates").select("*").eq("client_id", client_id).execute()
            if templates_data.data:
                email_templates = {
                    t["template_name"]: t["template_content"]
                    for t in templates_data.data
                }
        except Exception:
            pass

        # Construire le ClientContext
        return ClientContext(
            client_id=client_id,
            client_name=client.get("name", ""),
            offerings=offerings,
            personas=personas,
            pain_solved=pain_solved,
            value_proposition=client.get("value_proposition", ""),
            target_industries=client.get("target_industries", []),
            target_company_sizes=client.get("target_company_sizes", []),
            real_case_studies=case_studies,
            competitors=client.get("competitors", []),
            email_templates=email_templates,
            created_at=client.get("created_at"),
            updated_at=client.get("updated_at"),
        )

    def _infer_pain_solved(self, client_name: str) -> str:
        """Devine pain_solved depuis le nom du client."""
        name_lower = client_name.lower()

        if "kaleads" in name_lower or "lead" in name_lower:
            return "génération de leads B2B qualifiés via l'automatisation"
        elif "sales" in name_lower or "vente" in name_lower:
            return "optimisation des processus de vente et augmentation du pipeline"
        elif "talent" in name_lower or "recruit" in name_lower or "rh" in name_lower:
            return "recrutement et gestion RH efficace"
        elif "devops" in name_lower or "cloud" in name_lower:
            return "déploiements rapides et infrastructure scalable"
        else:
            return "amélioration de l'efficacité opérationnelle"
```

**1.3 Refactoriser les agents**

Fichier : `src/agents/agents_optimized.py`

```python
from src.models.client_context import ClientContext

# AVANT
class PainPointAgentOptimized:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[dict] = None  # AVANT : dict
    ):
        # ... code qui parse le dict
        if client_context and isinstance(client_context, dict):
            client_name = client_context.get("client_name", "le client")
            # ...

# APRÈS
class PainPointAgentOptimized:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[ClientContext] = None  # APRÈS : ClientContext
    ):
        self.client_context = client_context

        # Générer le prompt de contexte
        if client_context:
            context_str = f"""
🎯 CRITICAL CONTEXT:
- Client Name: {client_context.client_name}
- What Client Sells: {client_context.get_offerings_str()}
- Problem Client Solves: {client_context.pain_solved}
- Target Industries: {client_context.get_target_industries_str()}
"""
            background.append(context_str)

        # ... reste du code
```

**Répéter pour tous les agents** : PersonaExtractor, Competitor, Signal, System, CaseStudy

**1.4 Mettre à jour l'API**

Fichier : `src/api/n8n_optimized_api.py`

```python
from src.models.client_context import ClientContext
from src.providers.supabase_client import SupabaseClient

async def generate_email_with_agents(
    contact: ContactInput,
    client_id: str,
    template_content: Optional[str] = None,
    enable_scraping: bool = True,
    model_preference: str = "balanced"
) -> Dict[str, Any]:
    start_time = datetime.now()

    # AVANT : Charger et construire manuellement
    # supabase_client = SupabaseClient()
    # raw_context = supabase_client.load_client_context(client_id)
    # context_str = f"🎯 CRITICAL CONTEXT - YOUR ROLE:\n- You work FOR: {raw_context.client_name}\n..."
    # client_context_dict = {"client_name": raw_context.client_name, ...}

    # APRÈS : Charger le ClientContext standardisé
    supabase_client = SupabaseClient()
    client_context = supabase_client.load_client_context_v3(client_id)

    # Initialiser les agents avec le contexte standardisé
    persona_agent = PersonaExtractorAgentOptimized(
        enable_scraping=enable_scraping,
        client_context=client_context  # Maintenant tous prennent ClientContext
    )

    pain_agent = PainPointAgentOptimized(
        enable_scraping=enable_scraping,
        client_context=client_context
    )

    proof_agent = ProofGeneratorOptimized(  # Renommé de CaseStudyAgent
        enable_scraping=enable_scraping,
        client_context=client_context,
        mode="client_case_studies"  # Mode explicite
    )

    # ... reste du code
```

#### Tests Phase 1

```python
# tests/test_client_context.py
def test_load_client_context_v3():
    """Teste le chargement du ClientContext depuis Supabase."""
    supabase = SupabaseClient()
    context = supabase.load_client_context_v3("kaleads-uuid")

    assert context.client_name == "Kaleads"
    assert "lead generation" in context.offerings[0].lower()
    assert context.pain_solved != ""
    assert len(context.target_industries) > 0

def test_client_context_methods():
    """Teste les méthodes utilitaires de ClientContext."""
    context = ClientContext(
        client_id="test",
        client_name="TestCorp",
        offerings=["service A", "service B", "service C"],
        target_industries=["SaaS", "Tech"],
        real_case_studies=[
            CaseStudy(company="ClientA", industry="SaaS", result="résultat A"),
            CaseStudy(company="ClientB", industry="Finance", result="résultat B"),
        ]
    )

    assert context.get_offerings_str(limit=2) == "service A, service B"
    assert context.has_real_case_studies() == True
    assert context.find_case_study_by_industry("SaaS").company == "ClientA"
    assert context.find_case_study_by_industry("Finance").company == "ClientB"
    assert context.find_case_study_by_industry("Unknown") is None
```

**Résultat attendu** :
- ✅ Tous les agents utilisent `ClientContext`
- ✅ Code plus lisible et maintenable
- ✅ Tests passent

---

### Phase 2 : Clarification des Rôles (Semaine 3-4)

**Objectif** : Chaque agent a un rôle clair et générique

#### Actions

**2.1 Refactoriser PainPointAgent**

Actuellement, l'agent a des instructions hardcodées pour lead generation. Il faut générer les instructions dynamiquement.

Fichier : `src/agents/pain_point_agent.py` (nouveau fichier dédié)

```python
from src.models.client_context import ClientContext
from typing import Optional, Literal

def classify_pain_type(pain_solved: str) -> Literal["client_acquisition", "hr_recruitment", "tech_infrastructure", "ops_efficiency", "generic"]:
    """
    Classifie le type de pain point selon ce que le client résout.

    Args:
        pain_solved: Description du problème résolu par le client

    Returns:
        Type de pain point
    """
    pain_lower = pain_solved.lower()

    # Client acquisition (lead gen, sales, prospecting)
    if any(kw in pain_lower for kw in ["lead", "prospect", "client", "sales", "pipeline", "commercial", "vente"]):
        return "client_acquisition"

    # HR/Recruitment
    elif any(kw in pain_lower for kw in ["rh", "recruit", "talent", "embauche", "hiring", "onboarding"]):
        return "hr_recruitment"

    # Tech/Infrastructure
    elif any(kw in pain_lower for kw in ["devops", "cloud", "infrastructure", "deploy", "ci/cd", "tech"]):
        return "tech_infrastructure"

    # Ops/Efficiency
    elif any(kw in pain_lower for kw in ["ops", "efficiency", "process", "automation", "workflow"]):
        return "ops_efficiency"

    else:
        return "generic"


PAIN_TYPE_INSTRUCTIONS = {
    "client_acquisition": {
        "focus": "CLIENT ACQUISITION, LEAD GENERATION, SALES GROWTH",
        "examples": [
            "✅ 'difficulté à acquérir de nouveaux prospects qualifiés'",
            "✅ 'prospection manuelle qui consomme 15h par semaine'",
            "✅ 'taux de conversion faible des campagnes commerciales'",
        ],
        "avoid": [
            "❌ 'processus RH inefficaces' (not related to client acquisition)",
            "❌ 'infrastructure technique obsolète' (not related to sales)",
        ],
    },
    "hr_recruitment": {
        "focus": "HR, RECRUITMENT, TALENT MANAGEMENT, ONBOARDING",
        "examples": [
            "✅ 'processus de recrutement manuel qui prend 3 semaines par poste'",
            "✅ 'difficulté à attirer des talents qualifiés'",
            "✅ 'taux de turnover élevé (30% par an)'",
        ],
        "avoid": [
            "❌ 'difficulté à acquérir des clients' (not related to HR)",
            "❌ 'infrastructure cloud non scalable' (not related to HR)",
        ],
    },
    "tech_infrastructure": {
        "focus": "TECH INFRASTRUCTURE, DEVOPS, SCALABILITY, DEPLOYMENT",
        "examples": [
            "✅ 'déploiements manuels qui prennent 4h et génèrent des incidents'",
            "✅ 'infrastructure non scalable pour gérer la croissance'",
            "✅ 'pas de CI/CD, ce qui ralentit le time-to-market'",
        ],
        "avoid": [
            "❌ 'difficulté à recruter des développeurs' (not infrastructure)",
            "❌ 'manque de prospects qualifiés' (not tech)",
        ],
    },
    "ops_efficiency": {
        "focus": "OPERATIONAL EFFICIENCY, PROCESS AUTOMATION, WORKFLOW OPTIMIZATION",
        "examples": [
            "✅ 'processus manuels qui consomment 20h par semaine'",
            "✅ 'pas d'automatisation, beaucoup de tâches répétitives'",
            "✅ 'workflows inefficaces qui ralentissent la productivité'",
        ],
        "avoid": [
            "❌ 'difficulté à acquérir des clients' (not ops efficiency)",
        ],
    },
    "generic": {
        "focus": "BUSINESS CHALLENGES, GROWTH, EFFICIENCY",
        "examples": [
            "✅ 'processus inefficaces qui limitent la croissance'",
            "✅ 'difficulté à scaler les opérations'",
        ],
        "avoid": [],
    },
}


class PainPointAgent:
    """
    Agent générique pour identifier les pain points.

    S'adapte au type de problème résolu par le client grâce au ClientContext.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[ClientContext] = None
    ):
        self.client_context = client_context

        # Déterminer le type de pain point selon le client
        if client_context and client_context.pain_solved:
            pain_type = classify_pain_type(client_context.pain_solved)
            instructions = PAIN_TYPE_INSTRUCTIONS[pain_type]
        else:
            pain_type = "generic"
            instructions = PAIN_TYPE_INSTRUCTIONS["generic"]

        # Construire le background avec les instructions adaptées
        background = [
            "⚠️ CRITICAL INSTRUCTION - WILL BE EVALUATED ⚠️",
            "You MUST respond EXCLUSIVELY in FRENCH (français).",
            "",
            f"🎯 PAIN POINT FOCUS: {instructions['focus']}",
            "",
            "GOOD EXAMPLES:",
        ]

        background.extend(instructions['examples'])

        if instructions['avoid']:
            background.append("")
            background.append("BAD EXAMPLES:")
            background.extend(instructions['avoid'])

        # Ajouter le contexte client si disponible
        if client_context:
            background.append("")
            background.append(f"🎯 CLIENT CONTEXT:")
            background.append(f"- Client Name: {client_context.client_name}")
            background.append(f"- What Client Sells: {client_context.get_offerings_str()}")
            background.append(f"- Problem Client Solves: {client_context.pain_solved}")
            background.append(f"- Target Industries: {client_context.get_target_industries_str()}")

        # ... reste du code pour créer l'agent
```

**Test** :

```python
# tests/test_pain_point_agent.py
def test_pain_point_agent_lead_gen():
    """Teste PainPointAgent pour un client lead generation."""
    context = ClientContext(
        client_id="test",
        client_name="Kaleads",
        pain_solved="génération de leads B2B qualifiés",
    )

    agent = PainPointAgent(client_context=context)
    result = agent.run(PainPointInputSchema(
        company_name="Aircall",
        industry="SaaS",
    ))

    # Le pain point doit être lié à CLIENT ACQUISITION
    assert "client" in result.problem_specific.lower() or "prospect" in result.problem_specific.lower()
    assert "rh" not in result.problem_specific.lower()  # Pas de RH
    assert "infrastructure" not in result.problem_specific.lower()  # Pas de tech


def test_pain_point_agent_hr():
    """Teste PainPointAgent pour un client HR tech."""
    context = ClientContext(
        client_id="test",
        client_name="TalentHub",
        pain_solved="recrutement et gestion RH efficace",
    )

    agent = PainPointAgent(client_context=context)
    result = agent.run(PainPointInputSchema(
        company_name="TechCorp",
        industry="Tech",
    ))

    # Le pain point doit être lié à HR
    assert "recrutement" in result.problem_specific.lower() or "talent" in result.problem_specific.lower() or "rh" in result.problem_specific.lower()
    assert "client" not in result.problem_specific.lower()  # Pas de client acquisition
```

**2.2 Refactoriser ProofGenerator (ex-CaseStudyAgent)**

Renommer l'agent et clarifier les deux modes.

Fichier : `src/agents/proof_generator_agent.py`

```python
from src.models.client_context import ClientContext, CaseStudy
from typing import Optional, Literal

class ProofGenerator:
    """
    Agent générique pour générer une preuve sociale.

    Deux modes :
    - "client_case_studies" : Utilise les vraies case studies du CLIENT (défaut)
    - "prospect_achievements" : Scrape les case studies du PROSPECT
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[ClientContext] = None,
        mode: Literal["client_case_studies", "prospect_achievements"] = "client_case_studies"
    ):
        self.client_context = client_context
        self.mode = mode
        self.enable_scraping = enable_scraping

        # Construire le prompt selon le mode
        if mode == "client_case_studies":
            background = self._build_client_case_studies_prompt()
        else:
            background = self._build_prospect_achievements_prompt()

        # ... créer l'agent avec ce background

    def _build_client_case_studies_prompt(self) -> List[str]:
        """Prompt pour mode client_case_studies."""
        background = [
            "🚨 CRITICAL ANTI-HALLUCINATION RULES 🚨",
            "",
            "RULE 1: USE REAL CASE STUDIES IF PROVIDED",
            "- If client_context includes real case studies → adapt one to this prospect",
            "",
            "RULE 2: IF NO REAL DATA, USE GENERIC FALLBACK",
            "- ❌ NEVER: 'TechCo à augmenter son pipeline de 300%' (fake)",
            "- ✅ OK: 'des entreprises similaires à optimiser leur prospection'",
        ]

        # Si le client a des vraies case studies, les lister
        if self.client_context and self.client_context.has_real_case_studies():
            background.append("")
            background.append(f"🎯 REAL CASE STUDIES FROM {self.client_context.client_name}:")
            background.append("")
            for cs in self.client_context.real_case_studies:
                background.append(f"- {cs.company} ({cs.industry}): {cs.result}")
            background.append("")
            background.append("USE THESE REAL CASE STUDIES:")
            background.append("- Select the most relevant one for this prospect")
            background.append("- Use REAL company names and metrics")
        else:
            background.append("")
            background.append("NO REAL CASE STUDIES PROVIDED.")
            background.append("YOU MUST USE GENERIC FALLBACK:")
            background.append("- 'des entreprises similaires à optimiser leur génération de prospects'")
            background.append("DO NOT invent fake company names or metrics.")

        return background

    def _build_prospect_achievements_prompt(self) -> List[str]:
        """Prompt pour mode prospect_achievements."""
        return [
            "🎯 MODE: PROSPECT ACHIEVEMENTS",
            "",
            "Your job is to find what the PROSPECT company has achieved.",
            "Scrape their /customers, /case-studies, /success-stories pages.",
            "",
            "Example: 'aidé TechCo à augmenter leur productivité de 50%'",
        ]

    def run(self, input_data: CaseStudyInputSchema) -> CaseStudyOutputSchema:
        """Génère la preuve sociale."""
        if self.mode == "client_case_studies":
            return self._use_client_case_studies(input_data)
        else:
            return self._scrape_prospect_achievements(input_data)

    def _use_client_case_studies(self, input_data) -> CaseStudyOutputSchema:
        """Utilise les case studies du CLIENT."""
        if not self.client_context or not self.client_context.has_real_case_studies():
            # Fallback générique
            return CaseStudyOutputSchema(
                case_study_result="des entreprises similaires à optimiser significativement leur prospection",
                confidence_score=1,
                fallback_level=3,
                reasoning="No real case studies available, using generic fallback"
            )

        # Trouver une case study pertinente pour l'industrie du prospect
        case_study = self.client_context.find_case_study_by_industry(input_data.industry)

        if case_study:
            # Utiliser la vraie case study
            return CaseStudyOutputSchema(
                case_study_result=f"{case_study.company} à {case_study.result}",
                confidence_score=5,
                fallback_level=0,
                reasoning=f"Using real case study: {case_study.company} from {case_study.industry} industry"
            )
        else:
            # Adapter une case study à l'industrie du prospect
            first_cs = self.client_context.real_case_studies[0]
            adapted = f"une entreprise {input_data.industry} similaire à {first_cs.result}"
            return CaseStudyOutputSchema(
                case_study_result=adapted,
                confidence_score=4,
                fallback_level=1,
                reasoning=f"Adapted case study from {first_cs.industry} to {input_data.industry}"
            )

    def _scrape_prospect_achievements(self, input_data) -> CaseStudyOutputSchema:
        """Scrape les achievements du PROSPECT."""
        # ... logique de scraping
        pass
```

**Test** :

```python
# tests/test_proof_generator.py
def test_proof_generator_with_real_case_studies():
    """Teste ProofGenerator avec vraies case studies."""
    context = ClientContext(
        client_id="test",
        client_name="Kaleads",
        real_case_studies=[
            CaseStudy(company="Salesforce France", industry="SaaS", result="augmenter son pipeline de 300%"),
            CaseStudy(company="BNP Paribas", industry="Finance", result="générer 500 leads/mois"),
        ]
    )

    agent = ProofGenerator(client_context=context, mode="client_case_studies")

    # Test pour un prospect SaaS
    result_saas = agent.run(CaseStudyInputSchema(
        company_name="Aircall",
        industry="SaaS",
    ))

    assert "Salesforce France" in result_saas.case_study_result
    assert result_saas.confidence_score == 5

    # Test pour un prospect Finance
    result_finance = agent.run(CaseStudyInputSchema(
        company_name="Société Générale",
        industry="Finance",
    ))

    assert "BNP Paribas" in result_finance.case_study_result
    assert result_finance.confidence_score == 5

    # Test pour un prospect industrie inconnue
    result_other = agent.run(CaseStudyInputSchema(
        company_name="HealthCorp",
        industry="Healthcare",
    ))

    assert "similaire" in result_other.case_study_result.lower()
    assert result_other.confidence_score == 4  # Adapted


def test_proof_generator_without_case_studies():
    """Teste ProofGenerator sans case studies."""
    context = ClientContext(
        client_id="test",
        client_name="NewClient",
        real_case_studies=[]  # Pas de case studies
    )

    agent = ProofGenerator(client_context=context, mode="client_case_studies")
    result = agent.run(CaseStudyInputSchema(
        company_name="Test Corp",
        industry="Tech",
    ))

    # Doit utiliser un fallback générique
    assert "similaires" in result.case_study_result.lower()
    assert result.confidence_score == 1
    assert result.fallback_level == 3
```

#### Tests Phase 2

```bash
# Lancer les tests
pytest tests/test_pain_point_agent.py -v
pytest tests/test_proof_generator.py -v

# Résultat attendu
# test_pain_point_agent_lead_gen PASSED
# test_pain_point_agent_hr PASSED
# test_proof_generator_with_real_case_studies PASSED
# test_proof_generator_without_case_studies PASSED
```

**Résultat attendu** :
- ✅ PainPointAgent adapte son comportement selon `pain_solved`
- ✅ ProofGenerator a deux modes clairs
- ✅ Agents génériques et réutilisables

---

### Phase 3 : Templates Dynamiques (Semaine 5-6)

**Objectif** : Templates dans Supabase, éditables par le client

#### Actions

**3.1 Créer la table email_templates (ENRICHIE)**

⚠️ **IMPORTANT** : Les templates doivent inclure **contexte + exemple** en plus du template !

```sql
-- Migration Supabase
CREATE TABLE IF NOT EXISTS email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id) ON DELETE CASCADE,
    template_name VARCHAR(100) NOT NULL,

    -- Template structure
    template_content TEXT NOT NULL,
    required_variables TEXT[], -- Liste des variables nécessaires
    recommended_pipeline VARCHAR(50), -- Pipeline recommandé ("basic", "pain_focused", etc.)
    description TEXT,

    -- 🆕 NOUVEAU : Contexte du template (intention, ton, style)
    context JSONB DEFAULT '{}'::jsonb, -- Structure: {intention, tone, approach, style, dos[], donts[]}

    -- 🆕 NOUVEAU : Exemple concret pour guider les agents
    example JSONB DEFAULT '{}'::jsonb, -- Structure: {for_contact: {...}, perfect_email: "...", why_it_works: "..."}

    -- Metadata
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, template_name)
);

-- Index pour performance
CREATE INDEX idx_email_templates_client_id ON email_templates(client_id);
CREATE INDEX idx_email_templates_active ON email_templates(is_active) WHERE is_active = true;

-- Trigger pour updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_email_templates_updated_at BEFORE UPDATE ON email_templates
FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

**Format du champ `context` (JSONB)** :

```json
{
  "intention": "Cold outreach pour générer un meeting",
  "tone": "Professionnel mais friendly, pas trop commercial",
  "approach": "Signal-focused + Social proof",
  "style": "Court (< 100 mots), direct, une seule CTA",
  "dos": [
    "Mentionner un signal factuel du prospect",
    "Utiliser une vraie case study avec métriques",
    "Proposer un échange court (15-20min)"
  ],
  "donts": [
    "Ne pas faire de pitch produit détaillé",
    "Ne pas utiliser de superlatifs",
    "Ne pas mentionner le prix"
  ]
}
```

**Format du champ `example` (JSONB)** :

```json
{
  "for_contact": {
    "company_name": "Aircall",
    "first_name": "Sophie",
    "industry": "SaaS",
    "target_persona": "VP Sales"
  },
  "perfect_email": "Bonjour Sophie,\n\nJ'ai vu qu'Aircall recrute 3 commerciaux selon votre page carrières.\n\nOn a aidé Salesforce France à augmenter son pipeline de 300% en 6 mois.\n\nSeriez-vous ouverte à un échange rapide de 15min?\n\nCordialement,\nL'équipe Kaleads",
  "why_it_works": "Signal factuel (hiring) + case study réelle avec métrique + CTA simple"
}
```

**3.2 Insérer des templates ENRICHIS par défaut pour Kaleads**

```sql
-- Template 1 : Signal-focused (ultra court)
INSERT INTO email_templates (
    client_id,
    template_name,
    template_content,
    required_variables,
    recommended_pipeline,
    description,
    context,
    example
) VALUES (
    'kaleads-uuid',
    'cold_outreach_signal_focused',
    'Bonjour {{first_name}},

J''ai vu que {{company_name}} {{specific_signal_1}}.

On a aidé {{case_study_result}}.

Seriez-vous ouvert(e) à un échange rapide de 15min?

Cordialement,
L''équipe Kaleads',
    ARRAY['first_name', 'company_name', 'specific_signal_1', 'case_study_result'],
    'basic',
    'Template ultra court basé sur un signal d''intention',
    '{
        "intention": "Cold outreach basé sur un signal d''intention",
        "tone": "Direct, factuel, pas de fluff",
        "approach": "Signal factuel + Social proof + CTA simple",
        "style": "Ultra court (< 80 mots), une phrase par paragraphe",
        "dos": [
            "Utiliser un signal vérifiable (hiring, funding, product launch)",
            "Mentionner une vraie case study avec métrique",
            "CTA simple et court (15-20min)"
        ],
        "donts": [
            "Pas de pitch produit",
            "Pas de questions rhétoriques",
            "Pas de superlatifs"
        ]
    }'::jsonb,
    '{
        "for_contact": {
            "company_name": "Aircall",
            "first_name": "Sophie",
            "industry": "SaaS",
            "target_persona": "VP Sales"
        },
        "perfect_email": "Bonjour Sophie,\n\nJ''ai vu qu''Aircall recrute 3 commerciaux selon votre page carrières.\n\nOn a aidé Salesforce France à augmenter son pipeline de 300% en 6 mois.\n\nSeriez-vous ouverte à un échange rapide de 15min?\n\nCordialement,\nL''équipe Kaleads",
        "why_it_works": "Signal factuel (hiring) + case study réelle avec métrique + CTA simple"
    }'::jsonb
);

-- Template 2 : Pain-focused (empathique)
INSERT INTO email_templates (
    client_id,
    template_name,
    template_content,
    required_variables,
    recommended_pipeline,
    description,
    context,
    example
) VALUES (
    'kaleads-uuid',
    'cold_outreach_pain_focused',
    'Bonjour {{first_name}},

En tant que {{target_persona}} chez {{company_name}}, vous faites probablement face à {{problem_specific}}.

Cela peut avoir un impact sur {{impact_measurable}}.

On a aidé {{case_study_result}}.

Seriez-vous ouvert(e) à en discuter?

Cordialement,
L''équipe Kaleads',
    ARRAY['first_name', 'target_persona', 'company_name', 'problem_specific', 'impact_measurable', 'case_study_result'],
    'pain_focused',
    'Template focalisé sur l''empathie du pain point',
    '{
        "intention": "Cold outreach basé sur l''empathie du pain point",
        "tone": "Empathique, consultatif, pas agressif",
        "approach": "Pain point + Impact + Solution (via case study)",
        "style": "Moyen (100-120 mots), structure problème-solution",
        "dos": [
            "Identifier un vrai pain point du prospect",
            "Quantifier l''impact si possible",
            "Proposer une discussion, pas une démo"
        ],
        "donts": [
            "Ne pas inventer de faux problèmes",
            "Ne pas être condescendant",
            "Ne pas présumer que le prospect a ce problème"
        ]
    }'::jsonb,
    '{
        "for_contact": {
            "company_name": "Doctolib",
            "first_name": "Thomas",
            "industry": "HealthTech",
            "target_persona": "VP Sales"
        },
        "perfect_email": "Bonjour Thomas,\n\nEn tant que VP Sales chez Doctolib, vous faites probablement face à la difficulté de qualifier rapidement les milliers de praticiens qui visitent votre site.\n\nCela peut ralentir votre cycle de vente et limiter la croissance de votre équipe commerciale.\n\nOn a aidé Salesforce France à augmenter son pipeline de 300% en automatisant la qualification des prospects.\n\nSeriez-vous ouvert à en discuter?\n\nCordialement,\nL''équipe Kaleads",
        "why_it_works": "Pain point spécifique au secteur + impact quantifié + case study pertinente"
    }'::jsonb
);

-- Template 3 : Competitor-focused (respectueux)
INSERT INTO email_templates (
    client_id,
    template_name,
    template_content,
    required_variables,
    recommended_pipeline,
    description,
    context,
    example
) VALUES (
    'kaleads-uuid',
    'cold_outreach_competitor_focused',
    'Bonjour {{first_name}},

J''ai remarqué que {{company_name}} utilise {{competitor_name}}.

Nous aidons des entreprises qui utilisent {{competitor_name}} à optimiser leur génération de leads avec de l''enrichissement de données en temps réel.

On a aidé {{case_study_result}}.

Seriez-vous ouvert(e) à comparer les approches?

Cordialement,
L''équipe Kaleads',
    ARRAY['first_name', 'company_name', 'competitor_name', 'case_study_result'],
    'competitor',
    'Template basé sur l''usage d''un concurrent',
    '{
        "intention": "Cold outreach basé sur l''usage d''un concurrent",
        "tone": "Respectueux du concurrent, focus sur la différenciation",
        "approach": "Reconnaissance du concurrent + Notre valeur ajoutée unique",
        "style": "Court (90-100 mots), pas agressif envers le concurrent",
        "dos": [
            "Mentionner le concurrent avec respect",
            "Expliquer la valeur ajoutée SANS dénigrer",
            "Proposer une comparaison objective"
        ],
        "donts": [
            "Ne jamais dénigrer le concurrent",
            "Ne pas dire \"on est mieux que X\"",
            "Ne pas forcer un switch immédiat"
        ]
    }'::jsonb,
    '{
        "for_contact": {
            "company_name": "Payfit",
            "first_name": "Marie",
            "industry": "HRTech",
            "competitor_name": "HubSpot"
        },
        "perfect_email": "Bonjour Marie,\n\nJ''ai remarqué que Payfit utilise HubSpot pour votre prospection.\n\nNous aidons des entreprises qui utilisent HubSpot à automatiser davantage leur qualification de leads avec de l''enrichissement de données en temps réel.\n\nOn a aidé Aircall à réduire leur coût d''acquisition client de 40% grâce à cette approche.\n\nSeriez-vous ouverte à comparer les approches?\n\nCordialement,\nL''équipe Kaleads",
        "why_it_works": "Respect du concurrent + valeur ajoutée claire + métrique forte"
    }'::jsonb
);
```

**3.3 Mettre à jour SupabaseClient**

```python
# src/providers/supabase_client.py
class SupabaseClient:
    # ... existing code

    def get_client_templates(self, client_id: str) -> List[Dict[str, Any]]:
        """
        Récupère tous les templates du client.

        Args:
            client_id: UUID du client

        Returns:
            Liste des templates
        """
        result = self.client.table("email_templates") \
            .select("*") \
            .eq("client_id", client_id) \
            .eq("is_active", True) \
            .execute()

        return result.data if result.data else []

    def get_template_by_name(self, client_id: str, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Récupère un template spécifique par son nom.

        Args:
            client_id: UUID du client
            template_name: Nom du template

        Returns:
            Template ou None si non trouvé
        """
        result = self.client.table("email_templates") \
            .select("*") \
            .eq("client_id", client_id) \
            .eq("template_name", template_name) \
            .eq("is_active", True) \
            .single() \
            .execute()

        return result.data if result.data else None

    def create_template(self, client_id: str, template: Dict[str, Any]) -> Dict[str, Any]:
        """Crée un nouveau template."""
        template["client_id"] = client_id
        result = self.client.table("email_templates").insert(template).execute()
        return result.data[0] if result.data else {}

    def update_template(self, template_id: str, updates: Dict[str, Any]) -> Dict[str, Any]:
        """Met à jour un template existant."""
        result = self.client.table("email_templates") \
            .update(updates) \
            .eq("id", template_id) \
            .execute()
        return result.data[0] if result.data else {}

    def delete_template(self, template_id: str) -> bool:
        """Supprime (désactive) un template."""
        result = self.client.table("email_templates") \
            .update({"is_active": False}) \
            .eq("id", template_id) \
            .execute()
        return bool(result.data)
```

**3.4 Ajouter endpoints API**

```python
# src/api/n8n_optimized_api.py

@app.get("/api/v3/templates")
async def list_templates(client_id: str):
    """
    Liste tous les templates du client.

    Args:
        client_id: UUID du client

    Returns:
        Liste des templates avec métadonnées
    """
    try:
        supabase = SupabaseClient()
        templates = supabase.get_client_templates(client_id)

        return {
            "success": True,
            "templates": templates,
            "count": len(templates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v3/templates/{template_name}")
async def get_template(client_id: str, template_name: str):
    """
    Récupère un template spécifique.

    Args:
        client_id: UUID du client
        template_name: Nom du template

    Returns:
        Template avec son contenu
    """
    try:
        supabase = SupabaseClient()
        template = supabase.get_template_by_name(client_id, template_name)

        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return {
            "success": True,
            "template": template
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class CreateTemplateRequest(BaseModel):
    """Request pour créer un template."""
    client_id: str
    template_name: str
    template_content: str
    required_variables: List[str] = []
    recommended_pipeline: Optional[str] = "basic"
    description: Optional[str] = ""


@app.post("/api/v3/templates")
async def create_template(request: CreateTemplateRequest):
    """
    Crée un nouveau template.

    Args:
        request: Données du template

    Returns:
        Template créé avec son ID
    """
    try:
        supabase = SupabaseClient()
        template = supabase.create_template(
            client_id=request.client_id,
            template={
                "template_name": request.template_name,
                "template_content": request.template_content,
                "required_variables": request.required_variables,
                "recommended_pipeline": request.recommended_pipeline,
                "description": request.description,
            }
        )

        return {
            "success": True,
            "template": template
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/v3/templates/{template_id}")
async def update_template(template_id: str, updates: Dict[str, Any]):
    """Met à jour un template."""
    try:
        supabase = SupabaseClient()
        template = supabase.update_template(template_id, updates)

        return {
            "success": True,
            "template": template
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/v3/templates/{template_id}")
async def delete_template(template_id: str):
    """Supprime (désactive) un template."""
    try:
        supabase = SupabaseClient()
        success = supabase.delete_template(template_id)

        return {
            "success": success
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

**3.5 Utiliser les templates dans la génération**

```python
# src/api/n8n_optimized_api.py

@app.post("/api/v3/generate-email")
async def generate_email_v3(request: GenerateEmailRequest):
    """
    Génère un email avec template depuis Supabase.

    Request peut contenir :
    - template_content : Template directement (comme v2)
    - template_name : Nom du template à charger depuis Supabase (nouveau)

    Si template_name est fourni, il prend la priorité.
    """
    try:
        # Charger le template si template_name fourni
        if request.template_name:
            supabase = SupabaseClient()
            template_data = supabase.get_template_by_name(request.client_id, request.template_name)

            if not template_data:
                raise HTTPException(status_code=404, detail=f"Template '{request.template_name}' not found")

            template_content = template_data["template_content"]
            recommended_pipeline = template_data.get("recommended_pipeline", "basic")
        elif request.template_content:
            template_content = request.template_content
            recommended_pipeline = "basic"
        else:
            # Fallback : template par défaut
            template_content = None  # Utilisera le template hardcodé
            recommended_pipeline = "basic"

        # Générer l'email
        result = await generate_email_with_agents(
            contact=request.contact,
            client_id=request.client_id,
            template_content=template_content,
            enable_scraping=request.options.get("enable_scraping", True),
            model_preference=request.options.get("model_preference", "balanced")
        )

        return GenerateEmailResponse(
            success=True,
            **result
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

#### Tests Phase 3

```bash
# Test API templates
curl -X GET "http://localhost:20001/api/v3/templates?client_id=kaleads-uuid"

curl -X POST http://localhost:20001/api/v3/templates \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "kaleads-uuid",
    "template_name": "follow_up",
    "template_content": "Bonjour {{first_name}},\n\nJe rebondis sur mon dernier email...",
    "required_variables": ["first_name", "company_name"],
    "recommended_pipeline": "basic"
  }'

# Test génération avec template_name
curl -X POST http://localhost:20001/api/v3/generate-email \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "kaleads-uuid",
    "template_name": "cold_outreach_basic",
    "contact": {
      "company_name": "Aircall",
      "first_name": "Sophie",
      "website": "https://aircall.io"
    }
  }'
```

**Résultat attendu** :
- ✅ Templates stockés dans Supabase
- ✅ API CRUD complète pour les templates
- ✅ Génération d'email avec template_name

---

### Phase 4 : Documentation & Migration (Semaine 7-8)

**Objectif** : Documentation complète + migrer les clients existants

#### Actions

**4.1 Documenter la nouvelle architecture**

Créer `docs/API_V3.md` :

```markdown
# API v3.0 Documentation

## Overview

v3.0 introduces a modular, context-driven architecture where:
- Agents are generic and reusable
- Client context is standardized (`ClientContext`)
- Templates are stored in Supabase
- Pipelines are composable

## Endpoints

### Templates

#### `GET /api/v3/templates`
List all templates for a client.

**Query Parameters**:
- `client_id` (required): Client UUID

**Response**:
```json
{
  "success": true,
  "templates": [
    {
      "id": "uuid",
      "template_name": "cold_outreach_basic",
      "template_content": "Bonjour {{first_name}}...",
      "required_variables": ["first_name", "company_name"],
      "recommended_pipeline": "basic"
    }
  ],
  "count": 2
}
```

#### `POST /api/v3/generate-email`
Generate an email using a template.

**Request**:
```json
{
  "client_id": "uuid",
  "template_name": "cold_outreach_basic",  // NEW: Load template from Supabase
  "contact": {
    "company_name": "Aircall",
    "first_name": "Sophie",
    "website": "https://aircall.io"
  },
  "options": {
    "model_preference": "balanced",
    "enable_scraping": true
  }
}
```

## Migration from v2 to v3

### For Existing Clients

1. **Extract templates from code** → Insert into Supabase
2. **Load `ClientContext`** → Verify all fields are populated
3. **Update API calls** → Use `template_name` instead of `template_content`

### Breaking Changes

- `CaseStudyAgent` renamed to `ProofGenerator`
- `client_context` now expects `ClientContext` object (not dict/string)
- Templates must be in Supabase (or use `template_content` fallback)
```

**4.2 Migrer Kaleads vers v3**

Script de migration : `scripts/migrate_kaleads_to_v3.py`

```python
"""
Script de migration pour passer Kaleads de v2 à v3.

Actions :
1. Créer ClientContext structuré dans Supabase
2. Migrer les templates hardcodés vers la table email_templates
3. Tester la génération d'email avec v3
"""

from src.providers.supabase_client import SupabaseClient
from src.models.client_context import ClientContext, CaseStudy

def migrate_kaleads():
    """Migre Kaleads vers v3."""
    supabase = SupabaseClient()

    # 1. Créer/Mettre à jour le client dans Supabase
    print("1. Creating/updating Kaleads client...")

    # 2. Ajouter les case studies
    print("2. Adding case studies...")
    case_studies = [
        {
            "client_id": "kaleads-uuid",
            "company": "Salesforce France",
            "industry": "SaaS",
            "result": "augmenter son pipeline de 300% en 6 mois",
            "metric": "300% pipeline increase",
            "persona": "VP Sales"
        },
        {
            "client_id": "kaleads-uuid",
            "company": "BNP Paribas",
            "industry": "Finance",
            "result": "générer 500 leads qualifiés par mois",
            "metric": "500 qualified leads/month",
            "persona": "Head of Sales"
        }
    ]

    for cs in case_studies:
        supabase.client.table("case_studies").upsert(cs).execute()

    # 3. Migrer les templates
    print("3. Migrating templates...")
    templates = [
        {
            "client_id": "kaleads-uuid",
            "template_name": "cold_outreach_basic",
            "template_content": """Bonjour {{first_name}},

J'ai vu que {{company_name}} {{specific_signal_1}}.

On aide des entreprises comme la vôtre à optimiser leur génération de leads B2B.

On a aidé {{case_study_result}}.

Seriez-vous ouvert(e) à un échange rapide?

Cordialement,
L'équipe Kaleads""",
            "required_variables": ["first_name", "company_name", "specific_signal_1", "case_study_result"],
            "recommended_pipeline": "basic",
            "description": "Template basique pour cold outreach"
        },
        {
            "client_id": "kaleads-uuid",
            "template_name": "cold_outreach_pain_focused",
            "template_content": """Bonjour {{first_name}},

En tant que {{target_persona}} chez {{company_name}}, vous faites probablement face à {{problem_specific}}.

Cela peut avoir un impact sur {{impact_measurable}}.

On a aidé {{case_study_result}}.

Seriez-vous ouvert(e) à un échange pour voir comment on pourrait vous aider?

Cordialement,
L'équipe Kaleads""",
            "required_variables": ["first_name", "target_persona", "company_name", "problem_specific", "impact_measurable", "case_study_result"],
            "recommended_pipeline": "pain_focused",
            "description": "Template focalisé sur le pain point"
        }
    ]

    for template in templates:
        supabase.create_template("kaleads-uuid", template)

    # 4. Tester le chargement du ClientContext
    print("4. Testing ClientContext loading...")
    context = supabase.load_client_context_v3("kaleads-uuid")

    print(f"✅ Client Name: {context.client_name}")
    print(f"✅ Offerings: {context.get_offerings_str()}")
    print(f"✅ Pain Solved: {context.pain_solved}")
    print(f"✅ Case Studies: {len(context.real_case_studies)}")
    print(f"✅ Templates: {len(context.email_templates)}")

    print("\n✅ Migration completed successfully!")

if __name__ == "__main__":
    migrate_kaleads()
```

**4.3 Tests end-to-end**

```python
# tests/test_v3_end_to_end.py
def test_full_workflow_v3():
    """Teste le workflow complet v3.0."""
    import requests

    # 1. Lister les templates
    response = requests.get(
        "http://localhost:20001/api/v3/templates",
        params={"client_id": "kaleads-uuid"}
    )

    assert response.status_code == 200
    templates = response.json()["templates"]
    assert len(templates) >= 2

    # 2. Générer un email avec template_name
    response = requests.post(
        "http://localhost:20001/api/v3/generate-email",
        json={
            "client_id": "kaleads-uuid",
            "template_name": "cold_outreach_basic",
            "contact": {
                "company_name": "Aircall",
                "first_name": "Sophie",
                "website": "https://aircall.io",
                "industry": "SaaS"
            },
            "options": {
                "model_preference": "balanced",
                "enable_scraping": True,
                "enable_validation": True
            }
        }
    )

    assert response.status_code == 200
    result = response.json()

    assert result["success"] == True
    assert "Sophie" in result["email_content"]
    assert "Aircall" in result["email_content"]
    assert result["quality_score"] >= 95

    # 3. Vérifier que la case study utilisée est réelle
    if "Salesforce" in result["email_content"]:
        # C'est une vraie case study !
        assert result["fallback_levels"]["case_study"] == 0

    print("✅ Full v3 workflow working!")
```

---

## 📊 Résultats Attendus

| Métrique | v2.x (Actuel) | v3.0 (Cible) | Amélioration |
|----------|---------------|--------------|--------------|
| **Réutilisabilité** | 0% (Kaleads only) | 100% (N clients) | **Infinie** |
| **Temps onboarding nouveau client** | 2 jours (code custom) | 1h (config Supabase) | **96% plus rapide** |
| **Maintenabilité (LoC)** | ~3000 lignes | ~2000 lignes | **-33%** |
| **Flexibilité templates** | 1 hardcodé | N éditables | **Infinie** |
| **Tests coverage** | 60% | 85% | **+25%** |
| **Clarté du code** | 6/10 | 9/10 | **+50%** |

---

## 🎯 Checklist Complète

### Phase 1 : Standardisation (Semaine 1-2)
- [ ] Créer `src/models/client_context.py` avec `ClientContext`
- [ ] Mettre à jour `SupabaseClient.load_client_context_v3()`
- [ ] Refactoriser tous les agents pour accepter `ClientContext`
- [ ] Mettre à jour `n8n_optimized_api.py`
- [ ] Tests unitaires pour `ClientContext`
- [ ] Tests d'intégration pour chaque agent

### Phase 2 : Clarification (Semaine 3-4)
- [ ] Créer `src/agents/pain_point_agent.py` avec classification dynamique
- [ ] Renommer `CaseStudyAgent` → `ProofGenerator`
- [ ] Implémenter les deux modes de `ProofGenerator`
- [ ] Tests pour chaque type de pain point (lead gen, HR, tech, ops)
- [ ] Tests pour les deux modes de ProofGenerator

### Phase 3 : Templates (Semaine 5-6)
- [ ] Créer table `email_templates` dans Supabase
- [ ] Insérer templates par défaut pour Kaleads
- [ ] Implémenter CRUD dans `SupabaseClient`
- [ ] Ajouter endpoints API `/api/v3/templates`
- [ ] Mettre à jour génération pour utiliser `template_name`
- [ ] Tests API pour templates

### Phase 4 : Documentation (Semaine 7-8)
- [ ] Créer `docs/API_V3.md`
- [ ] Créer script de migration `scripts/migrate_kaleads_to_v3.py`
- [ ] Migrer Kaleads vers v3
- [ ] Tests end-to-end complets
- [ ] Déploiement en production
- [ ] Monitoring post-déploiement

---

## 🚀 Déploiement en Production

### Stratégie de Déploiement

**Option 1 : Big Bang (Déconseillé)**
- Déployer v3 directement
- Risque élevé si bugs

**Option 2 : Blue-Green (Recommandé)**
- Déployer v3 sur un nouveau endpoint `/api/v3/`
- Garder v2 sur `/api/v2/`
- Tester v3 en parallèle
- Basculer progressivement les clients
- Désactiver v2 après 2 semaines

**Option 3 : Canary (Idéal)**
- Déployer v3
- Router 10% du trafic vers v3
- Monitorer les métriques
- Augmenter progressivement (25%, 50%, 100%)

### Rollback Plan

Si v3 a des problèmes :
1. Basculer le trafic vers v2 (1 minute)
2. Investiguer les logs
3. Fixer en local
4. Redéployer v3

---

## 📞 Support

Pour toute question sur la migration v3 :
- **Documentation** : [ARCHITECTURE_FONDAMENTALE.md](ARCHITECTURE_FONDAMENTALE.md)
- **Exemples** : `tests/test_v3_end_to_end.py`
- **API Docs** : `docs/API_V3.md`

---

*Document généré le 14 novembre 2025*
*Version: 3.0.0*
