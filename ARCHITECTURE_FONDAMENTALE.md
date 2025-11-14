# Architecture Fondamentale - Kaleads Atomic Agents

**Version**: 3.0 (Refonte architecturale)
**Date**: 14 novembre 2025
**Objectif**: Établir les bases d'un système d'agents fondamentaux, génériques et réutilisables

---

## 🎯 Philosophie du Projet

### Principe Fondamental : Séparation Agents ↔ Contexte

```
┌─────────────────────────────────────────────────────────────┐
│  AGENT FONDAMENTAL                                          │
│  - Générique et réutilisable                               │
│  - Pas lié à un client spécifique                          │
│  - Un rôle clair et unique                                 │
│  - Applicable à N contextes différents                     │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    INJECTION DE CONTEXTE
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  CONTEXTE CLIENT                                            │
│  - Qui est le client (nom, offres, personas)               │
│  - Quel problème il résout                                 │
│  - Ses case studies réelles                                │
│  - Son ICP (Ideal Customer Profile)                        │
│  - Ses templates d'emails                                  │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    COMPORTEMENT ADAPTÉ
                            ↓
┌─────────────────────────────────────────────────────────────┐
│  RÉSULTAT PERSONNALISÉ                                      │
│  - Email adapté au client                                  │
│  - Variables pertinentes pour le prospect                  │
│  - Logique métier respectée                                │
└─────────────────────────────────────────────────────────────┘
```

**Règle d'Or** : Un agent ne doit JAMAIS contenir de logique spécifique à un client. Toute personnalisation passe par l'injection de contexte.

---

## 🧩 Les 6 Agents Fondamentaux

### Vue d'ensemble

| Agent | Rôle Fondamental | Analyse | Output Type | Variantes |
|-------|------------------|---------|-------------|-----------|
| **PersonaExtractor** | Identifier le décideur cible | Prospect | Persona title + Product category | Scraping vs Inference |
| **CompetitorFinder** | Identifier les concurrents | Prospect | Concurrent name + Category | Scraping vs Industry knowledge |
| **PainPointAnalyzer** | Identifier le problème à résoudre | Prospect + Client Context | Pain point + Impact | Client acquisition vs Internal ops |
| **SignalDetector** | Détecter les signaux d'intention | Prospect | 2 signaux + 2 targets | Factual vs Generic |
| **SystemMapper** | Cartographier les systèmes/processus | Prospect | 3 systèmes utilisés | Tech stack vs Business process |
| **ProofGenerator** | Générer une preuve sociale | Client Context | Case study / Résultat | Real case vs Generic |

---

## 📋 Spécification Détaillée des Agents

### 1. PersonaExtractor

**Rôle fondamental** : Analyser une entreprise pour identifier le décideur cible et la catégorie de produit qu'elle vend.

**Ce qu'il analyse** : LE PROSPECT (l'entreprise qu'on va contacter)

**Inputs** :
- `company_name` : Nom de l'entreprise prospect
- `website` : URL du site web
- `industry` : Secteur d'activité
- `website_content` : Contenu scrapé (optionnel)

**Outputs** :
- `target_persona` : Titre du décideur (ex: "VP Sales", "Directeur Commercial")
- `product_category` : Catégorie de produit que le prospect vend (ex: "solution de téléphonie cloud")
- `confidence_score` : 1-5 (1=deviné, 5=trouvé sur site)
- `fallback_level` : Niveau de fallback utilisé
- `reasoning` : Raisonnement (chain-of-thought)

**Variantes d'utilisation** :

| Variante | Description | Méthode | Exemple |
|----------|-------------|---------|---------|
| **Scraping** | Scraper le site du prospect pour trouver l'équipe/leadership | Scrape `/about`, `/team`, `/equipe` | Trouve "Sophie Martin - VP Sales" sur la page équipe |
| **Industry Inference** | Déduire du secteur d'activité | Logique sectorielle | "SaaS B2B" → probablement "VP Sales" ou "Head of Growth" |
| **Company Name Inference** | Deviner du nom de l'entreprise | Analyse du nom | "TechRecruit" → probablement "DRH" ou "Head of Talent" |

**Injection de contexte** : ❌ PAS NÉCESSAIRE

Cet agent est purement analytique. Il n'a pas besoin de savoir qui est votre client ni ce qu'il vend.

**Exemple de code** :
```python
# Agent fondamental (générique)
persona_agent = PersonaExtractorAgent()

# Utilisation sans contexte client
result = persona_agent.run(PersonaExtractorInputSchema(
    company_name="Aircall",
    website="https://aircall.io",
    industry="SaaS",
    website_content=""  # Optionnel : contenu pré-scrapé
))

# Output:
# {
#   "target_persona": "VP Sales",
#   "product_category": "solution de téléphonie cloud pour équipes commerciales",
#   "confidence_score": 5,
#   "fallback_level": 0,
#   "reasoning": "Found 'VP Sales' on about page, product clearly described as cloud phone solution"
# }
```

---

### 2. CompetitorFinder

**Rôle fondamental** : Identifier les concurrents ou outils similaires utilisés par le prospect.

**Ce qu'il analyse** : LE PROSPECT

**Inputs** :
- `company_name`, `website`, `industry`
- `product_category` : (vient de PersonaExtractor)
- `website_content`

**Outputs** :
- `competitor_name` : Nom du concurrent identifié
- `competitor_product_category` : Catégorie du produit concurrent
- `confidence_score`, `fallback_level`, `reasoning`

**Variantes d'utilisation** :

| Variante | Description | Méthode |
|----------|-------------|---------|
| **Direct Mention** | Concurrent mentionné sur le site | Scrape `/customers`, `/integrations` |
| **Industry Standard** | Concurrent standard du secteur | Knowledge base sectorielle |
| **Product Category Match** | Concurrent basé sur la catégorie de produit | Mapping produit → concurrent |

