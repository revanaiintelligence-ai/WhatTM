from future import annotations

from uuid import uuid4
from typing import Optional

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

Registra información y mantiene el estado del caso.
La inteligencia conversacional decide qué preguntar,
qué hipótesis explorar y cuándo existe suficiencia.
"""

def __init__(self) -> None:
    self.question_manager = WTMQuestionManager()

def create_initial_output(
    self,
    form_input: WTMFormInput,
) -> WTMOutput:
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
            )
        )

    for item in form_input.evidence:
        output.evidence.append(
            WTMEvidence(
                id=str(uuid4()),
                content=item,
                type="USER_STATEMENT",
                source="initial_form",
            )
        )

    return self._update_questions(output)

def process_message(
    self,
    output: WTMOutput,
    conversation_input: WTMConversationInput,
) -> WTMOutput:
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
        )
    )

    output.status = "CLARIFYING"
    output.ready_for_binah = False

    return self._update_questions(output)

def _update_questions(self, output: WTMOutput) -> WTMOutput:
    output.questions = self.question_manager.build_basic_questions(
        context=bool(output.context),
        objective=bool(output.objective),
        situation=bool(output.situation),
    )

    output.status = (
        "CLARIFYING" if output.questions else "VERIFYING"
    )

    # Las preguntas no bloquean automáticamente el proceso.
    output.blocking_reasons = []
    return output

def mark_ready_for_binah(self, output: WTMOutput) -> WTMOutput:
    output.status = "READY_FOR_BINAH"
    output.ready_for_binah = True
    output.blocking_reasons = []
    return output

def mark_not_ready_for_binah(
    self,
    output: WTMOutput,
    reasons: Optional[list[str]] = None,
) -> WTMOutput:
    output.ready_for_binah = False
    output.status = "VERIFYING"
    output.blocking_reasons = list(reasons or [])
    return output