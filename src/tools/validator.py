"""
Email Validator Tool

Valide la qualité d'un email généré selon des règles strictes.
"""

import re
from typing import Dict, List


class EmailValidator:
    """
    Validateur de qualité pour les emails générés.

    Critères:
    - Longueur appropriée (180-220 mots idéal)
    - Pas de jargon corporate
    - Pas de majuscules incorrectes
    - Présence de métriques mesurables
    - Ton conversationnel
    """

    # Liste de jargon corporate à éviter
    CORPORATE_JARGON = [
        "innovant", "disruptif", "révolutionnaire", "game-changer", "cutting-edge",
        "best-in-class", "world-class", "industry-leading", "next-generation",
        "state-of-the-art", "paradigm", "synergy", "leverage", "optimize",
        "maximize", "streamline", "robust", "scalable", "turnkey",
        "end-to-end", "holistic", "360-degree", "proactive", "value-add"
    ]

    # Patterns de majuscules incorrectes (hors début de phrase et acronymes)
    INCORRECT_CAPS_PATTERN = re.compile(r'(?<!^)(?<!\. )[A-Z]{2,}(?![A-Z])')

    def __init__(self):
        """Initialise le validateur."""
        pass

    def validate(self, email: str) -> Dict:
        """
        Valide un email et retourne un score de qualité avec détails.

        Args:
            email: Le texte de l'email à valider

        Returns:
            Dict avec:
            - quality_score: Score 0-100
            - word_count: Nombre de mots
            - issues: Liste des problèmes détectés
            - warnings: Liste des avertissements
            - suggestions: Liste de suggestions d'amélioration
        """
        issues = []
        warnings = []
        suggestions = []
        score = 100  # On part de 100 et on enlève des points

        # 1. Vérifier la longueur (180-220 mots idéal)
        word_count = len(email.split())
        if word_count < 120:
            issues.append(f"Email trop court ({word_count} mots < 120 minimum)")
            score -= 20
        elif word_count < 180:
            warnings.append(f"Email court ({word_count} mots, idéal: 180-220)")
            score -= 10
        elif word_count > 280:
            issues.append(f"Email trop long ({word_count} mots > 280 maximum)")
            score -= 20
        elif word_count > 220:
            warnings.append(f"Email un peu long ({word_count} mots, idéal: 180-220)")
            score -= 5

        # 2. Détecter le jargon corporate
        jargon_found = []
        email_lower = email.lower()
        for jargon in self.CORPORATE_JARGON:
            if jargon in email_lower:
                jargon_found.append(jargon)

        if jargon_found:
            issues.append(f"Jargon corporate détecté: {', '.join(jargon_found[:3])}")
            score -= min(15, len(jargon_found) * 5)
            suggestions.append("Remplacer le jargon par des termes plus conversationnels")

        # 3. Détecter les majuscules incorrectes
        incorrect_caps = self._find_incorrect_caps(email)
        if incorrect_caps:
            issues.append(f"Majuscules incorrectes: {', '.join(incorrect_caps[:3])}")
            score -= min(10, len(incorrect_caps) * 3)
            suggestions.append("Utiliser des minuscules sauf pour les acronymes (VP, CEO)")

        # 4. Vérifier la présence de métriques mesurables
        has_metrics = self._check_metrics(email)
        if not has_metrics:
            warnings.append("Aucune métrique mesurable détectée (%, temps, coût)")
            score -= 10
            suggestions.append("Ajouter des métriques concrètes pour plus d'impact")

        # 5. Vérifier la structure (3 paragraphes courts)
        paragraph_count = len([p for p in email.split('\n\n') if p.strip()])
        if paragraph_count < 2:
            warnings.append("Email avec peu de paragraphes, peut être difficile à lire")
            score -= 5
            suggestions.append("Structurer en 2-3 paragraphes courts")

        # 6. Détecter les verbes d'action en début de phrase (interdit pour les signaux)
        action_verbs = self._find_action_verbs_at_start(email)
        if action_verbs:
            issues.append(f"Verbes d'action en début: {', '.join(action_verbs[:2])}")
            score -= 10
            suggestions.append("Reformuler sans verbe d'action en début de phrase")

        # 7. Vérifier les variables non remplacées
        unreplaced_vars = re.findall(r'\{\{(\w+)\}\}', email)
        if unreplaced_vars:
            issues.append(f"Variables non remplacées: {', '.join(unreplaced_vars)}")
            score -= 30  # Critique
            suggestions.append("Toutes les variables doivent être remplacées")

        # 8. Vérifier les placeholders génériques
        if "[INFORMATION NON DISPONIBLE]" in email or "[CLIENT_NAME]" in email or "[SIGNATURE]" in email:
            issues.append("Placeholders génériques non remplacés")
            score -= 25
            suggestions.append("Remplacer tous les placeholders par des valeurs réelles")

        # Score final (min 0, max 100)
        final_score = max(0, min(100, score))

        return {
            "quality_score": final_score,
            "word_count": word_count,
            "issues": issues,
            "warnings": warnings,
            "suggestions": suggestions,
            "jargon_found": jargon_found,
            "incorrect_caps": incorrect_caps,
            "has_metrics": has_metrics
        }

    def _find_incorrect_caps(self, email: str) -> List[str]:
        """
        Trouve les majuscules incorrectes dans l'email.

        Args:
            email: Texte de l'email

        Returns:
            Liste des mots avec majuscules incorrectes
        """
        # Exceptions: acronymes valides
        valid_acronyms = ["VP", "CEO", "CTO", "CFO", "CRM", "SaaS", "B2B", "API", "ROI", "KPI"]

        incorrect = []
        # Chercher les mots avec plusieurs majuscules qui ne sont pas des acronymes valides
        words = email.split()
        for word in words:
            # Nettoyer la ponctuation
            clean_word = re.sub(r'[^\w]', '', word)
            # Si mot a des majuscules au milieu (hors acronymes)
            if re.search(r'[a-z][A-Z]', clean_word) and clean_word not in valid_acronyms:
                incorrect.append(word)

        return list(set(incorrect))[:5]  # Max 5 exemples

    def _check_metrics(self, email: str) -> bool:
        """
        Vérifie si l'email contient des métriques mesurables.

        Args:
            email: Texte de l'email

        Returns:
            True si des métriques sont trouvées
        """
        # Patterns de métriques
        patterns = [
            r'\d+%',  # Pourcentages (40%, +30%)
            r'\d+[hH]/(?:jour|semaine|mois)',  # Temps (3h/jour)
            r'\d+\s*(?:mois|semaines|jours)',  # Durées (4 mois)
            r'[€$]\s*\d+',  # Coûts (50K€, $10K)
            r'\d+K[€$]',  # Coûts (50K€)
            r'x\d+',  # Multiplicateurs (x2, x10)
        ]

        for pattern in patterns:
            if re.search(pattern, email):
                return True

        return False

    def _find_action_verbs_at_start(self, email: str) -> List[str]:
        """
        Trouve les verbes d'action en début de phrase (interdit).

        Args:
            email: Texte de l'email

        Returns:
            Liste des verbes d'action trouvés
        """
        # Verbes d'action courants à éviter en début
        action_verbs = [
            "Ciblent", "Utilisent", "Cherchent", "Veulent", "Ont besoin",
            "Souhaitent", "Désirent", "Planifient", "Développent"
        ]

        found = []
        sentences = re.split(r'[.!?]\s+', email)
        for sentence in sentences:
            sentence = sentence.strip()
            for verb in action_verbs:
                if sentence.startswith(verb):
                    found.append(verb)

        return list(set(found))


# Fonction helper pour validation simple
def validate_email(email: str) -> int:
    """
    Helper function pour valider un email et retourner juste le score.

    Args:
        email: Texte de l'email

    Returns:
        Score de qualité (0-100)
    """
    validator = EmailValidator()
    result = validator.validate(email)
    return result["quality_score"]


def validate_email_detailed(email: str) -> Dict:
    """
    Helper function pour validation complète avec détails.

    Args:
        email: Texte de l'email

    Returns:
        Dict complet avec score et détails
    """
    validator = EmailValidator()
    return validator.validate(email)
