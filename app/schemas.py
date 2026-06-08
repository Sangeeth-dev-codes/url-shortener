from pydantic import BaseModel, HttpUrl, Field
from datetime import datetime
from typing import Optional


class URLCreate(BaseModel):
    url: HttpUrl
    custom_code: Optional[str] = None
    
    expires_in_days: int = Field(
        default=30,
        ge=1,
        description="Number of days before URL expires"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "url": "https://openai.com",
                "custom_code": "openai",
                "expires_in_days": 30
            }
        }


class URLResponse(BaseModel):
    original_url: str
    short_code: str
    short_url: str
    expires_at: datetime


class HomeResponse(BaseModel):
    message: str


class URLStatsResponse(BaseModel):
    original_url: str
    short_code: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime]
    status: str

    class Config:
        from_attributes = True


class DeleteResponse(BaseModel):
    message: str


class UpdateResponse(BaseModel):
    message: str
    new_code: str


class UpdateCodeRequest(BaseModel):
    new_code: str

    class Config:
        json_schema_extra = {
            "example": {
                "new_code": "OPENAI123"
            }
        }


class SearchResponse(BaseModel):
    id: int
    original_url: str
    short_code: str

    class Config:
        from_attributes = True


class URLListResponse(BaseModel):
    id: int
    original_url: str
    short_code: str
    clicks: int
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True