
from __future__ import annotations

from typing import Literal, TypedDict

from .prompt_loader import WTMSPromptLoader


MessageRole = Literal["user", "assistant"]


class ConversationMessage(TypedDict):
    role: MessageRole
    content: str


class WTMConversationBuilder:
    """
    Prepara los mensajes de WhatTM para un modelo conversacional.

    Las instrucciones oficiales se mantienen en
    prompts/system_prompt.md.

    Este componente no ejecuta el modelo ni modifica
    las instrucciones originales.
    """

    def __init__(
        self,
        prompt_loader: WTMSPromptLoader | None = None,
    ) -> None:
        self.prompt_loader = (
            prompt_loader or WTMSPromptLoader()
        )

    def build_messages(
        self,
        current_message: str,
        history: list[ConversationMessage] | None = None,
    ) -> list[dict[str, str]]:
        """
        Devuelve las instrucciones, el historial y el
        mensaje actual en el orden esperado por el modelo.
        """

        message = current_message.strip()

        if not message:
            raise ValueError(
                "El mensaje del usuario no puede estar vacío."
            )

        messages: list[dict[str, str]] = [
            {
                "role": "system",
                "content": self.prompt_loader.load(),
            }
        ]

        for item in history or []:
            role = item.get("role")
            content = item.get("content", "").strip()

            if role not in ("user", "assistant"):
                raise ValueError(
                    "El historial solo admite los roles "
                    "'user' y 'assistant'."
                )

            if not content:
                raise ValueError(
                    "El historial contiene un mensaje vacío."
                )

            messages.append(
                {
                    "role": role,
                    "content": content,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": message,
            }
        )

        return messages
