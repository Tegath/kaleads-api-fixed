# Guide Simple: Générer et Corriger des Emails

## Problème Résolu

❌ **Avant**: Le terminal ne permet pas de coller des emails multi-lignes
✅ **Maintenant**: Vous éditez un fichier texte dans votre éditeur favori!

---

## Méthode Simple en 3 Étapes

### Étape 1: Générer l'Email Initial

```bash
python test_simple.py
```

**Ce qui se passe**:
1. Génère un email avec le contact par défaut (Aircall)
2. Sauvegarde dans `output/current_email.txt`
3. Affiche les métriques (quality score, fallback levels, etc.)

**Output**:
```
[OK] Email sauvegarde: output/current_email.txt

[*] PROCHAINE ETAPE:
1. Ouvrez output/current_email.txt dans votre editeur de texte
2. Ajoutez votre feedback a la fin du fichier
3. Sauvegardez
4. Relancez: python test_simple.py --regenerate
```

---

### Étape 2: Donner Votre Feedback

Ouvrez `output/current_email.txt` dans votre éditeur (VSCode, Notepad++, etc.)

**Le fichier ressemble à ça**:
```
============================================================
EMAIL GENERE - A REVIEWER
============================================================

Contact: Aircall
Quality Score: 76/100
Generation Time: 22921ms

Fallback Levels:
  [OK] persona_agent: Level 2
  [OK] competitor_agent: Level 1
  ...

------------------------------------------------------------
CONTENU:
------------------------------------------------------------

Bonjour Sophie,

entreprises SaaS de 100-500 employés...

[... le reste de l'email ...]

============================================================
FEEDBACK (A REMPLIR)
============================================================

RATING (1-4):
1 = Parfait
2 = Bon mais ajustements mineurs
3 = Moyen, corrections importantes
4 = Mauvais, a regenerer

Votre rating: [ECRIVEZ ICI]

PROBLEMES IDENTIFIES:
[ECRIVEZ ICI - Ex: persona incorrect, pain point vague]


CORRECTIONS DETAILLEES:
[ECRIVEZ ICI - Soyez specifique]
Ex:
- Le persona devrait etre VP Sales pas Customer Support Manager
- Le pain point devrait mentionner la perte de temps concrete
- Le ton doit etre plus formel


EXEMPLE D'EMAIL IDEAL (optionnel):
[COLLEZ ICI votre exemple si vous avez une vision precise]
```

**Remplissez le feedback**:
```
Votre rating: 3

PROBLEMES IDENTIFIES:
persona incorrect, pain point trop vague, manque de chiffres ROI

CORRECTIONS DETAILLEES:
- Le persona devrait etre VP Sales ou CRO, pas customer support manager
- Le pain point doit mentionner la perte concrete de leads (20-30%)
- Ajouter un chiffre ROI dans le case study (+40% de conversion minimum)
- Le ton doit etre plus corporate et moins casual

EXEMPLE D'EMAIL IDEAL (optionnel):
Bonjour Sophie,

J'ai remarqué qu'Aircall aide les équipes sales à améliorer leur productivité.

Le défi que je vois souvent chez les scale-ups SaaS: les VP Sales perdent
20-30% de leurs leads qualifiés à cause d'un temps de réponse trop lent.

Chez [CLIENT], nous aidons les VP Sales comme vous à résoudre ce problème
en remplaçant [concurrent] par notre solution de routage intelligent.

Résultat concret: +42% de conversion en 6 mois chez un de nos clients SaaS
(150 employés).

Intéressé(e) pour échanger 15min cette semaine?

Cordialement,
[SIGNATURE]
```

**Sauvegardez le fichier!**

---

### Étape 3: Régénérer avec Corrections

```bash
python test_simple.py --regenerate
```

**Ce qui se passe**:
1. Lit votre feedback dans `output/current_email.txt`
2. Archive l'ancien email → `output/email_v1_YYYYMMDD-HHMMSS.txt`
3. Régénère avec vos corrections
4. Sauvegarde le nouvel email → `output/current_email.txt`

**Output**:
```
[OK] Feedback charge:
  Rating: 3
  Problemes: persona incorrect, pain point trop vague
  Corrections: 4

[*] Ancien email archive: output/email_v1_20250106-143022.txt
[*] Regeneration avec feedback...
[OK] Email sauvegarde: output/current_email.txt

============================================================
COMPARAISON AVANT/APRES
============================================================

Email AVANT: output/email_v1_20250106-143022.txt
Email APRES: output/current_email.txt

Ouvrez les 2 fichiers cote a cote pour comparer!
```

---

## Itérations Multiples

Vous pouvez répéter le cycle autant de fois que nécessaire:

```bash
# 1. Generer
python test_simple.py

# 2. Editer output/current_email.txt (ajouter feedback)

# 3. Regenerer
python test_simple.py --regenerate

# 4. Editer output/current_email.txt (ajouter nouveau feedback)

# 5. Regenerer encore
python test_simple.py --regenerate

# etc...
```

**Tous les emails sont archivés**:
- `output/email_v1_YYYYMMDD-HHMMSS.txt`
- `output/email_v2_YYYYMMDD-HHMMSS.txt`
- `output/email_v3_YYYYMMDD-HHMMSS.txt`

---

## Personnaliser le Contact et Directives

### Méthode 1: Éditer config_email.json

À la première exécution, un fichier `config_email.json` est créé:

```json
{
  "contact": {
    "company_name": "Aircall",
    "first_name": "Sophie",
    "last_name": "Durand",
    "email": "sophie@aircall.io",
    "website": "https://aircall.io",
    "industry": "SaaS"
  },
  "template_path": "data/templates/cold_email_template_example.md",
  "directives": "Ton professionnel, focus sur le ROI mesurable"
}
```

