
"""Proveedor Google Gemini para WhatTM y Streamlit."""

from __future__ import annotations

import os
from typing import Any

import streamlit as st
from google import genai
from google.genai import types


class GeminiAIProvider:
    """Conecta WhatTM con el mismo proveedor Gemini que REVA.N."""

    def __init__(self) -> None:
        api_key = self._setting("GEMINI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "Falta GEMINI_API_KEY. Configúrala en "
                "Streamlit Secrets o en la variable de entorno "
                "GEMINI_API_KEY."
            )

        self.model = (
            self._setting("GEMINI_MODEL")
            or "gemini-3.6-flash"
        )

        self.client = genai.Client(api_key=api_key)

    @staticmethod
    def _setting(name: str) -> str | None:
        """Lee la configuración de Streamlit o del entorno."""
        try:
            value: Any = st.secrets.get(name)
            if value:
                return str(value).strip()
        except Exception:
            pass

        value = os.getenv(name)
        return value.strip() if value else None

    def generate_reply(
        self,
        system_instruction: str,
        messages: list[dict[str, str]],
    ) -> str:
        """Genera una respuesta usando el prompt y el historial."""

        contents = []

        for message in messages:
            role = message.get("role")
            content = message.get("content", "").strip()

            if role not in {"user", "assistant"} or not content:
                continue

            contents.append(
                types.Content(
                    role="user" if role == "user" else "model",
                    parts=[
                        types.Part.from_text(text=content)
                    ],
                )
            )

        if not contents:
            raise ValueError(
                "La conversación no contiene mensajes."
            )

        response = self.client.models.generate_content(
            model=self.model,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
            ),
        )

        reply = (response.text or "").strip()

        if not reply:
            raise RuntimeError(
                "Gemini no devolvió texto. "
                "Intenta reformular el mensaje."
            )

        return reply
