"""Owner-scoped API for manuscript claims and evidence review."""
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Request, status

from paperweave.api.dependencies import get_current_user
from paperweave.api.schemas.evidence import (
    ClaimCreate, ClaimResponse, ClaimUpdate, EvidenceLinkCreate,
    EvidenceLinkResponse, ReviewRequest,
)
from paperweave.infrastructure.db.evidence_repository import EvidenceRepository

router = APIRouter(prefix="/projects/{project_id}/claims", tags=["evidence"])


def get_evidence_repository(request: Request):
    with request.app.state.session_factory() as session:
        yield EvidenceRepository(session)


EvidenceRepo = Annotated[EvidenceRepository, Depends(get_evidence_repository)]


@router.get("", response_model=list[ClaimResponse])
def list_claims(project_id: UUID, repo: EvidenceRepo, user=Depends(get_current_user)):
    result = repo.list_claims(user.id, project_id)
    if result is None:
        raise HTTPException(404, "Project or manuscript not found")
    return result


@router.post("", response_model=ClaimResponse, status_code=status.HTTP_201_CREATED)
def create_claim(project_id: UUID, payload: ClaimCreate, repo: EvidenceRepo, user=Depends(get_current_user)):
    result = repo.create_claim(user.id, project_id, payload.block_position, payload.text)
    if result is None:
        raise HTTPException(404, "Project or manuscript not found")
    return result


@router.put("/{claim_id}", response_model=ClaimResponse)
def update_claim(project_id: UUID, claim_id: UUID, payload: ClaimUpdate, repo: EvidenceRepo,
                 user=Depends(get_current_user)):
    result = repo.update_claim(user.id, project_id, claim_id, payload.expected_version, payload.text)
    if result is None:
        raise HTTPException(409, "Claim not found or version conflict")
    return result


@router.post("/{claim_id}/links", response_model=EvidenceLinkResponse, status_code=status.HTTP_201_CREATED)
def create_link(project_id: UUID, claim_id: UUID, payload: EvidenceLinkCreate, repo: EvidenceRepo,
                user=Depends(get_current_user)):
    if payload.relation not in {"supports", "contradicts", "contextualizes"}:
        raise HTTPException(422, "Unsupported evidence relation")
    result = repo.create_link(user.id, project_id, claim_id, payload.passage_id,
                              payload.relation, payload.rationale)
    if result is None:
        raise HTTPException(404, "Claim or passage not found in this project")
    return result


@router.delete("/links/{link_id}", response_model=EvidenceLinkResponse)
def retract_link(project_id: UUID, link_id: UUID, repo: EvidenceRepo, user=Depends(get_current_user)):
    result = repo.retract_link(user.id, project_id, link_id)
    if result is None:
        raise HTTPException(404, "Evidence link not found")
    return result


@router.post("/links/{link_id}/review", response_model=EvidenceLinkResponse)
def review_link(project_id: UUID, link_id: UUID, payload: ReviewRequest, repo: EvidenceRepo,
                user=Depends(get_current_user)):
    if payload.decision not in {"verified", "rejected"}:
        raise HTTPException(422, "Decision must be verified or rejected")
    result = repo.review(user.id, project_id, link_id, payload.decision, payload.note)
    if result is None:
        raise HTTPException(404, "Evidence link not found")
    if result.get("stale"):
        raise HTTPException(409, "Claim or manuscript changed; review the evidence again")
    return result
