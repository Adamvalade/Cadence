"""Optional demo dataset: seeded users, albums, reviews, track ratings, likes, follows (idempotent)."""

from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import hash_password
from app.models.album import Album
from app.models.follow import Follow
from app.models.like import Like
from app.models.review import Review
from app.models.track import Track
from app.models.track_rating import TrackRating
from app.models.user import User

logger = logging.getLogger(__name__)


def _utc_naive_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)


_ALBUMS: tuple[tuple[str, str, str, int, str, str | None], ...] = (
    ("cadence-demo-001", "Random Access Memories", "Daft Punk", 2013, "https://picsum.photos/seed/cadence1/300/300", "Electronic"),
    ("cadence-demo-002", "To Pimp a Butterfly", "Kendrick Lamar", 2015, "https://picsum.photos/seed/cadence2/300/300", "Hip-Hop"),
    ("cadence-demo-003", "Midnights", "Taylor Swift", 2022, "https://picsum.photos/seed/cadence3/300/300", "Pop"),
    ("cadence-demo-004", "The Rise and Fall of a Midwest Princess", "Chappell Roan", 2023, "https://picsum.photos/seed/cadence4/300/300", "Pop"),
    ("cadence-demo-005", "Blonde", "Frank Ocean", 2016, "https://picsum.photos/seed/cadence5/300/300", "R&B"),
    ("cadence-demo-006", "The Miseducation of Lauryn Hill", "Lauryn Hill", 1998, "https://picsum.photos/seed/cadence6/300/300", "R&B"),
    ("cadence-demo-007", "AM", "Arctic Monkeys", 2013, "https://picsum.photos/seed/cadence7/300/300", "Rock"),
    ("cadence-demo-008", "Currents", "Tame Impala", 2015, "https://picsum.photos/seed/cadence8/300/300", "Psychedelic Pop"),
    ("cadence-demo-009", "Golden Hour", "Kacey Musgraves", 2018, "https://picsum.photos/seed/cadence9/300/300", "Country"),
    ("cadence-demo-010", "Ctrl", "SZA", 2017, "https://picsum.photos/seed/cadence10/300/300", "R&B"),
    ("cadence-demo-011", "Punisher", "Phoebe Bridgers", 2020, "https://picsum.photos/seed/cadence11/300/300", "Indie"),
    ("cadence-demo-012", "Melodrama", "Lorde", 2017, "https://picsum.photos/seed/cadence12/300/300", "Pop"),
    ("cadence-demo-013", "The ArchAndroid", "Janelle Monáe", 2010, "https://picsum.photos/seed/cadence13/300/300", "R&B"),
    ("cadence-demo-014", "In Rainbows", "Radiohead", 2007, "https://picsum.photos/seed/cadence14/300/300", "Alternative"),
    ("cadence-demo-015", "Flower Boy", "Tyler, The Creator", 2017, "https://picsum.photos/seed/cadence15/300/300", "Hip-Hop"),
    ("cadence-demo-016", "Hozier", "Hozier", 2014, "https://picsum.photos/seed/cadence16/300/300", "Folk Rock"),
    ("cadence-demo-017", "Visions", "Grimes", 2012, "https://picsum.photos/seed/cadence17/300/300", "Electronic"),
    ("cadence-demo-018", "The Low End Theory", "A Tribe Called Quest", 1991, "https://picsum.photos/seed/cadence18/300/300", "Hip-Hop"),
    ("cadence-demo-019", "Rumours", "Fleetwood Mac", 1977, "https://picsum.photos/seed/cadence19/300/300", "Rock"),
    ("cadence-demo-020", "Carrie & Lowell", "Sufjan Stevens", 2015, "https://picsum.photos/seed/cadence20/300/300", "Folk"),
)

# username, display_name, email, dicebear seed
_BOTS: tuple[tuple[str, str, str, str], ...] = (
    ("nina_vinyl", "Nina Park", "nina@bots.cadence.demo", "nina"),
    ("marcus_beats", "Marcus Cole", "marcus@bots.cadence.demo", "marcus"),
    ("sam_indie", "Sam Rivera", "sam@bots.cadence.demo", "sam"),
    ("alex_tapes", "Alex Kim", "alex@bots.cadence.demo", "alex"),
)

