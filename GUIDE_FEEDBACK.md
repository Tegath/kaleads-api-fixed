# Guide: Feedback et Amelioration des Emails

## Vue d'Ensemble

Ce guide explique comment:
1. **Configurer** votre campagne email (template + contexte)
2. **Reviser** les emails generes
3. **Corriger** et regenerer
4. **Ameliorer automatiquement** les agents avec le feedback

---

## Workflow Complet

```
1. CONFIGURATION
   ↓ (humain decide du template et contexte)
2. GENERATION
   ↓ (6 agents generent les variables)
3. REVIEW
   ↓ (humain identifie les problemes)
4. FEEDBACK ANALYSIS
   ↓ (AI identifie quels agents corriger)
5. REGENERATION
   ↓ (avec corrections)
6. COMPARAISON
   ↓ (avant/apres)
7. VALIDATION ou retour a l'etape 3
```

---

## Methode 1: Mode Interactif (Recommande)

### Lancer le Mode Interactif

```bash
python test_interactive.py
```

### Etapes Detaillees

#### Etape 1: Configuration du Contact
```
[1] CONTACT
Voulez-vous utiliser le contact de test (Aircall) ? (O/n)
> n

Entrez les informations du contact:
  Company name: Stripe
  First name: Jean
  Last name: Martin
  Email: jean@stripe.com
  Website: https://stripe.com
  Industry: FinTech
```

#### Etape 2: Configuration du Template
```
[2] TEMPLATE
Voulez-vous utiliser le template par defaut ? (O/n)
> o

[OK] Template charge (458 caracteres)
```

Ou creez votre propre template:
```
> n

Collez votre template (finissez par une ligne vide):
Bonjour {{first_name}},

J'ai remarque que {{company_name}} {{specific_signal_1}}.

Le probleme que je vois souvent: {{problem_specific}}.
L'impact: {{impact_measurable}}.

Chez MonEntreprise, nous aidons les {{target_persona}}
a resoudre ce probleme en remplacant {{competitor_name}}.

Resultat: {{case_study_result}}.

Interesse(e) ?

[ligne vide pour finir]
```

#### Etape 3: Directives Specifiques
```
[3] CONTEXTE ET DIRECTIVES
Ajoutez des directives specifiques pour cette campagne (optionnel):
(Ex: 'Insister sur la rapidite', 'Ton formel', 'Focus sur le ROI')
> Ton tres professionnel, focus sur le ROI mesurable, eviter le jargon
```

#### Etape 4: Generation
```
[*] Generation en cours...
[OK] Email genere!

EMAIL GENERE
============================================================
Contact: Stripe
Quality Score: 73/100
Generation Time: 22921ms

Fallback Levels:
  [!] persona_agent: Level 3    <- Probleme ici!
  [OK] competitor_agent: Level 1
  [OK] pain_agent: Level 1
  ...
```

#### Etape 5: Feedback
```
Que pensez-vous de cet email?
1. Parfait - je le valide
2. Bon mais necessite des ajustements mineurs
3. Moyen - des corrections importantes necessaires
4. Mauvais - a regenerer completement

Votre choix (1-4): 3

Quels elements posent probleme? (separees par des virgules)
> persona incorrect, ton pas assez professionnel

Que souhaitez-vous ameliorer?
(Soyez specifique)

Ajoutez vos corrections (ligne vide pour terminer):
> Le persona devrait etre CFO pas customer support manager
> Le ton doit etre plus formel et corporate
> Ajouter des chiffres ROI concrets
> [ligne vide]
```

#### Etape 6: Regeneration
```
[*] Regeneration avec 3 corrections...
[OK] Email genere!

COMPARAISON AVANT/APRES
============================================================
QUALITY SCORES:
  Avant: 73/100
  Apres: 82/100
  Difference: +9

FALLBACK LEVELS:
  persona_agent: 3 -> 2    <- Ameliore!

VARIABLES CHANGEES:
  target_persona:
    Avant: customer support manager
    Apres: cFO
```

#### Etape 7: Continuer ou Valider
```
Voulez-vous continuer a ameliorer? (o/N)
> n

[*] Session sauvegardee: output/sessions/session-20250106-143022.json

SESSION TERMINEE
============================================================
Nombre d'iterations: 2
Quality score final: 82/100
```

---

## Methode 2: Feedback Programmatique

### Analyser le Feedback Automatiquement

