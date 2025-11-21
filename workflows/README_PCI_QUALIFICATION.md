# Système de Qualification PCI Progressive

Ce système permet de qualifier progressivement vos leads en fonction de votre Profil Client Idéal (PCI), de manière automatique et économique.

## 🎯 Objectif

Au lieu d'enrichir tous vos leads (coûteux), ce système :
1. **Qualifie** d'abord tous les leads (gratuit/quasi-gratuit)
2. **Score** chaque lead de 0 à 100 selon votre PCI
3. **Priorise** les leads à fort potentiel pour l'enrichissement
4. **Traite progressivement** 50 leads par heure (1200/jour, 36k/mois)

## 💰 Économies

- **Qualification** : ~0.0001€ par lead (scraping Jina.ai gratuit + API presque gratuit)
- **Enrichissement** : ~0.50-1€ par lead (seulement pour les leads qualifiés >70)

**Exemple** : Sur 180 000 leads
- Qualifier tous les leads : ~18€
- Enrichir seulement les 10% meilleurs (18k leads) : ~9000€
- Vs enrichir tout : ~90 000€
- **Économie : 81 000€** 🎉

## 📋 Prérequis

### 1. Base de données Supabase

Exécutez la migration SQL pour ajouter les colonnes nécessaires :

```sql
-- Fichier: migrations/add_qualification_columns.sql

ALTER TABLE leads
ADD COLUMN IF NOT EXISTS stage TEXT DEFAULT 'new',
ADD COLUMN IF NOT EXISTS score INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS pci_match BOOLEAN DEFAULT false,
ADD COLUMN IF NOT EXISTS website_content TEXT,
ADD COLUMN IF NOT EXISTS qualified_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS monthly_batch TEXT,
ADD COLUMN IF NOT EXISTS qualification_reasons TEXT[];

-- Index pour performance
CREATE INDEX IF NOT EXISTS idx_leads_stage ON leads(stage);
CREATE INDEX IF NOT EXISTS idx_leads_score ON leads(score DESC);
CREATE INDEX IF NOT EXISTS idx_leads_monthly_batch ON leads(monthly_batch);
```

### 2. API déployée

L'endpoint `/api/v2/pci/qualify` doit être disponible sur votre serveur.

### 3. Variables d'environnement n8n

Dans n8n, configurez :
- `SUPABASE_URL` : URL de votre instance Supabase
- `SUPABASE_KEY` : Clé API Supabase (service_role_key)

## 🚀 Installation

### 1. Déployer l'API

```bash
# Commit et push
git add .
git commit -m "Add PCI qualification endpoint"
git push origin main

# Déployer sur le serveur
ssh root@92.112.193.183 "cd /opt/kaleads-api && git pull && docker-compose down && docker-compose up -d --build"
```

### 2. Importer le workflow n8n

1. Ouvrez n8n
2. Cliquez sur "+" → "Import from File"
3. Sélectionnez `workflows/n8n_pci_qualification_workflow.json`
4. Configurez vos credentials Supabase si nécessaire
5. Activez le workflow

## 📊 Fonctionnement

### Workflow n8n (toutes les heures)

```
1. Cron (toutes les heures)
   ↓
2. Récupère 50 leads (stage='new') depuis Supabase
   ↓
3. Pour chaque lead:
   ├─ Si website existe:
   │  ├─ Scrape avec Jina.ai (gratuit)
   │  ├─ Appelle /api/v2/pci/qualify
   │  └─ Met à jour Supabase (stage, score, reasons)
   └─ Si pas de website:
      └─ Marque comme 'no_site'
```

### Stages de qualification

- `new` : Lead non encore qualifié
- `qualifying` : En cours de qualification
- `qualified_high` : Score ≥ 70 → **À enrichir immédiatement**
- `qualified_medium` : Score 50-69 → À surveiller
- `qualified_low` : Score 30-49 → Faible priorité
- `disqualified` : Score < 30 → Ne pas enrichir
- `no_site` : Pas de site web → Impossible à qualifier

### Actions recommandées

L'API retourne aussi une `recommended_action` :
- `enrich` : Enrichir ce lead (trouver emails, contacts)
- `watch` : Garder en watchlist
- `skip` : Passer ce lead

## 📈 Critères de scoring

Le scoring se base sur :

1. **Tech stack détecté** (+20 points) : React, Vue, AWS, Salesforce, etc.
2. **Correspondance industrie** (+30 points) : Match avec vos industries cibles
3. **Taille entreprise** (+0 à +20) : 10-200 employés = idéal pour Kaleads
4. **Note Google** (+10/-10) : >4.0 = bon, <3.0 = mauvais
5. **Nombre d'avis** (+10/-5) : >50 avis = actif, <5 = peu actif
6. **Qualité du site** (+10) : Contenu substantiel (>2000 chars)