# username, album_sid, rating 1–10, body, days_ago
_REVIEWS: tuple[tuple[str, str, int, str, int], ...] = (
    ("nina_vinyl", "cadence-demo-001", 9, "Finally sat with this front to back—still feels futuristic.", 1),
    ("nina_vinyl", "cadence-demo-003", 7, "Perfect late-night listen. A few tracks are instant repeats.", 3),
    ("marcus_beats", "cadence-demo-002", 10, "Dense but rewarding. New detail every relisten.", 2),
    ("marcus_beats", "cadence-demo-005", 8, "Emotional and honest—hard to pick a favorite track.", 4),
    ("sam_indie", "cadence-demo-004", 10, "So much personality. Already queued for the next road trip.", 1),
    ("sam_indie", "cadence-demo-006", 6, "Timeless songwriting. Vocals are unreal.", 5),
    ("alex_tapes", "cadence-demo-001", 5, "Grooves for days. A couple of transitions blew my mind.", 2),
    ("alex_tapes", "cadence-demo-003", 9, "Catchy without feeling shallow—rare combo.", 6),
    ("nina_vinyl", "cadence-demo-005", 4, "Took me a few passes—now I get the hype.", 7),
    ("marcus_beats", "cadence-demo-006", 10, "Every song hits. Added the whole thing to my rotation.", 3),
    ("nina_vinyl", "cadence-demo-002", 3, "Respect the craft; not my everyday spin.", 12),
    ("marcus_beats", "cadence-demo-004", 8, "Hooks for days—played it three times the week I found it.", 9),
    ("sam_indie", "cadence-demo-001", 7, "The robots still sound warmer than most humans.", 11),
    ("alex_tapes", "cadence-demo-006", 9, "Classic for a reason—no filler.", 8),
)

_REVIEW_SNIPPETS_EXTRA = (
    "Front-loaded but the back half grew on me.",
    "Instant add-to-library energy.",
    "Skipped around at first—now I run it straight through.",
    "A couple of deep cuts I’ll defend in group chat.",
    "Not flawless, but the highs are ridiculous.",
    "Soundtracked a whole month for me.",
    "Would replay side A alone on a long drive.",
    "Quietly ambitious—rewards headphones.",
    "The one everyone recommends? They’re right.",
    "Took a week to click, then wouldn’t stop.",
    "Rough edges in a good way.",
    "Polished to a fault, but I’m not mad.",
    "Saved almost every other track.",
    "Perfect background until track 4 hits.",
)

_TRACK_OVERRIDES: dict[str, tuple[str, str, str, str]] = {
    "cadence-demo-001": ("Give Life Back to Music", "Giorgio by Moroder", "Instant Crush", "Contact"),
    "cadence-demo-002": ("Wesley’s Theory", "Alright", "The Blacker the Berry", "Mortal Man"),
    "cadence-demo-003": ("Lavender Haze", "Anti-Hero", "Karma", "Mastermind"),
    "cadence-demo-004": ("Femininomenon", "Red Wine Supernova", "Casual", "Pink Pony Club"),
    "cadence-demo-005": ("Nikes", "Ivy", "Self Control", "White Ferrari"),
    "cadence-demo-006": ("Lost Ones", "Doo Wop (That Thing)", "Everything Is Everything", "Tell Him"),
}


def _default_four_tracks(album_title: str, sid: str) -> tuple[str, str, str, str]:
    short = (album_title[:28] + "…") if len(album_title) > 28 else album_title
    h = sum(ord(c) for c in sid)
    packs = (
        (f"{short} — I", "The one with the hook", "Slow spiral", "Lights-out closer"),
        ("Cold open", "Side A peak", "Interlude I always wait for", "Final sprint"),
        ("First spin favorite", "Deep cut energy", "Bridge out of nowhere", "Fade worth sitting through"),
        ("Track I replayed", "Groove pocket", "Quiet storm middle", "Walk-home outro"),
    )
    return packs[h % len(packs)]


def _track_titles_for_album(sid: str, album_title: str) -> tuple[str, str, str, str]:
    if sid in _TRACK_OVERRIDES:
        return _TRACK_OVERRIDES[sid]
    return _default_four_tracks(album_title, sid)


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


async def _ensure_tracks_for_album(db: AsyncSession, album: Album) -> list[Track]:
    titles = _track_titles_for_album(album.spotify_id, album.title)
    out: list[Track] = []
    for i, title in enumerate(titles, start=1):
        spotify_tid = f"{album.spotify_id}-{i:02d}"
        r = await db.execute(
            select(Track).where(Track.album_id == album.id, Track.spotify_track_id == spotify_tid)
        )
        existing = r.scalar_one_or_none()
        if existing:
            out.append(existing)
            continue
        t = Track(
            album_id=album.id,
            spotify_track_id=spotify_tid,
            title=title,
            disc_number=1,
            track_number=i,
        )
        db.add(t)
        await db.flush()
        out.append(t)
    return out


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
    when = _utc_naive_now() - timedelta(days=days_ago)
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