```python
from src.agents.feedback_agent import analyze_email_feedback
from src.orchestrator import CampaignOrchestrator
from src.schemas.campaign_schemas import CampaignRequest, Contact

# 1. Generer un email
orchestrator = CampaignOrchestrator(...)
result = orchestrator.run(request)
email = result.emails_generated[0]

# 2. Donner du feedback
human_feedback = """
Le persona est incorrect - devrait etre VP Sales pas customer support.
Le pain point est trop vague, manque de specificite.
Le ton n'est pas assez professionnel.
"""

issues = "persona incorrect, pain point vague, ton informel"

# 3. Analyser le feedback avec l'AI
from src.agents.feedback_agent import analyze_email_feedback

analysis = analyze_email_feedback(
    email_result=email,
    human_feedback=human_feedback,
    issues=issues
)

# 4. Voir les recommandations
print("Agents problematiques:", analysis.problematic_agents)
# => ['persona_agent', 'pain_agent']

print("Causes:", analysis.root_causes)
# => {
#      'persona_agent': 'Manque d\'exemples concrets dans le prompt',
#      'pain_agent': 'Instructions trop generiques'
#    }

print("Suggestions:", analysis.improvement_suggestions)
# => {
#      'persona_agent': [
#        'Ajouter des exemples de personas par industrie',
#        'Preciser le niveau de seniorite attendu'
#      ],
#      'pain_agent': [
#        'Demander des chiffres concrets',
#        'Eviter les formulations vagues'
#      ]
#    }

print("Ajustements aux prompts:", analysis.prompt_adjustments)
# => {
#      'persona_agent': {
#        'background': 'Ajouter: Pour FinTech, focus sur CFO/VP Finance',
#        'output_instructions': 'Exemples: CFO (FinTech), VP Sales (SaaS)'
#      }
#    }
```

---

## Methode 3: Batch avec Feedback CSV

### Workflow
1. Generez un batch d'emails
2. Exportez en CSV
3. Ajoutez votre feedback dans Excel
4. Importez le CSV avec feedback
5. Analysez et regenerez

### Commandes

```bash
# 1. Generer le batch
python test_batch.py

# 2. Ouvrir output/batch-XXX_results.csv dans Excel
# 3. Ajouter feedback dans la colonne "feedback"
# 4. Sauvegarder

# 5. Analyser le feedback (script a creer)
python analyze_feedback_csv.py output/batch-XXX_results.csv
```

---

## Comment l'AI S'Ameliore

### 1. Analyse Automatique du Feedback

Le `FeedbackAgent` analyse:
- **Quelles variables** sont problematiques
- **Quel agent** est responsable de chaque variable
- **Pourquoi** l'agent a echoue (cause racine)
- **Comment** ameliorer le prompt

### 2. Mapping Variables → Agents

```python
VARIABLE_TO_AGENT = {
    "target_persona": "persona_agent",         # Agent 1
    "competitor_name": "competitor_agent",     # Agent 2
    "problem_specific": "pain_agent",          # Agent 3
    "specific_signal_1": "signal_agent",       # Agent 4
    "system_1": "system_agent",                # Agent 5
    "case_study_result": "case_study_agent"    # Agent 6
}
```

Si vous dites "le persona est incorrect", l'AI sait que c'est `persona_agent` a corriger.

### 3. Suggestions d'Amelioration

L'AI propose des modifications aux 3 sections du prompt:

**Exemple pour PersonaExtractorAgent**:

```python
# Avant
system_prompt_generator = SystemPromptGenerator(
    background=[
        "Tu es un expert en analyse de marches B2B."
    ],
    steps=[
        "1. Analyse le site web"
    ],
    output_instructions=[
        "Format: minuscule"
    ]
)

# Apres (avec suggestions de l'AI)
system_prompt_generator = SystemPromptGenerator(
    background=[
        "Tu es un expert en analyse de marches B2B.",
        "Pour FinTech, focus sur CFO/VP Finance",  # AJOUTE
        "Pour SaaS, focus sur VP Sales/CRO"         # AJOUTE
    ],
    steps=[
        "1. Analyse le site web",
        "2. Identifie l'industrie",                 # AJOUTE
        "3. Deduis le persona selon l'industrie"    # AJOUTE
    ],
    output_instructions=[
        "Format: minuscule sauf acronymes",
        "Exemples: cFO (FinTech), vP Sales (SaaS)", # AJOUTE
        "Eviter: 'decision maker', 'responsable'"   # AJOUTE
    ]
)
```

### 4. Application Manuelle (Pour l'instant)

**Important**: Pour l'instant, l'AI SUGGERE les ameliorations mais ne les applique PAS automatiquement.

Vous devez:
1. Lire les suggestions
2. Ouvrir `src/agents/agents_v2.py`
3. Copier-coller les ameliorations dans les prompts
4. Re-tester

**Pourquoi manuel?**
- Securite: Vous gardez le controle
- Qualite: Vous validez chaque modification
- Apprentissage: Vous comprenez ce qui est change

---

## Apprentissage Continu

### Accumuler le Feedback

