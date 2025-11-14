# 📚 Guide Complet d'Amélioration du Système v3.0

Guide pour améliorer la qualité et la personnalisation des emails générés.

---

## 🎯 Objectifs

1. **Contexte d'email**: Fournir des instructions de style, ton, structure
2. **Exemples parfaits**: Donner des emails de référence à imiter
3. **Correction automatique**: Le validator doit corriger les erreurs, pas juste les détecter
4. **Cohérence**: Garantir que tous les emails suivent le même style

---

## 📋 Table des matières

1. [Problème actuel](#problème-actuel)
2. [Solution proposée](#solution-proposée)
3. [Implémentation étape par étape](#implémentation)
4. [Exemples d'utilisation](#exemples)
5. [Bonnes pratiques](#bonnes-pratiques)

---

## ❌ Problème actuel

### Ce qui ne marche pas

**1. Validator détecte mais ne corrige pas**
```json
{
  "attempt": 1,
  "quality_score": 70,
  "issues": [
    "Missing space after punctuation: non? .",
    "Incorrect capital after case study variable: ça → Ça"
  ]
}
// → 3 tentatives, même score de 70, aucune correction!
```

**2. Pas de contexte pour guider la génération**
- Impossible de spécifier le ton (formel, casual, etc.)
- Impossible de donner des exemples à suivre
- Pas de guidelines sur la structure

**3. Template rigide**
```json
{
  "template_content": "Bonjour {{first_name}},\n\n{{problem_specific}}..."
}
// → Variables remplies bêtement sans contexte
```

---

## ✅ Solution proposée

### Architecture améliorée

```
┌─────────────────────────────────────────────────────┐
│              API Request (Enhanced)                 │
├─────────────────────────────────────────────────────┤
│  client_id: "kaleads"                               │
│  contact: {...}                                     │
│  template_content: "..."                            │
│  email_guidelines: {                    ← NOUVEAU  │
│    tone: "conversational",                          │
│    style: "casual",                                 │
│    structure: "hook + value + cta",                 │
│    dos: [...],                                      │
│    donts: [...],                                    │
│    examples: [...]                                  │
│  }                                                  │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│          Generate Email with Context                │
├─────────────────────────────────────────────────────┤
│  1. Load ClientContext                              │
│  2. Inject email_guidelines                         │
│  3. Run agents with guidelines                      │
│  4. Render template with context                    │
└─────────────────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────┐
│        Validator with Auto-Correction               │
├─────────────────────────────────────────────────────┤
│  1. Detect issues                                   │
│  2. Apply corrections (LLM-based)      ← AMÉLIORÉ  │
│  3. Re-validate                                     │
│  4. Return corrected email                          │
└─────────────────────────────────────────────────────┘
```

---

## 🛠️ Implémentation

### Étape 1: Mettre à jour ClientContext

**Fichier**: `src/models/client_context.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional

class EmailGuidelines(BaseModel):
    """Guidelines pour la génération d'emails."""

    tone: str = Field(
        default="professional",
        description="Tone of voice: professional, conversational, casual, formal"
    )

    style: str = Field(
        default="direct",
        description="Writing style: direct, storytelling, data-driven"
    )

    structure: str = Field(
        default="hook-value-cta",
        description="Email structure pattern"
    )

    max_length: int = Field(
        default=150,
        description="Maximum words in email body"
    )

    dos: List[str] = Field(
        default_factory=list,
        description="Things to DO in emails"
    )

    donts: List[str] = Field(
        default_factory=list,
        description="Things to AVOID in emails"
    )

    formatting_rules: Dict[str, str] = Field(
        default_factory=dict,
        description="Specific formatting rules (spacing, punctuation, etc.)"
    )


class ExampleEmail(BaseModel):
    """Un email exemple à imiter."""

    context: str = Field(
        description="Contexte de cet exemple (quel type de prospect, situation)"
    )

    email_content: str = Field(
        description="Le contenu complet de l'email"
    )

    why_it_works: str = Field(
        description="Pourquoi cet email fonctionne (pour que l'agent comprenne)"
    )

    quality_score: int = Field(
        default=100,
        description="Score de qualité de cet exemple (0-100)"
    )


class ClientContext(BaseModel):
    """Enhanced ClientContext avec guidelines."""

    # ... (fields existants) ...

    # NOUVEAU: Email guidelines
    email_guidelines: Optional[EmailGuidelines] = Field(
        default=None,
        description="Guidelines for email generation"
    )

    # NOUVEAU: Example emails
    example_emails: List[ExampleEmail] = Field(
        default_factory=list,
        description="Perfect example emails to learn from"
    )

    def get_email_context_prompt(self) -> str:
        """
        Generate a prompt section for email generation guidelines.

        Returns:
            Formatted string with guidelines and examples
        """
        if not self.email_guidelines:
            return ""

        g = self.email_guidelines

        prompt = f"""
EMAIL GENERATION GUIDELINES:

Tone: {g.tone}
Style: {g.style}
Structure: {g.structure}
Max length: {g.max_length} words

DO:
{chr(10).join(f"  ✓ {item}" for item in g.dos)}

DON'T:
{chr(10).join(f"  ✗ {item}" for item in g.donts)}
"""

        if self.example_emails:
            prompt += "\n\nPERFECT EXAMPLES TO LEARN FROM:\n"
            for i, ex in enumerate(self.example_emails, 1):
                prompt += f"""
Example {i} ({ex.context}):
---
{ex.email_content}
---
Why it works: {ex.why_it_works}
"""

        return prompt
```

### Étape 2: Mettre à jour l'API Request Schema

**Fichier**: `src/api/n8n_optimized_api.py`

```python
class EmailGenerationRequest(BaseModel):
    """Enhanced request with guidelines."""

    client_id: str
    contact: ContactInfo
    template_content: Optional[str] = None

    # NOUVEAU: Guidelines inline (override client defaults)
    email_guidelines: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Email generation guidelines (inline, overrides client defaults)"
    )

    # NOUVEAU: Example emails inline
    example_emails: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Example emails to learn from (inline)"
    )

    options: EmailGenerationOptions = Field(default_factory=EmailGenerationOptions)
```

### Étape 3: Créer un EmailWriter Agent

**Fichier**: `src/agents/email_writer_agent.py`

```python
"""
EmailWriter Agent v3.0

Génère le contenu final de l'email en suivant les guidelines et exemples.
"""

from atomic_agents.lib.base.base_agent import BaseAgent, BaseAgentConfig
from atomic_agents.lib.base.base_io_schema import BaseIOSchema
from pydantic import Field
from typing import Optional
import os


class EmailWriterInputSchema(BaseIOSchema):
    """Input for EmailWriter."""

    # Variables from agents
    first_name: str
    company_name: str
    target_persona: str
    problem_specific: str
    case_study_result: str
    specific_signal_1: str

    # Template to follow
    template_content: str = Field(
        description="Template with {{variables}} to fill"
    )

    # Guidelines context
    email_guidelines_context: str = Field(
        default="",
        description="Formatted guidelines and examples from ClientContext"
    )

    # Client info
    client_name: str
    client_offerings: str


class EmailWriterOutputSchema(BaseIOSchema):
    """Output from EmailWriter."""

    email_content: str = Field(
        description="Final email content, following all guidelines"
    )

    guidelines_followed: bool = Field(
        description="Whether guidelines were successfully followed"
    )

    tone_match_score: int = Field(
        ge=0, le=100,
        description="How well the tone matches the guidelines (0-100)"
    )


class EmailWriterAgent(BaseAgent):
    """
    EmailWriter Agent v3.0

    Generates final email content following guidelines and examples.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None
    ):
        api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        model = model or "anthropic/claude-3.5-sonnet"

        system_prompt = """You are an expert email copywriter for cold outreach.

Your job:
1. Take the template with {{variables}}
2. Fill variables with provided data
3. Follow the email guidelines EXACTLY
4. Learn from the example emails provided
5. Ensure perfect formatting (spacing, punctuation, capitalization)

CRITICAL RULES:
- Match the tone specified in guidelines
- Follow the structure pattern
- Respect max length
- Apply all DO's and DON'Ts
- Fix any formatting errors (spacing, caps, etc.)
- Make it sound natural, not robotic

You will receive:
- Template with variables
- Variable values
- Email guidelines
- Example emails to learn from

Return:
- Perfectly formatted email
- Confirmation you followed guidelines
- Tone match score"""

        config = BaseAgentConfig(
            client=self._get_client(api_key),
            model=model,
            system_prompt_template=system_prompt,
            input_schema=EmailWriterInputSchema,
            output_schema=EmailWriterOutputSchema
        )

        super().__init__(config)

    def _get_client(self, api_key: str):
        """Get OpenRouter client."""
        from openai import OpenAI
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key
        )


if __name__ == "__main__":
    # Test
    agent = EmailWriterAgent()

    result = agent.run(EmailWriterInputSchema(
        first_name="Sophie",
        company_name="Aircall",
        target_persona="Head of Sales",
        problem_specific="difficulté à générer des leads qualifiés",
        case_study_result="Nous avons aidé TechCorp à augmenter leur pipeline de 300%",
        specific_signal_1="recrute actuellement",
        template_content="Bonjour {{first_name}},\n\nJ'ai vu que {{company_name}} {{specific_signal_1}}.\n\n{{case_study_result}}.\n\nIntéressé(e)?",
        email_guidelines_context="""
EMAIL GENERATION GUIDELINES:
Tone: conversational
Style: direct
Max length: 100 words
DO:
  ✓ Keep it short and punchy
  ✓ Use natural language
  ✓ Add value upfront
DON'T:
  ✗ Use corporate jargon
  ✗ Make it too long
        """,
        client_name="Kaleads",
        client_offerings="Cold email automation, Lead enrichment"
    ))

    print("Email:", result.email_content)
    print("Guidelines followed:", result.guidelines_followed)
    print("Tone match:", result.tone_match_score)
```

### Étape 4: Améliorer le Validator avec Auto-Correction

**Fichier**: `src/agents/validator_agent.py` (modification)

```python
class EmailValidatorAgent(BaseAgent):
    """
    Enhanced validator with auto-correction.
    """

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        # ... existing init ...

        # Update system prompt to include correction instructions
        system_prompt = """You are an expert email validator AND corrector.

Your job:
1. Validate the email against criteria
2. Detect any issues
3. **AUTOMATICALLY CORRECT THE ISSUES**
4. Return the corrected email

CRITICAL: Don't just list issues - FIX THEM!

Common fixes:
- Add missing spaces after punctuation
- Fix capitalization errors
- Remove double spaces
- Fix line breaks
- Ensure proper greeting/closing

Return:
- quality_score: 0-100
- is_valid: true/false
- issues: [] (what was wrong)
- corrections_applied: [] (what you fixed)
- corrected_email: the fixed version"""

        # ... rest of init ...


class EmailValidationOutputSchema(BaseIOSchema):
    """Enhanced output with corrected email."""

    quality_score: int = Field(ge=0, le=100)
    is_valid: bool
    issues: List[str] = Field(default_factory=list)
    suggestions: List[str] = Field(default_factory=list)

    # NOUVEAU: Auto-correction
    corrections_applied: List[str] = Field(
        default_factory=list,
        description="List of corrections that were automatically applied"
    )

    corrected_email: str = Field(
        description="The email with all corrections applied"
    )
```

### Étape 5: Mettre à jour la logique de génération

**Fichier**: `src/api/n8n_optimized_api.py` (modification)

```python
async def generate_email_with_agents(...):
    """Enhanced generation with guidelines."""

    # 1. Load client context
    client_context = supabase_client.load_client_context_v3(client_id)

    # 2. Override with inline guidelines if provided
    if email_guidelines:
        from src.models.client_context import EmailGuidelines
        client_context.email_guidelines = EmailGuidelines(**email_guidelines)

    if example_emails:
        from src.models.client_context import ExampleEmail
        client_context.example_emails = [
            ExampleEmail(**ex) for ex in example_emails
        ]

    # 3. Run agents (existing code)
    persona_result = persona_agent.run(...)
    # ... etc ...

    # 4. Use EmailWriter instead of simple template rendering
    from src.agents.email_writer_agent import EmailWriterAgent, EmailWriterInputSchema

    email_writer = EmailWriterAgent()

    email_result = email_writer.run(EmailWriterInputSchema(
        first_name=contact.first_name,
        company_name=contact.company_name,
        target_persona=persona_result.role,
        problem_specific=pain_result.problem_specific,
        case_study_result=proof_result.case_study_result,
        specific_signal_1=signal_result.signal_description,
        template_content=template_content or DEFAULT_TEMPLATE,
        email_guidelines_context=client_context.get_email_context_prompt(),
        client_name=client_context.client_name,
        client_offerings=client_context.get_offerings_str()
    ))

    email_content = email_result.email_content

    # 5. Validate with auto-correction
    if validator:
        validation = validator.run(EmailValidationInputSchema(
            email_content=email_content,
            contact_company=contact.company_name,
            client_name=client_context.client_name,
            client_offering=client_context.get_offerings_str()
        ))

        # Use corrected email if validation found issues
        if validation.corrections_applied:
            email_content = validation.corrected_email

    return {
        "email_content": email_content,
        "tone_match_score": email_result.tone_match_score,
        "corrections_applied": validation.corrections_applied if validator else [],
        # ... rest ...
    }
```

---

## 📝 Exemples d'utilisation

### Exemple 1: Email avec guidelines inline

```json
{
  "client_id": "kaleads",
  "contact": {
    "company_name": "Aircall",
    "first_name": "Sophie",
    "website": "https://aircall.io",
    "industry": "SaaS"
  },
  "template_content": "Bonjour {{first_name}},\n\nJ'ai remarqué que {{company_name}} {{specific_signal_1}}.\n\nEn tant que {{target_persona}}, vous faites face à {{problem_specific}}.\n\n{{case_study_result}}.\n\nÇa vous parle?",
  "email_guidelines": {
    "tone": "conversational",
    "style": "direct",
    "structure": "hook-value-cta",
    "max_length": 100,
    "dos": [
      "Utiliser un langage simple et direct",
      "Poser une question engageante",
      "Montrer de la valeur rapidement"
    ],
    "donts": [
      "Utiliser du jargon corporate",
      "Faire des emails trop longs",
      "Parler de nous avant de parler d'eux"
    ],
    "formatting_rules": {
      "spacing": "Single space after punctuation",
      "capitalization": "Capitalize after variables",
      "line_breaks": "Max 2 consecutive line breaks"
    }
  },
  "example_emails": [
    {
      "context": "SaaS company, hiring signal detected",
      "email_content": "Bonjour Sophie,\n\nVu que vous recrutez, je me suis dit que vous étiez peut-être en mode scale.\n\nOn aide des boîtes comme la vôtre à générer +200 leads/mois sans recruter.\n\nÇa vous parle?",
      "why_it_works": "Court, direct, parle du problème (hiring = need leads), value prop claire",
      "quality_score": 95
    }
  ],
  "options": {
    "model_preference": "quality",
    "enable_scraping": true,
    "enable_tavily": true
  }
}
```

**Résultat attendu:**
```json
{
  "success": true,
  "email_content": "Bonjour Sophie,\n\nVu qu'Aircall recrute actuellement, je me suis dit que vous étiez en phase de croissance.\n\nOn a aidé TechCorp à augmenter leur pipeline de 300% en 3 mois sans recruter en masse.\n\nÇa vous parle?",
  "tone_match_score": 95,
  "corrections_applied": [
    "Added space after 'croissance.'",
    "Capitalized 'Ça' after variable"
  ],
  "quality_score": 98
}
```

### Exemple 2: Guidelines dans Supabase (réutilisables)

**Dans Supabase, table `clients`:**

```sql
UPDATE clients
SET email_guidelines = '{
  "tone": "conversational",
  "style": "direct",
  "max_length": 120,
  "dos": [
    "Keep it under 100 words",
    "Use natural language",
    "Focus on their problem first"
  ],
  "donts": [
    "Use corporate jargon",
    "Talk about yourself first",
    "Write long paragraphs"
  ]
}'::jsonb,
example_emails = '[
  {
    "context": "Tech company with hiring signal",
    "email_content": "Salut {{first_name}},\n\nVu que {{company_name}} recrute, je suppose que vous êtes en croissance.\n\nOn aide des boîtes comme vous à scaler leur acquisition sans recruter.\n\nCurieux?",
    "why_it_works": "Direct, empathetic, focused on their situation",
    "quality_score": 95
  }
]'::jsonb
WHERE client_id = 'kaleads';
```

**Requête API (plus simple):**
```json
{
  "client_id": "kaleads",
  "contact": {...},
  "template_content": "...",
  "options": {
    "model_preference": "quality"
  }
}
```
→ Guidelines chargées depuis Supabase automatiquement!

---

## 🎯 Bonnes pratiques

### 1. Structure des guidelines

**DO:**
```json
{
  "tone": "conversational",  // Specific
  "dos": [
    "Use natural, spoken language",  // Actionable
    "Keep under 100 words"  // Measurable
  ]
}
```

**DON'T:**
```json
{
  "tone": "good",  // Too vague
  "dos": [
    "Be nice"  // Not actionable
  ]
}
```

### 2. Exemples de qualité

**DO:**
```json
{
  "context": "SaaS, hiring signal, Head of Sales persona",
  "email_content": "...",
  "why_it_works": "Opens with their situation (hiring), shows empathy, gives specific result (300%), natural language"
}
```

**DON'T:**
```json
{
  "context": "example",
  "email_content": "...",
  "why_it_works": "good"
}
```

### 3. Templates

**DO:**
```
Bonjour {{first_name}},

{{specific_signal_1}} chez {{company_name}}, ça doit être excitant!

{{case_study_result}}.

Ça vous parle?
```
- Variables claires
- Structure simple
- Questions engageantes

**DON'T:**
```
Bonjour {{first_name}}, Je suis {{my_name}} de {{client_name}}. {{long_pitch}}. {{case_study}}. Voici mon calendrier: {{calendar_link}}
```
- Trop de variables
- Trop long
- Trop "salesy"

### 4. Validation

Le validator détecte:
- Formatage (espaces, caps)
- Longueur
- Tone match
- Hallucinations
- Spam words

Et maintenant il **corrige automatiquement** au lieu de juste détecter!

---

## 📊 Métriques de qualité

### Avant amélioration
```
Quality Score: 70
Issues: 5
Corrections: 0
Tone Match: Unknown
```

### Après amélioration
```
Quality Score: 95
Issues: 0 (corrected)
Corrections: 3 applied
Tone Match: 95/100
Guidelines Followed: ✓
```

---

## 🚀 Déploiement

### Étape 1: Mise à jour de la DB

```sql
-- Ajouter colonnes si nécessaire
ALTER TABLE clients
ADD COLUMN IF NOT EXISTS email_guidelines JSONB,
ADD COLUMN IF NOT EXISTS example_emails JSONB;

-- Exemple d'insertion
UPDATE clients
SET
  email_guidelines = '{...}'::jsonb,
  example_emails = '[...]'::jsonb
WHERE client_id = 'kaleads';
```

### Étape 2: Code update

```bash
# Sur ton PC local
git add .
git commit -m "feat: Add email guidelines and auto-correction

- EmailGuidelines model
- ExampleEmail model
- EmailWriter agent
- Enhanced validator with auto-correction
- API support for inline guidelines"
git push origin main

# Sur le serveur
cd /root/kaleads-atomic-agents
git pull origin main
docker stop kaleads-api-v3 && docker rm kaleads-api-v3
docker build -t kaleads-api:v3.1 .
docker run -d \
  --name kaleads-api-v3 \
  --network n8n-network \
  -p 8001:8001 \
  --env-file .env \
  --restart unless-stopped \
  kaleads-api:v3.1
```

### Étape 3: Test

```bash
curl -X POST http://92.112.193.183:8001/api/v2/generate-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-key" \
  -d '{
    "client_id": "kaleads",
    "contact": {...},
    "email_guidelines": {...},
    "example_emails": [{...}]
  }'
```

---

## 🔍 Debugging

### Problème: Tone match faible

**Solution**: Améliorer les exemples

```json
{
  "example_emails": [
    {
      "context": "Detailed context here",
      "email_content": "Perfect example",
      "why_it_works": "DETAILED explanation of why"
    }
  ]
}
```

### Problème: Corrections non appliquées

**Solution**: Vérifier les logs du validator

```python
print(f"Issues detected: {validation.issues}")
print(f"Corrections applied: {validation.corrections_applied}")
print(f"Original: {email_content}")
print(f"Corrected: {validation.corrected_email}")
```

### Problème: Guidelines ignorées

**Solution**: Vérifier le prompt context

```python
context = client_context.get_email_context_prompt()
print(context)
# → Devrait montrer guidelines + examples
```

---

## ✅ Checklist avant production

- [ ] ClientContext mis à jour avec EmailGuidelines + ExampleEmail
- [ ] SupabaseClient charge email_guidelines et example_emails
- [ ] EmailWriter agent créé et testé
- [ ] Validator avec auto-correction implémenté
- [ ] API accepte email_guidelines inline
- [ ] Tests avec différents types de guidelines
- [ ] Documentation à jour
- [ ] Déployé sur serveur
- [ ] Tests end-to-end depuis n8n

---

**Happy Improving! 🚀**
