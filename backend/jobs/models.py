import uuid
from sqlalchemy import Column, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from backend.database import Base


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String, nullable=False)

    engine = Column(String, nullable=False)  # e.g. "video"
    status = Column(String, nullable=False)  # queued | running | completed | failed

    input_type = Column(String, nullable=False)  # pdf | text | prompt
    config = Column(JSON, nullable=False)

    output_dir = Column(String, nullable=False)

    error_type = Column(String, nullable=True)  # system | user | null
    error_message = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )
