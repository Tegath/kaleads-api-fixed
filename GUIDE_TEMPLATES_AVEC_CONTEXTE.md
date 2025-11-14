# 📧 Guide Templates avec Contexte et Exemples

Guide pratique pour utiliser les templates email avec contexte et exemples parfaits.

---

## 🎯 Concept

Au lieu de juste un template avec des variables, on fournit:

1. **Template**: Le contenu avec `{{variables}}`
2. **Contexte**: Instructions sur le ton, style, approche
3. **Exemple parfait**: Un email de référence qui fonctionne

→ Le système apprend du contexte + exemple pour générer des emails parfaits

---

## 📦 Structure d'un Template Complet

```json
{
  "template_name_v1": {
    "template_content": "Bonjour {{first_name}},...",
    "context": {
      "intention": "Générer un meeting",
      "tone": "Conversational",
      "approach": "Signal + Social proof",
      "style": "Court (< 100 mots)",
      "dos": [
        "Utiliser un signal factuel",
        "Donner une métrique précise"
      ],
      "donts": [
        "Utiliser du jargon",
        "Faire plus de 100 mots"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Aircall",
        "first_name": "Sophie"
      },
      "perfect_email": "L'email parfait complet",
      "why_it_works": "Pourquoi il fonctionne"
    }
  }
}
```

---

## 🚀 Mise en place (3 options)

### Option 1: Configuration dans Supabase (RECOMMANDÉ)

**Avantages**:
- ✅ Réutilisable pour tous les contacts
- ✅ Un seul endroit à mettre à jour
- ✅ Requêtes API plus simples
- ✅ Versionning facile (v1, v2, etc.)

**Étapes**:

1. **Préparer votre configuration SQL**

Utilisez le fichier `supabase_email_templates_examples.sql` comme base:

```sql
UPDATE clients
SET email_templates = '{
  "outreach_signal_v1": {
    "template_content": "Bonjour {{first_name}},...",
    "context": {...},
    "example": {...}
  }
}'::jsonb
WHERE client_id = 'kaleads';
```

2. **Exécuter dans Supabase**

- Aller dans Supabase SQL Editor
- Coller la requête
- Run

3. **Vérifier**

```sql
SELECT
  client_name,
  jsonb_pretty(email_templates)
FROM clients
WHERE client_id = 'kaleads';
```

4. **Utiliser dans l'API**

```json
{
  "client_id": "kaleads",
  "contact": {...},
  "template_name": "outreach_signal_v1",
  "options": {...}
}
```

→ Le système charge automatiquement le template + contexte + exemple depuis Supabase!

---

### Option 2: Inline dans la requête API

**Avantages**:
- ✅ Test rapide sans toucher à Supabase
- ✅ Override ponctuel d'un template

**Inconvénients**:
- ❌ Requête API plus grosse
- ❌ Doit répéter le contexte à chaque fois

**Exemple**:

```json
{
  "client_id": "kaleads",
  "contact": {
    "company_name": "Aircall",
    "first_name": "Sophie",
    "website": "https://aircall.io",
    "industry": "SaaS"
  },
  "template_content": "Bonjour {{first_name}},\n\nJ'ai vu que {{company_name}} {{specific_signal_1}}.\n\n{{case_study_result}}.\n\nÇa vous parle?",
  "template_context": {
    "intention": "Générer un meeting",
    "tone": "Conversational",
    "approach": "Signal + Social proof",
    "style": "Court (< 100 mots)",
    "dos": [
      "Utiliser un signal factuel",
      "Donner une métrique précise",
      "Rester sous 100 mots"
    ],
    "donts": [
      "Utiliser du jargon corporate",
      "Faire un pitch produit"
    ]
  },
  "template_example": {
    "for_contact": {
      "company_name": "Salesforce",
      "first_name": "Jean"
    },
    "perfect_email": "Bonjour Jean,\n\nJ'ai vu que Salesforce recrute 5 commerciaux.\n\nOn a aidé HubSpot à réduire leur ramp-up de 6 à 2 mois.\n\nÇa vous parle?",
    "why_it_works": "Signal factuel + métrique concrète + ton conversational"
  },
  "options": {
    "model_preference": "quality"
  }
}
```

---

### Option 3: Hybride (Supabase + Override)

**Cas d'usage**: Template de base dans Supabase, mais override ponctuel du ton/style

```json
{
  "client_id": "kaleads",
  "contact": {...},
  "template_name": "outreach_signal_v1",
  "template_context_override": {
    "tone": "Ultra casual",
    "dos": [
      "Tutoyer",
      "Utiliser des emojis"
    ]
  },
  "options": {...}
}
```

