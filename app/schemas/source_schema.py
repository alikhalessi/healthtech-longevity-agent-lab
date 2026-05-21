from pydantic import BaseModel, Field
from typing import List, Optional


class SourceRecord(BaseModel):
    source_id: str = Field(description="Unique local source identifier")
    title: str
    source_type: str = Field(description="article, abstract, paper, web_text, note, or other")
    url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    text: str
    text_preview: str
    character_count: int
    created_at: str