**Injection de contexte** : ⚠️ OPTIONNEL (pour éviter de suggérer votre client comme concurrent)

```python
# Contexte pour éviter de suggérer votre client comme concurrent
client_context = {
    "client_name": "Kaleads",
    "client_products": ["lead generation platform", "B2B prospecting automation"]
}

competitor_agent = CompetitorFinderAgent(client_context=client_context)

# L'agent évitera de suggérer Kaleads comme concurrent
```

---

### 3. PainPointAnalyzer

**Rôle fondamental** : Identifier le problème spécifique que le prospect a, EN LIEN avec ce que votre client vend.

**Ce qu'il analyse** : LE PROSPECT (à travers le prisme du CLIENT)

**Inputs** :
- `company_name`, `website`, `industry`
- `target_persona`, `product_category` (viennent d'autres agents)
- `website_content`

**Outputs** :
- `problem_specific` : Pain point spécifique (format: fragment lowercase sans ponctuation finale)
- `impact_measurable` : Impact mesurable du pain point
- `confidence_score`, `fallback_level`, `reasoning`

**Variantes d'utilisation** :

| Variante | Description | Contexte Client Nécessaire | Exemple |
|----------|-------------|---------------------------|---------|
| **Client Acquisition Pain** | Prospect a besoin de plus de clients | Oui (client vend lead gen) | "difficulté à acquérir de nouveaux prospects qualifiés" |
| **Internal Ops Pain** | Prospect a des problèmes internes | Oui (client vend ops tools) | "processus RH manuels qui consomment 20h/semaine" |
| **Tech Infrastructure Pain** | Prospect a des problèmes techniques | Oui (client vend tech) | "infrastructure cloud non scalable pour gérer la croissance" |

**Injection de contexte** : ✅ OBLIGATOIRE

Le contexte client détermine **quel type de pain point** chercher :

```python
# Exemple 1 : Client vend de la lead generation
client_context = {
    "client_name": "Kaleads",
    "offerings": ["lead generation B2B", "prospecting automation"],
    "pain_solved": "génération de leads B2B qualifiés via l'automatisation",
    "target_industries": ["SaaS", "Consulting", "Agencies"]
}

pain_agent = PainPointAnalyzer(client_context=client_context)

# L'agent va chercher des pain points liés à CLIENT ACQUISITION
# Output possible : "difficulté à acquérir de nouveaux prospects qualifiés"

# Exemple 2 : Client vend des solutions RH
client_context = {
    "client_name": "TalentHub",
    "offerings": ["plateforme de recrutement", "gestion des talents"],
    "pain_solved": "recrutement et gestion RH efficace",
    "target_industries": ["Tech", "Healthcare"]
}

pain_agent = PainPointAnalyzer(client_context=client_context)

# L'agent va chercher des pain points liés à RH
# Output possible : "processus de recrutement manuel qui prend 3 semaines par poste"
```

**Règle Critique** : Le pain point doit TOUJOURS être quelque chose que votre client peut résoudre.

---

### 4. SignalDetector

**Rôle fondamental** : Détecter des signaux d'intention ou triggers events chez le prospect.

**Ce qu'il analyse** : LE PROSPECT (événements factuels)

**Inputs** :
- `company_name`, `website`, `industry`
- `product_category`, `target_persona`
- `website_content`

**Outputs** :
- `specific_signal_1` : Premier signal d'intention (volume élevé)
- `specific_signal_2` : Deuxième signal d'intention (niche)
- `specific_target_1` : Premier ciblage spécifique
- `specific_target_2` : Deuxième ciblage spécifique
- `confidence_score`, `fallback_level`, `reasoning`

**Variantes d'utilisation** :

| Variante | Description | Source | Confiance |
|----------|-------------|--------|-----------|
| **Factual Signals** | Signaux vérifiables | Scrape `/blog`, `/news`, `/press`, `/careers` | 5/5 |
| **Inferred Signals** | Signaux déduits de l'industrie | Knowledge base | 3/5 |
| **Generic Fallback** | Signaux génériques B2B | Templates | 1/5 |

**Exemples de signaux** :

```python
# Factual (confidence_score = 5, trouvé sur le site)
"vient de lever 5M€ en série A selon leur communiqué de presse"
"recrute 3 commerciaux selon leur page carrières"
"vient de lancer une nouvelle offre SaaS selon leur blog"

# Inferred (confidence_score = 3, déduit de l'industrie)
"développe son équipe commerciale dans le secteur SaaS"
"cherche à optimiser sa prospection B2B"

# Generic (confidence_score = 1, fallback)
"cherche à développer son activité commerciale"
"souhaite augmenter son pipeline commercial"
```

**Injection de contexte** : ⚠️ OPTIONNEL (pour filtrer les signaux pertinents)

```python
# Sans contexte : détecte TOUS les signaux
signal_agent = SignalDetector()

# Avec contexte : filtre les signaux pertinents pour le client
client_context = {
    "client_name": "Kaleads",
    "pain_solved": "lead generation",
    "relevant_signals": ["hiring sales", "expansion", "funding", "product launch"]
}

signal_agent = SignalDetector(client_context=client_context)

# L'agent va prioriser les signaux de hiring/expansion (pertinents pour lead gen)
```

**Règle Anti-Hallucination** : Si aucun signal factuel n'est trouvé, utiliser un fallback générique. JAMAIS inventer de chiffres.

---

### 5. SystemMapper

**Rôle fondamental** : Cartographier les systèmes, outils ou processus utilisés par le prospect.

**Ce qu'il analyse** : LE PROSPECT

**Inputs** :
- `company_name`, `website`
- `target_persona`, `specific_target_1`, `specific_target_2`, `problem_specific`
- `website_content`

**Outputs** :
- `system_1`, `system_2`, `system_3` : Trois systèmes/processus identifiés
- `confidence_score`, `fallback_level`, `reasoning`

**Variantes d'utilisation** :

| Variante | Description | Méthode |
|----------|-------------|---------|
| **Tech Stack Detection** | Outils techniques utilisés | Scrape `/integrations`, Wappalyzer-style |
| **Business Process Inference** | Processus métier | Déduit du secteur + persona |
| **Generic Fallback** | Processus standard de l'industrie | Templates sectoriels |

**Injection de contexte** : ⚠️ OPTIONNEL (pour cibler les systèmes pertinents)

```python
# Exemple : Client vend du CRM, on veut savoir quels CRMs le prospect utilise
client_context = {
    "client_name": "MyCRM",
    "competes_with": ["Salesforce", "HubSpot", "Pipedrive"],
    "relevant_systems": ["CRM", "sales tools", "marketing automation"]
}

system_agent = SystemMapper(client_context=client_context)

# L'agent va prioriser la détection de CRMs et outils commerciaux
```

---

### 6. ProofGenerator

**Rôle fondamental** : Générer une preuve sociale (case study, résultat mesurable) pertinente pour le prospect.

**Ce qu'il analyse** : LE CLIENT (ses case studies) + LE PROSPECT (pour matcher)

⚠️ **ATTENTION** : Cet agent est DIFFÉRENT des autres car il analyse principalement le CLIENT, pas le prospect.

**Inputs** :
- `company_name`, `website`, `industry` (du PROSPECT)
- `target_persona`, `problem_specific` (du PROSPECT)
- `website_content` (optionnel, du PROSPECT)

**Outputs** :
- `case_study_result` : Résultat mesurable d'un case study (format: commence par minuscule ou majuscule selon le contexte)
- `confidence_score`, `fallback_level`, `reasoning`

**Variantes d'utilisation** :

| Variante | Description | Source | Confiance | Exemple |
|----------|-------------|--------|-----------|---------|
| **Real Client Case Study** | Case study réelle du CLIENT | Supabase `client_context.case_studies` | 5/5 | "Salesforce France à augmenter son pipeline de 300% en 6 mois" |
| **Adapted Case Study** | Case study adaptée à l'industrie du prospect | Supabase + adaptation | 4/5 | "une entreprise SaaS similaire à tripler son nombre de leads qualifiés" |
| **Generic Proof** | Preuve sociale générique | Templates | 1/5 | "des entreprises similaires à optimiser significativement leur prospection" |
| **Prospect Case Study** | Case study du PROSPECT (ce qu'ILS ont fait) | Scrape `/customers`, `/case-studies` | 3/5 | "aidé TechCo à réduire leurs coûts de 40%" (usage rare) |

**Injection de contexte** : ✅ OBLIGATOIRE

Le contexte client contient les **vraies case studies** :

```python
# Exemple : Client a des vraies case studies
client_context = {
    "client_name": "Kaleads",
    "real_case_studies": [
        {
            "company": "Salesforce France",
            "industry": "SaaS",
            "result": "augmenter son pipeline de 300% en 6 mois",
            "metric": "300% pipeline increase"
        },
        {
            "company": "BNP Paribas",
            "industry": "Finance",
            "result": "générer 500 leads qualifiés par mois",
            "metric": "500 qualified leads/month"
        }
    ]
}

proof_agent = ProofGenerator(client_context=client_context)

# Pour un prospect dans le SaaS
result = proof_agent.run(CaseStudyInputSchema(
    company_name="Aircall",
    industry="SaaS",
    problem_specific="difficulté à acquérir de nouveaux prospects",
))

# Output: "Salesforce France à augmenter son pipeline de 300% en 6 mois"
# (confidence_score=5, fallback_level=0)

# Pour un prospect hors des industries connues
result = proof_agent.run(CaseStudyInputSchema(
    company_name="HealthTech Corp",
    industry="Healthcare",
    problem_specific="prospection manuelle inefficace",
))

# Output: "des entreprises similaires à optimiser significativement leur prospection"
# (confidence_score=1, fallback_level=3, car pas de case study Healthcare)
```

**Usage alternatif : Scraper les case studies du PROSPECT** (rare)

Dans certains cas, on peut vouloir mentionner ce que le prospect a accompli :

```python
# Contexte : On veut complimenter le prospect sur ses propres résultats
client_context = {
    "client_name": "Kaleads",
    "usage_mode": "prospect_achievement"  # Mode alternatif
}

proof_agent = ProofGenerator(client_context=client_context)

# L'agent va scraper `/customers`, `/case-studies` du PROSPECT
# Output possible : "aidé TechCo à augmenter leur productivité de 50%"
```

**Règle Anti-Hallucination** :
- Si `real_case_studies` est fourni → utiliser une vraie case study ou adapter
- Si `real_case_studies` est vide → utiliser un fallback générique
- JAMAIS inventer de fausses entreprises (TechCo, StartupX) ou fausses métriques

---

## 🔄 Injection de Contexte : Standardisation

### Problème Actuel

Actuellement, le contexte est injecté de manière incohérente :
- Certains agents reçoivent un `string` (context_str)
- D'autres reçoivent un `dict` (client_context_dict)
- Le format n'est pas standardisé

### Architecture Cible : Context Standard

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class ClientContext(BaseModel):
    """
    Contexte client standardisé pour injection dans tous les agents.

    Ce contexte contient TOUTES les informations sur le client qui prospecte,
    et permet aux agents de personnaliser leur comportement.
    """

    # Identité
    client_id: str = Field(..., description="UUID du client dans Supabase")
    client_name: str = Field(..., description="Nom du client (ex: 'Kaleads')")

    # Offres
    offerings: List[str] = Field(
        default_factory=list,
        description="Liste des offres/services du client (ex: ['lead generation B2B', 'prospecting automation'])"
    )

    personas: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Liste des personas cibles du client (format Supabase)"
    )

    # Value Proposition
    pain_solved: str = Field(
        default="",
        description="Quel problème le client résout (ex: 'génération de leads B2B qualifiés')"
    )

    value_proposition: str = Field(
        default="",
        description="Proposition de valeur du client"
    )

    # ICP (Ideal Customer Profile)
    target_industries: List[str] = Field(
        default_factory=list,
        description="Industries cibles (ex: ['SaaS', 'Consulting', 'Agencies'])"
    )

    target_company_sizes: List[str] = Field(
        default_factory=list,
        description="Tailles d'entreprises cibles (ex: ['10-50', '50-200'])"
    )

    # Preuves sociales
    real_case_studies: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="""
        Vraies case studies du client. Format:
        [
            {
                "company": "Salesforce France",
                "industry": "SaaS",
                "result": "augmenter son pipeline de 300% en 6 mois",
                "metric": "300% pipeline increase",
                "persona": "VP Sales"
            }
        ]
        """
    )

    # Concurrence
    competitors: List[str] = Field(
        default_factory=list,
        description="Liste des concurrents du client (pour éviter de les suggérer)"
    )

    # Templates
    email_templates: Dict[str, str] = Field(
        default_factory=dict,
        description="Templates d'emails par type (ex: {'cold_outreach': '...', 'follow_up': '...'})"
    )

    # Metadata
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Usage dans les agents
class BaseAgent:
    """Classe de base pour tous les agents."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[ClientContext] = None  # Standardisé !
    ):
        self.client_context = client_context
        # ... reste de l'init

    def _build_context_prompt(self) -> str:
        """
        Construit le prompt de contexte à partir du ClientContext.
        Chaque agent peut adapter ce prompt selon ses besoins.
        """
        if not self.client_context:
            return ""

        return f"""
