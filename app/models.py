from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class WTMFormInput(BaseModel):
    business: str = "Por determinar"
    context: Optional[str] = None
    objective: Optional[str] = None
    description: Optional[str] = None
    evidence: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WTMConversationInput(BaseModel):
    message: str = Field(..., min_length=1)
    conversation_id: Optional[str] = None
    turn: Optional[int] = None


class WTMEvidence(BaseModel):
    id: str
    content: str
    type: Literal[
        "FACT",
        "OBSERVATION",
        "USER_STATEMENT",
        "DOCUMENT",
        "METRIC",
        "RECORD",
        "OTHER",
    ] = "USER_STATEMENT"
    source: Optional[str] = None
    status: Literal[
        "PROVISIONAL",
        "SUPPORTED",
        "VERIFIED",
        "DISPUTED",
    ] = "PROVISIONAL"
    supports: List[str] = Field(default_factory=list)
    contradicts: List[str] = Field(default_factory=list)


class WTMObservation(BaseModel):
    id: str
    statement: str
    source_evidence_ids: List[str] = Field(default_factory=list)
    status: Literal[
        "PROVISIONAL",
        "SUPPORTED",
        "VERIFIED",
        "DISPUTED",
    ] = "PROVISIONAL"


class WTMHypothesis(BaseModel):
    id: str
    statement: str
    basis_ids: List[str] = Field(default_factory=list)
    status: Literal[
        "PROVISIONAL",
        "SUPPORTED",
        "VERIFIED",
        "REJECTED",
    ] = "PROVISIONAL"
    verification_required: bool = True


class WTMUnknown(BaseModel):
    id: str
    statement: str
    importance: Literal[
        "LOW",
        "MEDIUM",
        "HIGH",
        "CRITICAL",
    ] = "MEDIUM"
    blocks_binah: bool = False


class WTMContradiction(BaseModel):
    id: str
    statement_a: str
    statement_b: str
    source_ids: List[str] = Field(default_factory=list)
    resolved: bool = False
    resolution: Optional[str] = None


class WTMQuestion(BaseModel):
    id: str
    text: str
    type: str = "CLARIFICATION"
    target: Optional[str] = None
    required: bool = True
    answered: bool = False


class WTMNeedCandidate(BaseModel):
    statement: str
    type: Optional[str] = None
    area: Optional[str] = None
    function: Optional[str] = None
    process: Optional[str] = None
    activity: Optional[str] = None
    task: Optional[str] = None
    actor: Optional[str] = None
    basis_ids: List[str] = Field(default_factory=list)
    confidence_status: Literal[
        "PROVISIONAL",
        "SUPPORTED",
        "VERIFIED",
    ] = "PROVISIONAL"


class WTMTraceability(BaseModel):
    source_evidence_ids: List[str] = Field(default_factory=list)
    observation_ids: List[str] = Field(default_factory=list)
    hypothesis_ids: List[str] = Field(default_factory=list)
    unknown_ids: List[str] = Field(default_factory=list)
    contradiction_ids: List[str] = Field(default_factory=list)
    question_ids: List[str] = Field(default_factory=list)


class WTMOutput(BaseModel):
    methodology: str = "WTM"
    version: str = "0.2"
    status: str = "INITIAL"

    business: str = "Por determinar"
    context: Optional[str] = None
    objective: Optional[str] = None
    situation: Optional[str] = None

    observations: List[WTMObservation] = Field(default_factory=list)
    hypotheses: List[WTMHypothesis] = Field(default_factory=list)
    unknowns: List[WTMUnknown] = Field(default_factory=list)
    contradictions: List[WTMContradiction] = Field(default_factory=list)
    evidence: List[WTMEvidence] = Field(default_factory=list)
    questions: List[WTMQuestion] = Field(default_factory=list)

    need_candidate: Optional[WTMNeedCandidate] = None
    conversation_summary: Optional[str] = None

    ready_for_binah: bool = False
    blocking_reasons: List[str] = Field(default_factory=list)
    traceability: WTMTraceability = Field(
        default_factory=WTMTraceability
    )