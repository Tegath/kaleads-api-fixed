@echo off
echo ========================================
echo Installation du systeme de campagne email
echo ========================================

echo.
echo [1/4] Verification de Python...
python --version
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

echo.
echo [2/4] Creation de l'environnement virtuel...
if not exist venv (
    python -m venv venv
    echo Environnement virtuel cree
) else (
    echo Environnement virtuel existe deja
)

echo.
echo [3/4] Activation et installation des dependances...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements-test.txt

echo.
echo [4/4] Configuration de l'environnement...
if not exist .env (
    copy .env.example .env
    echo Fichier .env cree - IMPORTANT: Ajoutez votre OPENAI_API_KEY!
) else (
    echo Fichier .env existe deja
)

echo.
echo ========================================
echo Installation terminee!
echo ========================================
echo.
echo Prochaines etapes:
echo 1. Editez .env et ajoutez votre OPENAI_API_KEY
echo 2. Lancez: venv\Scripts\activate.bat
echo 3. Testez: python test_campaign.py
echo.
pause
