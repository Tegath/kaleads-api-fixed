# 📊 Google Sheets Templates - Structure des Colonnes

Templates de colonnes pour créer vos Google Sheets de lead generation.

---

## 📋 Template 1: Google Maps Leads

**Nom suggéré**: `[Client] - Google Maps Leads`
**Exemple**: `Kaleads - Google Maps`

### Colonnes (Header Row 1)

Copier-coller cette ligne dans votre Google Sheet:

```
company_name	phone	website	address	city	rating	reviews_count	place_id	search_query	client_id	campaign_id	date_scraped	source	enriched	email	linkedin_url	linkedin_company	industry	status
```

### Description des Colonnes

| Colonne | Type | Description | Rempli par |
|---------|------|-------------|------------|
| `company_name` | Text | Nom de l'entreprise | API (Google Maps) |
| `phone` | Text | Téléphone | API (Google Maps) |
| `website` | URL | Site web | API (Google Maps) |
| `address` | Text | Adresse complète | API (Google Maps) |
| `city` | Text | Ville | API (Google Maps) |
| `rating` | Number | Note Google (0-5) | API (Google Maps) |
| `reviews_count` | Number | Nombre d'avis | API (Google Maps) |
| `place_id` | Text | Google Place ID unique | API (Google Maps) |
| `search_query` | Text | Mot-clé utilisé pour trouver | API (Google Maps) |
| `client_id` | Text | ID du client Kaleads | n8n (Transform) |
| `campaign_id` | Text | ID de la campagne (ex: kaleads_2025-11-17) | n8n (Transform) |
| `date_scraped` | DateTime | Date/heure du scraping | n8n (Transform) |
| `source` | Text | Source (toujours "google_maps") | n8n (Transform) |
| `enriched` | Boolean | Lead enrichi? (TRUE/FALSE) | Manuel/Clay |
| `email` | Email | Email enrichi | Clay/Enrichissement |
| `linkedin_url` | URL | LinkedIn du décideur | Clay/Enrichissement |
| `linkedin_company` | URL | LinkedIn de l'entreprise | Clay/Enrichissement |
| `industry` | Text | Industrie détectée | Clay/Enrichissement |
| `status` | Text | Statut (new/contacted/replied/qualified) | Manuel/CRM |

### Exemple de Ligne

```
Aircall | +33 1 23 45 67 89 | https://aircall.io | 123 rue de Paris, 75001 Paris | Paris | 4.5 | 234 | ChIJ... | agence SaaS | kaleads | kaleads_2025-11-17 | 2025-11-17T10:30:00Z | google_maps | FALSE | | | | | new
```

---

## 💼 Template 2: JobSpy Leads (Hiring Signals)

**Nom suggéré**: `[Client] - JobSpy Hiring Signals`
**Exemple**: `Kaleads - JobSpy`

### Colonnes (Header Row 1)

Copier-coller cette ligne dans votre Google Sheet:

```
company_name	website	job_title	location	company_size	posted_date	job_url	hiring_signal	job_board	client_id	campaign_id	date_scraped	source	enriched	email	phone	linkedin_url	linkedin_company	industry	status
```

### Description des Colonnes

| Colonne | Type | Description | Rempli par |
|---------|------|-------------|------------|
| `company_name` | Text | Nom de l'entreprise | API (JobSpy) |
| `website` | URL | Site web | API (JobSpy) |
| `job_title` | Text | Poste recherché | API (JobSpy) |
| `location` | Text | Localisation du poste | API (JobSpy) |
| `company_size` | Text | Taille entreprise (ex: 11-50) | API (JobSpy) |
| `posted_date` | Date | Date de publication offre | API (JobSpy) |
| `job_url` | URL | Lien vers l'offre | API (JobSpy) |
| `hiring_signal` | Text | Signal détecté (ex: "Recruiting for Sales = Need leads") | API (JobSpy) |
| `job_board` | Text | Source (LinkedIn, Indeed, etc.) | API (JobSpy) |
| `client_id` | Text | ID du client Kaleads | n8n (Transform) |
| `campaign_id` | Text | ID de la campagne | n8n (Transform) |
| `date_scraped` | DateTime | Date/heure du scraping | n8n (Transform) |
| `source` | Text | Source (toujours "jobspy") | n8n (Transform) |
| `enriched` | Boolean | Lead enrichi? (TRUE/FALSE) | Manuel/Clay |
| `email` | Email | Email enrichi | Clay/Enrichissement |
| `phone` | Text | Téléphone enrichi | Clay/Enrichissement |
| `linkedin_url` | URL | LinkedIn du recruteur/décideur | Clay/Enrichissement |
| `linkedin_company` | URL | LinkedIn de l'entreprise | Clay/Enrichissement |
| `industry` | Text | Industrie détectée | Clay/Enrichissement |
| `status` | Text | Statut (new/contacted/replied/qualified) | Manuel/CRM |