**Éditez-le pour personnaliser**:
```json
{
  "contact": {
    "company_name": "Stripe",
    "first_name": "Jean",
    "last_name": "Martin",
    "email": "jean@stripe.com",
    "website": "https://stripe.com",
    "industry": "FinTech"
  },
  "template_path": "data/templates/cold_email_template_example.md",
  "directives": "Ton tres corporate, focus ROI quantifiable, eviter jargon technique, public CFO/VP Finance"
}
```

Puis relancez:
```bash
python test_simple.py
```

---

## Comparer Plusieurs Versions

Ouvrez plusieurs fichiers dans votre éditeur:

**VSCode**:
```bash
code output/email_v1_*.txt output/email_v2_*.txt output/current_email.txt
```

**Notepad++**:
```
Fichier > Ouvrir > Sélectionner les 3 fichiers
```

**Comparaison côte à côte**:
- Version 1 (gauche)
- Version 2 (milieu)
- Version finale (droite)

---

## Exemples de Feedback Efficace

### Exemple 1: Persona Incorrect

**Feedback**:
```
Votre rating: 3

PROBLEMES IDENTIFIES:
persona incorrect

CORRECTIONS DETAILLEES:
- Le persona devrait etre VP Sales ou CRO, pas customer support manager
- Pour une entreprise SaaS comme Aircall, le decision maker est VP Sales
```

### Exemple 2: Manque de ROI

**Feedback**:
```
Votre rating: 3

PROBLEMES IDENTIFIES:
case study trop vague, manque chiffres ROI

CORRECTIONS DETAILLEES:
- Le case study doit contenir un chiffre de ROI precis (+40% minimum)
- Ajouter la duree (6 mois, 1 an)
- Mentionner la taille de l'entreprise du case study (ex: 150 employees)
```

### Exemple 3: Ton Incorrect

**Feedback**:
```
Votre rating: 2

PROBLEMES IDENTIFIES:
ton trop casual

CORRECTIONS DETAILLEES:
- Remplacer "Interesse?" par "Souhaitez-vous echanger sur le sujet?"
- Eviter les contractions (j'ai → je suis)
- Utiliser "Cordialement" au lieu de "Belle journee"
```

### Exemple 4: Email Complet Ideal

**Feedback**:
```
Votre rating: 4

PROBLEMES IDENTIFIES:
structure complete a revoir

CORRECTIONS DETAILLEES:
- Suivre exactement l'exemple ci-dessous

EXEMPLE D'EMAIL IDEAL:
Bonjour {{first_name}},

J'ai remarqué que {{company_name}} aide les équipes à optimiser
leur productivité avec une solution de téléphonie cloud.

Le défi que je constate souvent: les VP Sales perdent 25% de leurs
leads qualifiés à cause d'un temps de réponse supérieur à 5 minutes.

Chez MonEntreprise, nous aidons les VP Sales comme vous à résoudre
ce problème en remplaçant {{competitor_name}} par notre solution
de routage intelligent et prédictif.

Résultat concret chez un de nos clients SaaS (200 employés):
+45% de taux de conversion en 6 mois, soit 180K€ de revenue additionnel.

Seriez-vous intéressé(e) pour échanger 15 minutes cette semaine?

Cordialement,
Marc Dubois
CEO, MonEntreprise
```

---

## Avantages de Cette Méthode

✅ **Pas de problème de terminal**: Éditez dans votre éditeur préféré
✅ **Feedback multi-lignes**: Collez des emails complets comme exemple
✅ **Historique complet**: Tous les emails sont sauvegardés
✅ **Comparaison facile**: Ouvrez plusieurs versions côte à côte
✅ **Configuration persistante**: `config_email.json` sauvegarde vos préférences
✅ **Simple et rapide**: 2 commandes seulement

---

## Workflow Idéal

```
1. Editez config_email.json (contact + directives)
   ↓
2. python test_simple.py
   ↓
3. Ouvrez output/current_email.txt
   ↓
4. Ajoutez votre feedback (rating + corrections + exemple optionnel)
   ↓
5. Sauvegardez
   ↓
6. python test_simple.py --regenerate
   ↓
7. Comparez output/email_v1_*.txt avec output/current_email.txt
   ↓
8. Si pas satisfait: retour à l'étape 3
   ↓
9. Si satisfait: email final prêt!
```

---

## Raccourcis

```bash
# Génération initiale
python test_simple.py

# Régénération (alias court)
python test_simple.py -r

# Tout en une ligne (Windows)
python test_simple.py && code output\current_email.txt

# Comparer les versions
code output\email_v*.txt output\current_email.txt
```

---

## FAQ

**Q: Puis-je utiliser mon propre template?**
R: Oui! Éditez `config_email.json`:
```json
{
  "template_path": "mon_template_perso.md",
  ...
}
```

**Q: Comment tester plusieurs contacts?**
R: Utilisez plutôt `test_batch.py` pour ça. `test_simple.py` est pour peaufiner UN email.

**Q: Les corrections sont-elles permanentes?**
R: Non, chaque régénération utilise le template original + vos corrections. Pour rendre permanentes les améliorations, modifiez `src/agents/agents_v2.py`.

**Q: Puis-je supprimer les vieux emails?**
R: Oui, supprimez `output/email_v*.txt` quand vous voulez.

---

## Prochaine Étape

```bash
# Testez maintenant!
python test_simple.py

# Puis ouvrez et éditez:
code output/current_email.txt  # ou notepad++ ou autre

# Puis régénérez:
python test_simple.py -r
```

C'est tout! 🚀
