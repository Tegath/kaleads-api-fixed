#!/bin/bash
# Script de déploiement rapide sur Docker

echo "🚀 Déploiement Kaleads API sur Docker..."

# 1. Stopper et supprimer les anciens conteneurs
echo "📦 Nettoyage des anciens conteneurs..."
docker ps -a | grep kaleads-atomic-agents | awk '{print $1}' | xargs docker rm -f 2>/dev/null || true

# 2. Descendre les services
echo "⬇️  Arrêt des services..."
docker-compose down

# 3. Rebuild sans cache
echo "🔨 Rebuild de l'image Docker..."
docker-compose build --no-cache

# 4. Démarrer les services
echo "⬆️  Démarrage des services..."
docker-compose up -d

# 5. Attendre que le service soit prêt
echo "⏳ Attente du démarrage (15 secondes)..."
sleep 15

# 6. Vérifier le health
echo "🏥 Vérification du health check..."
curl -s http://localhost:20001/health | python3 -m json.tool

# 7. Tester le coordinator
echo ""
echo "🧪 Test du coordinator..."
curl -s -X POST http://localhost:20001/api/v2/coordinator/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: lL^nc2U%tU8f2!LH48!29!mW8" \
  -d '{"client_id": "kaleads", "target_count": 500, "country": "France"}' \
  | python3 -m json.tool | head -30

echo ""
echo "✅ Déploiement terminé!"
echo "📊 Logs: docker logs -f kaleads-atomic-agents"
echo "🔗 API: http://92.112.193.183:20001"
