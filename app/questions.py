from .models import WTMQuestion, WTMOutput


class WTMQuestionManager:
    """
    Genera preguntas auxiliares para identificar información faltante.

    Estas preguntas son sugerencias para orientar la conversación.
    No constituyen un formulario obligatorio ni determinan por sí
    solas si un caso está listo para BINAH.
    """

    def build_basic_questions(
        self,
        context: bool,
        objective: bool,
        situation: bool,
    ) -> list[WTMQuestion]:
        questions: list[WTMQuestion] = []

        if not situation:
            questions.append(
                WTMQuestion(
                    id="q_situation",
                    text="¿Qué está ocurriendo exactamente?",
                    type="CLARIFICATION",
                    target="situation",
                )
            )

        if not context:
            questions.append(
                WTMQuestion(
                    id="q_context",
                    text="¿En qué contexto está ocurriendo?",
                    type="SCOPE",
                    target="context",
                )
            )

        if not objective:
            questions.append(
                WTMQuestion(
                    id="q_objective",
                    text="¿Qué te gustaría conseguir?",
                    type="OBJECTIVE",
                    target="objective",
                )
            )

        return questions

    def pending(self, output: WTMOutput) -> list[WTMQuestion]:
        return [
            question
            for question in output.questions
            if question.required and not question.answered
        ]