async def _ensure_track_rating(db: AsyncSession, user_id: uuid.UUID, track_id: uuid.UUID, rating: int) -> None:
    r = await db.execute(
        select(TrackRating).where(TrackRating.user_id == user_id, TrackRating.track_id == track_id)
    )
    if r.scalar_one_or_none():
        return
    db.add(TrackRating(user_id=user_id, track_id=track_id, rating=rating))


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


async def _seed_cross_album_bot_reviews(
    db: AsyncSession,
    bots: dict[str, User],
    album_by_sid: dict[str, Album],
) -> None:
    extra_sids = tuple(s for s in album_by_sid if s >= "cadence-demo-007")
    rating_cycle = (10, 4, 8, 6, 9, 5, 7, 10, 3, 8, 6, 9, 7, 5, 10, 4, 8, 6)
    n = 0
    for sid in sorted(extra_sids):
        album = album_by_sid[sid]
        for bot in bots.values():
            await _get_or_create_review(
                db,
                bot.id,
                album.id,
                rating_cycle[n % len(rating_cycle)],
                _REVIEW_SNIPPETS_EXTRA[n % len(_REVIEW_SNIPPETS_EXTRA)],
                1 + (n % 26),
            )
            n += 1


async def _seed_bot_track_ratings(
    db: AsyncSession,
    bots: dict[str, User],
    album_by_sid: dict[str, Album],
) -> None:
    tracks_by_sid: dict[str, list[Track]] = {}
    for sid, album in album_by_sid.items():
        tracks_by_sid[sid] = await _ensure_tracks_for_album(db, album)

    rating_pattern = (10, 5, 8, 4, 9, 6, 10, 7, 3, 9, 8, 5, 10, 6, 7, 8, 4, 10, 6, 9)
    n = 0
    for username in bots:
        bot = bots[username]
        for sid in sorted(album_by_sid.keys()):
            tlist = tracks_by_sid.get(sid) or []
            if len(tlist) < 4:
                continue
            for ti in (0, 2):
                r = rating_pattern[n % len(rating_pattern)]
                n += 1
                await _ensure_track_rating(db, bot.id, tlist[ti].id, r)


async def seed_demo_public_dataset(db: AsyncSession) -> None:
    if not settings.demo_login_available:
        return

    album_by_sid: dict[str, Album] = {}
    for spec in _ALBUMS:
        a = await _get_or_create_album(db, spec)
        album_by_sid[spec[0]] = a

    for album in album_by_sid.values():
        await _ensure_tracks_for_album(db, album)

    bots: dict[str, User] = {}
    for username, display, email, seed in _BOTS:
        bots[username] = await _get_or_create_bot(db, username, display, email, seed)

    for username, sid, rating, body, days_ago in _REVIEWS:
        u = bots[username]
        album = album_by_sid[sid]
        await _get_or_create_review(db, u.id, album.id, rating, body, days_ago)

    await _seed_cross_album_bot_reviews(db, bots, album_by_sid)
    await _seed_bot_track_ratings(db, bots, album_by_sid)

    all_bot_ids = [u.id for u in bots.values()]
    if all_bot_ids:
        result = await db.execute(select(Review).where(Review.user_id.in_(all_bot_ids)))
        all_reviews = list(result.scalars().all())

        for i, rev in enumerate(all_reviews):
            liker = all_bot_ids[(i + 1) % len(all_bot_ids)]
            if liker != rev.user_id:
                await _ensure_like(db, liker, rev.id)
            liker2 = all_bot_ids[(i + 3) % len(all_bot_ids)]
            if liker2 != rev.user_id and liker2 != liker:
                await _ensure_like(db, liker2, rev.id)

    logger.info(
        "Demo public dataset ensured (bots=%s, albums=%s)",
        len(bots),
        len(album_by_sid),
    )


