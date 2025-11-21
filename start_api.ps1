# start_api.ps1
# Script pour démarrer l'API Kaleads en local

Write-Host ""
Write-Host "🚀 Démarrage API Kaleads Lead Generation" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Vérifier qu'on est dans le bon dossier
if (-not (Test-Path "src/api/n8n_optimized_api.py")) {
    Write-Host "❌ Erreur: Pas dans le bon dossier!" -ForegroundColor Red
    Write-Host "   Naviguez vers: kaleads-atomic-agents" -ForegroundColor Yellow
    exit 1
}

# Activer le venv
Write-Host "📦 Activation de l'environnement virtuel..." -ForegroundColor Yellow
if (Test-Path "venv\Scripts\Activate.ps1") {
    & ".\venv\Scripts\Activate.ps1"
    Write-Host "   ✅ venv activé" -ForegroundColor Green
} else {
    Write-Host "   ❌ venv introuvable! Créer avec: python -m venv venv" -ForegroundColor Red
    exit 1
}

# Vérifier que supabase est installé
Write-Host ""
Write-Host "🔍 Vérification des dépendances..." -ForegroundColor Yellow
$supabaseInstalled = python -c "import supabase" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "   ⚠️  Module 'supabase' non trouvé. Installation..." -ForegroundColor Yellow
    pip install supabase | Out-Null
    Write-Host "   ✅ supabase installé" -ForegroundColor Green
} else {
    Write-Host "   ✅ Toutes les dépendances OK" -ForegroundColor Green
}

# Définir les variables d'environnement
Write-Host ""
Write-Host "🔐 Configuration Supabase..." -ForegroundColor Yellow
$env:SUPABASE_URL = "https://ckrspaktqohjenqfuuzl.supabase.co"
$env:SUPABASE_SERVICE_ROLE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImNrcnNwYWt0cW9oamVucWZ1dXpsIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MjYxNjQyMiwiZXhwIjoyMDc4MTkyNDIyfQ.uxZKZuCqZJnadg7ysnliZ5M4TfcKIl5jbW-eR1mpiBU"
Write-Host "   ✅ Variables d'environnement configurées" -ForegroundColor Green

# Démarrer l'API
Write-Host ""
Write-Host "✅ Démarrage du serveur API..." -ForegroundColor Green
Write-Host ""
Write-Host "   📍 URL: http://localhost:8001" -ForegroundColor Cyan
Write-Host "   📚 Documentation: http://localhost:8001/docs" -ForegroundColor Cyan
Write-Host "   ❤️  Health Check: http://localhost:8001/health" -ForegroundColor Cyan
Write-Host ""
Write-Host "   💡 Endpoints disponibles:" -ForegroundColor White
Write-Host "      - POST /api/v2/coordinator/analyze" -ForegroundColor Gray
Write-Host "      - POST /api/v2/leads/google-maps" -ForegroundColor Gray
Write-Host "      - POST /api/v2/leads/jobspy" -ForegroundColor Gray
Write-Host ""
Write-Host "   🧪 Pour tester: Ouvrir un nouveau terminal et lancer:" -ForegroundColor White
Write-Host "      python test_api_quick.py" -ForegroundColor Cyan
Write-Host ""
Write-Host "   🛑 Pour arrêter: Appuyez sur Ctrl+C" -ForegroundColor Yellow
Write-Host ""
Write-Host "=========================================" -ForegroundColor Green
Write-Host ""

# Lancer uvicorn
python -m uvicorn src.api.n8n_optimized_api:app --host 0.0.0.0 --port 8001 --reload










