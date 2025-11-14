# Implementation Log - v3.0 Refonte Architecturale

**Date de début** : 14 novembre 2025
**Status** : Phase 1 en cours (Standardisation du Contexte)

---

## ✅ Tâches Terminées

### 1. Mise à jour des Documents (14 nov 2025)

**Fichiers créés/modifiés** :
- `ARCHITECTURE_FONDAMENTALE.md` : +400 lignes
  - Ajout du concept **Templates Enrichis** (template + contexte + exemple)
  - Détails sur les 6 agents fondamentaux
  - Exemples de templates enrichis par use case
- `PLAN_ACTION_V3.md` : +600 lignes
  - Plan détaillé en 4 phases (8 semaines)
  - Code complet pour chaque phase
  - Tests et validation
  - Checklist complète

**Concept clé ajouté** : **Template + Contexte + Exemple = Génération Guidée**

Au lieu d'envoyer juste un template vide, on envoie :
1. **Le template** : Structure avec `{{variables}}`
2. **Le contexte** : Intention, ton, approche, style, dos/donts
3. **Un exemple parfait** : Email concret pour un contact type qui montre aux agents ce qu'on attend

**Exemple de template enrichi** :
```json
{
  "template_content": "Bonjour {{first_name}},...",
  "context": {
    "intention": "Cold outreach pour générer un meeting",
    "tone": "Professionnel mais friendly",
    "approach": "Signal-focused + Social proof",
    "style": "Court (< 100 mots)",
    "dos": ["Utiliser un signal factuel", "Mentionner une vraie case study"],
    "donts": ["Pas de pitch produit", "Pas de superlatifs"]
  },
  "example": {
    "for_contact": {"company_name": "Aircall", "first_name": "Sophie"},
    "perfect_email": "Bonjour Sophie,\n\nJ'ai vu qu'Aircall recrute 3 commerciaux...",
    "why_it_works": "Signal factuel + case study réelle + CTA simple"
  }
}
```

---

### 2. Création du Modèle ClientContext (14 nov 2025)

**Fichiers créés** :
- `src/models/__init__.py`
- `src/models/client_context.py` : ~500 lignes

**Classes créées** :

#### `CaseStudy`
Représente une vraie case study du client.

```python
CaseStudy(
    company="Salesforce France",
    industry="SaaS",
    result="augmenter son pipeline de 300% en 6 mois",
    metric="300% pipeline increase",
    persona="VP Sales"
)
```

Méthodes utiles :
- `to_short_string()` → "Salesforce France à augmenter son pipeline de 300%"
- `to_detailed_string()` → "Salesforce France (SaaS) à augmenter son pipeline..."

#### `TemplateContext`
Contexte et guidelines pour un template d'email.

```python
TemplateContext(
    intention="Cold outreach pour générer un meeting",
    tone="Professionnel mais friendly",
    approach="Signal-focused + Social proof",
    style="Court (< 100 mots)",
    dos=["Mentionner un signal factuel", ...],
    donts=["Pas de pitch produit", ...]
)
```

Méthodes utiles :
- `to_prompt_string()` → Formatted string for agent prompts

#### `TemplateExample`
Un exemple parfait d'email pour un contact type.

```python
TemplateExample(
    for_contact={"company_name": "Aircall", "first_name": "Sophie"},
    perfect_email="Bonjour Sophie,\n\n...",
    why_it_works="Signal factuel + case study réelle + CTA simple"
)
```

Méthodes utiles :
- `to_prompt_string()` → Formatted example for agents

#### `ClientContext` ⭐
**Le modèle central de v3.0**. Contient TOUTES les informations sur un client.

**Champs** :
- **Identity** : `client_id`, `client_name`
- **Offerings** : `offerings[]`, `personas[]`
- **Value Proposition** : `pain_solved`, `value_proposition`
- **ICP** : `target_industries[]`, `target_company_sizes[]`, `target_regions[]`
- **Social Proof** : `real_case_studies[]`, `testimonials[]`
- **Competition** : `competitors[]`
- **Templates** : `email_templates{}`
- **Metadata** : `created_at`, `updated_at`

**Méthodes utiles** :
- `get_offerings_str(limit=3)` → "lead generation B2B, prospecting automation"
- `get_target_industries_str()` → "SaaS, Consulting, Agencies"
- `has_real_case_studies()` → bool
- `find_case_study_by_industry("SaaS")` → CaseStudy ou None
- `get_best_case_study(prospect_industry)` → Best matching case study
- `get_template(template_name)` → Template dict
- `to_context_prompt()` → Formatted string for agent prompts

