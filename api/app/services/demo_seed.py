"""
Idempotent demo dataset: fake users, albums, reviews, likes, and follows for recruiter demos.
Runs at API startup when demo login is configured; extends graph when the demo account logs in.
"""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.album import Album
from app.models.follow import Follow
from app.models.like import Like
from app.models.review import Review
from app.models.user import User

logger = logging.getLogger(__name__)

# Synthetic Spotify IDs — never collide with real imports if you use the same prefix consistently.
_ALBUMS: tuple[tuple[str, str, str, int, str, str | None], ...] = (
    ("cadence-demo-001", "Random Access Memories", "Daft Punk", 2013, "https://picsum.photos/seed/cadence1/300/300", "Electronic"),
    ("cadence-demo-002", "To Pimp a Butterfly", "Kendrick Lamar", 2015, "https://picsum.photos/seed/cadence2/300/300", "Hip-Hop"),
    ("cadence-demo-003", "Midnights", "Taylor Swift", 2022, "https://picsum.photos/seed/cadence3/300/300", "Pop"),
    ("cadence-demo-004", "The Rise and Fall of a Midwest Princess", "Chappell Roan", 2023, "https://picsum.photos/seed/cadence4/300/300", "Pop"),
    ("cadence-demo-005", "Blonde", "Frank Ocean", 2016, "https://picsum.photos/seed/cadence5/300/300", "R&B"),
    ("cadence-demo-006", "The Miseducation of Lauryn Hill", "Lauryn Hill", 1998, "https://picsum.photos/seed/cadence6/300/300", "R&B"),
)

# username, display_name, email, dicebear seed
_BOTS: tuple[tuple[str, str, str, str], ...] = (
    ("nina_vinyl", "Nina Park", "nina@bots.cadence.demo", "nina"),
    ("marcus_beats", "Marcus Cole", "marcus@bots.cadence.demo", "marcus"),
    ("sam_indie", "Sam Rivera", "sam@bots.cadence.demo", "sam"),
    ("alex_tapes", "Alex Kim", "alex@bots.cadence.demo", "alex"),
)

# username, album spotify_id, rating, body, days_ago
_REVIEWS: tuple[tuple[str, str, int, str, int], ...] = (
    ("nina_vinyl", "cadence-demo-001", 5, "Finally sat with this front to back—still feels futuristic.", 1),
    ("nina_vinyl", "cadence-demo-003", 4, "Perfect late-night listen. A few tracks are instant repeats.", 3),
    ("marcus_beats", "cadence-demo-002", 5, "Dense but rewarding. New detail every relisten.", 2),
    ("marcus_beats", "cadence-demo-005", 5, "Emotional and honest—hard to pick a favorite track.", 4),
    ("sam_indie", "cadence-demo-004", 5, "So much personality. Already queued for the next road trip.", 1),
    ("sam_indie", "cadence-demo-006", 4, "Timeless songwriting. Vocals are unreal.", 5),
    ("alex_tapes", "cadence-demo-001", 4, "Grooves for days. A couple of transitions blew my mind.", 2),
    ("alex_tapes", "cadence-demo-003", 5, "Catchy without feeling shallow—rare combo.", 6),
    ("nina_vinyl", "cadence-demo-005", 4, "Took me a few passes—now I get the hype.", 7),
    ("marcus_beats", "cadence-demo-006", 5, "Every song hits. Added the whole thing to my rotation.", 3),
)


async def _get_or_create_album(db: AsyncSession, spec: tuple[str, str, str, int, str, str | None]) -> Album:
    sid, title, artist, year, cover, genre = spec
    r = await db.execute(select(Album).where(Album.spotify_id == sid))
    existing = r.scalar_one_or_none()
    if existing:
        return existing
    a = Album(
        spotify_id=sid,
        title=title,
        artist=artist,
        release_year=year,
        cover_image_url=cover,
        genre=genre,
    )
    db.add(a)
    await db.flush()
    return a


async def _get_or_create_bot(db: AsyncSession, username: str, display_name: str, email: str, seed: str) -> User:
    r = await db.execute(select(User).where(User.email == email))
    existing = r.scalar_one_or_none()
    if existing:
        return existing
    u = User(
        email=email,
        username=username,
        password_hash=hash_password(secrets.token_urlsafe(24)),
        display_name=display_name,
        avatar_url=f"https://api.dicebear.com/7.x/notionists/svg?seed={seed}",
        bio="Demo listener on Cadence—here to share picks.",
    )
    db.add(u)
    await db.flush()
    return u


