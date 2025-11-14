# 🧪 Guide de Test v3.0

Guide complet pour tester le système v3.0.

---

## 🎯 Options de Test

### ✅ Option 1: Test de Configuration (RECOMMANDÉ POUR COMMENCER)

Vérifie que tout est bien installé et configuré:

```bash
python test_v3_setup.py
```

**Ce script vérifie**:
- ✅ Variables d'environnement (.env)
- ✅ Imports des agents v3
- ✅ ClientContext model
- ✅ Tavily connexion
- ✅ Supabase connexion
- ✅ Initialisation de chaque agent

**Résultat attendu**:
```
🧪 Testing v3.0 Setup
============================================================
1️⃣ Checking Environment Variables...
   ✅ OPENROUTER_API_KEY: Configured
   ✅ TAVILY_API_KEY: Configured
   ✅ SUPABASE_URL: Configured
   ✅ SUPABASE_KEY: Configured

2️⃣ Checking v3 Imports...
   ✅ All v3 agents import successfully

...

✅ Setup test complete!
```

---

### ✅ Option 2: Test d'un Agent Individuel (SANS SUPABASE)

Teste un agent directement avec un ClientContext fictif:

```bash
python test_single_agent.py
```

**Ce script**:
- Crée un ClientContext fictif (Kaleads - lead gen)
- Teste les 6 agents v3 avec le prospect "Aircall"
- Affiche les résultats de chaque agent
- Utilise inference (pas de Tavily) pour éviter les appels API

**Résultat attendu**:
```
3️⃣ Testing PersonaExtractorV3...
   ✅ PersonaExtractorV3 completed
   📊 Results:
      - Role: Head of Sales
      - Department: Sales
      - Seniority: VP / Director
      - Pain Points: ['Difficulté à générer leads qualifiés', ...]
      🟠 Confidence: 3/5, Fallback: 1, Source: inference
```

