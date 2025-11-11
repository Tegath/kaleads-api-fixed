"""
PersonaContextProvider : Injecte les personas cibles détaillés.
"""

from atomic_agents.lib.components.context_providers import BaseDynamicContextProvider
from typing import Optional
import os


class PersonaContextProvider(BaseDynamicContextProvider):
    """Injecte les personas cibles détaillés"""

    def __init__(self, personas_content: Optional[str] = None, personas_file_path: Optional[str] = None):
        super().__init__(title="Personas Cibles Détaillés")
        self.personas_content = personas_content
        self.personas_file_path = personas_file_path

    def get_info(self) -> str:
        if self.personas_content:
            personas_text = self.personas_content
        elif self.personas_file_path and os.path.exists(self.personas_file_path):
            with open(self.personas_file_path, "r", encoding="utf-8") as f:
                personas_text = f.read()
        else:
            return "⚠️ Personas non disponibles"

        return f"""
## 👥 PERSONAS CIBLES

{personas_text}

---

**Instructions :**
- Utilise ces personas comme référence pour identifier le persona de l'entreprise cible
- Si le persona exact n'est pas trouvé, choisis le plus proche parmi cette liste
- Retourne TOUJOURS un persona, même si c'est une approximation
"""
