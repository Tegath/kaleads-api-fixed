#!/bin/bash

# Script de test pour déploiement Docker v3.0
# Usage: bash test_docker_deployment.sh

echo "======================================"
echo "🧪 Test Déploiement v3.0"
echo "======================================"

# Configuration
API_URL="http://localhost:8001"
API_KEY="your-secure-api-key-for-n8n"  # ⚠️ REMPLACE avec ta vraie clé
CLIENT_ID="ton-client-uuid"  # ⚠️ REMPLACE avec un vrai client_id

echo ""
echo "1️⃣ Health Check..."
HEALTH=$(curl -s $API_URL/health)
VERSION=$(echo $HEALTH | grep -o '"version":"[^"]*"' | cut -d'"' -f4)
echo "   Version: $VERSION"

if [ "$VERSION" = "3.0.0" ]; then
    echo "   ✅ v3.0 déployé"
else
    echo "   ❌ Version incorrecte: $VERSION"
    exit 1
fi

echo ""
echo "2️⃣ Vérification Agents v3..."
ROOT=$(curl -s $API_URL/)
if echo $ROOT | grep -q "PersonaExtractorV3"; then
    echo "   ✅ Agents v3 présents"
else
    echo "   ❌ Agents v3 manquants"
    exit 1
fi

echo ""
echo "3️⃣ Test Configuration..."
TAVILY=$(echo $HEALTH | grep -o '"tavily_configured":[^,}]*' | cut -d':' -f2)
SUPABASE=$(echo $HEALTH | grep -o '"supabase_configured":[^,}]*' | cut -d':' -f2)
OPENROUTER=$(echo $HEALTH | grep -o '"openrouter_key_configured":[^,}]*' | cut -d':' -f2)

echo "   - Tavily: $TAVILY"
echo "   - Supabase: $SUPABASE"
echo "   - OpenRouter: $OPENROUTER"

if [ "$TAVILY" = "true" ] && [ "$SUPABASE" = "true" ] && [ "$OPENROUTER" = "true" ]; then
    echo "   ✅ Toutes les clés configurées"
else
    echo "   ⚠️  Certaines clés manquantes"
fi

echo ""
echo "4️⃣ Test Génération Email (IMPORTANT)..."
echo "   ⏳ Envoi requête..."

RESPONSE=$(curl -s -X POST $API_URL/api/v2/generate-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d "{
    \"client_id\": \"$CLIENT_ID\",
    \"contact\": {
      \"company_name\": \"Aircall\",
      \"first_name\": \"Sophie\",
      \"last_name\": \"Martin\",
      \"website\": \"https://aircall.io\",
      \"industry\": \"SaaS\"
    },
    \"options\": {
      \"enable_tavily\": true,
      \"enable_scraping\": false,
      \"enable_pci_filter\": false
    }
  }")

# Vérifier succès
if echo $RESPONSE | grep -q '"success":true'; then
    echo "   ✅ Email généré avec succès"

    # Extraire métriques
    PERSONA=$(echo $RESPONSE | grep -o '"target_persona":"[^"]*"' | cut -d'"' -f4)
    COMPETITOR=$(echo $RESPONSE | grep -o '"competitor_name":"[^"]*"' | cut -d'"' -f4)
    QUALITY=$(echo $RESPONSE | grep -o '"quality_score":[0-9]*' | cut -d':' -f2)
    TIME=$(echo $RESPONSE | grep -o '"generation_time_seconds":[0-9.]*' | cut -d':' -f2)

    echo ""
    echo "   📊 Métriques:"
    echo "      - Persona: $PERSONA"
    echo "      - Concurrent: $COMPETITOR"
    echo "      - Quality: $QUALITY/100"
    echo "      - Temps: ${TIME}s"

    # Vérifier fallback levels
    echo ""
    echo "   🎯 Fallback Levels:"
    echo $RESPONSE | grep -o '"fallback_levels":\{[^}]*\}' | sed 's/[{},"]//g' | sed 's/:/: /g'

    # Sauvegarder résultat
    echo $RESPONSE | python3 -m json.tool > /tmp/last_test_result.json
    echo ""
    echo "   💾 Résultat complet sauvegardé: /tmp/last_test_result.json"

elif echo $RESPONSE | grep -q '"detail"'; then
    echo "   ❌ Erreur API"
    ERROR=$(echo $RESPONSE | grep -o '"detail":"[^"]*"' | cut -d'"' -f4)
    echo "   Détail: $ERROR"
    exit 1
else
    echo "   ❌ Réponse inattendue"
    echo $RESPONSE
    exit 1
fi

echo ""
echo "======================================"
echo "✅ Tests Terminés"
echo "======================================"
echo ""
echo "🎉 v3.0 fonctionne correctement!"
echo ""
echo "📝 Prochaines étapes:"
echo "   1. Tester avec plusieurs client_id différents"
echo "   2. Vérifier dans n8n que l'API v3 fonctionne"
echo "   3. Comparer qualité des emails v2 vs v3"
echo ""
