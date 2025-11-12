"""
Structured logging for agent decisions and email quality

Logs sont sauvegardés dans ./logs/ au format JSON Lines pour analyse ultérieure
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional


class AgentLogger:
    """
    Logger structuré pour les décisions des agents

    Sauvegarde:
    - Décisions de chaque agent (input/output/model/cost/durée)
    - Résultats de validation (quality_score/issues/suggestions)
    - Métadonnées des générations (attempts/retries/success)
    """

    def __init__(self, log_dir: str = "./logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)

    def log_agent_run(
        self,
        agent_name: str,
        input_data: Any,
        output_data: Any,
        model_used: str,
        cost_usd: float,
        duration_seconds: float,
        metadata: Optional[Dict] = None
    ):
        """
        Log une exécution d'agent

        Args:
            agent_name: Nom de l'agent (PersonaExtractor, CompetitorFinder, etc.)
            input_data: Données d'entrée (BaseIOSchema ou dict)
            output_data: Données de sortie (BaseIOSchema ou dict)
            model_used: Modèle utilisé (openai/gpt-4o-mini, etc.)
            cost_usd: Coût en USD
            duration_seconds: Durée en secondes
            metadata: Métadonnées additionnelles
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent": agent_name,
            "input": self._serialize(input_data),
            "output": self._serialize(output_data),
            "model": model_used,
            "cost_usd": cost_usd,
            "duration_seconds": duration_seconds,
            "metadata": metadata or {}
        }

        # Sauvegarder dans logs/agents_YYYYMMDD.jsonl
        log_file = self.log_dir / f"agents_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def log_validation(
        self,
        email_id: str,
        email_content: str,
        attempt: int,
        quality_score: int,
        is_valid: bool,
        issues: List[str],
        suggestions: List[str],
        metadata: Optional[Dict] = None
    ):
        """
        Log un résultat de validation

        Args:
            email_id: ID unique de l'email
            email_content: Contenu de l'email
            attempt: Numéro de tentative (1, 2, 3)
            quality_score: Score de qualité 0-100
            is_valid: True si >= threshold
            issues: Liste des problèmes détectés
            suggestions: Liste des suggestions
            metadata: Métadonnées additionnelles
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "email_id": email_id,
            "email_content": email_content,
            "attempt": attempt,
            "quality_score": quality_score,
            "is_valid": is_valid,
            "issues": issues,
            "suggestions": suggestions,
            "metadata": metadata or {}
        }

        # Sauvegarder dans logs/validations_YYYYMMDD.jsonl
        log_file = self.log_dir / f"validations_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def log_email_generation(
        self,
        email_id: str,
        client_id: str,
        contact_company: str,
        attempts: int,
        final_quality_score: int,
        generation_time_seconds: float,
        cost_usd: float,
        success: bool,
        validation_attempts: List[Dict],
        metadata: Optional[Dict] = None
    ):
        """
        Log une génération complète d'email

        Args:
            email_id: ID unique
            client_id: ID du client
            contact_company: Nom de l'entreprise contactée
            attempts: Nombre de tentatives
            final_quality_score: Score final
            generation_time_seconds: Temps total
            cost_usd: Coût total
            success: True si validation passée
            validation_attempts: Liste des tentatives de validation
            metadata: Métadonnées additionnelles
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "email_id": email_id,
            "client_id": client_id,
            "contact_company": contact_company,
            "attempts": attempts,
            "final_quality_score": final_quality_score,
            "generation_time_seconds": generation_time_seconds,
            "cost_usd": cost_usd,
            "success": success,
            "validation_attempts": validation_attempts,
            "metadata": metadata or {}
        }

        # Sauvegarder dans logs/emails_YYYYMMDD.jsonl
        log_file = self.log_dir / f"emails_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def _serialize(self, data: Any) -> Dict:
        """Sérialise un objet BaseIOSchema ou dict en dict"""
        if hasattr(data, "dict"):
            return data.dict()
        elif isinstance(data, dict):
            return data
        else:
            return {"value": str(data)}


# Instance globale
agent_logger = AgentLogger()


# Helper functions
def log_agent(agent_name: str, input_data: Any, output_data: Any, model: str, cost: float, duration: float):
    """Helper pour logger rapidement une exécution d'agent"""
    agent_logger.log_agent_run(agent_name, input_data, output_data, model, cost, duration)


def log_validation(email_id: str, email: str, attempt: int, score: int, valid: bool, issues: List[str], suggestions: List[str]):
    """Helper pour logger rapidement une validation"""
    agent_logger.log_validation(email_id, email, attempt, score, valid, issues, suggestions)


def log_email(email_id: str, client_id: str, company: str, attempts: int, score: int, time: float, cost: float, success: bool, validations: List[Dict]):
    """Helper pour logger rapidement une génération complète"""
    agent_logger.log_email_generation(email_id, client_id, company, attempts, score, time, cost, success, validations)
