from __future__ import annotations

from uuid import uuid4

from .models import (
    WTMConversationInput,
    WTMEvidence,
    WTMFormInput,
    WTMOutput,
    WTMQuestion,
)
from .questions import WTMQuestionManager


class WTMEngine:
    """
    Motor estructural de WhatTM.

    Registra declaraciones, conserva la trazabilidad y actualiza
    el estado de clarificación. No confunde declaraciones con
    hechos verificados ni decide automáticamente que un caso
    está listo para BINAH.
    """

    def __init__(self) -> None:
        self.question_manager = WTMQuestionManager()

    def create_initial_output(
        self,
        form_input: WTMFormInput,
    ) -> WTMOutput:
        """Crea el estado inicial a partir del formulario."""

        output = WTMOutput(
            business=form_input.business,
            context=form_input.context,
            objective=form_input.objective,
            situation=form_input.description,
        )

        if form_input.description and form_input.description.strip():
            output.evidence.append(
                WTMEvidence(
                    id=str(uuid4()),
                    content=form_input.description.strip(),
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
        self._refresh_traceability(output)
        return output

    def process_message(
        self,
        output: WTMOutput,
        conversation_input: WTMConversationInput,
    ) -> WTMOutput:
        """
        Registra un mensaje del usuario y actualiza el estado.

        El mensaje se conserva como declaración provisional.
        Este método no interpreta automáticamente su significado
        ni inventa hechos, observaciones o hipótesis.
        """

        message = conversation_input.message.strip()

        if not message:
            return output

        source = (
            f"conversation:{conversation_input.conversation_id}"
            if conversation_input.conversation_id
            else "conversation"
        )

        output.evidence.append(
            WTMEvidence(
                id=str(uuid4()),
                content=message,
                type="USER_STATEMENT",
                source=source,
                status="PROVISIONAL",
            )
        )

        output.status = "CLARIFYING"
        output.ready_for_binah = False
        output.blocking_reasons = []

        # No se borran las preguntas anteriores: se conserva
        # el historial y se actualiza únicamente el estado actual.
        self._update_questions(output)
        self._refresh_traceability(output)

        return output

    def _update_questions(
        self,
        output: WTMOutput,
    ) -> WTMOutput:
        """
        Actualiza las preguntas auxiliares según los campos del caso.

        La generación de preguntas no demuestra por sí sola que
        el caso esté completo ni que esté listo para BINAH.
        """

        generated = self.question_manager.build_basic_questions(
            context=bool(output.context and output.context.strip()),
            objective=bool(output.objective and output.objective.strip()),
            situation=bool(output.situation and output.situation.strip()),
        )

        existing_by_id = {
            question.id: question
            for question in output.questions
        }

        merged_questions = list(output.questions)

        for question in generated:
            if question.id not in existing_by_id:
                merged_questions.append(question)

        # Las preguntas auxiliares solo se marcan como respondidas
        # cuando el campo correspondiente ya contiene información.
        field_values = {
            "context": output.context,
            "objective": output.objective,
            "situation": output.situation,
        }

        for question in merged_questions:
            if question.target in field_values:
                value = field_values[question.target]
                if value and value.strip():
                    question.answered = True

        output.questions = merged_questions

        pending = self.question_manager.pending(output)

        if pending:
            output.status = "CLARIFYING"
        elif output.status != "READY_FOR_BINAH":
            output.status = "VERIFYING"

        return output

    def mark_ready_for_binah(
        self,
        output: WTMOutput,
    ) -> WTMOutput:
        """
        Marca la preparación para BINAH solo cuando los campos
        mínimos de contexto, objetivo y situación están presentes.

        Esta comprobación es estructural, no una validación
        semántica completa de la calidad de la información.
        """

        missing = []

        if not output.situation or not output.situation.strip():
            missing.append("Falta describir la situación.")

        if not output.context or not output.context.strip():
            missing.append("Falta especificar el contexto.")

        if not output.objective or not output.objective.strip():
            missing.append("Falta definir el objetivo.")

        if missing:
            output.ready_for_binah = False
            output.status = "CLARIFYING"
            output.blocking_reasons = missing
            return output

        output.status = "READY_FOR_BINAH"
        output.ready_for_binah = True
        output.blocking_reasons = []

        return output

    def mark_not_ready_for_binah(
        self,
        output: WTMOutput,
        reasons: list[str] | None = None,
    ) -> WTMOutput:
        """Registra las razones por las que el caso no está listo."""

        output.ready_for_binah = False
        output.status = "VERIFYING"
        output.blocking_reasons = list(reasons or [])

        return output

    def _refresh_traceability(
        self,
        output: WTMOutput,
    ) -> None:
        """Actualiza los identificadores de trazabilidad existentes."""

        output.traceability.source_evidence_ids = [
            item.id for item in output.evidence
        ]
        output.traceability.observation_ids = [
            item.id for item in output.observations
        ]
        output.traceability.hypothesis_ids = [
            item.id for item in output.hypotheses
        ]
        output.traceability.unknown_ids = [
            item.id for item in output.unknowns
        ]
        output.traceability.contradiction_ids = [
            item.id for item in output.contradictions
        ]
        output.traceability.question_ids = [
            item.id for item in output.questions
        ]