**Exemple d'utilisation** :
```python
from src.models.client_context import ClientContext, CaseStudy

context = ClientContext(
    client_id="kaleads-uuid",
    client_name="Kaleads",
    offerings=["lead generation B2B", "prospecting automation"],
    pain_solved="génération de leads B2B qualifiés via l'automatisation",
    target_industries=["SaaS", "Consulting"],
    real_case_studies=[
        CaseStudy(
            company="Salesforce France",
            industry="SaaS",
            result="augmenter son pipeline de 300%"
        )
    ]
)

# Utiliser dans un agent
from src.agents.pain_point_agent import PainPointAgent

agent = PainPointAgent(client_context=context)
# L'agent va adapter son comportement selon le pain_solved
```

---

### 3. Mise à jour de SupabaseClient (14 nov 2025)

**Fichier modifié** : `src/providers/supabase_client.py`

**Méthode ajoutée** : `load_client_context_v3(client_id: str) -> ClientContextV3`

**Ce que fait la méthode** :
1. ✅ Charge les données client depuis `client_contexts` table
2. ✅ Extrait les personas et offerings
3. ✅ Extrait `pain_solved` (priorité : explicit > persona > infer from name)
4. ✅ Extrait l'ICP (industries, company sizes, regions)
5. ✅ Charge les **case studies** depuis table `case_studies` (ou fallback sur `reference_clients`)
6. ✅ Extrait les **competitors**
7. ✅ Charge les **email templates** avec contexte et exemple depuis table `email_templates`
8. ✅ Construit et retourne un `ClientContextV3` complet

**Méthodes auxiliaires ajoutées** :
- `_extract_pain_solved(data, personas)` : Extrait le pain_solved avec fallback
- `_infer_pain_solved(client_name)` : Devine le pain_solved depuis le nom du client
  - "kaleads" / "lead" → génération de leads
  - "sales" / "vente" → optimisation des ventes
  - "talent" / "recruit" / "rh" → recrutement et RH
  - "devops" / "cloud" → infrastructure et déploiements
  - "marketing" → automatisation marketing
  - Autre → efficacité opérationnelle
- `_get_mock_context_v3(client_id)` : Context mock pour les tests

**Gestion des erreurs** :
- ✅ Graceful degradation si tables n'existent pas encore (case_studies, email_templates)
- ✅ Fallback sur mock context si erreur
- ✅ Skip invalid case studies plutôt que crash

**Exemple d'utilisation** :
```python
from src.providers.supabase_client import SupabaseClient

supabase = SupabaseClient()
context = supabase.load_client_context_v3("kaleads-uuid")

print(context.client_name)  # "Kaleads"
print(context.get_offerings_str())  # "lead generation B2B, prospecting automation"
print(context.pain_solved)  # "génération de leads B2B qualifiés..."
print(context.has_real_case_studies())  # True

# Trouver une case study pour un prospect SaaS
cs = context.find_case_study_by_industry("SaaS")
if cs:
    print(cs.to_short_string())  # "Salesforce France à augmenter son pipeline de 300%"

# Obtenir le template enrichi
template = context.get_template("cold_outreach_signal_focused")
if template:
    print(template["template_content"])  # Template avec {{variables}}
    print(template["context"].to_prompt_string())  # Context formaté
    print(template["example"].to_prompt_string())  # Exemple formaté
```

---

---

### 4. Intégration de Tavily pour recherches web (14 nov 2025)

**Fichiers créés** :
- `src/providers/tavily_client.py` : ~350 lignes
- `.env.example` : Ajout de TAVILY_API_KEY

**Qu'est-ce que Tavily ?**

Tavily est un moteur de recherche AI qui fournit aux agents des informations **factuelles et à jour** depuis le web. C'est comme donner aux agents un accès à Google, mais avec des réponses structurées.

**Clé API fournie** : `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`

**Méthodes disponibles** :

1. **`search(query, max_results=5)`** : Recherche générale
   ```python
   results = tavily.search("Who are the competitors of Salesforce?")
   print(results["answer"])  # "The main competitors include HubSpot, Microsoft..."
   ```