## 🔍 Exemple d'appel API

### Request

```bash
curl -X POST "http://92.112.193.183:20001/api/v2/pci/qualify" \
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Aircall",
    "website": "https://aircall.io",
    "website_content": "Aircall is a cloud-based phone system for modern businesses. Built for Salesforce, HubSpot, and 100+ integrations...",
    "city": "Paris",
    "rating": 4.5,
    "reviews_count": 120,
    "client_id": "kaleads"
  }'
```

### Response

```json
{
  "score": 85,
  "stage": "qualified_high",
  "match": true,
  "reasons": [
    "Tech stack detected: Salesforce, HubSpot, AWS",
    "Industry match: SaaS, Tech",
    "Company size: 10-50",
    "High rating: 4.5/5",
    "Many reviews: 120",
    "Substantial website content"
  ],
  "recommended_action": "enrich",
  "tech_stack": ["Salesforce", "HubSpot", "AWS"],
  "estimated_company_size": "10-50",
  "industry_match": true
}
```

## 📊 Suivi de progression

### Dans Supabase

```sql
-- Voir la distribution des stages
SELECT stage, COUNT(*) as count
FROM leads
WHERE client_id = 'kaleads'
GROUP BY stage
ORDER BY count DESC;

-- Top 10 leads qualifiés
SELECT company_name, city, score, stage, qualification_reasons
FROM leads
WHERE stage = 'qualified_high' AND client_id = 'kaleads'
ORDER BY score DESC
LIMIT 10;

-- Statistiques de qualification
SELECT
  COUNT(*) as total,
  COUNT(CASE WHEN stage = 'qualified_high' THEN 1 END) as high,
  COUNT(CASE WHEN stage = 'qualified_medium' THEN 1 END) as medium,
  COUNT(CASE WHEN stage = 'qualified_low' THEN 1 END) as low,
  COUNT(CASE WHEN stage = 'disqualified' THEN 1 END) as disqualified,
  COUNT(CASE WHEN stage = 'no_site' THEN 1 END) as no_site
FROM leads
WHERE client_id = 'kaleads';
```

## 🎯 Prochaines étapes

Une fois que vous avez des leads qualifiés :

### 1. Workflow d'enrichissement (à créer)

```
1. Récupère 500 leads (stage='qualified_high', monthly_batch IS NULL)
   ↓
2. Pour chaque lead:
   ├─ Enrichir avec Clay/Apollo (trouver décideurs + emails)
   ├─ Marquer monthly_batch = '2025-01'
   └─ Mettre stage = 'enriched'
```

### 2. Workflow de génération d'emails (existant)

```
1. Récupère leads enrichis
   ↓
2. Génère emails personnalisés avec l'API /api/v2/generate-email
   ↓
3. Envoie avec Lemlist/Instantly
```

## 🔧 Configuration avancée

### Modifier la fréquence

Dans le workflow n8n, ajustez le Cron :
- Toutes les heures : `0 * * * *`
- Toutes les 30min : `*/30 * * * *`
- Toutes les 6h : `0 */6 * * *`

### Modifier le batch size

Dans le nœud "Get 50 New Leads", changez `limit=50` à la valeur désirée.

### Personnaliser le scoring

Modifiez `src/agents/pci_qualifier_agent.py` :
- Ajustez les poids des critères (lignes 106-151)
- Ajoutez de nouveaux critères
- Modifiez les seuils de qualification (lignes 157-172)

## 🐛 Debugging

### Tester l'API manuellement

```bash
# Test de santé
curl http://92.112.193.183:20001/api/v2/pci/health

# Test de qualification
curl -X POST "http://92.112.193.183:20001/api/v2/pci/qualify" \
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8" \
  -H "Content-Type: application/json" \
  -d '{
    "company_name": "Test Corp",
    "website": "https://example.com",
    "client_id": "kaleads"
  }'
```

### Logs Docker

```bash
ssh root@92.112.193.183 "docker logs kaleads-atomic-agents --tail 100 -f"
```

### Logs n8n

Dans n8n, cliquez sur "Executions" pour voir l'historique.

## 📞 Support

Questions ? Vérifiez :
1. Les logs Docker
2. Les executions n8n
3. Les données Supabase (`SELECT * FROM leads LIMIT 10`)

---

**Fait avec ❤️ pour Kaleads**