### Exemple de Ligne

```
Aircall | https://aircall.io | Head of Sales France | Paris | 51-200 | 2025-11-10 | https://linkedin.com/jobs/... | Recruiting for Head of Sales = Need leads/pipeline | LinkedIn Jobs | kaleads | kaleads_2025-11-17 | 2025-11-17T10:35:00Z | jobspy | FALSE | | | | | | new
```

---

## 🎯 Template 3: Master List (Leads Consolidés)

**Nom suggéré**: `[Client] - Master List`
**Exemple**: `Kaleads - Master List`

Cette sheet regroupe tous les leads qualifiés après enrichissement et déduplication.

### Colonnes (Header Row 1)

```
company_name	website	source	city	industry	company_size	phone	email	linkedin_url	linkedin_company	icp_score	icp_match	enriched	status	assigned_to	notes	campaign_id	date_added	last_contacted
```

### Description des Colonnes

| Colonne | Type | Description |
|---------|------|-------------|
| `company_name` | Text | Nom de l'entreprise |
| `website` | URL | Site web |
| `source` | Text | Source d'origine (google_maps/jobspy/linkedin) |
| `city` | Text | Ville principale |
| `industry` | Text | Industrie (SaaS, Tech, Consulting, etc.) |
| `company_size` | Text | Taille (11-50, 51-200, etc.) |
| `phone` | Text | Téléphone |
| `email` | Email | Email du décideur |
| `linkedin_url` | URL | LinkedIn du décideur |
| `linkedin_company` | URL | LinkedIn de l'entreprise |
| `icp_score` | Number | Score ICP (0-100) |
| `icp_match` | Boolean | Match ICP? (TRUE/FALSE) |
| `enriched` | Boolean | Lead enrichi? (TRUE/FALSE) |
| `status` | Text | new/contacted/replied/meeting_scheduled/qualified/not_interested |
| `assigned_to` | Text | Nom du commercial assigné |
| `notes` | Text | Notes libres |
| `campaign_id` | Text | Campagne d'origine |
| `date_added` | DateTime | Date ajout à la master list |
| `last_contacted` | DateTime | Dernière date de contact |

### Exemple de Ligne

```
Aircall | https://aircall.io | jobspy | Paris | SaaS | 51-200 | +33 1 23 45 67 89 | sales@aircall.io | https://linkedin.com/in/john-doe | https://linkedin.com/company/aircall | 92 | TRUE | TRUE | contacted | Jean Dupont | Très intéressé par notre offre | kaleads_2025-11-17 | 2025-11-17T14:00:00Z | 2025-11-18T09:30:00Z
```

---

## 🔍 Template 4: Feuille de Déduplication (Optionnel)

**Nom suggéré**: `[Client] - Dedup Tracker`

Pour éviter les doublons entre sources.

### Colonnes

```
company_name	website	normalized_name	found_in_google_maps	found_in_jobspy	found_in_linkedin	total_sources	keep_source	merged_to_master	date_processed
```

### Usage

1. Extraire tous les company_name + website de toutes les sources
2. Normaliser les noms (lowercase, trim, remove "sarl", "sas", etc.)
3. Compter combien de fois chaque entreprise apparaît
4. Choisir la meilleure source (priority: jobspy > google_maps > linkedin)
5. Merger vers Master List