_DEMO_USER_ALBUM_REVIEWS: tuple[tuple[str, int, str, int], ...] = (
    ("cadence-demo-001", 8, "Daft Punk phase I didn’t expect to revisit this hard.", 2),
    ("cadence-demo-002", 10, "Still unpacking lines—saved half the album.", 4),
    ("cadence-demo-003", 7, "Trying Cadence—love how clean the feed is. This one’s been on repeat.", 1),
    ("cadence-demo-004", 9, "So much fun live-in-the-room energy on record.", 3),
    ("cadence-demo-005", 7, "Mood record—best when it’s late and quiet.", 5),
    ("cadence-demo-007", 6, "Scrappy and loud; three tracks on repeat.", 6),
    ("cadence-demo-008", 10, "Synth fog I can’t get enough of.", 7),
    ("cadence-demo-010", 9, "Vocals melt me every time.", 8),
    ("cadence-demo-012", 8, "Pop with teeth—lyrics hit harder than expected.", 9),
    ("cadence-demo-014", 9, "Weird and pretty in the same breath.", 10),
    ("cadence-demo-016", 5, "Gorgeous but samey in the middle for me.", 11),
    ("cadence-demo-018", 10, "Timeless bounce—added to every playlist.", 12),
    ("cadence-demo-020", 8, "Sparse and devastating; can’t rush it.", 13),
)

_DEMO_USER_TRACK_RATINGS: tuple[tuple[str, int, int], ...] = (
    ("cadence-demo-001", 1, 10),
    ("cadence-demo-001", 3, 9),
    ("cadence-demo-002", 2, 10),
    ("cadence-demo-003", 2, 7),
    ("cadence-demo-003", 4, 8),
    ("cadence-demo-004", 1, 9),
    ("cadence-demo-005", 3, 10),
    ("cadence-demo-006", 2, 9),
    ("cadence-demo-007", 1, 8),
    ("cadence-demo-008", 2, 10),
    ("cadence-demo-009", 3, 7),
    ("cadence-demo-010", 1, 9),
    ("cadence-demo-011", 4, 8),
    ("cadence-demo-012", 2, 9),
    ("cadence-demo-013", 1, 10),
    ("cadence-demo-014", 3, 6),
    ("cadence-demo-015", 2, 9),
    ("cadence-demo-016", 1, 7),
    ("cadence-demo-017", 2, 8),
    ("cadence-demo-018", 3, 10),
    ("cadence-demo-019", 2, 8),
    ("cadence-demo-020", 1, 9),
    ("cadence-demo-020", 4, 10),
)


async def personalize_demo_account(db: AsyncSession, demo_user: User) -> None:
    if not settings.demo_login_available:
        return

    if not settings.demo_seed_at_startup_enabled:
        await seed_demo_public_dataset(db)

    fc = await db.execute(select(func.count()).where(Follow.follower_id == demo_user.id))
    if (fc.scalar() or 0) >= len(_BOTS):
        logger.debug("Demo user already personalized (follows in place); skipping")
        return

    bot_users: list[User] = []
    for username, _, email, _ in _BOTS:
        r = await db.execute(select(User).where(User.email == email))
        u = r.scalar_one_or_none()
        if u:
            bot_users.append(u)

    for b in bot_users:
        await _ensure_follow(db, demo_user.id, b.id)

    album_by_sid: dict[str, Album] = {}
    r = await db.execute(select(Album).where(Album.spotify_id.startswith("cadence-demo-")))
    for al in r.scalars().all():
        album_by_sid[al.spotify_id] = al

    for sid, rating, body, days_ago in _DEMO_USER_ALBUM_REVIEWS:
        album = album_by_sid.get(sid)
        if not album:
            continue
        await _get_or_create_review(db, demo_user.id, album.id, rating, body, days_ago)

    for sid in album_by_sid:
        await _ensure_tracks_for_album(db, album_by_sid[sid])

    for sid, track_i, rating in _DEMO_USER_TRACK_RATINGS:
        album = album_by_sid.get(sid)
        if not album:
            continue
        spotify_tid = f"{sid}-{track_i:02d}"
        tr = await db.execute(
            select(Track).where(Track.album_id == album.id, Track.spotify_track_id == spotify_tid)
        )
        track = tr.scalar_one_or_none()
        if track:
            await _ensure_track_rating(db, demo_user.id, track.id, rating)

    bids = [b.id for b in bot_users]
    if bids:
        res = await db.execute(
            select(Review)
            .where(Review.user_id.in_(bids))
            .order_by(Review.created_at.desc())
            .limit(8)
        )
        for rev in res.scalars().all()[:5]:
            await _ensure_like(db, demo_user.id, rev.id)

    logger.info("Personalized demo account user_id=%s", demo_user.id)
