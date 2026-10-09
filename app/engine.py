from __future__ import annotations

import re
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

    Responsabilidades:
    - Registrar los mensajes como declaraciones provisionales.
    - Actualizar situación, contexto y objetivo cuando exista
      información explícita o una respuesta a una pregunta pendiente.
    - Mantener la trazabilidad de la información.
    - Evitar repetir preguntas auxiliares ya respondidas.
    - Comprobar los bloqueos conocidos antes de preparar el caso
      para BINAH.

    Este motor no sustituye a un modelo de lenguaje ni verifica
    automáticamente la veracidad de las declaraciones.
    """

    def __init__(self) -> None:
        self.question_manager = WTMQuestionManager()

    def create_initial_output(
        self,
        form_input: WTMFormInput,
    ) -> WTMOutput:
        """Construye el estado inicial a partir del formulario."""

        output = WTMOutput(
            business=form_input.business,
            context=self._clean(form_input.context),
            objective=self._clean(form_input.objective),
            situation=self._clean(form_input.description),
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
        Registra un mensaje y actualiza el caso.

        Si el mensaje responde a una pregunta pendiente, intenta
        incorporarlo al campo correspondiente. Si contiene una
        declaración explícita sobre contexto, objetivo o situación,
        utiliza esa declaración para actualizar el campo indicado.
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

        self._apply_message_to_case(output, message)

        output.ready_for_binah = False
        output.blocking_reasons = []

        self._update_questions(output)
        self._refresh_traceability(output)

        return output

    def _apply_message_to_case(
        self,
        output: WTMOutput,
        message: str,
    ) -> None:
        """
        Actualiza campos únicamente cuando existe una señal clara.

        Las expresiones explícitas tienen prioridad sobre la pregunta
        pendiente. No se infiere que una respuesta sea un hecho probado.
        """

        explicit_fields = self._extract_explicit_fields(message)

        if explicit_fields:
            for field, value in explicit_fields.items():
                setattr(output, field, value)
            return

        pending = self.question_manager.pending(output)

        if not pending:
            return

        # La primera pregunta pendiente orienta la interpretación
        # de la respuesta, pero no convierte la respuesta en un hecho.
        target = pending[0].target

        if target in {"situation", "context", "objective"}:
            current_value = getattr(output, target)

            if not current_value or not current_value.strip():
                setattr(output, target, message)

    def _extract_explicit_fields(
        self,
        message: str,
    ) -> dict[str, str]:
        """
        Extrae campos solo cuando el usuario utiliza expresiones
        explícitas. Es una regla básica, no comprensión semántica.
        """

        patterns = {
            "objective": (
                r"(?:mi objetivo es|el objetivo es|"
                r"quiero conseguir|quiero lograr|"
                r"me gustaría conseguir|necesito conseguir)"
                r"\s*[:,-]?\s*(.+)"
            ),
            "context": (
                r"(?:el contexto es|mi contexto es|"
                r"esto ocurre en|ocurre en|"
                r"en mi negocio|en mi empresa|"
                r"en mi trabajo)"
                r"\s*[:,-]?\s*(.+)"
            ),
            "situation": (
                r"(?:la situación es|el problema es|"
                r"lo que ocurre es|está ocurriendo que)"
                r"\s*[:,-]?\s*(.+)"
            ),
        }

        extracted: dict[str, str] = {}

        for field, pattern in patterns.items():
            match = re.search(
                pattern,
                message,
                flags=re.IGNORECASE,
            )

            if match:
                value = self._clean(match.group(1))

                if value:
                    extracted[field] = value

        return extracted

    def _update_questions(
        self,
        output: WTMOutput,
    ) -> WTMOutput:
        """
        Sincroniza las preguntas auxiliares con los campos actuales.

        Conserva el historial de preguntas existentes, pero solo
        genera nuevas preguntas para campos que siguen vacíos.
        """

        generated = self.question_manager.build_basic_questions(
            context=bool(self._clean(output.context)),
            objective=bool(self._clean(output.objective)),
            situation=bool(self._clean(output.situation)),
        )

        existing_by_id = {
            question.id: question
            for question in output.questions
        }

        for question in generated:
            if question.id not in existing_by_id:
                output.questions.append(question)
                existing_by_id[question.id] = question

        field_values = {
            "context": output.context,
            "objective": output.objective,
            "situation": output.situation,
        }

        for question in output.questions:
            if question.target in field_values:
                value = field_values[question.target]

                if self._clean(value):
                    question.answered = True

        pending = self.question_manager.pending(output)

        if pending:
            output.status = "CLARIFYING"
            output.ready_for_binah = False
        elif output.status not in {"READY_FOR_BINAH"}:
            output.status = "VERIFYING"
            output.ready_for_binah = False

        return output

    def mark_ready_for_binah(
        self,
        output: WTMOutput,
    ) -> WTMOutput:
        """
        Evalúa las condiciones estructurales conocidas para BINAH.

        La presencia de los tres campos mínimos no garantiza por sí
        sola la calidad ni la veracidad de la información.
        """

        missing: list[str] = []

        if not self._clean(output.situation):
            missing.append("Falta describir la situación.")

        if not self._clean(output.context):
            missing.append("Falta especificar el contexto.")

        if not self._clean(output.objective):
            missing.append("Falta definir el objetivo.")

        pending = self.question_manager.pending(output)

        if pending:
            missing.append(
                "Existen preguntas de clarificación obligatorias "
                "sin responder."
            )

        blocking_unknowns = [
            item
            for item in output.unknowns
            if item.blocks_binah
        ]

        if blocking_unknowns:
            missing.append(
                "Existen incógnitas que bloquean el análisis de BINAH."
            )

        unresolved_contradictions = [
            item
            for item in output.contradictions
            if not item.resolved
        ]

        if unresolved_contradictions:
            missing.append(
                "Existen contradicciones sin resolver."
            )

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
        """Sincroniza los identificadores de trazabilidad."""

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

    @staticmethod
    def _clean(value: str | None) -> str | None:
        """Devuelve texto limpio o None si está vacío."""

        if value is None:
            return None

        cleaned = value.strip()
        return cleaned or None