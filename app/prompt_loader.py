from __future__ import annotations

from pathlib import Path


class WTMSPromptLoader:
    """
    Carga las instrucciones conversacionales oficiales de WhatTM.

    El prompt permanece en prompts/system_prompt.md como fuente
    única de instrucciones. Este componente no llama a ningún
    proveedor de IA ni modifica el contenido del prompt.
    """

    def __init__(self, prompt_path: str | Path | None = None) -> None:
        if prompt_path is None:
            project_root = Path(__file__).resolve().parent.parent
            prompt_path = (
                project_root / "prompts" / "system_prompt.md"
            )

        self.prompt_path = Path(prompt_path)

    def load(self) -> str:
        """Devuelve el prompt completo como texto UTF-8."""

        if not self.prompt_path.exists():
            raise FileNotFoundError(
                "No se encontró el prompt conversacional de WhatTM: "
                f"{self.prompt_path}"
            )

        if not self.prompt_path.is_file():
            raise ValueError(
                "La ruta del prompt no corresponde a un archivo: "
                f"{self.prompt_path}"
            )

        prompt = self.prompt_path.read_text(encoding="utf-8").strip()

        if not prompt:
            raise ValueError(
                "El prompt conversacional de WhatTM está vacío."
            )

        return prompt