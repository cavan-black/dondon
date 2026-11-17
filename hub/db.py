"""Per-user storage, so progress follows you from phone to tablet to laptop.

Everything a learner does lives here, keyed by their sign-in email: settings, grammar
progress, and the state of every vocab card. The GitHub repo is public and holds only
code and the decks themselves — never anyone's data.

DATABASE_URL picks the database: a Postgres URL in production (any host works —
Neon and Supabase both have a free tier that's ample for a small group), and a local
SQLite file when it's unset, which is what development and the tests use. The schema
is plain SQLAlchemy Core with JSON kept as text, so the same code runs on both.
"""
import datetime, json, os

import sqlalchemy as sa
import streamlit as st

from .store import ROOT, secret

meta = sa.MetaData()

users = sa.Table(
    "users", meta,
    sa.Column("email", sa.String(320), primary_key=True),
    sa.Column("name", sa.String(200)),
    sa.Column("settings", sa.Text, nullable=False, default="{}"),
    sa.Column("created", sa.DateTime(timezone=True)),
)
invites = sa.Table(
    "invites", meta,
    sa.Column("email", sa.String(320), primary_key=True),
    sa.Column("invited_by", sa.String(320)),
    sa.Column("created", sa.DateTime(timezone=True)),
)
progress = sa.Table(
    "progress", meta,
    sa.Column("email", sa.String(320), primary_key=True),
    sa.Column("lang", sa.String(8), primary_key=True),
    sa.Column("data", sa.Text, nullable=False),
)
cards = sa.Table(
    "cards", meta,
    sa.Column("email", sa.String(320), primary_key=True),
    sa.Column("lang", sa.String(8), primary_key=True),
    sa.Column("card_id", sa.String(40), primary_key=True),
    sa.Column("tier", sa.Integer, nullable=False),
    sa.Column("due", sa.DateTime(timezone=True), nullable=False),
    sa.Column("reps", sa.Integer, nullable=False, default=0),
    sa.Column("fsrs", sa.Text, nullable=False),
    sa.Column("introduced", sa.Date, nullable=False),
    sa.Index("cards_due", "email", "lang", "due"),
)
reviews = sa.Table(
    "reviews", meta,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column("email", sa.String(320), nullable=False),
    sa.Column("lang", sa.String(8), nullable=False),
    sa.Column("card_id", sa.String(40), nullable=False),
    sa.Column("rating", sa.Integer, nullable=False),
    sa.Column("ms", sa.Integer),
    sa.Column("at", sa.DateTime(timezone=True), nullable=False),
)
# Reading passages, shared by everyone on the same language and level: one learner
# generating a passage stocks the library for the rest. Adapted Wikipedia text is
# CC BY-SA, credited via source_title/source_url. Text people paste in is never stored.
passages = sa.Table(
    "passages", meta,
    sa.Column("id", sa.String(40), primary_key=True),
    sa.Column("lang", sa.String(8), nullable=False),
    sa.Column("level", sa.Integer, nullable=False),
    sa.Column("topic", sa.String(80)),
    sa.Column("title", sa.String(300)),
    sa.Column("source_title", sa.String(300)),
    sa.Column("source_url", sa.String(600)),
    sa.Column("data", sa.Text, nullable=False),
    sa.Column("created_by", sa.String(320)),
    sa.Column("created", sa.DateTime(timezone=True), nullable=False),
    sa.Index("passages_level", "lang", "level"),
)


@st.cache_resource
def engine(url=None):
    url = url or secret("DATABASE_URL") or \
        "sqlite:///" + os.path.join(ROOT, ".local.db").replace("\\", "/")
    # Hosted Postgres URLs are often written postgres://; SQLAlchemy wants a driver.
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    eng = sa.create_engine(url, pool_pre_ping=True)
    meta.create_all(eng)
    return eng


def _upsert(table, row, keys):
    eng = engine()
    if eng.dialect.name == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    else:
        from sqlalchemy.dialects.sqlite import insert
    stmt = insert(table).values(**row)
    stmt = stmt.on_conflict_do_update(index_elements=keys,
                                      set_={k: v for k, v in row.items() if k not in keys})
    with eng.begin() as c:
        c.execute(stmt)