🎯 CLIENT CONTEXT:
- Client Name: {self.client_context.client_name}
- What Client Sells: {', '.join(self.client_context.offerings)}
- Problem Client Solves: {self.client_context.pain_solved}
- Target Industries: {', '.join(self.client_context.target_industries)}
"""
```

### Migration

```python
# AVANT (incohérent)
persona_agent = PersonaExtractorAgent(client_context="string...")
pain_agent = PainPointAgent(client_context={"client_name": "...", ...})

# APRÈS (standardisé)
from src.models.client_context import ClientContext

# Charger le contexte depuis Supabase
supabase_client = SupabaseClient()
raw_context = supabase_client.load_client_context(client_id)

# Convertir en ClientContext standard
client_context = ClientContext(
    client_id=client_id,
    client_name=raw_context.client_name,
    offerings=[p.get("title", "") for p in raw_context.personas],
    pain_solved=extract_pain_solved(raw_context),
    target_industries=raw_context.target_industries or [],
    real_case_studies=raw_context.case_studies or [],
    competitors=raw_context.competitors or [],
)

# Injecter dans TOUS les agents de manière uniforme
persona_agent = PersonaExtractorAgent(client_context=client_context)
pain_agent = PainPointAgent(client_context=client_context)
proof_agent = ProofGenerator(client_context=client_context)
# etc.
```

---

## 📧 Système de Templates Enrichis

### Principe : Template + Contexte + Exemple = Génération Guidée

Un template seul n'est pas suffisant ! Il faut donner aux agents :

1. **Le template** (structure avec {{placeholders}})
2. **Le contexte du mail** (intention, ton, approche)
3. **Un exemple concret** (email parfait pour un contact type)

#### Exemple de Template Enrichi

```json
{
  "template_name": "cold_outreach_storytelling",
  "template_content": "Bonjour {{first_name}},\n\nJ'ai vu que {{company_name}} {{specific_signal_1}}.\n\nOn a aidé {{case_study_result}}.\n\nSeriez-vous ouvert(e) à un échange?\n\nCordialement,\nL'équipe {{client_name}}",

  "context": {
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
      "Ne pas utiliser de superlatifs ('meilleur', 'révolutionnaire')",
      "Ne pas mentionner le prix"
    ]
  },

  "example": {
    "for_contact": {
      "company_name": "Aircall",
      "first_name": "Sophie",
      "industry": "SaaS",
      "target_persona": "VP Sales"
    },
    "perfect_email": "Bonjour Sophie,\n\nJ'ai vu qu'Aircall recrute 3 commerciaux selon votre page carrières.\n\nOn a aidé Salesforce France à augmenter son pipeline de 300% en 6 mois grâce à l'automatisation de la prospection.\n\nSeriez-vous ouverte à un échange rapide de 15min?\n\nCordialement,\nL'équipe Kaleads",
    "why_it_works": "Signal factuel (hiring), case study réelle avec métrique, CTA simple"
  }
}
```

#### Comment les Agents Utilisent le Template Enrichi

```python
# L'agent reçoit :
# 1. Le template (structure)
# 2. Le contexte (intention, ton, style)
# 3. L'exemple (email parfait pour un contact similaire)

agent_prompt = f"""
You are generating variables for this email template:

{template_content}

CONTEXT & INTENTION:
- Intention: {context.intention}
- Tone: {context.tone}
- Approach: {context.approach}
- Style: {context.style}

DO:
{context.dos}

DON'T:
{context.donts}

EXAMPLE OF PERFECT EMAIL:
For a contact at {example.for_contact.company_name} ({example.for_contact.industry}):

{example.perfect_email}

WHY IT WORKS: {example.why_it_works}

NOW, generate variables for the new prospect following the same quality standard.
"""
```

**Avantages** :
- ✅ Les agents comprennent **l'intention** (pas juste remplir des variables)
- ✅ Le **ton et style** sont guidés par l'exemple
- ✅ Les **bonnes pratiques** sont explicites
- ✅ La **qualité** est plus consistente

### Variables Fondamentales

| Catégorie | Variable | Agent Source | Type |
|-----------|----------|--------------|------|
| **Contact** | `first_name`, `last_name`, `company_name`, `website`, `industry` | Input | Static |
| **Persona** | `target_persona`, `product_category` | PersonaExtractor | Dynamic |
| **Concurrent** | `competitor_name`, `competitor_product_category` | CompetitorFinder | Dynamic |
| **Pain Point** | `problem_specific`, `impact_measurable` | PainPointAnalyzer | Dynamic |
| **Signaux** | `specific_signal_1`, `specific_signal_2`, `specific_target_1`, `specific_target_2` | SignalDetector | Dynamic |
| **Systèmes** | `system_1`, `system_2`, `system_3` | SystemMapper | Dynamic |
| **Preuve** | `case_study_result` | ProofGenerator | Dynamic |
| **Client** | `client_name`, `client_offerings` | ClientContext | Static |

### Templates Enrichis par Use Case

Chaque template doit inclure : **structure + contexte + exemple**

```python
ENRICHED_TEMPLATES = {
    "cold_outreach_signal_focused": {
        "template_content": """Bonjour {{first_name}},