→ Le système charge le template de Supabase, mais override le contexte

---

## 📝 Exemples d'utilisation

### Exemple 1: Lead Gen (Kaleads)

**Dans Supabase** (`supabase_email_templates_examples.sql`):

```sql
UPDATE clients
SET email_templates = '{
  "outreach_signal_v1": {
    "template_content": "Bonjour {{first_name}},\\n\\nJ''ai remarqué que {{company_name}} {{specific_signal_1}}.\\n\\nEn tant que {{target_persona}}, vous faites probablement face à {{problem_specific}}.\\n\\n{{case_study_result}}.\\n\\nÇa vous parle?",
    "context": {
      "intention": "Générer un meeting avec un décideur Sales/Marketing",
      "tone": "Conversational et direct",
      "approach": "Signal factuel + Empathie + Social proof concret",
      "style": "Court (< 100 mots), question engageante",
      "dos": [
        "Utiliser un signal factuel (hiring, funding, etc.)",
        "Montrer de l''empathie",
        "Donner une métrique précise",
        "Rester sous 100 mots"
      ],
      "donts": [
        "Utiliser du jargon corporate",
        "Faire un pitch produit",
        "Utiliser des superlatifs"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Aircall",
        "first_name": "Sophie",
        "signal": "recrute 3 commerciaux"
      },
      "perfect_email": "Bonjour Sophie,\\n\\nJ''ai vu qu''Aircall recrute 3 commerciaux en ce moment.\\n\\nEn tant que Head of Sales, vous devez chercher à accélérer leur montée en compétence.\\n\\nOn a aidé Salesforce France à réduire leur ramp-up de 6 mois à 2 mois.\\n\\nÇa vous parle?",
      "why_it_works": "Signal factuel (hiring) + empathie (ramp-up) + métrique (6→2 mois) + ton conversational"
    }
  }
}'::jsonb
WHERE client_id = 'kaleads';
```

**Requête API**:

```json
{
  "client_id": "kaleads",
  "contact": {
    "company_name": "Jumppe",
    "first_name": "Cathy",
    "website": "https://www.jumppe.fr",
    "industry": "DevOps"
  },
  "template_name": "outreach_signal_v1",
  "options": {
    "model_preference": "quality",
    "enable_scraping": true,
    "enable_tavily": true
  }
}
```

**Email généré** (suit le contexte + exemple):

```
Bonjour Cathy,

J'ai remarqué que Jumppe recrute actuellement.

En tant que Head of Engineering, vous cherchez probablement à scaler sans recruter 10+ DevOps.

On a aidé Doctolib à passer de 20 à 400 déploiements/semaine en 3 mois.

Ça vous parle?
```

**Qualité**:
- ✅ Tone match: 95/100
- ✅ Guidelines followed: true
- ✅ Formatting corrections: 0 (parfait dès la 1ère génération)

---

### Exemple 2: DevOps Agency (Casual)

**Dans Supabase**:

```sql
UPDATE clients
SET email_templates = '{
  "outreach_cto_v1": {
    "template_content": "Salut {{first_name}},\\n\\nVu que {{company_name}} {{specific_signal_1}}, je suppose que vous scalez.\\n\\n{{case_study_result}}.\\n\\nOn en parle?",
    "context": {
      "intention": "Meeting pour DevOps part-time",
      "tone": "Casual tech-friendly",
      "approach": "Direct + Metrics",
      "style": "Ultra court, aucun fluff",
      "dos": [
        "Tutoyer si possible",
        "Vocabulaire tech (deploys, incidents)",
        "Métriques de vélocité",
        "CTA minimal"
      ],
      "donts": [
        "Vocabulaire marketing/sales",
        "Faire plus de 3 phrases",
        "Expliquer ce qu''on fait"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Ledger",
        "first_name": "Alex",
        "signal": "recrute 5 SREs"
      },
      "perfect_email": "Salut Alex,\\n\\nVu que Ledger recrute 5 SREs, je suppose que vous scalez l''infra.\\n\\nOn a aidé Sorare à passer de 20 à 400 deploys/semaine sans recruiter.\\n\\nOn en parle?",
      "why_it_works": "Casual (Salut), vocab tech, métrique (20→400), pas de bullshit"
    }
  }
}'::jsonb
WHERE client_name = 'DevOps Experts';
```

**Résultat**:
- Ton casual ✅
- Vocabulaire tech ✅
- Ultra court ✅

---

## 🔧 Debugging

### Problème: L'email ne suit pas le ton

**Solution**: Améliorer l'exemple

```json
{
  "example": {
    "for_contact": {...},
    "perfect_email": "Email complet ici",
    "why_it_works": "DÉTAILLER pourquoi le ton est bon"
  }
}
```

