"""
PainPointsProvider : Injecte les pain points adressés par la solution.
"""

from atomic_agents.lib.components.context_providers import BaseDynamicContextProvider
from typing import Optional
import os


class PainPointsProvider(BaseDynamicContextProvider):
    """Injecte les pain points connus"""

    def __init__(self, pain_points_content: Optional[str] = None, pain_points_file: Optional[str] = None):
        super().__init__(title="Pain Points Adressés")
        self.pain_points_content = pain_points_content
        self.pain_points_file = pain_points_file

    def get_info(self) -> str:
        if self.pain_points_content:
            pain_text = self.pain_points_content
        elif self.pain_points_file and os.path.exists(self.pain_points_file):
            with open(self.pain_points_file, "r", encoding="utf-8") as f:
                pain_text = f.read()
        else:
            return "⚠️ Pain points non disponibles"

        return f"""
## 💥 PAIN POINTS ADRESSÉS PAR NOTRE SOLUTION

{pain_text}

---

**Instructions :**
- Utilise ces pain points pour comprendre ce que nous résolvons
- Identifie quel pain point correspond le mieux à l'entreprise cible
- Adapte le wording au contexte spécifique de l'entreprise
"""