2. **`search_competitors(company_name, industry)`** : Trouve les concurrents
   ```python
   competitors = tavily.search_competitors("Aircall", "SaaS")
   # ["Talkdesk", "Dialpad", "RingCentral"]
   ```

3. **`search_company_news(company_name, months=3)`** : News récentes
   ```python
   news = tavily.search_company_news("Aircall")
   # [{"title": "Aircall raises $120M", "url": "...", "content": "..."}]
   ```

4. **`search_tech_stack(company_name, website)`** : Tech stack
   ```python
   tech = tavily.search_tech_stack("Aircall")
   # ["Salesforce", "HubSpot", "AWS", "React"]
   ```

5. **`quick_fact_check(statement)`** : Vérification de faits
   ```python
   check = tavily.quick_fact_check("Aircall raised $5M in 2024")
   # {"verified": False, "confidence": 0.8, "explanation": "..."}
   ```

**Usage dans les agents** :

Les agents décident **eux-mêmes** quand utiliser Tavily :

```python
from src.providers.tavily_client import get_tavily_client

class CompetitorFinderAgent:
    def __init__(self, client_context=None, enable_tavily=True):
        self.tavily = get_tavily_client() if enable_tavily else None

    def run(self, input_data):
        # Agent décide si Tavily est nécessaire
        if self.tavily and self.tavily.enabled:
            # Recherche web pour trouver des concurrents
            competitors = self.tavily.search_competitors(
                company_name=input_data.company_name,
                industry=input_data.industry
            )
            # Utilise les résultats...
        else:
            # Fallback sur logique sans web search
            pass
```

**Agents qui bénéficient de Tavily** :

| Agent | Usage Tavily | Bénéfice |
|-------|--------------|----------|
| **CompetitorFinder** | `search_competitors()` | Trouve les vrais concurrents au lieu de deviner |
| **SignalDetector** | `search_company_news()` | Détecte les vrais signaux (funding, hiring, launch) |
| **SystemMapper** | `search_tech_stack()` | Identifie les outils utilisés par le prospect |
| **ProofGenerator** | `search()` | Vérifie les case studies (fact-checking) |

**Graceful degradation** :

Si Tavily n'est pas configuré :
- Les agents fonctionnent quand même (fallback sur logique sans web)
- Warning dans les logs : `"Web search disabled (Tavily not configured)"`
- Pas de crash, juste moins d'information

---

## 🚧 Tâches en Cours

### 5. Refactoriser les agents pour accepter ClientContext (À faire)

**Objectif** : Mettre à jour tous les agents pour qu'ils acceptent `ClientContext` au lieu de `str` ou `dict`.

**Agents à refactoriser** :
- [ ] `PersonaExtractorAgent` (actuellement pas besoin de contexte)
- [ ] `CompetitorFinderAgent` (contexte optionnel pour éviter le client comme concurrent)
- [ ] `PainPointAgent` ⚠️ **CRITIQUE** (contexte obligatoire pour déterminer le type de pain)
- [ ] `SignalDetectorAgent` (contexte optionnel pour filtrer les signaux pertinents)
- [ ] `SystemMapperAgent` (contexte optionnel pour cibler les systèmes)
- [ ] `ProofGenerator` (ex-CaseStudyAgent) ⚠️ **CRITIQUE** (contexte obligatoire pour case studies)

**Pattern à suivre** :
```python
class MyAgent:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        enable_scraping: bool = True,
        client_context: Optional[ClientContext] = None  # NOUVEAU
    ):
        self.client_context = client_context

        # Construire le prompt selon le contexte
        if client_context:
            context_prompt = client_context.to_context_prompt()
            background.append(context_prompt)

        # ... reste de l'init
```

---

### 5. Mettre à jour l'API (À faire)

**Fichier** : `src/api/n8n_optimized_api.py`

**Changements nécessaires** :
- Remplacer `load_client_context()` par `load_client_context_v3()`
- Passer le `ClientContext` aux agents au lieu de `str` ou `dict`
- Supprimer la construction manuelle du `context_str` et `client_context_dict`

**Avant** :
```python
raw_context = supabase.load_client_context(client_id)
context_str = f"🎯 CRITICAL CONTEXT...\n- Client: {raw_context.client_name}\n..."
client_context_dict = {"client_name": raw_context.client_name, ...}

persona_agent = PersonaExtractorAgent(client_context=context_str)
pain_agent = PainPointAgent(client_context=client_context_dict)
```

