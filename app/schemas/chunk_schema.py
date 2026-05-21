from pydantic import BaseModel, Field
from typing import List, Optional


class SourceChunk(BaseModel):
    chunk_id: str = Field(description="Unique chunk identifier")
    source_id: str
    source_title: str
    source_type: str
    source_url: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    chunk_index: int
    text: str
    character_count: int
    created_at: str