Chaque session interactive sauvegarde:
```json
{
  "contact": {...},
  "template": "...",
  "history": [
    {
      "timestamp": "2025-01-06T14:30:22",
      "quality_score": 73,
      "feedback": {
        "rating": "3",
        "issues": "persona incorrect",
        "improvements": ["Le persona devrait etre CFO"]
      }
    },
    {
      "timestamp": "2025-01-06T14:32:15",
      "quality_score": 82,
      "feedback": null  // Valide!
    }
  ]
}
```

### Analyser les Patterns

Apres 10-20 sessions, vous pouvez:

```python
import json
import glob

# Charger toutes les sessions
sessions = []
for file in glob.glob("output/sessions/*.json"):
    with open(file) as f:
        sessions.append(json.load(f))

# Analyser les patterns
problems_count = {}
for session in sessions:
    for entry in session["history"]:
        if entry["feedback"]:
            issues = entry["feedback"]["issues"]
            # Compter les problemes recurrents
            for issue in issues.split(","):
                issue = issue.strip()
                problems_count[issue] = problems_count.get(issue, 0) + 1

# Problemes les plus frequents
print("Problemes recurrents:")
for issue, count in sorted(problems_count.items(), key=lambda x: x[1], reverse=True):
    print(f"  {issue}: {count} fois")
```

**Output exemple**:
```
Problemes recurrents:
  persona incorrect: 12 fois
  pain point vague: 8 fois
  ton informel: 5 fois
```

→ Cela vous dit quels agents ameliorer en priorite!

---

## Best Practices

### 1. Soyez Specifique dans le Feedback

**Mauvais**:
```
"C'est pas bon"
"Le persona est faux"
```

**Bon**:
```
"Le persona devrait etre CFO pas customer support manager"
"Le pain point manque de chiffres concrets (ex: perte de 20% de temps)"
"Le ton doit etre plus formel et corporate"
```

### 2. Testez les Modifications Incrementalement

```
1. Ameliorez UN agent a la fois
2. Re-testez
3. Comparez les quality scores
4. Si amelioration → gardez
5. Si degradation → annulez
```

### 3. Documentez vos Modifications

```python
# Version 1.0 (2025-01-06): Initial
# Version 1.1 (2025-01-06): Ajout exemples FinTech (feedback: persona incorrect)
# Version 1.2 (2025-01-07): Ton plus formel (feedback: ton informel)
system_prompt_generator = SystemPromptGenerator(...)
```

### 4. Gardez un Baseline

Avant de modifier, lancez un test batch et sauvegardez:
```bash
python test_batch.py
# Sauvegarder output/batch-XXX_results.csv comme "baseline_v1.0.csv"
```

Apres modifications:
```bash
python test_batch.py
# Comparer avec baseline_v1.0.csv
```

---

## Prochaines Ameliorations Possibles

### 1. Auto-Application des Suggestions (Avance)

Creer un script qui:
1. Lit les suggestions du FeedbackAgent
2. Parse `src/agents/agents_v2.py`
3. Modifie automatiquement les prompts
4. Teste et valide

### 2. Fine-Tuning (Tres Avance)

Avec beaucoup de feedback (100+ emails):
1. Creer un dataset de feedback
2. Fine-tuner un modele OpenAI specifique
3. Utiliser ce modele pour les agents problematiques

### 3. Systeme de A/B Testing

Tester 2 versions d'un agent en parallele:
- Version A: Prompt actuel
- Version B: Prompt ameliore
- Comparer les quality scores

---

## FAQ

**Q: L'AI peut-elle s'ameliorer toute seule?**
R: Partiellement. Elle peut SUGGERER des ameliorations mais vous devez les appliquer manuellement (pour l'instant).

**Q: Combien de feedback avant d'ameliorer?**
R: 3-5 emails similaires suffisent pour identifier un pattern.

**Q: Les ameliorations sont-elles permanentes?**
R: Oui, si vous modifiez `src/agents/agents_v2.py`, les changements restent.

**Q: Puis-je avoir plusieurs versions de prompts?**
R: Oui! Creez `agents_v2_fintech.py`, `agents_v2_saas.py` par industrie.

**Q: Comment savoir si une modification a marche?**
R: Comparez les quality scores avant/apres sur un batch de 10+ contacts.

---

## Exemple Complet

```bash
# 1. Test initial
python test_batch.py
# Quality moyenne: 73/100

# 2. Mode interactif pour identifier problemes
python test_interactive.py
# Feedback: "persona incorrect 3 fois sur 5"

# 3. Analyser avec FeedbackAgent
python -c "
from src.agents.feedback_agent import analyze_email_feedback
# ... analyser les problemes
"
# Output: "Ajouter exemples FinTech au PersonaExtractorAgent"

# 4. Modifier src/agents/agents_v2.py
# Ajouter les exemples suggeres

# 5. Re-tester
python test_batch.py
# Quality moyenne: 81/100
# => +8 points d'amelioration!
```

---

Bon feedback! 🚀