J'ai vu que {{company_name}} {{specific_signal_1}}.

On a aidé {{case_study_result}}.

Seriez-vous ouvert(e) à un échange rapide de 15min?

Cordialement,
{{client_name}}""",

        "context": {
            "intention": "Cold outreach basé sur un signal d'intention",
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
        },

        "example": {
            "for_contact": {
                "company_name": "Aircall",
                "first_name": "Sophie",
                "industry": "SaaS"
            },
            "perfect_email": """Bonjour Sophie,

J'ai vu qu'Aircall recrute 3 commerciaux selon votre page carrières.

On a aidé Salesforce France à augmenter son pipeline de 300% en 6 mois.

Seriez-vous ouverte à un échange rapide de 15min?

Cordialement,
L'équipe Kaleads""",
            "why_it_works": "Signal factuel + case study réelle + CTA court"
        }
    },

    "cold_outreach_pain_focused": {
        "template_content": """Bonjour {{first_name}},

En tant que {{target_persona}} chez {{company_name}}, vous faites probablement face à {{problem_specific}}.

Cela peut avoir un impact sur {{impact_measurable}}.

On a aidé {{case_study_result}}.

Seriez-vous ouvert(e) à en discuter?

Cordialement,
{{client_name}}""",

        "context": {
            "intention": "Cold outreach basé sur l'empathie du pain point",
            "tone": "Empathique, consultatif, pas agressif",
            "approach": "Pain point + Impact + Solution (via case study)",
            "style": "Moyen (100-120 mots), structure problème-solution",
            "dos": [
                "Identifier un vrai pain point du prospect",
                "Quantifier l'impact si possible",
                "Proposer une discussion, pas une démo"
            ],
            "donts": [
                "Ne pas inventer de faux problèmes",
                "Ne pas être condescendant",
                "Ne pas présumer que le prospect a ce problème"
            ]
        },

        "example": {
            "for_contact": {
                "company_name": "Doctolib",
                "first_name": "Thomas",
                "industry": "HealthTech"
            },
            "perfect_email": """Bonjour Thomas,

En tant que VP Sales chez Doctolib, vous faites probablement face à la difficulté de qualifier rapidement les milliers de praticiens qui visitent votre site.

Cela peut ralentir votre cycle de vente et limiter la croissance de votre équipe commerciale.

On a aidé Salesforce France à augmenter son pipeline de 300% en automatisant la qualification des prospects.

Seriez-vous ouvert à en discuter?

Cordialement,
L'équipe Kaleads""",
            "why_it_works": "Pain point spécifique au secteur + impact quantifié + case study pertinente"
        }
    },

    "cold_outreach_competitor_focused": {
        "template_content": """Bonjour {{first_name}},

J'ai remarqué que {{company_name}} utilise {{competitor_name}}.

Nous aidons des entreprises qui utilisent {{competitor_name}} à {{pain_solved}}.

{{case_study_result}}

Seriez-vous ouvert(e) à comparer les approches?

Cordialement,
{{client_name}}""",

        "context": {
            "intention": "Cold outreach basé sur l'usage d'un concurrent",
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
                "Ne pas dire 'on est mieux que X'",
                "Ne pas forcer un switch immédiat"
            ]
        },

        "example": {
            "for_contact": {
                "company_name": "Payfit",
                "first_name": "Marie",
                "industry": "HRTech"
            },
            "perfect_email": """Bonjour Marie,

J'ai remarqué que Payfit utilise HubSpot pour votre prospection.

Nous aidons des entreprises qui utilisent HubSpot à automatiser davantage leur qualification de leads avec de l'enrichissement de données en temps réel.

On a aidé Aircall à réduire leur coût d'acquisition client de 40% grâce à cette approche.

Seriez-vous ouverte à comparer les approches?

Cordialement,
L'équipe Kaleads""",
            "why_it_works": "Respect du concurrent + valeur ajoutée claire + métrique forte"
        }
    }
}
```

---

## 🏗️ Architecture Modulaire

### Système de Composition

Les agents doivent pouvoir se composer pour créer différents workflows :

```python
from typing import List, Dict, Any
from src.agents.base import BaseAgent
from src.models.client_context import ClientContext

