import uuid
from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Track(Base):
    __tablename__ = "tracks"
    __table_args__ = (UniqueConstraint("album_id", "spotify_track_id", name="uq_tracks_album_spotify_track"),)

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    album_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("albums.id", ondelete="CASCADE"), index=True)
    spotify_track_id: Mapped[str] = mapped_column(String(100), index=True)
    title: Mapped[str] = mapped_column(String(500))
    disc_number: Mapped[int] = mapped_column(Integer, default=1)
    track_number: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    album: Mapped["Album"] = relationship(back_populates="tracks", lazy="selectin")  # noqa: F821
    ratings: Mapped[list["TrackRating"]] = relationship(back_populates="track", lazy="selectin")  # noqa: F821
