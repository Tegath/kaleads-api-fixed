"""
PCIContextProvider : Injecte le Profil Client Idéal dans le contexte des agents.
"""

from atomic_agents.lib.components.context_providers import BaseDynamicContextProvider
from typing import Optional
import os


class PCIContextProvider(BaseDynamicContextProvider):
    """
    Injecte le Profil Client Idéal (PCI) dans le contexte de tous les agents.

    Peut lire depuis un fichier Markdown local ou directement depuis une string.
    """

    def __init__(self, pci_content: Optional[str] = None, pci_file_path: Optional[str] = None):
        """
        Initialise le provider avec soit du contenu direct, soit un chemin vers un fichier.

        Args:
            pci_content: Contenu PCI en string (prioritaire)
            pci_file_path: Chemin vers le fichier PCI.md (fallback)
        """
        super().__init__(title="Profil Client Idéal (PCI)")
        self.pci_content = pci_content
        self.pci_file_path = pci_file_path

    def get_info(self) -> str:
        """
        Charge et retourne le PCI formaté pour injection dans les prompts.
        """
        # Priorité 1: Contenu fourni directement
        if self.pci_content:
            pci_text = self.pci_content

        # Priorité 2: Charger depuis fichier
        elif self.pci_file_path and os.path.exists(self.pci_file_path):
            with open(self.pci_file_path, "r", encoding="utf-8") as f:
                pci_text = f.read()

        else:
            return "⚠️ PCI non disponible - utiliser les informations générales disponibles"

        return f"""
## 📋 PROFIL CLIENT IDÉAL (PCI)

{pci_text}

---

**Instructions pour l'agent :**
- Référence SYSTÉMATIQUEMENT ce PCI dans ton raisonnement
- Vérifie que tes outputs sont alignés avec ces critères
- Si incertitude, priorise les informations du PCI
- Utilise ce PCI pour comprendre le positionnement et la cible du client
"""
