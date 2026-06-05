from pydantic import BaseModel, HttpUrl
from datetime import datetime
from typing import Optional


class URLCreate(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None


class URLResponse(BaseModel):
    original_url: str
    short_code: str
    short_url: str


class URLStatsResponse(BaseModel):
    original_url: str
    short_code: str
    clicks: int
    created_at: datetime


class DeleteResponse(BaseModel):
    message: str


class UpdateCodeRequest(BaseModel):
    new_code: str


class SearchResponse(BaseModel):
    id: int
    original_url: str
    short_code: str