class AgentPipeline:
    """
    Pipeline d'agents composable.

    Permet de créer différents workflows en composant les agents.
    """

    def __init__(
        self,
        agents: List[BaseAgent],
        client_context: ClientContext,
        enable_scraping: bool = True
    ):
        self.agents = agents
        self.client_context = client_context
        self.enable_scraping = enable_scraping

    def run(self, contact: Dict[str, Any], template: str) -> Dict[str, Any]:
        """
        Exécute le pipeline d'agents et génère l'email.

        Args:
            contact: Informations du contact prospect
            template: Template d'email avec {{variables}}

        Returns:
            Dict avec email_content et toutes les variables
        """
        variables = {
            "first_name": contact["first_name"],
            "company_name": contact["company_name"],
            # ... autres variables statiques
        }

        # Exécuter chaque agent séquentiellement
        for agent in self.agents:
            agent_result = agent.run(
                contact=contact,
                previous_variables=variables,
                client_context=self.client_context
            )
            variables.update(agent_result)

        # Rendre le template
        email_content = render_template(template, variables)

        return {
            "email_content": email_content,
            **variables
        }


# Exemple : Pipeline pour cold outreach basique
basic_pipeline = AgentPipeline(
    agents=[
        PersonaExtractorAgent(),
        SignalDetectorAgent(),
        ProofGeneratorAgent(),
    ],
    client_context=client_context
)

# Exemple : Pipeline pour outreach pain-focused
pain_focused_pipeline = AgentPipeline(
    agents=[
        PersonaExtractorAgent(),
        PainPointAnalyzerAgent(),
        ProofGeneratorAgent(),
    ],
    client_context=client_context
)

# Exemple : Pipeline complet (tous les agents)
full_pipeline = AgentPipeline(
    agents=[
        PersonaExtractorAgent(),
        CompetitorFinderAgent(),
        PainPointAnalyzerAgent(),
        SignalDetectorAgent(),
        SystemMapperAgent(),
        ProofGeneratorAgent(),
    ],
    client_context=client_context
)
```

---

## 🎯 Cas d'Usage Concrets

### Use Case 1 : Lead Generation Agency (Kaleads)

**Contexte** :
- Client vend : "lead generation B2B automatisée"
- Problème résolu : "manque de prospects qualifiés"
- ICP : SaaS, Consulting, Agencies
- Case studies : Salesforce (+300% pipeline), BNP Paribas (500 leads/mois)

**Configuration des agents** :

```python
client_context = ClientContext(
    client_id="kaleads-uuid",
    client_name="Kaleads",
    offerings=["lead generation B2B", "prospection automatisée", "enrichissement de données"],
    pain_solved="génération de leads B2B qualifiés via l'automatisation",
    target_industries=["SaaS", "Consulting", "Agencies", "Tech"],
    real_case_studies=[
        {
            "company": "Salesforce France",
            "industry": "SaaS",
            "result": "augmenter son pipeline de 300% en 6 mois"
        }
    ]
)

# Agents configurés avec ce contexte
pain_agent = PainPointAnalyzer(client_context=client_context)
# → Va chercher des pain points liés à CLIENT ACQUISITION

proof_agent = ProofGenerator(client_context=client_context)
# → Va utiliser la case study Salesforce si prospect est SaaS

# Exemple d'output
pain_result = "difficulté à acquérir suffisamment de prospects qualifiés pour alimenter les ventes"
proof_result = "Salesforce France à augmenter son pipeline de 300% en 6 mois"
```

---

### Use Case 2 : HR Tech Platform (TalentHub)

**Contexte** :
- Client vend : "plateforme de recrutement et gestion des talents"
- Problème résolu : "processus de recrutement manuel et inefficace"
- ICP : Tech, Healthcare, Finance
- Case studies : AXA (-50% time-to-hire), Doctolib (500 embauches/an)

**Configuration des agents** :

```python
client_context = ClientContext(
    client_id="talenthub-uuid",
    client_name="TalentHub",
    offerings=["plateforme de recrutement", "gestion des talents", "onboarding automatisé"],
    pain_solved="recrutement et gestion RH efficace",
    target_industries=["Tech", "Healthcare", "Finance"],
    real_case_studies=[
        {
            "company": "AXA",
            "industry": "Finance",
            "result": "réduire leur time-to-hire de 50%"
        }
    ]
)

pain_agent = PainPointAnalyzer(client_context=client_context)
# → Va chercher des pain points liés à RH/RECRUTEMENT

proof_agent = ProofGenerator(client_context=client_context)
# → Va utiliser la case study AXA si prospect est Finance

# Exemple d'output
pain_result = "processus de recrutement manuel qui prend 3 semaines par poste"
proof_result = "AXA à réduire leur time-to-hire de 50%"
```

---

### Use Case 3 : DevOps Platform (CloudOps)

**Contexte** :
- Client vend : "plateforme DevOps pour CI/CD et infrastructure cloud"
- Problème résolu : "déploiements lents et infrastructure non scalable"
- ICP : Tech companies, Startups
- Case studies : Stripe (10x deployments/day), Netflix (99.99% uptime)

**Configuration des agents** :

```python
client_context = ClientContext(
    client_id="cloudops-uuid",
    client_name="CloudOps",
    offerings=["CI/CD automation", "infrastructure as code", "cloud orchestration"],
    pain_solved="déploiements rapides et infrastructure scalable",
    target_industries=["Tech", "SaaS", "E-commerce"],
    real_case_studies=[
        {
            "company": "Stripe",
            "industry": "FinTech",
            "result": "passer de 2 à 20 déploiements par jour"
        }
    ]
)

pain_agent = PainPointAnalyzer(client_context=client_context)
# → Va chercher des pain points liés à TECH/INFRASTRUCTURE

proof_agent = ProofGenerator(client_context=client_context)
# → Va utiliser la case study Stripe si prospect est FinTech/Tech

