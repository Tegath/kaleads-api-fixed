# Quick Start - Système Optimisé (5 Minutes)

## Démarrage Ultra-Rapide

### 1. Installer (30 secondes)

```bash
pip install -r requirements.txt
```

### 2. Obtenir Clé OpenRouter (2 minutes)

1. Allez sur [openrouter.ai](https://openrouter.ai)
2. Sign up (gratuit)
3. Generate API key
4. Ajoutez $5 de crédits (= 10,000 emails!)
5. Copiez votre clé: `sk-or-v1-...`

### 3. Configurer (30 secondes)

```bash
# Copier .env.example
cp .env.example .env

# Éditer .env
# Remplacez:
OPENROUTER_API_KEY=sk-or-v1-VOTRE-CLE-ICI
```

**Note**: C'est tout! Supabase est optionnel pour commencer.

### 4. Tester (30 secondes)

**Terminal 1**: Démarrer l'API
```bash
python -m uvicorn src.api.n8n_optimized_api:app --reload --port 8001
```

**Terminal 2**: Générer 1 email
```bash
curl -X POST http://localhost:8001/api/v2/generate-email \
  -H "X-API-Key: your-secure-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test",
    "contact": {
      "company_name": "Aircall",
      "first_name": "Sophie",
      "website": "https://aircall.io",
      "industry": "SaaS"
    },
    "options": {
      "model_preference": "cheap",
      "enable_scraping": false
    }
  }'
```

**Résultat attendu** (18-22 secondes):
```json
{
  "success": true,
  "cost_usd": 0.0005,
  "email_content": "Bonjour Sophie,\n\nJ'ai remarqué que Aircall...",
  "quality_score": 82,
  "target_persona": "VP Sales",
  "competitor_name": "Zendesk Talk",
  ...
}
```

### 5. Vérifier les Coûts (30 secondes)

1. Allez sur [openrouter.ai/activity](https://openrouter.ai/activity)
2. Vous devriez voir ~$0.0005 de coût
3. Vérifiez que les modèles utilisés sont "deepseek/deepseek-chat" et "google/gemini-flash-1.5"

---

## C'est Tout! 🎉

Vous avez maintenant:
- ✅ API qui génère des emails à **$0.0005** (97% moins cher que GPT-4o!)
- ✅ Temps de génération: **18-22 secondes**
- ✅ Qualité: **82/100** (très acceptable)

---

## Prochaines Étapes (Optionnelles)

### A. Activer le Scraping (pour meilleure qualité)

```bash
# Installer Crawl4AI
pip install crawl4ai
playwright install

# Puis régénérer avec scraping activé:
curl ... -d '{"options": {"enable_scraping": true}}'
```

**Résultat**: Quality score passe de 82 → 88 (scraping = +6 points)

### B. Setup Supabase (pour contexte client)

1. Créez compte sur [supabase.com](https://supabase.com)
2. Exécutez SQL dans [ARCHITECTURE_OPTIMISEE.md](ARCHITECTURE_OPTIMISEE.md#L140-L173)
3. Ajoutez dans `.env`:
```bash
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJhbGci...
```

**Résultat**: PCI filtering disponible + contexte personnalisé par client

### C. Tester PCI Filtering

```bash
curl -X POST http://localhost:8001/api/v2/pci-filter \
  -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "client_id": "test",
    "contacts": [
      {"company_name": "Aircall", "industry": "SaaS", "employees": 500},
      {"company_name": "Bakery", "industry": "Food", "employees": 5}
    ]
  }'
```

**Résultat**: Filtre automatiquement les mauvais leads (70% filtrés = 83% économie!)

### D. Intégrer avec n8n

Voir [GUIDE_OPTIMISATION.md](GUIDE_OPTIMISATION.md#workflow-n8n-optimisé) pour workflow complet.

---

## Dépannage Express

### Erreur: "Invalid API Key"
```bash
# Dans .env, vérifiez:
API_KEY=your-secure-api-key

# Dans curl, header doit matcher:
-H "X-API-Key: your-secure-api-key"
```

### Erreur: "OpenRouter API key required"
```bash
# Dans .env, ajoutez:
OPENROUTER_API_KEY=sk-or-v1-...
```

### Timeout > 30s
```bash
# Désactivez scraping pour première fois:
"options": {"enable_scraping": false}
```

---

## Aide Complète

- 📖 [GUIDE_OPTIMISATION.md](GUIDE_OPTIMISATION.md) - Guide complet
- 🏗️ [ARCHITECTURE_OPTIMISEE.md](ARCHITECTURE_OPTIMISEE.md) - Architecture détaillée
- ✅ [IMPLEMENTATION_COMPLETE.md](IMPLEMENTATION_COMPLETE.md) - Récapitulatif complet

---

**Questions?** Lisez d'abord [GUIDE_OPTIMISATION.md](GUIDE_OPTIMISATION.md) section Troubleshooting!

Bon scaling! 🚀
