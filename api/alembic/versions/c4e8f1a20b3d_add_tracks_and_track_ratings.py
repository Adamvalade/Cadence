"""add tracks and track_ratings

Revision ID: c4e8f1a20b3d
Revises: ab35e8d933c3
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c4e8f1a20b3d"
down_revision: Union[str, None] = "ab35e8d933c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tracks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("album_id", sa.UUID(), nullable=False),
        sa.Column("spotify_track_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("disc_number", sa.Integer(), nullable=False),
        sa.Column("track_number", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["album_id"], ["albums.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("album_id", "spotify_track_id", name="uq_tracks_album_spotify_track"),
    )
    op.create_index(op.f("ix_tracks_album_id"), "tracks", ["album_id"], unique=False)
    op.create_index(op.f("ix_tracks_spotify_track_id"), "tracks", ["spotify_track_id"], unique=False)

    op.create_table(
        "track_ratings",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("track_id", sa.UUID(), nullable=False),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["track_id"], ["tracks.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "track_id", name="uq_track_ratings_user_track"),
    )
    op.create_index(op.f("ix_track_ratings_track_id"), "track_ratings", ["track_id"], unique=False)
    op.create_index(op.f("ix_track_ratings_user_id"), "track_ratings", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_track_ratings_user_id"), table_name="track_ratings")
    op.drop_index(op.f("ix_track_ratings_track_id"), table_name="track_ratings")
    op.drop_table("track_ratings")
    op.drop_index(op.f("ix_tracks_spotify_track_id"), table_name="tracks")
    op.drop_index(op.f("ix_tracks_album_id"), table_name="tracks")
    op.drop_table("tracks")