# Exemple d'output
pain_result = "déploiements manuels qui prennent 4h et génèrent des incidents"
proof_result = "Stripe à passer de 2 à 20 déploiements par jour"
```

---

## 📊 Matrice de Compatibilité Agent × Context

| Agent | Nécessite Contexte? | Type de Contexte | Impact |
|-------|---------------------|------------------|--------|
| PersonaExtractor | ❌ Non | N/A | Aucun (purement analytique) |
| CompetitorFinder | ⚠️ Optionnel | `client_name`, `offerings`, `competitors` | Évite de suggérer le client comme concurrent |
| PainPointAnalyzer | ✅ Obligatoire | `pain_solved`, `offerings`, `target_industries` | Détermine le TYPE de pain point cherché |
| SignalDetector | ⚠️ Optionnel | `pain_solved`, `relevant_signals` | Filtre les signaux pertinents |
| SystemMapper | ⚠️ Optionnel | `relevant_systems`, `competes_with` | Priorise certains systèmes |
| ProofGenerator | ✅ Obligatoire | `real_case_studies`, `client_name` | Source des case studies |

---

## 🔄 Plan de Migration v2.x → v3.0

### Phase 1 : Standardisation du Contexte (1 semaine)

**Objectif** : Tous les agents utilisent le même format `ClientContext`

**Actions** :
1. Créer `src/models/client_context.py` avec la classe `ClientContext`
2. Mettre à jour `SupabaseClient.load_client_context()` pour retourner un `ClientContext`
3. Refactoriser tous les agents pour accepter `ClientContext` au lieu de `str` ou `dict`
4. Mettre à jour `n8n_optimized_api.py` pour utiliser le nouveau format

**Code** :
```python
# Créer src/models/client_context.py
# Implémenter ClientContext avec Pydantic

# Mettre à jour chaque agent
class PersonaExtractorAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[ClientContext] = None  # NOUVEAU
    ):
        self.client_context = client_context
        # ...
```

**Tests** :
- Vérifier que tous les agents acceptent `ClientContext`
- Tester backward compatibility (anciens appels fonctionnent encore)
- Valider que les prompts sont bien générés

---

### Phase 2 : Clarification des Rôles (2 semaines)

**Objectif** : Chaque agent a un rôle clair et unique

**Actions** :
1. **PainPointAnalyzer** : Rendre explicite que le pain point dépend du `pain_solved` du client
2. **ProofGenerator** : Séparer les deux usages (client case studies vs prospect achievements)
3. **SignalDetector** : Renforcer l'anti-hallucination (fallback si aucun signal factuel)
4. **CompetitorFinder** : Ajouter logique pour éviter de suggérer le client

**Code** :
```python
# PainPointAnalyzer : adapter le prompt selon pain_solved
def _build_pain_prompt(self) -> str:
    if not self.client_context:
        return "Identify any business problem"

    pain_type = classify_pain_type(self.client_context.pain_solved)

    if pain_type == "client_acquisition":
        return "Focus on CLIENT ACQUISITION, LEAD GENERATION, SALES GROWTH"
    elif pain_type == "hr_recruitment":
        return "Focus on HR, RECRUITMENT, TALENT MANAGEMENT"
    elif pain_type == "tech_infrastructure":
        return "Focus on TECH INFRASTRUCTURE, DEVOPS, SCALABILITY"
    # etc.

# ProofGenerator : mode explicite
class ProofGenerator:
    def __init__(
        self,
        client_context: Optional[ClientContext] = None,
        mode: Literal["client_case_studies", "prospect_achievements"] = "client_case_studies"
    ):
        self.mode = mode
        # ...

    def run(self, input_data):
        if self.mode == "client_case_studies":
            # Utiliser client_context.real_case_studies
            return self._use_client_case_studies()
        else:
            # Scraper le site du prospect
            return self._scrape_prospect_achievements()
```

**Tests** :
- PainPointAnalyzer : Tester avec différents `pain_solved` (lead gen, HR, tech)
- ProofGenerator : Tester les deux modes (client vs prospect)
- Valider que les outputs sont cohérents

---

### Phase 3 : Système de Composition (3 semaines)

**Objectif** : Agents composables en pipelines

**Actions** :
1. Créer `src/pipelines/agent_pipeline.py` avec la classe `AgentPipeline`
2. Définir des pipelines pré-configurés (`basic`, `pain_focused`, `full`)
3. Mettre à jour l'API pour accepter un `pipeline_type` paramètre
4. Créer des templates adaptatifs par pipeline

**Code** :
```python
# src/pipelines/agent_pipeline.py
class AgentPipeline:
    # ... (voir section Architecture Modulaire)

# src/pipelines/presets.py
PIPELINE_PRESETS = {
    "basic": ["persona", "signal", "proof"],
    "pain_focused": ["persona", "pain", "proof"],
    "competitor_focused": ["persona", "competitor", "proof"],
    "full": ["persona", "competitor", "pain", "signal", "system", "proof"],
}

# API endpoint
@app.post("/api/v3/generate-email")
async def generate_email_v3(
    request: GenerateEmailRequest,
    pipeline_type: str = "basic"  # NOUVEAU
):
    pipeline = create_pipeline(pipeline_type, client_context)
    result = pipeline.run(contact, template)
    return result
```

**Tests** :
- Tester chaque preset de pipeline
- Valider que les variables sont correctement propagées
- Mesurer le coût et le temps par pipeline

---

### Phase 4 : Templates Dynamiques (2 semaines)

**Objectif** : Templates stockés dans Supabase, éditables par le client

**Actions** :
1. Ajouter table `email_templates` dans Supabase
2. Créer interface pour gérer les templates (UI ou API)
3. Charger les templates depuis Supabase au lieu du code
4. Permettre au client de créer des templates custom

**Schema Supabase** :
```sql
CREATE TABLE email_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID REFERENCES clients(id),
    template_name VARCHAR(100) NOT NULL,
    template_content TEXT NOT NULL,
    required_variables TEXT[], -- Liste des variables nécessaires
    recommended_pipeline VARCHAR(50), -- Pipeline recommandé
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(client_id, template_name)
);

