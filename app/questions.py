from __future__ import annotations

from .models import WTMQuestion, WTMOutput


class WTMQuestionManager:
    """
    Administra preguntas auxiliares de clarificación.

    No dirige la conversación del modelo ni impone una secuencia
    obligatoria. Las instrucciones conversacionales pertenecen
    a prompts/system_prompt.md.

    Este componente identifica campos estructurales que siguen
    vacíos y mantiene el estado de las preguntas registradas.
    """

    FIELD_QUESTIONS = {
        "situation": {
            "id": "q_situation",
            "text": "¿Qué está ocurriendo exactamente?",
            "type": "CLARIFICATION",
        },
        "context": {
            "id": "q_context",
            "text": "¿En qué contexto está ocurriendo?",
            "type": "SCOPE",
        },
        "objective": {
            "id": "q_objective",
            "text": "¿Qué te gustaría conseguir?",
            "type": "OBJECTIVE",
        },
    }

    def build_basic_questions(
        self,
        context: bool,
        objective: bool,
        situation: bool,
    ) -> list[WTMQuestion]:
        """
        Sugiere preguntas solo para campos que no tienen contenido.

        El orden no representa una secuencia conversacional
        obligatoria ni determina la prioridad del modelo.
        """

        available = {
            "situation": situation,
            "context": context,
            "objective": objective,
        }

        questions: list[WTMQuestion] = []

        for target, has_content in available.items():
            if has_content:
                continue

            definition = self.FIELD_QUESTIONS[target]

            questions.append(
                WTMQuestion(
                    id=definition["id"],
                    text=definition["text"],
                    type=definition["type"],
                    target=target,
                    required=True,
                    answered=False,
                )
            )

        return questions

    def pending(
        self,
        output: WTMOutput,
    ) -> list[WTMQuestion]:
        """
        Devuelve las preguntas obligatorias todavía pendientes.

        Si el campo asociado ya tiene contenido, la pregunta no
        se considera pendiente, aunque su indicador answered
        todavía no se haya actualizado.
        """

        field_values = {
            "situation": output.situation,
            "context": output.context,
            "objective": output.objective,
        }

        pending_questions: list[WTMQuestion] = []

        for question in output.questions:
            if not question.required:
                continue

            if question.answered:
                continue

            target = question.target

            if target in field_values:
                value = field_values[target]

                if value and value.strip():
                    continue

            pending_questions.append(question)

        return pending_questions