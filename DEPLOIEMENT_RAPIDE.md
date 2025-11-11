# Déploiement Rapide pour Clay

## Option 1: Railway.app (Recommandé - Gratuit)

### Étape 1: Préparer le Repo

```bash
# Si pas encore de repo Git
git init
git add .
git commit -m "Initial commit - Clay-compatible API"

# Pusher sur GitHub
# (créez un repo sur github.com)
git remote add origin https://github.com/votre-username/votre-repo.git
git branch -M main
git push -u origin main
```

### Étape 2: Déployer sur Railway

1. **Allez sur [railway.app](https://railway.app)**

2. **Sign up** avec votre compte GitHub

3. **New Project** → **Deploy from GitHub repo**

4. **Sélectionnez votre repo**

5. Railway détecte automatiquement:
   - `Procfile` → Utilise uvicorn
   - `requirements-test.txt` → Installe les dépendances
   - `railway.json` → Configuration

6. **Configurez les variables d'environnement**:
   - Settings → Variables
   - Ajoutez:
     ```
     OPENAI_API_KEY=sk-proj-...
     API_KEY=votre-cle-secrete-aleatoire
     ```

7. **Déployez** → Le deploy démarre automatiquement

8. **Notez l'URL** → Settings → Domain
   - Ex: `https://votre-app.up.railway.app`

### Étape 3: Tester

```bash
curl https://votre-app.up.railway.app/health
# Devrait retourner: {"status": "healthy", ...}

curl -X POST https://votre-app.up.railway.app/api/generate-email \
  -H "X-API-Key: votre-cle-secrete" \
  -H "Content-Type: application/json" \
  -d '{
    "contact": {
      "company_name": "Test Corp",
      "first_name": "Jean",
      "website": "https://example.com",
      "industry": "Tech"
    }
  }'
```

### Étape 4: Utiliser dans Clay

Dans Clay, HTTP Request enrichment:
- URL: `https://votre-app.up.railway.app/api/generate-email`
- Headers: `X-API-Key: votre-cle-secrete`
- Body: (voir GUIDE_CLAY.md)

---

## Option 2: Render.com (Alternative Gratuite)

### Étape 1: Web Service

1. Allez sur [render.com](https://render.com)

2. **New** → **Web Service**

3. **Connect GitHub repo**

4. Configuration:
   - Name: `email-generator-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements-test.txt`
   - Start Command: `uvicorn src.api.clay_compatible_api:app --host 0.0.0.0 --port $PORT`

5. **Environment Variables**:
   ```
   OPENAI_API_KEY=sk-proj-...
   API_KEY=votre-cle-secrete
   ```

6. **Create Web Service**

7. **URL**: `https://votre-app.onrender.com`

---

## Option 3: Vercel (Serverless)

### Prérequis

Modifiez `src/api/clay_compatible_api.py` pour Vercel:

```python
# Ajoutez en haut du fichier
from mangum import Mangum

# Ajoutez en bas du fichier
handler = Mangum(app)
```

### Fichier vercel.json

Créez `vercel.json`:
```json
{
  "builds": [
    {
      "src": "src/api/clay_compatible_api.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "src/api/clay_compatible_api.py"
    }
  ]
}
```

### Déployer

```bash
# Installer Vercel CLI
npm install -g vercel

# Déployer
vercel

# Variables d'environnement
vercel env add OPENAI_API_KEY
vercel env add API_KEY

# URL: https://votre-app.vercel.app
```

---

## Option 4: Local + ngrok (Pour Tests Rapides)

### Étape 1: Démarrer l'API localement

```bash
python -m uvicorn src.api.clay_compatible_api:app --reload --port 8000
```

### Étape 2: Exposer avec ngrok

```bash
# Installer ngrok
# https://ngrok.com/download

# Exposer le port 8000
ngrok http 8000

# Notez l'URL: https://xxxx-xx-xx.ngrok-free.app
```

### Étape 3: Utiliser dans Clay

**⚠️ Attention**: L'URL ngrok change à chaque redémarrage!

Pour une URL fixe:
- Créez un compte ngrok
- Utilisez: `ngrok http 8000 --domain=votre-domain.ngrok-free.app`

---

## Monitoring

### Railway

- Logs en temps réel: Dashboard → Logs
- Métriques: CPU, Memory, Network
- Alertes: Settings → Notifications

### Render

- Logs: Dashboard → Logs
- Metrics: Dashboard → Metrics
- Alertes: Settings → Notifications

### Custom Monitoring

Ajoutez Sentry pour tracking des erreurs:

```bash
pip install sentry-sdk[fastapi]
```

Dans `clay_compatible_api.py`:
```python
import sentry_sdk

sentry_sdk.init(
    dsn="https://xxx@xxx.ingest.sentry.io/xxx",
    traces_sample_rate=1.0,
)
```

---

## Scaling

### Railway

- Free tier: 500h/mois, 512MB RAM
- Pro: $5/mois, 8GB RAM
- Auto-scaling: Oui

### Render

- Free tier: 750h/mois, 512MB RAM
- Starter: $7/mois, 512MB RAM
- Auto-scaling: Plan payant

### Performance

Pour 1,000 requêtes/jour:
- Railway/Render Free: ✅ Suffisant
- Pour 10,000+ requêtes/jour: Plan payant recommandé

---

## Troubleshooting

### Build Failed

```
Cause: requirements-test.txt non trouvé

Solution:
1. Vérifiez que requirements-test.txt est à la racine
2. Ou spécifiez: pip install -r requirements.txt
```

### Import Error

```
Cause: Structure de dossiers incorrecte

Solution:
1. Assurez-vous que src/__init__.py existe
2. Ou ajoutez au Procfile: PYTHONPATH=.
```

### Timeout 500

```
Cause: Génération trop lente (>30s)

Solution:
1. Augmentez le timeout (Railway: Settings → Timeout)
2. Utilisez gpt-4o-mini au lieu de gpt-4o
```

---

## Coûts

### Hébergement

| Provider | Free Tier | Prix Pro |
|----------|-----------|----------|
| Railway | 500h/mois | $5/mois |
| Render | 750h/mois | $7/mois |
| Vercel | Illimité* | $20/mois |

*Limite: 100GB bandwidth, 100h serverless

### OpenAI

- gpt-4o-mini: $0.15/$0.60 per 1M tokens
- 1,000 emails: ~$1.20
- 10,000 emails: ~$12

### Total pour 1,000 emails/mois

- Hébergement: $0 (free tier)
- OpenAI: $1.20
- **Total: $1.20/mois**

---

## Checklist de Déploiement

- [ ] Code pushé sur GitHub
- [ ] requirements-test.txt à jour
- [ ] Procfile créé
- [ ] Variables d'environnement configurées (OPENAI_API_KEY, API_KEY)
- [ ] API déployée
- [ ] Endpoint /health accessible
- [ ] Test avec curl réussi
- [ ] Configuré dans Clay
- [ ] Test avec 1 ligne Clay réussi
- [ ] Logs/monitoring configurés
- [ ] URL documentée pour l'équipe

---

## Commandes Rapides

```bash
# Test local
python -m uvicorn src.api.clay_compatible_api:app --reload --port 8000

# Test health check
curl http://localhost:8000/health

# Test endpoint complet
curl -X POST http://localhost:8000/api/generate-email \
  -H "X-API-Key: test" \
  -H "Content-Type: application/json" \
  -d '{"contact": {"company_name": "Test", "first_name": "Jean", "website": "https://test.com"}}'

# Déployer sur Railway (avec Railway CLI)
railway login
railway init
railway up

# Déployer sur Render
git push origin main
# (webhook automatique si configuré)
```

---

Bon déploiement! 🚀
