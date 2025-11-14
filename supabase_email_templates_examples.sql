-- ============================================
-- Exemples de configuration email_templates avec contexte et exemples
-- Pour Supabase - table clients
-- ============================================

-- Exemple 1: Kaleads - Lead Gen / Prospection B2B
UPDATE clients
SET email_templates = '{
  "outreach_signal_v1": {
    "template_content": "Bonjour {{first_name}},\\n\\nJ''ai remarqué que {{company_name}} {{specific_signal_1}}.\\n\\nEn tant que {{target_persona}}, vous faites probablement face à {{problem_specific}}.\\n\\n{{case_study_result}}.\\n\\nÇa vous parle?",
    "context": {
      "intention": "Générer un meeting avec un décideur Sales/Marketing",
      "tone": "Conversational et direct",
      "approach": "Signal factuel + Empathie + Social proof concret",
      "style": "Court (< 100 mots), question engageante à la fin",
      "dos": [
        "Utiliser un signal factuel trouvé par Tavily (hiring, funding, etc.)",
        "Montrer de l''empathie pour leur situation",
        "Donner une métrique précise dans la case study",
        "Poser une question naturelle et engageante",
        "Rester sous 100 mots"
      ],
      "donts": [
        "Utiliser du jargon corporate (''solutions innovantes'', ''leader du marché'')",
        "Faire un pitch produit",
        "Utiliser des superlatifs (''le meilleur'', ''révolutionnaire'')",
        "Parler de nous avant de parler d''eux",
        "Avoir des erreurs de formatage (espaces, caps)"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Aircall",
        "first_name": "Sophie",
        "industry": "SaaS",
        "signal": "recrute 3 commerciaux"
      },
      "perfect_email": "Bonjour Sophie,\\n\\nJ''ai vu qu''Aircall recrute 3 commerciaux en ce moment.\\n\\nEn tant que Head of Sales, vous devez chercher à accélérer leur montée en compétence.\\n\\nOn a aidé Salesforce France à réduire leur ramp-up de 6 mois à 2 mois.\\n\\nÇa vous parle?",
      "why_it_works": "Signal factuel (hiring) + empathie (ramp-up challenge) + métrique concrète (6→2 mois) + ton conversational + CTA simple"
    }
  },

  "outreach_devops_v1": {
    "template_content": "Bonjour {{first_name}},\\n\\nVu que {{company_name}} {{specific_signal_1}}, je me suis dit que vous étiez en croissance.\\n\\n{{case_study_result}}.\\n\\nCurieux?",
    "context": {
      "intention": "Générer un meeting pour DevOps outsourcing",
      "tone": "Casual et direct",
      "approach": "Signal + Social proof + CTA ultra court",
      "style": "Ultra court (< 60 mots), pas de fluff",
      "dos": [
        "Aller droit au but",
        "Utiliser un signal de croissance (hiring, expansion)",
        "Donner une métrique de vélocité (déploiements, incidents)",
        "CTA minimal (''Curieux?'', ''Ça vous parle?'')"
      ],
      "donts": [
        "Expliquer ce qu''on fait (ils le devineront)",
        "Faire plus de 60 mots",
        "Utiliser un CTA long (''Seriez-vous disponible pour...'')"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Doctolib",
        "first_name": "Thomas",
        "industry": "HealthTech",
        "signal": "ouvre un bureau à Lyon"
      },
      "perfect_email": "Bonjour Thomas,\\n\\nVu que Doctolib ouvre un bureau à Lyon, je suppose que vous scalez.\\n\\nOn a aidé Alan à passer de 50 à 300 déploiements/semaine sans recruter 10 DevOps.\\n\\nCurieux?",
      "why_it_works": "Signal (expansion) + hypothèse (scaling) + métrique précise (50→300) + pas de DevOps à recruter + CTA minimal"
    }
  },

  "outreach_hr_v1": {
    "template_content": "Bonjour {{first_name}},\\n\\n{{company_name}} {{specific_signal_1}} - ça doit être intense côté recrutement.\\n\\n{{case_study_result}}.\\n\\nÇa vous intéresse?",
    "context": {
      "intention": "Générer un meeting pour HR tech / ATS",
      "tone": "Empathique et professionnel",
      "approach": "Signal + Empathie pour leur charge + Résultat concret",
      "style": "Court (< 80 mots), montrer qu''on comprend leur douleur",
      "dos": [
        "Montrer de l''empathie (''ça doit être intense'')",
        "Utiliser un signal de croissance RH (hiring spree, expansion)",
        "Donner un résultat lié au temps/efficacité (time-to-hire, etc.)",
        "Rester dans leur vocabulaire métier"
      ],
      "donts": [
        "Dire ''on a la solution parfaite''",
        "Minimiser leur douleur",
        "Parler features avant résultats"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Qonto",
        "first_name": "Marie",
        "industry": "FinTech",
        "signal": "recrute 50+ personnes"
      },
      "perfect_email": "Bonjour Marie,\\n\\nQonto recrute 50+ personnes - ça doit être intense côté screening.\\n\\nOn a aidé PayFit à réduire leur time-to-hire de 45 à 12 jours.\\n\\nÇa vous intéresse?",
      "why_it_works": "Signal (hiring spree) + empathie (intense screening) + métrique précise (45→12 jours) + ton pro mais chaleureux"
    }
  }
}'::jsonb
WHERE client_id = 'kaleads';


