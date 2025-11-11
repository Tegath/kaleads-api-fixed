# Template : Cold Email V1

Bonjour {{first_name}} - {{hook}}

{{specific_target_1}} et {{specific_target_2}}.

Le problème ? {{problem_specific}}. L'impact : {{impact_measurable}}.

Chez [CLIENT_NAME], nous aidons les {{target_persona}} comme vous à résoudre ce problème en remplaçant {{competitor_name}} par notre {{product_category}}.

Résultat : {{case_study_result}}.

Intéressé(e) pour en discuter 15 minutes cette semaine ?

Belle journée,
[SIGNATURE]

---

## Variables Nécessaires

- `{{first_name}}` : Prénom du contact
- `{{hook}}` : Accroche personnalisée (Agent: Hook Generator)
- `{{specific_target_1}}` : Premier signal d'intention (Agent 4)
- `{{specific_target_2}}` : Deuxième signal d'intention (Agent 4)
- `{{problem_specific}}` : Pain point spécifique (Agent 3)
- `{{impact_measurable}}` : Impact mesurable (Agent 3)
- `{{target_persona}}` : Persona cible (Agent 1)
- `{{competitor_name}}` : Concurrent identifié (Agent 2)
- `{{product_category}}` : Catégorie de produit (Agent 1)
- `{{case_study_result}}` : Résultat case study (Agent 6)

## Règles de Génération

1. **Longueur totale** : 180-220 mots
2. **Ton** : Conversationnel, professionnel mais accessible
3. **Structure** : 3 paragraphes courts
4. **INTERDIT** :
   - Jargon corporate (innovant, disruptif, etc.)
   - Majuscules au milieu de phrase
   - Verbes d'action en début de phrase pour les signaux
5. **OBLIGATOIRE** :
   - Minuscules sauf acronymes (vP, cEO)
   - Métriques concrètes dans case_study_result
   - Signaux contextuels (pas génériques)