---

## 🎨 Formatage Recommandé

### Couleurs

**Header Row (Ligne 1)**:
- Background: `#4285F4` (Bleu Google)
- Text: Blanc, Gras
- Freeze Row: Oui

**Colonnes de Tracking** (client_id, campaign_id, date_scraped, source):
- Background: `#F3F3F3` (Gris clair)

**Colonne `enriched`**:
- `FALSE` → Background rouge clair (`#FFEBEE`)
- `TRUE` → Background vert clair (`#E8F5E9`)

**Colonne `status`**:
- `new` → Blanc
- `contacted` → Jaune clair (`#FFF9C4`)
- `replied` → Orange clair (`#FFE0B2`)
- `qualified` → Vert clair (`#E8F5E9`)
- `not_interested` → Rouge clair (`#FFEBEE`)

### Filtres

Activer les filtres sur la ligne 1 (Data → Create a filter).

### Protection

Protéger les colonnes remplies automatiquement par n8n:
- `client_id`, `campaign_id`, `date_scraped`, `source`
- Permissions: View only (sauf pour n8n service account)

---

## 📐 Formules Utiles

### 1. Détecter les Doublons

Dans une colonne `is_duplicate`:
```
=COUNTIF(A:A, A2) > 1
```

### 2. Calculer ICP Score (Exemple Simple)

Dans une colonne `icp_score`:
```
=IF(AND(Q2="SaaS", R2="51-200", S2="Paris"), 100,
  IF(AND(Q2="Tech", R2="11-50"), 75,
    IF(Q2="SaaS", 60, 30)))
```

Où:
- Q2 = industry
- R2 = company_size
- S2 = city

### 3. Déterminer ICP Match

Dans une colonne `icp_match`:
```
=IF(icp_score >= 70, TRUE, FALSE)
```

### 4. Temps Écoulé depuis Scraping

Dans une colonne `days_since_scraped`:
```
=TODAY() - L2
```
Où L2 = date_scraped

### 5. Priorisation (Score Pondéré)

Dans une colonne `priority_score`:
```
=(icp_score * 0.5) + (IF(source="jobspy", 30, 0)) + (IF(days_since_scraped < 7, 20, 0))
```

---

## 🚀 Quick Setup Commands

### Créer les Sheets via API (Optionnel)

Si tu veux automatiser la création des sheets:

```python
from google.oauth2 import service_account
from googleapiclient.discovery import build

# Credentials
creds = service_account.Credentials.from_service_account_file('credentials.json')
service = build('sheets', 'v4', credentials=creds)

# Create spreadsheet
spreadsheet = {
    'properties': {'title': 'Kaleads - Google Maps'},
    'sheets': [{
        'properties': {'title': 'Sheet1'},
        'data': [{
            'rowData': [{
                'values': [
                    {'userEnteredValue': {'stringValue': 'company_name'}},
                    {'userEnteredValue': {'stringValue': 'phone'}},
                    # ... etc
                ]
            }]
        }]
    }]
}

result = service.spreadsheets().create(body=spreadsheet).execute()
print(f"Created: {result.get('spreadsheetId')}")
```

---

## ✅ Checklist Setup

Pour chaque client:

- [ ] Créer Google Sheet "Google Maps"
- [ ] Créer Google Sheet "JobSpy"
- [ ] Créer Google Sheet "Master List" (optionnel)
- [ ] Copier les headers de colonnes
- [ ] Activer les filtres (ligne 1)
- [ ] Formater les couleurs
- [ ] Freeze la ligne 1 (header)
- [ ] Partager avec le compte OAuth n8n (Editor access)
- [ ] Copier les Sheet IDs
- [ ] Configurer les IDs dans le workflow n8n
- [ ] Tester avec 10 leads
- [ ] Vérifier le formatage des données
- [ ] Lancer en production

---

## 📞 Support

Si colonnes manquantes ou format incorrect:
1. Vérifier les logs n8n (node "Transform Data")
2. Vérifier que les headers matchent exactement (sensible à la casse)
3. Utiliser "Auto-map" dans les nodes Google Sheets n8n