-- Exemple 2: DevOps Agency
UPDATE clients
SET email_templates = '{
  "outreach_cto_v1": {
    "template_content": "Salut {{first_name}},\\n\\nVu que {{company_name}} {{specific_signal_1}}, je suppose que vous scalez.\\n\\n{{case_study_result}}.\\n\\nOn en parle?",
    "context": {
      "intention": "Générer un meeting pour DevOps part-time",
      "tone": "Casual tech-friendly",
      "approach": "Direct + Pas de bullshit + Metrics",
      "style": "Ultra court, aucun fluff, parler comme un dev",
      "dos": [
        "Tutoyer si possible (dépend du contact)",
        "Utiliser du vocabulaire tech (deploys, incidents, uptime)",
        "Donner des métriques de vélocité/qualité",
        "CTA minimal"
      ],
      "donts": [
        "Utiliser du vocabulaire marketing/sales",
        "Faire plus de 3 phrases",
        "Expliquer ce qu''on fait (ils sont techs, ils pigent)"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Ledger",
        "first_name": "Alex",
        "industry": "Crypto",
        "signal": "recrute 5 SREs"
      },
      "perfect_email": "Salut Alex,\\n\\nVu que Ledger recrute 5 SREs, je suppose que vous scalez l''infra.\\n\\nOn a aidé Sorare à passer de 20 à 400 deploys/semaine sans recruiter.\\n\\nOn en parle?",
      "why_it_works": "Casual (Salut), tech vocab (SRE, infra, deploys), métrique précise (20→400), pas de bullshit"
    }
  }
}'::jsonb
WHERE client_name = 'DevOps Experts';


-- Exemple 3: Marketing Agency
UPDATE clients
SET email_templates = '{
  "outreach_cmo_v1": {
    "template_content": "Bonjour {{first_name}},\\n\\nJ''ai vu que {{company_name}} {{specific_signal_1}}.\\n\\nEn tant que {{target_persona}}, vous cherchez probablement à {{problem_specific}}.\\n\\n{{case_study_result}}.\\n\\nIntéressé(e)?",
    "context": {
      "intention": "Générer un meeting pour marketing automation",
      "tone": "Professionnel et data-driven",
      "approach": "Signal + Pain point business + ROI concret",
      "style": "Professionnel (< 100 mots), focus ROI/métriques",
      "dos": [
        "Utiliser des métriques business (pipeline, MQLs, conversion)",
        "Parler ROI et résultats mesurables",
        "Montrer qu''on comprend leurs KPIs",
        "Rester factuel et data-driven"
      ],
      "donts": [
        "Utiliser du jargon technique (APIs, webhooks, etc.)",
        "Parler features avant résultats",
        "Faire des promesses vagues (''augmenter vos résultats'')"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "ManoMano",
        "first_name": "Julie",
        "industry": "E-commerce",
        "signal": "lève 125M€"
      },
      "perfect_email": "Bonjour Julie,\\n\\nJ''ai vu que ManoMano vient de lever 125M€.\\n\\nEn tant que CMO, vous cherchez probablement à scaler l''acquisition sans exploser le CAC.\\n\\nOn a aidé Back Market à augmenter leur pipeline de 200% tout en réduisant le CAC de 30%.\\n\\nIntéressé(e)?",
      "why_it_works": "Signal factuel (funding) + pain point business (scale acquisition) + double métrique (pipeline + CAC) + ton pro"
    }
  }
}'::jsonb
WHERE client_name = 'Growth Agency';


-- ============================================
-- Template pour ajouter une nouvelle config
-- ============================================

-- TEMPLATE: Copiez et remplissez ceci pour votre client
/*
UPDATE clients
SET email_templates = '{
  "template_name_v1": {
    "template_content": "Votre template avec {{variables}}",
    "context": {
      "intention": "Quel est le but de cet email?",
      "tone": "Quel ton? (conversational, professional, casual, direct)",
      "approach": "Quelle approche? (signal + proof, pain + solution, etc.)",
      "style": "Quelles caractéristiques? (court, long, questions, etc.)",
      "dos": [
        "Chose à faire #1",
        "Chose à faire #2"
      ],
      "donts": [
        "Chose à éviter #1",
        "Chose à éviter #2"
      ]
    },
    "example": {
      "for_contact": {
        "company_name": "Entreprise exemple",
        "first_name": "Prénom",
        "industry": "Industrie",
        "signal": "Signal détecté"
      },
      "perfect_email": "L''email parfait complet ici",
      "why_it_works": "Pourquoi cet email fonctionne (facteurs clés de succès)"
    }
  }
}'::jsonb
WHERE client_id = 'your-client-uuid';
*/


-- ============================================
-- Vérification
-- ============================================

-- Vérifier que les templates sont bien configurés
SELECT
  client_id,
  client_name,
  jsonb_object_keys(email_templates) as template_names,
  jsonb_array_length(
    (email_templates->jsonb_object_keys(email_templates)->'context'->'dos')
  ) as num_dos,
  jsonb_array_length(
    (email_templates->jsonb_object_keys(email_templates)->'context'->'donts')
  ) as num_donts
FROM clients
WHERE email_templates IS NOT NULL;


-- Extraire un template spécifique pour inspection
SELECT
  client_name,
  email_templates->'outreach_signal_v1' as outreach_config
FROM clients
WHERE client_id = 'kaleads';
