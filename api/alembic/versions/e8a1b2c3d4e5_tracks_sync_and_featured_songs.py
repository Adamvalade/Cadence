"""tracks_synced_at on albums + user_featured_tracks

Revision ID: e8a1b2c3d4e5
Revises: c4e8f1a20b3d
Create Date: 2026-03-24

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e8a1b2c3d4e5"
down_revision: Union[str, None] = "c4e8f1a20b3d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "albums",
        sa.Column("tracks_synced_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        "user_featured_tracks",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("slot", sa.Integer(), nullable=False),
        sa.Column("spotify_track_id", sa.String(length=100), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("artist", sa.String(length=300), nullable=False),
        sa.Column("album_title", sa.String(length=300), nullable=True),
        sa.Column("cover_image_url", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "slot", name="uq_user_featured_slot"),
    )
    op.create_index(op.f("ix_user_featured_tracks_user_id"), "user_featured_tracks", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_user_featured_tracks_user_id"), table_name="user_featured_tracks")
    op.drop_table("user_featured_tracks")
    op.drop_column("albums", "tracks_synced_at")