async def _get_or_create_review(
    db: AsyncSession,
    user_id: uuid.UUID,
    album_id: uuid.UUID,
    rating: int,
    body: str,
    days_ago: int,
) -> Review | None:
    r = await db.execute(select(Review).where(Review.user_id == user_id, Review.album_id == album_id))
    if r.scalar_one_or_none():
        return None
    when = datetime.now(timezone.utc) - timedelta(days=days_ago)
    rev = Review(
        user_id=user_id,
        album_id=album_id,
        rating=rating,
        body=body,
        is_relisten=False,
        created_at=when,
        updated_at=when,
    )
    db.add(rev)
    await db.flush()
    return rev


async def _ensure_like(db: AsyncSession, user_id: uuid.UUID, review_id: uuid.UUID) -> None:
    r = await db.execute(select(Like).where(Like.user_id == user_id, Like.review_id == review_id))
    if r.scalar_one_or_none():
        return
    db.add(Like(user_id=user_id, review_id=review_id))


async def _ensure_follow(db: AsyncSession, follower_id: uuid.UUID, following_id: uuid.UUID) -> None:
    if follower_id == following_id:
        return
    r = await db.execute(
        select(Follow).where(Follow.follower_id == follower_id, Follow.following_id == following_id)
    )
    if r.scalar_one_or_none():
        return
    db.add(Follow(follower_id=follower_id, following_id=following_id))


async def seed_demo_public_dataset(db: AsyncSession) -> None:
    """Bots, albums, reviews, and cross-likes so Discover / Social tabs look alive before anyone logs in."""
    if not settings.demo_login_available:
        return

    album_by_sid: dict[str, Album] = {}
    for spec in _ALBUMS:
        a = await _get_or_create_album(db, spec)
        album_by_sid[spec[0]] = a

    bots: dict[str, User] = {}
    for username, display, email, seed in _BOTS:
        bots[username] = await _get_or_create_bot(db, username, display, email, seed)

    for username, sid, rating, body, days_ago in _REVIEWS:
        u = bots[username]
        album = album_by_sid[sid]
        await _get_or_create_review(db, u.id, album.id, rating, body, days_ago)

    # Refresh reviews list (include pre-existing)
    all_bot_ids = [u.id for u in bots.values()]
    if all_bot_ids:
        result = await db.execute(select(Review).where(Review.user_id.in_(all_bot_ids)))
        all_reviews = list(result.scalars().all())

        # Spread likes across bot reviews for “popular” tab
        for i, rev in enumerate(all_reviews[:12]):
            liker = all_bot_ids[(i + 1) % len(all_bot_ids)]
            if liker != rev.user_id:
                await _ensure_like(db, liker, rev.id)
            liker2 = all_bot_ids[(i + 3) % len(all_bot_ids)]
            if liker2 != rev.user_id and liker2 != liker:
                await _ensure_like(db, liker2, rev.id)

    logger.info("Demo public dataset ensured (bots=%s, albums=%s)", len(bots), len(album_by_sid))


async def personalize_demo_account(db: AsyncSession, demo_user: User) -> None:
    """Follow bot friends, add one review, like a couple of posts so /feed and profile feel real."""
    if not settings.demo_login_available:
        return

    await seed_demo_public_dataset(db)

    bot_users: list[User] = []
    for username, _, email, _ in _BOTS:
        r = await db.execute(select(User).where(User.email == email))
        u = r.scalar_one_or_none()
        if u:
            bot_users.append(u)

    for b in bot_users:
        await _ensure_follow(db, demo_user.id, b.id)

    # One starter review from the demo user (unique per user+album)
    ar = await db.execute(select(Album).where(Album.spotify_id == "cadence-demo-003"))
    album = ar.scalar_one_or_none()
    if album:
        r = await db.execute(select(Review).where(Review.user_id == demo_user.id, Review.album_id == album.id))
        if not r.scalar_one_or_none():
            when = datetime.now(timezone.utc) - timedelta(hours=6)
            db.add(
                Review(
                    user_id=demo_user.id,
                    album_id=album.id,
                    rating=5,
                    body="Trying Cadence—love how clean the feed is. This album’s been on repeat.",
                    is_relisten=False,
                    created_at=when,
                    updated_at=when,
                )
            )
            await db.flush()

    # Likes from demo user on two bot reviews
    bids = [b.id for b in bot_users]
    if bids:
        res = await db.execute(
            select(Review)
            .where(Review.user_id.in_(bids))
            .order_by(Review.created_at.desc())
            .limit(4)
        )
        for rev in res.scalars().all()[:2]:
            await _ensure_like(db, demo_user.id, rev.id)

    logger.info("Personalized demo account user_id=%s", demo_user.id)