def now():
    return datetime.datetime.now(datetime.timezone.utc)


# ---------------------------------------------------------------------- people

def ensure_user(email, name):
    with engine().begin() as c:
        row = c.execute(sa.select(users).where(users.c.email == email)).first()
        if row is None:
            c.execute(users.insert().values(email=email, name=name, settings="{}",
                                            created=now()))


def get_settings(email):
    with engine().connect() as c:
        row = c.execute(sa.select(users.c.settings).where(users.c.email == email)).first()
    return json.loads(row[0]) if row else {}


def put_settings(email, settings):
    with engine().begin() as c:
        c.execute(users.update().where(users.c.email == email)
                  .values(settings=json.dumps(settings)))


def is_invited(email):
    with engine().connect() as c:
        return c.execute(sa.select(invites.c.email)
                         .where(invites.c.email == email.lower())).first() is not None


def invite(email, by):
    _upsert(invites, {"email": email.strip().lower(), "invited_by": by,
                      "created": now()}, ["email"])


def uninvite(email):
    with engine().begin() as c:
        c.execute(invites.delete().where(invites.c.email == email))


def invited():
    with engine().connect() as c:
        return [r[0] for r in c.execute(sa.select(invites.c.email).order_by(invites.c.email))]


# -------------------------------------------------------------------- progress

def get_progress(email, lang):
    with engine().connect() as c:
        row = c.execute(sa.select(progress.c.data).where(
            (progress.c.email == email) & (progress.c.lang == lang))).first()
    return json.loads(row[0]) if row else {}


def put_progress(email, lang, data):
    _upsert(progress, {"email": email, "lang": lang, "data": json.dumps(data)},
            ["email", "lang"])


# ----------------------------------------------------------------------- cards

def card_rows(email, lang):
    """Every card this learner has started, as {card_id: row}."""
    with engine().connect() as c:
        rows = c.execute(sa.select(cards).where(
            (cards.c.email == email) & (cards.c.lang == lang))).mappings().all()
    return {r["card_id"]: dict(r) for r in rows}


def put_card(email, lang, card_id, tier, due, reps, fsrs_json, introduced):
    _upsert(cards, {"email": email, "lang": lang, "card_id": card_id, "tier": tier,
                    "due": due, "reps": reps, "fsrs": fsrs_json,
                    "introduced": introduced}, ["email", "lang", "card_id"])


def log_review(email, lang, card_id, rating, ms):
    with engine().begin() as c:
        c.execute(reviews.insert().values(email=email, lang=lang, card_id=card_id,
                                          rating=rating, ms=ms, at=now()))


# -------------------------------------------------------------------- passages

def put_passage(row):
    with engine().begin() as c:
        c.execute(passages.insert().values(**row, created=now()))


def library(lang, level, limit=60):
    """Newest first, without the (large) passage bodies."""
    cols = [passages.c[k] for k in ("id", "level", "topic", "title", "source_title",
                                    "created")]
    with engine().connect() as c:
        rows = c.execute(sa.select(*cols).where(
            (passages.c.lang == lang) & (passages.c.level == level))
            .order_by(passages.c.created.desc()).limit(limit)).mappings().all()
    return [dict(r) for r in rows]


def get_passage(pid):
    with engine().connect() as c:
        row = c.execute(sa.select(passages).where(passages.c.id == pid)).mappings().first()
    return dict(row) if row else None


def review_summary(email, lang, since=None):
    """(answers, answers that weren't Again) — all of them, or those since `since`."""
    passed = sa.func.sum(sa.case((reviews.c.rating > 1, 1), else_=0))
    where = (reviews.c.email == email) & (reviews.c.lang == lang)
    if since is not None:
        where &= reviews.c.at >= since
    with engine().connect() as c:
        n, ok = c.execute(sa.select(sa.func.count(), passed).where(where)).one()
    return n, int(ok or 0)