-- Exemple d'insertion
INSERT INTO email_templates (client_id, template_name, template_content, required_variables, recommended_pipeline)
VALUES (
    'kaleads-uuid',
    'cold_outreach_generic',
    'Bonjour {{first_name}},\n\nJ''ai vu que {{company_name}} {{specific_signal_1}}...',
    ARRAY['first_name', 'company_name', 'specific_signal_1', 'case_study_result'],
    'basic'
);
```

**API** :
```python
@app.get("/api/v3/templates")
async def list_templates(client_id: str):
    """Liste les templates du client."""
    supabase = SupabaseClient()
    templates = supabase.get_client_templates(client_id)
    return templates

@app.post("/api/v3/templates")
async def create_template(template: EmailTemplate):
    """Crée un nouveau template."""
    supabase = SupabaseClient()
    result = supabase.create_template(template)
    return result
```

**Tests** :
- CRUD complet sur les templates
- Validation des variables requises
- Génération d'email avec template custom

---

## 🎯 Métriques de Succès

### Pour Évaluer la Refonte

| Métrique | v2.x (Actuel) | v3.0 (Cible) | Amélioration |
|----------|---------------|--------------|--------------|
| **Réutilisabilité** | Agents liés à Kaleads | Agents génériques | 100% réutilisables |
| **Flexibilité** | 1 use case (lead gen) | N use cases | Infinie |
| **Maintenabilité** | Contexte incohérent | Contexte standardisé | +80% |
| **Temps d'onboarding nouveau client** | 2 jours (code custom) | 1h (config Supabase) | **96% plus rapide** |
| **Templates disponibles** | 1 hardcodé | N éditables | Infini |
| **Clarté du code** | Logique mélangée | Séparation claire | +90% lisibilité |

---

## 📚 Documentation pour Développeurs

### Comment Ajouter un Nouvel Agent?

1. **Créer la classe d'agent** :
```python
# src/agents/my_new_agent.py
from src.agents.base import BaseAgent
from src.models.client_context import ClientContext

class MyNewAgent(BaseAgent):
    """
    Description du rôle fondamental de l'agent.

    Ce qu'il analyse : PROSPECT ou CLIENT
    Outputs : ...
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[ClientContext] = None
    ):
        super().__init__(api_key, model, enable_scraping, client_context)
        # ... init spécifique

    def run(self, input_data: MyInputSchema) -> MyOutputSchema:
        # ... logique de l'agent
        pass
```

2. **Définir les schemas** :
```python
# src/schemas/my_new_agent_schemas.py
class MyInputSchema(BaseIOSchema):
    # ... inputs
    pass

class MyOutputSchema(BaseIOSchema):
    # ... outputs
    pass
```

3. **Ajouter aux pipelines** :
```python
# src/pipelines/presets.py
PIPELINE_PRESETS["my_pipeline"] = ["persona", "my_new_agent", "proof"]
```

4. **Tester** :
```python
# tests/test_my_new_agent.py
def test_my_new_agent():
    agent = MyNewAgent(client_context=test_context)
    result = agent.run(test_input)
    assert result.expected_field == "expected_value"
```

---

### Comment Onboarder un Nouveau Client?

1. **Créer le client dans Supabase** :
```sql
INSERT INTO clients (id, name, created_at)
VALUES ('new-client-uuid', 'NewClient Corp', NOW());
```

2. **Configurer le contexte client** :
```sql
INSERT INTO client_contexts (
    client_id,
    offerings,
    pain_solved,
    target_industries,
    real_case_studies
) VALUES (
    'new-client-uuid',
    '["service A", "service B"]'::jsonb,
    'problème résolu par le client',
    '["Industry1", "Industry2"]'::jsonb,
    '[{"company": "ClientX", "result": "résultat mesurable"}]'::jsonb
);
```

3. **Créer les personas cibles** :
```sql
INSERT INTO personas (client_id, title, description)
VALUES
    ('new-client-uuid', 'VP Sales', 'Decision maker for sales tools'),
    ('new-client-uuid', 'Head of Marketing', 'Decision maker for marketing tools');
```

4. **Créer les templates d'email** :
```sql
INSERT INTO email_templates (client_id, template_name, template_content)
VALUES (
    'new-client-uuid',
    'cold_outreach',
    'Bonjour {{first_name}},...'
);
```

5. **Tester l'API** :
```bash
curl -X POST http://localhost:20001/api/v3/generate-email \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "new-client-uuid",
    "contact": {
      "company_name": "Test Corp",
      "first_name": "John",
      "website": "https://testcorp.com"
    },
    "pipeline_type": "basic"
  }'
```

**Temps estimé** : 1 heure (vs 2 jours actuellement)

---

## 🚀 Conclusion

Cette refonte architecturale permet de :

✅ **Agents réutilisables** : Un seul codebase pour tous les clients
✅ **Flexibilité maximale** : Supporte N use cases (lead gen, HR tech, DevOps, etc.)
✅ **Onboarding rapide** : Nouveau client en 1h (vs 2 jours)
✅ **Maintenabilité** : Contexte standardisé, rôles clairs
✅ **Scalabilité** : Composition de pipelines, templates éditables

La philosophie **Agents Fondamentaux + Injection de Contexte** est la clé pour construire un système pérenne et évolutif.

---

*Document généré le 14 novembre 2025*
*Version: 3.0.0 (Refonte architecturale)*
