"""
CaseStudyProvider : Injecte les études de cas et success stories disponibles.
"""

from atomic_agents.lib.components.context_providers import BaseDynamicContextProvider
from typing import Optional
import os


class CaseStudyProvider(BaseDynamicContextProvider):
    """Injecte les études de cas disponibles"""

    def __init__(
        self,
        case_studies_content: Optional[str] = None,
        case_studies_dir: Optional[str] = None
    ):
        super().__init__(title="Études de Cas et Success Stories")
        self.case_studies_content = case_studies_content
        self.case_studies_dir = case_studies_dir

    def get_info(self) -> str:
        # Priorité 1: Contenu fourni directement
        if self.case_studies_content:
            case_studies_text = self.case_studies_content

        # Priorité 2: Charger depuis dossier
        elif self.case_studies_dir and os.path.exists(self.case_studies_dir):
            case_studies = []
            for filename in sorted(os.listdir(self.case_studies_dir)):
                if filename.endswith((".md", ".txt")):
                    filepath = os.path.join(self.case_studies_dir, filename)
                    with open(filepath, "r", encoding="utf-8") as f:
                        case_studies.append(f"### {filename}\n\n{f.read()}")

            if case_studies:
                case_studies_text = "\n\n---\n\n".join(case_studies)
            else:
                case_studies_text = "Aucune étude de cas trouvée dans le dossier"

        else:
            return "⚠️ Études de cas non disponibles"

        return f"""
## 📊 ÉTUDES DE CAS ET SUCCESS STORIES

{case_studies_text}

---

**Instructions :**
- Utilise ces exemples pour comprendre le type de résultats que nous produisons
- Si tu dois créer un case study insight, inspire-toi de ces formats
- Adapte les métriques au secteur de l'entreprise cible
- Retourne des résultats mesurables et crédibles
"""
