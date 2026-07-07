from pydantic import BaseModel


class DraftRequest(BaseModel):
    topic: str
    tone: str = "professional"
    length: str = "medium"  # short | medium | long


class TitlesRequest(BaseModel):
    topic: str


class ExcerptRequest(BaseModel):
    body_markdown: str


class SeoRequest(BaseModel):
    title: str
    body_markdown: str


class AIResponse(BaseModel):
    result: str
