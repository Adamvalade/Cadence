import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class UserFeaturedTrack(Base):
    __tablename__ = "user_featured_tracks"
    __table_args__ = (UniqueConstraint("user_id", "slot", name="uq_user_featured_slot"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    slot: Mapped[int] = mapped_column(Integer)
    spotify_track_id: Mapped[str] = mapped_column(String(100))
    title: Mapped[str] = mapped_column(String(500))
    artist: Mapped[str] = mapped_column(String(300))
    album_title: Mapped[str | None] = mapped_column(String(300), nullable=True)
    cover_image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="featured_tracks", lazy="selectin")  # noqa: F821
