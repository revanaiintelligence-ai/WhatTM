from __future__ import annotations

from typing import Optional
from uuid import uuid4

from .models import (
    WTMConversationInput,
    WTMEvidence,
    WTMFormInput,
    WTMOutput,
)
from .questions import WTMQuestionManager


class WTMEngine:
    """
    Motor estructural de WhatTM.

    Registra la información del caso, conserva la evidencia
    declarada por el usuario y mantiene el estado del análisis.

    Este motor no convierte automáticamente una declaración
    en un hecho verificado ni impone un cuestionario rígido.

    La inteligencia conversacional podrá utilizar esta estructura
    para formular preguntas, explorar hipótesis y determinar
    cuándo existe información suficiente para transferir el caso
    a BINAH.
    """

    def __init__(self) -> None:
        self.question_manager = WTMQuestionManager()

    def create_initial_output(
        self,
        form_input: WTMFormInput,
    ) -> WTMOutput:
        """
        Crea el estado inicial a partir del formulario del usuario.
        """

        output = WTMOutput(
            business=form_input.business,
            context=form_input.context,
            objective=form_input.objective,
            situation=form_input.description,
        )

        if form_input.description:
            output.evidence.append(
                WTMEvidence(
                    id=str(uuid4()),
                    content=form_input.description,
                    type="USER_STATEMENT",
                    source="initial_form",
                    status="PROVISIONAL",
                )
            )

        for item in form_input.evidence:
            if item and item.strip():
                output.evidence.append(
                    WTMEvidence(
                        id=str(uuid4()),
                        content=item.strip(),
                        type="USER_STATEMENT",
                        source="initial_form",
                        status="PROVISIONAL",
                    )
                )

        self._update_questions(output)

        return output

    def process_message(
        self,
        output: WTMOutput,
        conversation_input: WTMConversationInput,
    ) -> WTMOutput:
        """
        Registra un mensaje de la conversación.

        La función conserva el mensaje como declaración del usuario.
        No afirma que el contenido esté verificado ni inventa
        observaciones o hipótesis que el mensaje no sustente.
        """

        message = conversation_input.message.strip()

        if not message:
            return output

        if conversation_input.conversation_id:
            source = (
                f"conversation:{conversation_input.conversation_id}"
            )
        else:
            source = "conversation"

        output.evidence.append(
            WTMEvidence(
                id=str(uuid4()),
                content=message,
                type="USER_STATEMENT",
                source=source,
                status="PROVISIONAL",
            )
        )

        # Una nueva declaración exige revisar el estado del caso.
        # No implica que el caso esté listo para BINAH.
        output.status = "CLARIFYING"
        output.ready_for_binah = False

        self._update_questions(output)

        return output

    def _update_questions(
        self,
        output: WTMOutput,
    ) -> WTMOutput:
        """
        Genera preguntas auxiliares según la información disponible.

        Las preguntas pendientes orientan la clarificación,
        pero no bloquean por sí mismas el análisis ni la transferencia.
        """

        output.questions = (
            self.question_manager.build_basic_questions(
                context=bool(
                    output.context and output.context.strip()
                ),
                objective=bool(
                    output.objective and output.objective.strip()
                ),
                situation=bool(
                    output.situation and output.situation.strip()
                ),
            )
        )

        if output.questions:
            output.status = "CLARIFYING"
        else:
            output.status = "VERIFYING"

        # La ausencia de respuestas a preguntas auxiliares
        # no crea automáticamente bloqueos.
        output.blocking_reasons = []

        return output

    def mark_ready_for_binah(
        self,
        output: WTMOutput,
    ) -> WTMOutput:
        """
        Marca explícitamente el resultado como preparado para BINAH.

        Esta función no realiza por sí misma una validación semántica.
        La decisión debe proceder de la evaluación del caso.
        """

        output.status = "READY_FOR_BINAH"
        output.ready_for_binah = True
        output.blocking_reasons = []

        return output

    def mark_not_ready_for_binah(
        self,
        output: WTMOutput,
        reasons: Optional[list[str]] = None,
    ) -> WTMOutput:
        """
        Registra por qué el caso todavía no está preparado
        para transferirse a BINAH.
        """

        output.ready_for_binah = False
        output.status = "VERIFYING"
        output.blocking_reasons = list(reasons or [])

        return output