Plus le `why_it_works` est détaillé, mieux le système apprend.

### Problème: Formatting errors (espaces, caps)

**Solution**: Ajouter des règles de formatting dans `dos`

```json
{
  "dos": [
    "Un seul espace après chaque ponctuation",
    "Majuscule après un point",
    "Majuscule après une variable si nouvelle phrase"
  ]
}
```

### Problème: Email trop long

**Solution**: Spécifier la longueur max dans `style`

```json
{
  "style": "Ultra court (< 60 mots maximum)",
  "dos": [
    "Rester sous 60 mots IMPÉRATIVEMENT"
  ]
}
```

---

## 📊 Métriques de qualité

### Avant (sans contexte + exemple)

```json
{
  "quality_score": 70,
  "tone_match_score": null,
  "formatting_corrections": [],
  "validation_attempts": 3
}
```

→ 3 tentatives, score moyen, pas de correction

### Après (avec contexte + exemple)

```json
{
  "quality_score": 95,
  "tone_match_score": 95,
  "formatting_corrections": [],
  "validation_attempts": 1,
  "guidelines_followed": true
}
```

→ 1 tentative, score élevé, parfait dès le départ!

---

## 🎨 Bonnes pratiques

### 1. Contexte clair et actionnable

**✅ Bon**:
```json
{
  "tone": "Conversational et direct",
  "dos": [
    "Utiliser un signal factuel trouvé par Tavily",
    "Donner une métrique précise (avant → après)"
  ]
}
```

**❌ Mauvais**:
```json
{
  "tone": "Bien",
  "dos": ["Être sympa"]
}
```

### 2. Exemples réalistes

**✅ Bon**:
```json
{
  "perfect_email": "Email complet avec toutes les variables remplies",
  "why_it_works": "Signal factuel (hiring) + empathie + métrique (6→2 mois) + ton conversational + CTA simple"
}
```

**❌ Mauvais**:
```json
{
  "perfect_email": "Exemple court",
  "why_it_works": "C'est bien"
}
```

### 3. DOs et DON'Ts spécifiques

**✅ Bon**:
```json
{
  "dos": [
    "Rester sous 100 mots",
    "Utiliser des métriques précises (ex: '+300% pipeline')"
  ],
  "donts": [
    "Utiliser 'solutions innovantes' ou 'leader du marché'",
    "Faire plus de 2 paragraphes"
  ]
}
```

**❌ Mauvais**:
```json
{
  "dos": ["Faire bien"],
  "donts": ["Faire mal"]
}
```

---

## 🚀 Migration depuis templates simples

### Étape 1: Identifier vos meilleurs emails

Regardez vos emails qui ont les meilleurs taux de réponse.

### Étape 2: Analyser pourquoi ils fonctionnent

Pour chaque bon email, identifiez:
- Quel ton? (casual, pro, direct)
- Quelle structure? (signal + proof, pain + solution)
- Quelle longueur?
- Quels éléments clés? (métriques, empathie, etc.)

### Étape 3: Créer le contexte

```json
{
  "intention": "Générer un meeting",
  "tone": "[Ton identifié]",
  "approach": "[Structure identifiée]",
  "style": "[Caractéristiques identifiées]",
  "dos": ["Éléments qui marchent"],
  "donts": ["Ce qu'on évite"]
}
```

### Étape 4: Ajouter un exemple parfait

Prenez votre meilleur email et ajoutez-le comme exemple:

```json
{
  "example": {
    "for_contact": {...},
    "perfect_email": "Votre meilleur email ici",
    "why_it_works": "Pourquoi il a bien marché"
  }
}
```

### Étape 5: Tester

Générez 5-10 emails et comparez avec vos anciens résultats.

---

## 📚 Ressources

- **Exemples SQL**: `supabase_email_templates_examples.sql`
- **Guide amélioration**: `GUIDE_AMELIORATION_SYSTEME.md`
- **EmailWriter agent**: `src/agents/email_writer_agent.py`
- **ClientContext**: `src/models/client_context.py`

---

## ✅ Checklist

Avant de déployer un nouveau template:

- [ ] Template avec toutes les `{{variables}}` nécessaires
- [ ] Contexte avec intention, tone, approach, style
- [ ] Au moins 3 DOs spécifiques et actionnables
- [ ] Au moins 3 DON'Ts spécifiques
- [ ] Un exemple parfait complet
- [ ] `why_it_works` détaillé (pas juste "c'est bien")
- [ ] Testé sur 5+ prospects différents
- [ ] Tone match score > 90
- [ ] Pas de formatting errors

---

**Happy Templating! 📧**
