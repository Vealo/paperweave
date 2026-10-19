"""Owner-scoped API for mock-only manuscript proposals."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status

from paperweave.api.dependencies import get_current_user
from paperweave.api.schemas.ai_proposals import AIProposalCreate, AIProposalDecision, AIProposalResponse
from paperweave.integrations.llm.mock import MockLLMAdapter
from paperweave.infrastructure.db.ai_proposal_repository import AIProposalRepository
from paperweave.modules.ai_proposals.errors import ProposalAdapterError
from paperweave.modules.ai_proposals.service import AIProposalService

router = APIRouter(prefix="/projects/{project_id}/ai-proposals", tags=["ai-proposals"])


def get_ai_proposal_service(request: Request):
    with request.app.state.session_factory() as session:
        yield AIProposalService(AIProposalRepository(session), MockLLMAdapter())


AIProposalServiceDep = Annotated[AIProposalService, Depends(get_ai_proposal_service)]


@router.post("", response_model=AIProposalResponse, status_code=status.HTTP_201_CREATED)
def create_proposal(project_id: UUID, payload: AIProposalCreate,
                    service: AIProposalServiceDep, user=Depends(get_current_user)):
    try:
        result = service.create(user.id, project_id, expected_version=payload.expected_version,
                                target_position=payload.target_position,
                                selected_text=payload.selected_text,
                                instruction=payload.instruction.strip(),
                                idempotency_key=payload.idempotency_key)
    except ProposalAdapterError as exc:
        raise HTTPException(503, "AI proposal adapter failed; manuscript was not changed") from exc
    if result is None:
        raise HTTPException(404, "Project or manuscript not found")
    if result == "stale_target":
        raise HTTPException(409, "stale_target")
    if result == "invalid_selection":
        raise HTTPException(422, "invalid_selection")
    if result == "idempotency_conflict":
        raise HTTPException(409, "idempotency_conflict")
    if result.get("status") == "failed":
        raise HTTPException(503, "AI proposal adapter failed; manuscript was not changed")
    return AIProposalResponse.model_validate(result)


@router.get("/{proposal_id}", response_model=AIProposalResponse)
def get_proposal(project_id: UUID, proposal_id: UUID, service: AIProposalServiceDep,
                 user=Depends(get_current_user)):
    result = service.get(user.id, project_id, proposal_id)
    if result is None:
        raise HTTPException(404, "AI proposal not found")
    return AIProposalResponse.model_validate(result)


@router.post("/{proposal_id}/decision", response_model=AIProposalResponse)
def decide_proposal(project_id: UUID, proposal_id: UUID, payload: AIProposalDecision,
                    service: AIProposalServiceDep, user=Depends(get_current_user)):
    if payload.decision not in {"accepted", "rejected"}:
        raise HTTPException(422, "decision must be accepted or rejected")
    result = service.decide(user.id, project_id, proposal_id,
                            decision=payload.decision, note=payload.note)
    if result is None:
        raise HTTPException(404, "AI proposal not found")
    if result == "stale_target":
        raise HTTPException(409, "stale_target")
    if result == "already_decided":
        raise HTTPException(409, "already_decided")
    if result == "failed":
        raise HTTPException(409, "proposal_failed")
    if result.get("status") == "stale":
        raise HTTPException(409, "stale_target")
    return AIProposalResponse.model_validate(result)
