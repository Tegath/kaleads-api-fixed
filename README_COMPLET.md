# Systeme de Generation d'Emails Personnalises - Atomic Agents v2

Systeme multi-agents pour generer des emails de prospection ultra-personnalises en utilisant Atomic Agents v2.

## Installation Rapide

```bash
# 1. Lancer le script d'installation
setup.bat

# 2. Editer .env et ajouter votre cle API
# OPENAI_API_KEY=sk-proj-...

# 3. Tester
venv\Scripts\activate
python test_batch.py
```

## Vue d'Ensemble du Systeme

### Architecture

```
6 Agents Specialises → Orchestrateur → Email Final
```

**Les 6 Agents**:
1. **PersonaExtractorAgent**: Identifie le persona cible et la categorie de produit
2. **CompetitorFinderAgent**: Trouve le concurrent principal
3. **PainPointAgent**: Identifie le pain point specifique et son impact mesurable
4. **SignalGeneratorAgent**: Generate 4 signaux ultra-personnalises (2 signaux + 2 ciblages)
5. **SystemBuilderAgent**: Identifie 3 systemes/processus de l'entreprise
6. **CaseStudyAgent**: Generate un resultat de case study mesurable

**Workflow**:
- **Batch 1** (parallele conceptuel): Agents 1, 2, 3, 6
- **Batch 2** (sequentiel): Agent 4 → Agent 5
- **Assemblage**: Variables → Template → Email final

### Systeme de Fallbacks (4 niveaux)

Chaque agent a une hierarchie de fallbacks pour garantir un resultat:

- **Niveau 1**: Information parfaite (scraping reel du site web)
- **Niveau 2**: Information deduite (inference basee sur le contexte)
- **Niveau 3**: Fallback generique (base de connaissances)
- **Niveau 4**: Fallback minimal (valeur par defaut)

**Exemple**: PersonaExtractorAgent
```
Niveau 1: Scrape le site et trouve "VP Sales" dans la section testimonials
Niveau 2: Deduit "VP Sales" base sur industry="SaaS" + product="CRM"
Niveau 3: Utilise persona generique pour l'industrie SaaS
Niveau 4: Retourne "decision maker"
```

### Metriques de Qualite

**Quality Score** (0-100):
- 20 points: Longueur appropriee (180-220 mots)
- 40 points: Niveaux de fallback (moins de fallbacks = meilleur)
- 30 points: Scores de confiance (4-5/5 = meilleur)
- 10 points: Pas de variables manquantes

**Confidence Score** (1-5):
Chaque variable generee a un score de confiance:
- 5: Tres confiant (info explicite)
- 4: Confiant (info deduite)
- 3: Moyennement confiant
- 2: Peu confiant
- 1: Tres peu confiant

---

## Commandes Principales

### 1. Test Simple (1 contact)
```bash
venv\Scripts\activate
python test_campaign.py
```

**Sortie**: Console avec 1 email genere et metriques

---

### 2. Test Batch (plusieurs contacts + analyse)
```bash
venv\Scripts\activate
python test_batch.py
```

**Sorties**:
- `output/batch-YYYYMMDD-HHMMSS_results.csv` - Tableau Excel pour feedback
- `output/batch-YYYYMMDD-HHMMSS_1_CompanyName.txt` - Emails individuels

**Le CSV contient**:
- Toutes les variables generees
- Quality score
- Fallback levels par agent
- Confidence scores
- Colonne `feedback` vide pour vos commentaires

---

### 3. Test avec Vos Propres Contacts

**Etape 1**: Editez `contacts_test.csv`:
```csv
company_name,first_name,last_name,email,website,industry
VotreEntreprise,Jean,Dupont,jean@entreprise.com,https://entreprise.com,SaaS
```

**Etape 2**: Lancez le test:
```bash
venv\Scripts\activate
python test_batch.py
```

---

## Workflow de Feedback Rapide

```
1. python test_batch.py
   ↓
2. Ouvrir output/batch-XXX_results.csv dans Excel
   ↓
3. Lire les emails + ajouter feedback
   ↓
4. Identifier les patterns de problemes
   ↓
5. Modifier src/agents/agents_v2.py (prompts)
   ↓
6. Re-tester
   ↓
7. Comparer quality scores avant/apres
```

---

## Structure du Projet