**Avantages**:
- ✅ Rapide (pas d'appels API externes)
- ✅ Pas besoin de Supabase
- ✅ Teste la logique des agents

**Limitations**:
- ⚠️ Confidence scores plus bas (2-3)
- ⚠️ Pas de données réelles (Tavily)

---

### ✅ Option 3: Test des Exemples Intégrés

Chaque agent a un exemple `__main__` que tu peux lancer:

```bash
# Test PersonaExtractor
python src/agents/v3/persona_extractor_v3.py

# Test CompetitorFinder
python src/agents/v3/competitor_finder_v3.py

# Test PainPointAnalyzer
python src/agents/v3/pain_point_analyzer_v3.py

# Test SignalDetector
python src/agents/v3/signal_detector_v3.py

# Test SystemMapper
python src/agents/v3/system_mapper_v3.py

# Test ProofGenerator
python src/agents/v3/proof_generator_v3.py
```

⚠️ **Ces exemples utilisent Tavily** si configuré, donc vérifie ton `.env`.

**Résultat attendu**:
```
[CompetitorFinderV3] Using Tavily to find competitors for Aircall
Competitor: RingCentral
Confidence: 5/5
Source: web_search
Reasoning: Found via Tavily web search for 'Aircall' competitors
```

---

### ✅ Option 4: Test de l'API Complète (AVEC SUPABASE)

Teste l'API end-to-end avec une vraie requête:

#### Étape 1: Démarre l'API

```bash
python src/api/n8n_optimized_api.py
```

L'API démarre sur `http://localhost:8001`

#### Étape 2: Lance le test

```bash
python test_v3_api.py
```

⚠️ **IMPORTANT**: Édite `test_v3_api.py` et remplace `"test-client-uuid"` par un vrai client_id de ta base Supabase!

**Ce script**:
- ✅ Health check (`/health`)
- ✅ Root endpoint (`/`)
- ✅ Email generation (`/api/v2/generate-email`)

**Résultat attendu**:
```
3️⃣ Testing Email Generation (with test client)...
   Sending request (this may take 20-30 seconds)...

   ✅ Email generated successfully!

============================================================
Generated Email:
============================================================
Bonjour Sophie,

Je travaille chez Kaleads, spécialisé en Cold email automation, Lead enrichment.

J'ai remarqué que Aircall est en phase de croissance.

Nous avons aidé TechCorp à augmenter leur pipeline de 300% en 3 mois.

Seriez-vous ouvert(e) à un échange rapide?

Cordialement,
L'équipe Kaleads

============================================================
Metadata:
============================================================
   - Target Persona: Head of Sales
   - Competitor: RingCentral
   - Pain Point: Difficulté à générer suffisamment de leads qualifiés...
   - Signal: Aircall recrute actuellement
   - Tech Stack: Salesforce, HubSpot, Slack
   - Quality Score: 87/100
   - Cost: $0.001
   - Time: 25.3s

============================================================
Fallback Levels (0=best, 3=generic):
============================================================
   🟢 persona: 0
   🟢 competitor: 0
   🟡 pain: 1
   🟢 signal: 0
   🟡 system: 1
   🟢 proof: 0
```

---

### ✅ Option 5: Test avec curl

Si tu préfères curl:

#### Health Check
```bash
curl http://localhost:8001/health
```

#### Generate Email
```bash
curl -X POST http://localhost:8001/api/v2/generate-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "client_id": "kaleads-uuid",
    "contact": {
      "company_name": "Aircall",
      "first_name": "Sophie",
      "last_name": "Martin",
      "website": "https://aircall.io",
      "industry": "SaaS"
    },
    "options": {
      "enable_tavily": true
    }
  }'
```

---

## 🔍 Comprendre les Résultats

### Confidence Score (1-5)

| Score | Signification | Source |
|-------|---------------|--------|
| **5** | Données réelles trouvées (Tavily) | `web_search` |
| **4** | Trouvé sur le site web | `site_scrape` |
| **3** | Inféré de l'industrie/contexte | `inference` |
| **2** | Inférence générique | `inference` |
| **1** | Fallback générique | `generic` |

### Fallback Level (0-3)

| Level | Signification | Qualité |
|-------|---------------|---------|
| **0** | Meilleure source (web search) | 🟢 Excellent |
| **1** | Bonne source (scraping) | 🟡 Bon |
| **2** | Source OK (inference) | 🟠 Moyen |
| **3** | Fallback générique | 🔴 Basique |

### Source

- `web_search`: Tavily API
- `site_scrape`: Contenu du site web
- `inference`: Inférence basée industrie/contexte
- `generic`: Fallback générique

---

## ⚙️ Configuration des Tests

### Tester AVEC Tavily

Édite le script de test et change:
```python
enable_tavily=True
```

Résultat: Confidence 5, Fallback 0, données réelles

### Tester SANS Tavily

Édite le script de test et change:
```python
enable_tavily=False
```

Résultat: Confidence 2-3, Fallback 1-2, inférence

### Tester AVEC Scraping

```python
enable_scraping=True
```

Résultat: Confidence 4, Fallback 1 (si trouvé sur site)

### Tester Différents Types de Clients

Édite `test_single_agent.py` et change le `pain_solved`:

**Lead Gen Client (Kaleads)**:
```python
pain_solved="génération de leads B2B qualifiés via l'automatisation"
```
→ Agents ciblent: Head of Sales, focus client acquisition

**HR Tech Client**:
```python
pain_solved="recrutement et gestion des talents"
```
→ Agents ciblent: CHRO, focus recruitment

**DevOps Client**:
```python
pain_solved="déploiements rapides et infrastructure scalable"
```
→ Agents ciblent: CTO, focus infrastructure

**Marketing Client**:
```python
pain_solved="automatisation marketing et génération de demande"
```
→ Agents ciblent: CMO, focus marketing

---

## 🐛 Debugging

### Problème: "Could not initialize Tavily"

**Solution**: Vérifie `TAVILY_API_KEY` dans `.env`

```bash
# .env
TAVILY_API_KEY=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
```

### Problème: "Client context not found"

**Solution**: Le `client_id` n'existe pas dans Supabase

1. Vérifie que tu as un client dans ta table `clients`
2. Utilise le bon UUID dans le test

### Problème: "All agents return fallback_level=3"

**Solution**:
1. Active Tavily: `enable_tavily=True`
2. Vérifie que `TAVILY_API_KEY` est configurée
3. Vérifie que le site web du prospect est accessible

### Problème: API retourne 500

**Causes possibles**:
1. `client_id` invalide
2. API keys manquantes dans `.env`
3. Supabase connexion échoue

**Debug**:
```bash
# Check logs in terminal where API is running
python src/api/n8n_optimized_api.py
```

### Problème: Agents retournent des résultats bizarres

**Solution**: Vérifie le `pain_solved` dans ClientContext

Le `pain_solved` détermine comment les agents s'adaptent:
- Doit être descriptif
- Doit contenir des mots-clés pertinents (lead, sales, hr, devops, etc.)

---

## 📊 Métriques de Qualité

### Bonne Qualité
```
🟢 persona: 0 (web search)
🟢 competitor: 0 (web search)
🟡 pain: 1 (site scrape)
🟢 signal: 0 (web search)
🟡 system: 1 (site scrape)
🟢 proof: 0 (case study trouvé)
```
→ **Quality Score: 90-100**

### Qualité Moyenne
```
🟡 persona: 1 (site scrape)
🟠 competitor: 2 (inference)
🟠 pain: 2 (inference)
🟡 signal: 1 (site scrape)
🟠 system: 2 (inference)
🟡 proof: 1 (case study adapté)
```
→ **Quality Score: 70-85**

### Qualité Basique
```
🟠 persona: 2 (inference)
🔴 competitor: 3 (generic)
🔴 pain: 3 (generic)
🔴 signal: 3 (none)
🔴 system: 3 (generic)
🔴 proof: 3 (generic)
```
→ **Quality Score: 40-60**

---

## 📚 Ressources

- [V3_QUICK_START.md](./V3_QUICK_START.md) - Guide d'utilisation
- [V3_COMPLETION_SUMMARY.md](./V3_COMPLETION_SUMMARY.md) - Ce qui a été construit
- [ARCHITECTURE_FONDAMENTALE.md](./ARCHITECTURE_FONDAMENTALE.md) - Philosophie v3
- [src/agents/v3/README.md](./src/agents/v3/README.md) - Documentation agents

---

## ✅ Checklist de Test

Avant de déployer en production:

- [ ] `python test_v3_setup.py` → Tout ✅
- [ ] `python test_single_agent.py` → Tous les 6 agents ✅
- [ ] `python test_v3_api.py` → Email généré ✅
- [ ] Tester avec 3+ types de clients différents
- [ ] Tester avec Tavily activé (confidence 5)
- [ ] Tester avec Tavily désactivé (inference)
- [ ] Vérifier aucune hallucination (fake companies)
- [ ] Quality scores > 70 avec Tavily
- [ ] Temps de génération < 30s

---

**Happy Testing! 🚀**
