from pydantic import BaseModel, Field


class DraftRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=300)
    tone: str = Field(default="professional", max_length=50)
    length: str = Field(default="medium", max_length=20)  # short | medium | long


class TitlesRequest(BaseModel):
    topic: str = Field(min_length=1, max_length=300)


class ExcerptRequest(BaseModel):
    body_markdown: str = Field(min_length=1, max_length=20000)


class SeoRequest(BaseModel):
    title: str = Field(min_length=1, max_length=300)
    body_markdown: str = Field(min_length=1, max_length=20000)


class AIResponse(BaseModel):
    result: str
