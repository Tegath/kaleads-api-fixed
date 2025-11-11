"""
Agent qui analyse le feedback humain et propose des ameliorations aux prompts.

Cet agent:
1. Analyse le feedback humain sur un email genere
2. Identifie quel agent a cause le probleme
3. Propose des ameliorations aux prompts
4. Peut etre utilise pour auto-amelioration
"""

from atomic_agents import AtomicAgent, AgentConfig, BaseIOSchema
from atomic_agents.context import ChatHistory, SystemPromptGenerator
from pydantic import Field
from typing import Dict, List
import instructor
import openai
import os


class FeedbackAnalysisInputSchema(BaseIOSchema):
    """
    Input pour le FeedbackAgent.

    Contient l'email genere, les variables, et le feedback humain.
    """
    email_content: str = Field(..., description="Contenu de l'email genere")
    variables: Dict[str, str] = Field(..., description="Variables utilisees dans l'email")
    fallback_levels: Dict[str, int] = Field(..., description="Niveaux de fallback par agent")
    confidence_scores: Dict[str, int] = Field(..., description="Scores de confiance par variable")
    human_feedback: str = Field(..., description="Feedback textuel de l'humain")
    issues_identified: str = Field(..., description="Liste des problemes identifies")


class FeedbackAnalysisOutputSchema(BaseIOSchema):
    """
    Output du FeedbackAgent.

    Analyse du feedback et recommandations d'amelioration.
    """
    problematic_agents: List[str] = Field(
        ...,
        description="Liste des agents qui ont cause des problemes"
    )
    root_causes: Dict[str, str] = Field(
        ...,
        description="Cause racine du probleme pour chaque agent"
    )
    improvement_suggestions: Dict[str, List[str]] = Field(
        ...,
        description="Suggestions d'amelioration par agent"
    )
    prompt_adjustments: Dict[str, Dict[str, str]] = Field(
        ...,
        description="Ajustements specifiques aux prompts (background, steps, output_instructions)"
    )
    priority: int = Field(
        ...,
        ge=1,
        le=3,
        description="Priorite de correction (1=critique, 2=important, 3=mineur)"
    )
    reasoning: str = Field(
        ...,
        description="Raisonnement detaille de l'analyse"
    )


class FeedbackAgent:
    """
    Agent qui analyse le feedback et propose des ameliorations.

    Cet agent est un "meta-agent" qui aide a ameliorer les autres agents
    en analysant le feedback humain et en suggerant des modifications.
    """

    def __init__(self, api_key: str = None, model: str = "gpt-4o-mini"):
        api_key = api_key or os.getenv("OPENAI_API_KEY")
        client = instructor.from_openai(openai.OpenAI(api_key=api_key))

        system_prompt_generator = SystemPromptGenerator(
            background=[
                "Tu es un expert en analyse de systemes multi-agents et optimisation de prompts.",
                "Ta mission est d'analyser le feedback humain sur des emails generes",
                "et d'identifier quels agents ont cause des problemes.",
                "Tu dois TOUJOURS proposer des ameliorations concretes et actionnables."
            ],
            steps=[
                "1. Lis le feedback humain et identifie les problemes specifiques",
                "2. Analyse les variables generees et leurs scores",
                "3. Identifie quels agents sont responsables des problemes",
                "4. Pour chaque agent problematique:",
                "   a. Identifie la cause racine (prompt trop vague? manque d'exemples?)",
                "   b. Propose des ameliorations specifiques au prompt",
                "   c. Suggere des ajustements aux sections background/steps/output_instructions",
                "5. Priorise les corrections (1=critique, 2=important, 3=mineur)",
                "6. Documente ton raisonnement complet"
            ],
            output_instructions=[
                "problematic_agents: Liste des noms d'agents (ex: 'persona_agent', 'pain_agent')",
                "root_causes: Pour chaque agent, explique POURQUOI il a echoue",
                "improvement_suggestions: Suggestions concretes et actionnables",
                "prompt_adjustments: Modifications specifiques a apporter aux prompts",
                "  - background: Ajouts au contexte de l'agent",
                "  - steps: Ajouts/modifications aux etapes de raisonnement",
                "  - output_instructions: Ajouts aux instructions de sortie",
                "priority: 1 si critique (bloque l'envoi), 2 si important, 3 si mineur",
                "reasoning: Explique ton analyse complete"
            ]
        )

        config = AgentConfig(
            client=client,
            model=model,
            history=ChatHistory(),
            system_prompt_generator=system_prompt_generator
        )

        self.agent = AtomicAgent[FeedbackAnalysisInputSchema, FeedbackAnalysisOutputSchema](config=config)

    def run(self, input_data: FeedbackAnalysisInputSchema) -> FeedbackAnalysisOutputSchema:
        return self.agent.run(user_input=input_data)


# Mapping des variables vers les agents responsables
VARIABLE_TO_AGENT = {
    "target_persona": "persona_agent",
    "product_category": "persona_agent",
    "competitor_name": "competitor_agent",
    "competitor_product_category": "competitor_agent",
    "problem_specific": "pain_agent",
    "impact_measurable": "pain_agent",
    "specific_signal_1": "signal_agent",
    "specific_signal_2": "signal_agent",
    "specific_target_1": "signal_agent",
    "specific_target_2": "signal_agent",
    "system_1": "system_agent",
    "system_2": "system_agent",
    "system_3": "system_agent",
    "case_study_result": "case_study_agent"
}


def analyze_email_feedback(
    email_result,
    human_feedback: str,
    issues: str
) -> FeedbackAnalysisOutputSchema:
    """
    Helper function pour analyser le feedback sur un email.

    Args:
        email_result: Resultat EmailResult de l'orchestrateur
        human_feedback: Feedback textuel de l'humain
        issues: Problemes identifies (ex: "persona incorrect, pain point vague")

    Returns:
        FeedbackAnalysisOutputSchema avec l'analyse et les recommandations
    """
    agent = FeedbackAgent()

    input_data = FeedbackAnalysisInputSchema(
        email_content=email_result.email_generated,
        variables=email_result.variables,
        fallback_levels=email_result.fallback_levels,
        confidence_scores=email_result.confidence_scores,
        human_feedback=human_feedback,
        issues_identified=issues
    )

    return agent.run(input_data)
