import random
import string

from datetime import datetime, timezone, timedelta

from typing import List

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status,
    Request,
    Query
)

from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import engine, get_db
from app.models import URL

from app.schemas import (
    URLResponse,
    HomeResponse,
    URLStatsResponse,
    DeleteResponse,
    UpdateResponse,
    URLCreate,
    UpdateCodeRequest,
    SearchResponse,
    URLListResponse
)

tags_metadata = [
    {
        "name": "URLs",
        "description": "URL management operations"
    }
]

app = FastAPI(
    title="URL Shortener API",
    version="1.0.0",
    description="A URL Shortener built with FastAPI and SQLAlchemy",
    openapi_tags=tags_metadata
)

URL.metadata.create_all(bind=engine)


# =====================================
# Helper Function
# =====================================

def generate_short_code(db: Session) -> str:

    while True:

        short_code = "".join(
            random.choices(
                string.ascii_letters + string.digits,
                k=6
            )
        )

        existing = db.query(URL).filter(
            URL.short_code == short_code
        ).first()

        if not existing:
            return short_code


# =====================================
# Home
# =====================================

@app.get(
    "/",
    response_model=HomeResponse,
    summary="API Home",
    description="Returns a welcome message for the URL Shortener API."
)
def home():

    return {
        "message": "Welcome to URL Shortener API"
    }


# =====================================
# Create Short URL
# =====================================

@app.post(
    "/shorten",
    summary="Create a Short URL",
    description="Creates a shortened URL from a long URL. Supports optional custom short codes.",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["URLs"],
    responses={
        400: {
            "description": "Custom short code already exists"
        }
    }
)
def shorten_url(
    request: Request,
    data: URLCreate,
    db: Session = Depends(get_db)
):
    
    base_url = str(request.base_url)

    original_url = str(data.url)

    expires_at = datetime.now(timezone.utc) + timedelta(
        days=data.expires_in_days
    )

    # Check if URL already exists
    existing_url = db.query(URL).filter(
        URL.original_url == original_url
    ).first()

    if existing_url:

        return {
            "original_url": existing_url.original_url,
            "short_code": existing_url.short_code,
            "short_url": f"{base_url}{existing_url.short_code}",
            "expires_at": existing_url.expires_at
        }

    # Custom short code
    if data.custom_code:

        existing_code = db.query(URL).filter(
            URL.short_code == data.custom_code
        ).first()

        if existing_code:

            raise HTTPException(
                status_code=400,
                detail="Custom short code already exists"
            )

        short_code = data.custom_code

    else:

        short_code = generate_short_code(db)

    new_url = URL(
        original_url=original_url,
        short_code=short_code,
        expires_at=expires_at
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    return {
        "original_url": new_url.original_url,
        "short_code": new_url.short_code,
        "short_url": f"{base_url}{new_url.short_code}",
        "expires_at": new_url.expires_at
    }


# =====================================
# Get All URLs
# =====================================

@app.get(
    "/urls",
    summary="List All URLs",
    description="Returns paginated URLs.",
    response_model=List[URLListResponse],
    tags=["URLs"]
)
def get_urls(
    limit: int = Query(
        default=10,
        ge=1,
        le=100,
        description="Number of URLs to return"
    ),
    offset: int = Query(
        default=0,
        ge=0,
        description="Number of URLs to skip"
    ),
    db: Session = Depends(get_db)
):

    urls = (
        db.query(URL)
        .order_by(URL.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return urls


# =====================================
# URL Statistics
# =====================================

@app.get(
    "/stats/{short_code}",
    summary="Get URL Statistics",
    description="Returns click count and creation date for a short URL.",
    response_model=URLStatsResponse,
    tags=["URLs"],
    responses={
        404: {
            "description": "Short code not found"
        }
    }
)
def get_stats(
    short_code: str,
    db: Session = Depends(get_db)
):

    url = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if not url:

        raise HTTPException(
            status_code=404,
            detail="Short code not found"
        )

    status_text = "active"
    
    current_time = datetime.utcnow()
    
    if url.expires_at and current_time > url.expires_at:
        status_text = "expired"

    return {
        "original_url": url.original_url,
        "short_code": url.short_code,
        "clicks": url.clicks,
        "created_at": url.created_at,
        "expires_at": url.expires_at,
        "status": status_text
    }


# =====================================
# Search URLs
# =====================================

@app.get(
    "/search/{keyword}",
    summary="Search URLs",
    description="Search URLs by short code or original URL.",
    response_model=List[SearchResponse],
    tags=["URLs"]
)
def search_urls(
    keyword: str,
    db: Session = Depends(get_db)
):

    results = db.query(URL).filter(
        or_(
            URL.short_code.ilike(f"%{keyword}%"),
            URL.original_url.ilike(f"%{keyword}%")
        )
    ).all()

    return results


# =====================================
# Update Short Code
# =====================================

@app.put(
    "/update/{short_code}",
    summary="Update Short Code",
    description="Updates an existing short code with a new unique value.",
    response_model=UpdateResponse,
    tags=["URLs"],
    responses={
        400: {
            "description": "New short code already exists"
        },
        404: {
            "description": "Short code not found"
        }
    }
)
def update_short_code(
    short_code: str,
    data: UpdateCodeRequest,
    db: Session = Depends(get_db)
):

    url = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if not url:

        raise HTTPException(
            status_code=404,
            detail="Short code not found"
        )

    existing_code = db.query(URL).filter(
        URL.short_code == data.new_code
    ).first()

    if existing_code:

        raise HTTPException(
            status_code=400,
            detail="New short code already exists"
        )

    url.short_code = data.new_code

    db.commit()
    db.refresh(url)

    return {
        "message": "Short code updated successfully",
        "new_code": data.new_code
    }


# =====================================
# Delete URL
# =====================================

@app.delete(
    "/delete/{short_code}",
    summary="Delete URL",
    description="Deletes a shortened URL from the database.",
    response_model=DeleteResponse,
    tags=["URLs"],
    responses={
        404: {
            "description": "Short code not found"
        }
    }
)
def delete_url(
    short_code: str,
    db: Session = Depends(get_db)
):

    url = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if not url:

        raise HTTPException(
            status_code=404,
            detail="Short code not found"
        )

    db.delete(url)
    db.commit()

    return {
        "message": f"{short_code} deleted successfully"
    }


# =====================================
# Redirect URL
# =====================================

@app.get(
    "/{short_code}",
    summary="Redirect to Original URL",
    description="Redirects a short code to its original URL and increments the click counter.",
    tags=["URLs"]
)
def redirect_url(
    short_code: str,
    db: Session = Depends(get_db)
):

    url = db.query(URL).filter(
        URL.short_code == short_code
    ).first()

    if not url:

        raise HTTPException(
            status_code=404,
            detail="Short code not found"
        )

    current_time = datetime.utcnow()

    if (
        url.expires_at and
        current_time > url.expires_at
    ):

        raise HTTPException(
            status_code=410,
            detail="This URL has expired"
        )

    url.clicks += 1

    db.commit()

    return RedirectResponse(
        url=url.original_url,
        status_code=307
    )