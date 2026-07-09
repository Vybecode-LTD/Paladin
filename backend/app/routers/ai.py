"""Admin AI routes. These call the server-side Anthropic proxy so the API key
never touches the browser. Author role or higher may generate drafts."""
from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import require_role
from app.models.user import User, UserRole
from app.schemas.ai import (
    DraftRequest, TitlesRequest, ExcerptRequest, SeoRequest, CoverImageRequest,
    AIResponse,
)
from app.services.anthropic_service import anthropic_service, AIServiceError

router = APIRouter()


@router.post("/admin/ai/draft", response_model=AIResponse)
async def ai_draft(req: DraftRequest,
                   _: User = Depends(require_role(UserRole.author))):
    try:
        text = await anthropic_service.draft_post(req.topic, req.tone, req.length)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return AIResponse(result=text)


@router.post("/admin/ai/titles", response_model=AIResponse)
async def ai_titles(req: TitlesRequest,
                    _: User = Depends(require_role(UserRole.author))):
    try:
        text = await anthropic_service.suggest_titles(req.topic)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return AIResponse(result=text)


@router.post("/admin/ai/excerpt", response_model=AIResponse)
async def ai_excerpt(req: ExcerptRequest,
                     _: User = Depends(require_role(UserRole.author))):
    try:
        text = await anthropic_service.write_excerpt(req.body_markdown)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return AIResponse(result=text)


@router.post("/admin/ai/seo", response_model=AIResponse)
async def ai_seo(req: SeoRequest,
                 _: User = Depends(require_role(UserRole.author))):
    try:
        text = await anthropic_service.seo_meta(req.title, req.body_markdown)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return AIResponse(result=text)


@router.post("/admin/ai/cover-image", response_model=AIResponse)
async def ai_cover_image(req: CoverImageRequest,
                         _: User = Depends(require_role(UserRole.author))):
    try:
        svg = await anthropic_service.cover_image(req.title, req.brief, req.style)
    except AIServiceError as exc:
        raise HTTPException(status_code=502, detail=str(exc))
    return AIResponse(result=svg)
