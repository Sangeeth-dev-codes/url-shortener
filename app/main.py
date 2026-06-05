import random
import string

from typing import List

from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)

from fastapi.responses import RedirectResponse

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import engine, get_db
from app.models import URL

from app.schemas import (
    URLResponse,
    URLStatsResponse,
    DeleteResponse,
    URLCreate,
    UpdateCodeRequest,
    SearchResponse
)

app = FastAPI(
    title="URL Shortener API",
    version="1.0.0",
    description="A URL Shortener built with FastAPI and SQLAlchemy"
)

URL.metadata.create_all(bind=engine)


# =====================================
# Helper Function
# =====================================

def generate_short_code(db: Session):

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

@app.get("/")
def home():

    return {
        "message": "Welcome to URL Shortener API"
    }


# =====================================
# Create Short URL
# =====================================

@app.post(
    "/shorten",
    response_model=URLResponse,
    status_code=status.HTTP_201_CREATED
)
def shorten_url(
    data: URLCreate,
    db: Session = Depends(get_db)
):

    original_url = str(data.url)

    # Check if URL already exists
    existing_url = db.query(URL).filter(
        URL.original_url == original_url
    ).first()

    if existing_url:

        return {
            "original_url": existing_url.original_url,
            "short_code": existing_url.short_code,
            "short_url": (
                f"http://127.0.0.1:8000/"
                f"{existing_url.short_code}"
            )
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
        short_code=short_code
    )

    db.add(new_url)
    db.commit()
    db.refresh(new_url)

    return {
        "original_url": new_url.original_url,
        "short_code": new_url.short_code,
        "short_url": (
            f"http://127.0.0.1:8000/"
            f"{new_url.short_code}"
        )
    }


# =====================================
# Get All URLs
# =====================================

@app.get("/urls")
def get_urls(
    db: Session = Depends(get_db)
):

    urls = db.query(URL).all()

    return urls


# =====================================
# URL Statistics
# =====================================

@app.get(
    "/stats/{short_code}",
    response_model=URLStatsResponse
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

    return url


# =====================================
# Search URLs
# =====================================

@app.get(
    "/search/{keyword}",
    response_model=List[SearchResponse]
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

@app.put("/update/{short_code}")
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
    response_model=DeleteResponse
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

@app.get("/{short_code}")
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

    url.clicks += 1

    db.commit()

    return RedirectResponse(
        url=url.original_url,
        status_code=307
    )