import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class TrackRating(Base):
    __tablename__ = "track_ratings"
    __table_args__ = (UniqueConstraint("user_id", "track_id", name="uq_track_ratings_user_track"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    track_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("tracks.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    user: Mapped["User"] = relationship(back_populates="track_ratings", lazy="selectin")  # noqa: F821
    track: Mapped["Track"] = relationship(back_populates="ratings", lazy="selectin")  # noqa: F821
