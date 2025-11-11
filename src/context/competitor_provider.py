"""
CompetitorProvider : Injecte la liste des concurrents connus.
"""

from atomic_agents.lib.components.context_providers import BaseDynamicContextProvider
from typing import Optional, List, Dict
import os
import json


class CompetitorProvider(BaseDynamicContextProvider):
    """Injecte la liste des concurrents identifiés"""

    def __init__(
        self,
        competitors_content: Optional[str] = None,
        competitors_file: Optional[str] = None,
        competitors_list: Optional[List[Dict[str, str]]] = None
    ):
        super().__init__(title="Concurrents Identifiés")
        self.competitors_content = competitors_content
        self.competitors_file = competitors_file
        self.competitors_list = competitors_list

    def get_info(self) -> str:
        # Priorité 1: Liste structurée
        if self.competitors_list:
            competitors = self.competitors_list

        # Priorité 2: Fichier JSON
        elif self.competitors_file and os.path.exists(self.competitors_file):
            with open(self.competitors_file, "r", encoding="utf-8") as f:
                competitors = json.load(f)

        # Priorité 3: Contenu texte brut
        elif self.competitors_content:
            return f"""
## 🏢 CONCURRENTS DIRECTS ET INDIRECTS

{self.competitors_content}

**Instructions :**
- Priorise ces concurrents si l'entreprise cible est dans le même secteur
- Utilise cette liste comme fallback si recherche web échoue
"""
        else:
            return "⚠️ Concurrents non disponibles - effectuer une recherche web"

        # Format la liste de concurrents
        competitors_list_formatted = "\n".join([
            f"- **{c.get('name', 'Unknown')}** : {c.get('positioning', 'N/A')}"
            for c in competitors
        ])

        return f"""
## 🏢 CONCURRENTS DIRECTS ET INDIRECTS

{competitors_list_formatted}

---

**Instructions :**
- Priorise ces concurrents si l'entreprise cible est dans le même secteur
- Utilise cette liste comme fallback si recherche web échoue
- Vérifie la pertinence du concurrent par rapport au product_category
"""