**Après** :
```python
context = supabase.load_client_context_v3(client_id)

persona_agent = PersonaExtractorAgent(client_context=context)
pain_agent = PainPointAgent(client_context=context)
proof_agent = ProofGenerator(client_context=context, mode="client_case_studies")
```

---

### 6. Créer les tests unitaires (À faire)

**Fichiers à créer** :
- `tests/test_client_context.py` : Tests pour les modèles
- `tests/test_supabase_client_v3.py` : Tests pour load_client_context_v3()
- `tests/test_agents_with_context.py` : Tests des agents avec ClientContext

---

## 📊 Métriques

| Métrique | v2.x | v3.0 (actuel) | Objectif |
|----------|------|---------------|----------|
| **Lignes de code ajoutées** | - | ~1500 | - |
| **Fichiers créés** | - | 4 | - |
| **Fichiers modifiés** | - | 3 | - |
| **Documentation** | 0 pages | 2 guides complets | 2+ |
| **Tests coverage** | 60% | À faire | 85% |
| **Agents refactorisés** | 0/6 | 0/6 | 6/6 |

---

## 🎯 Prochaines Étapes

1. **Refactoriser PainPointAgent** (priorité haute)
   - Implémenter la classification automatique du type de pain (lead gen, HR, tech, ops)
   - Générer les instructions dynamiquement selon `pain_solved`
   - Tester avec différents contextes clients

2. **Refactoriser ProofGenerator** (priorité haute)
   - Renommer `CaseStudyAgent` → `ProofGenerator`
   - Implémenter les deux modes : `client_case_studies` et `prospect_achievements`
   - Utiliser `context.real_case_studies` pour les vraies case studies
   - Anti-hallucination : fallback générique si pas de case studies

3. **Refactoriser les autres agents** (priorité moyenne)
   - PersonaExtractor, Competitor, Signal, System
   - Adapter pour accepter ClientContext

4. **Mettre à jour l'API** (priorité haute)
   - Utiliser `load_client_context_v3()` partout
   - Tester la génération end-to-end

5. **Tests** (priorité haute)
   - Tests unitaires pour tous les modèles
   - Tests d'intégration pour la génération complète

---

## 💡 Insights & Décisions

### Pourquoi "Templates Enrichis" ?

**Problème initial** : Quand on envoie juste un template avec des `{{variables}}`, les agents ne comprennent pas :
- Le **ton** attendu (professionnel ? casual ? direct ?)
- L'**approche** (pain-focused ? signal-focused ? competitor-focused ?)
- Les **bonnes pratiques** (court ? long ? avec métriques ?)

**Solution** : Enrichir chaque template avec :
1. **Contexte** (intention, ton, approche, style, dos/donts)
2. **Exemple parfait** (email concret qui montre ce qu'on attend)

Cela permet aux agents de générer des variables **cohérentes avec le style** du template, pas juste de remplir des champs.

### Pourquoi ClientContext standardisé ?

**Problème initial** : Le contexte client était injecté de manière incohérente :
- PersonaAgent recevait un `string`
- PainPointAgent recevait un `dict`
- Format différent pour chaque agent

**Solution** : Une seule classe `ClientContext` utilisée par TOUS les agents. Bénéfices :
- Code plus maintenable
- Facile d'ajouter un nouveau champ (un seul endroit)
- Méthodes utilitaires réutilisables (`get_offerings_str()`, `find_case_study_by_industry()`, etc.)
- Type safety avec Pydantic

### Pourquoi deux modes pour ProofGenerator ?

**Problème** : L'ancien `CaseStudyAgent` avait deux usages contradictoires :
1. Scraper les case studies **du prospect** (ce qu'ils ont accompli)
2. Utiliser les case studies **du client** (ce qu'on a accompli pour nos clients)

C'est deux choses complètement différentes !

**Solution** : Renommer en `ProofGenerator` avec mode explicite :
- `mode="client_case_studies"` (défaut) : Utilise les vraies case studies du client
- `mode="prospect_achievements"` (rare) : Scrape le site du prospect pour mentionner leurs réussites

---

## 📝 Notes

- **Backward compatibility** : La méthode `load_client_context()` (v2.x) est toujours disponible
- **Graceful degradation** : Si les nouvelles tables n'existent pas, le système fonctionne quand même
- **Mock context** : Pour les tests, un mock context est disponible si Supabase n'est pas accessible

---

*Dernière mise à jour : 14 novembre 2025, 18h30*
