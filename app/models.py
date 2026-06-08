from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime, timezone

from app.database import Base


class URL(Base):
    __tablename__ = "urls"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    original_url = Column(
        String,
        index=True,
        nullable=False
    )

    short_code = Column(
        String,
        unique=True,
        index=True,
        nullable=False
    )

    clicks = Column(
        Integer,
        default=0
    )

    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc)
    )

    expires_at = Column(
        DateTime(timezone=True),
        nullable=True
    )