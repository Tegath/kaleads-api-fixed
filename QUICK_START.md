# Guide de Demarrage Rapide

## Installation (une seule fois)

```bash
# Methode 1: Script automatique (Windows)
setup.bat

# Methode 2: Manuelle
python -m venv venv
venv\Scripts\activate
pip install -r requirements-test.txt
copy .env.example .env
# Editez .env et ajoutez votre OPENAI_API_KEY
```

## Tests Rapides

### 1. Test Simple (1 contact)
```bash
venv\Scripts\activate
python test_campaign.py
```

**Resultat**: Console + affiche 1 email genere

---

### 2. Test Batch (plusieurs contacts + feedback)
```bash
venv\Scripts\activate
python test_batch.py
```

**Resultat**:
- `output/batch-YYYYMMDD-HHMMSS_results.csv` - Tableau pour feedback
- `output/batch-YYYYMMDD-HHMMSS_1_CompanyName.txt` - Emails individuels

**Workflow de feedback**:
1. Ouvrez le CSV dans Excel
2. Lisez chaque email
3. Ajoutez vos commentaires dans la colonne `feedback`
4. Notez les patterns de problemes

---

### 3. Test avec Vos Contacts
```bash
# 1. Editez contacts_test.csv avec vos contacts
# 2. Lancez le test
venv\Scripts\activate
python test_batch.py
```

**Format CSV requis**:
```csv
company_name,first_name,last_name,email,website,industry
Aircall,Sophie,Durand,sophie@aircall.io,https://aircall.io,SaaS
```

---

## Analyser les Resultats

### Metriques a Surveiller

1. **Quality Score** (objectif: >75/100)
   - < 60: Probleme majeur
   - 60-75: Amelioration necessaire
   - > 75: Bon

2. **Fallback Levels** (objectif: niveau 1-2)
   - Niveau 1: Info parfaite (scraping reel)
   - Niveau 2: Info deduite (bon)
   - Niveau 3: Fallback generique (moyen)
   - Niveau 4: Fallback minimal (probleme)

3. **Confidence Scores** (objectif: 4-5/5)
   - 5/5: Tres confiant
   - 3-4/5: Confiant
   - 1-2/5: Peu confiant (a verifier)

---

## Identifier les Problemes

### Probleme 1: Variables Manquantes
**Symptome**: `[INFORMATION NON DISPONIBLE]` dans l'email

**Causes possibles**:
- Agent n'a pas reussi a generer la variable
- Template contient une variable non supportee

**Solution**:
1. Verifiez les logs de l'agent concerne
2. Ajoutez un fallback plus robuste
3. Modifiez le template

---

### Probleme 2: Qualite Basse
**Symptome**: Quality score < 70

**Causes possibles**:
- Trop de fallbacks niveau 3-4
- Variables manquantes
- Email trop court/long
- Faibles confidence scores

**Solution**:
1. Consultez `analyze_results()` dans la console
2. Identifiez quel agent cause le probleme
3. Ameliorez les prompts de l'agent
4. Ajoutez plus de contexte (PCI, personas, etc.)

---

### Probleme 3: Agent Specifique Faible
**Symptome**: Un agent utilise souvent fallback niveau 3-4

**Solution**:
1. Ouvrez `src/agents/agents_v2.py`
2. Trouvez l'agent concerne
3. Ameliorez le `system_prompt_generator`:
   - `background`: Contexte de l'agent
   - `steps`: Etapes de raisonnement
   - `output_instructions`: Format de sortie

**Exemple**:
```python
system_prompt_generator = SystemPromptGenerator(
    background=[
        "AMELIOREZ ICI: Ajoutez plus de contexte",
        "Expliquez mieux la tache de l'agent"
    ],
    steps=[
        "AMELIOREZ ICI: Decomposez mieux les etapes",
        "Soyez plus specifique"
    ],
    output_instructions=[
        "AMELIOREZ ICI: Donnez plus d'exemples",
        "Soyez plus clair sur le format attendu"
    ]
)
```

---

## Iterations Rapides

### Cycle de Feedback

```
1. Lancez test_batch.py
   “
2. Analysez les resultats CSV
   “
3. Identifiez les patterns de problemes
   “
4. Modifiez les agents/prompts
   “
5. Re-testez
   “
6. Comparez les resultats (quality score, fallbacks)
   “
7. Repetez jusqu'a satisfaction
```

### Commandes pour Iterations

```bash
# Test rapide (1 contact pour debug)
python test_campaign.py

# Test complet (plusieurs contacts)
python test_batch.py

# Comparer 2 batchs
# Ouvrez les 2 CSV et comparez:
# - Quality score moyenne
# - % de fallback niveau 3-4
# - Feedback qualitatif
```

---

## Commandes en Une Ligne

```bash
# Installation complete
setup.bat

# Apres installation, a chaque fois:
venv\Scripts\activate && python test_batch.py
```

---

## Troubleshooting

### Erreur: OPENAI_API_KEY not found
```bash
# Verifiez que .env existe et contient:
OPENAI_API_KEY=sk-proj-...
```

### Erreur: Module not found
```bash
venv\Scripts\activate
pip install -r requirements-test.txt
```
