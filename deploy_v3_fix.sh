#!/bin/bash
# Script de déploiement du bug fix v3.0 sur le serveur Docker
# À exécuter sur le serveur 92.112.193.183

echo "========================================"
echo "🚀 Déploiement Bug Fix v3.0"
echo "========================================"
echo ""

# 1. Naviguer vers le projet
echo "1️⃣ Navigation vers le projet..."
cd /root/kaleads-atomic-agents

# 2. Récupérer les dernières modifications
echo ""
echo "2️⃣ Récupération des modifications depuis GitHub..."
git pull origin main

# 3. Arrêter l'ancien conteneur
echo ""
echo "3️⃣ Arrêt du conteneur actuel..."
docker stop kaleads-api-v3
docker rm kaleads-api-v3

# 4. Rebuild l'image Docker
echo ""
echo "4️⃣ Rebuild de l'image Docker (peut prendre 1-2 minutes)..."
docker build -t kaleads-api:v3.0 .

# 5. Relancer le conteneur
echo ""
echo "5️⃣ Démarrage du nouveau conteneur..."
docker run -d \
  --name kaleads-api-v3 \
  --network n8n-network \
  -p 8001:8001 \
  --env-file .env \
  --restart unless-stopped \
  kaleads-api:v3.0

# 6. Attendre le démarrage
echo ""
echo "6️⃣ Attente du démarrage de l'API..."
sleep 5

# 7. Vérifier les logs
echo ""
echo "7️⃣ Logs de démarrage:"
echo "========================================"
docker logs kaleads-api-v3 | tail -20

echo ""
echo "========================================"
echo "✅ Déploiement terminé!"
echo "========================================"
echo ""
echo "📝 Vérifications:"
echo "   - L'API devrait tourner sur http://92.112.193.183:8001"
echo "   - Teste depuis n8n avec la même requête"
echo "   - L'erreur 'pain_point_description' devrait être résolue"
echo ""
echo "💡 Pour voir les logs en temps réel:"
echo "   docker logs -f kaleads-api-v3"
echo ""