```
kaleads-atomic-agents/
├── src/
│   ├── agents/
│   │   ├── agents_v2.py          # Les 6 agents (MODIFIER ICI pour ameliorer)
│   │   └── __init__.py
│   ├── orchestrator/
│   │   ├── campaign_orchestrator_v2.py  # Orchestration des agents
│   │   └── __init__.py
│   ├── schemas/
│   │   ├── agent_schemas_v2.py   # Input/Output schemas des agents
│   │   └── campaign_schemas.py   # Schemas de campagne
│   └── api/
│       └── main.py               # API FastAPI (optionnel)
├── data/
│   ├── templates/
│   │   └── cold_email_template_example.md  # Template d'email
│   └── clients/
│       └── example-client/
│           └── pci.md            # Profil Client Ideal
├── output/                       # Resultats des tests (genere automatiquement)
├── test_campaign.py              # Test simple (1 contact)
├── test_batch.py                 # Test batch (plusieurs contacts)
├── contacts_test.csv             # Contacts de test (EDITER ICI)
├── .env                          # Config (OPENAI_API_KEY)
├── requirements-test.txt         # Dependances
├── setup.bat                     # Script d'installation
├── QUICK_START.md                # Guide rapide
└── MIGRATION_V2_COMPLETE.md      # Doc technique migration v2
```

---

## Ameliorer les Resultats

### Si Quality Score < 70

**Etape 1**: Identifier quel agent cause le probleme
- Regardez les fallback levels dans le CSV
- Un agent avec fallback niveau 3-4 = probleme

**Etape 2**: Ouvrir `src/agents/agents_v2.py`
- Trouvez l'agent problematique (ex: `PersonaExtractorAgent`)

**Etape 3**: Ameliorer le prompt
```python
system_prompt_generator = SystemPromptGenerator(
    background=[
        # AMELIOREZ ICI: Donnez plus de contexte
        "Tu es un expert en...",
        "Ta mission est de...",
    ],
    steps=[
        # AMELIOREZ ICI: Decomposez mieux la tache
        "1. Analyse le site web",
        "2. Identifie les signaux cles",
    ],
    output_instructions=[
        # AMELIOREZ ICI: Donnez plus d'exemples
        "Format: minuscule sauf acronymes",
        "Exemple BON: 'vP Sales'",
        "Exemple MAUVAIS: 'VP SALES'",
    ]
)
```

**Etape 4**: Re-tester et comparer

---

### Si Variables Manquantes

**Symptome**: `[INFORMATION NON DISPONIBLE]` dans l'email

**Causes**:
1. Agent n'a pas reussi a generer la variable
2. Template contient une variable non supportee

**Solution**:
1. Verifier que la variable existe dans `agent_schemas_v2.py`
2. Verifier que l'agent la genere bien
3. Verifier le template utilise `{{nom_variable}}` correct

---

### Si Generation Trop Lente

**Symptome**: > 30s par email

**Solutions**:
1. Utiliser `gpt-4o-mini` au lieu de `gpt-4o` (dans `.env`)
2. Activer le cache: `enable_cache=True`
3. Reduire le contexte dans les prompts

---

## Resultats Attendus

**Metriques cibles**:
- Success rate: **100%**
- Quality score moyen: **> 75/100**
- Fallback level moyen: **< 2.0**
- Temps par email: **< 25s**
- Cache hit rate: **> 80%** (apres 1er run)

**Exemple de resultat reel** (test du 2025-01-06):
```
Total contacts: 1
Success: 1/1 (100.0%)
Quality moyenne: 76.0/100
Temps total: 21.95s
Temps/email: 21.95s
Cache hit rate: 83.3%
Tokens: 3,100
Cout estime: $0.0012
```

---

## Couts Estimatifs

**Modele**: gpt-4o-mini
- Input: $0.15 / 1M tokens
- Output: $0.60 / 1M tokens

**Par email** (estimation):
- Tokens: ~3,000
- Cout: ~$0.0012 (0.12 centimes)

**Pour 1,000 emails**:
- Cout total: ~$1.20
- Temps total: ~6h (avec cache)

---

## Support et Documentation

- **QUICK_START.md**: Guide de demarrage rapide
- **MIGRATION_V2_COMPLETE.md**: Documentation technique migration v2
- **plan_atomic_agents_campagne_email.md**: Specifications completes

---

## Prochaines Etapes

1. **Installation**: Lancez `setup.bat`
2. **Premier test**: `python test_campaign.py`
3. **Test batch**: `python test_batch.py`
4. **Analyser resultats**: Ouvrez le CSV genere
5. **Ameliorer prompts**: Editez `src/agents/agents_v2.py`
6. **Re-tester**: Comparez avant/apres
7. **Production**: Integrez dans votre workflow

Bon test! 🚀
