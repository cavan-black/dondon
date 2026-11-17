"""In-app vocab reviews: the deck ladder and the scheduler.

DECKS are tiers of 1,500 words in frequency order — tier 1 is the most common 1,500
words, tier 2 the next 1,500, and so on — one JSON file per tier under decks/<lang>/,
written by tools/make_deck.py. New cards come from your current tier in rank order;
once every card in it has been introduced, new cards flow from the next tier. Reviews
of earlier tiers carry on forever, which is the point.

SCHEDULING is FSRS (the `fsrs` package, the same algorithm modern Anki uses), with
the two-button grading this app has always had: Again (FSRS Again) or Got it (Good).
"I know this" on a brand-new card answers Easy, which skips the learning steps and
shows it again in about a week, then further each time — for words you already have,
checked once more rather than taken on trust.

A card's whole FSRS state is one row in the database, written on every answer, so a
dropped connection costs at most the card on screen.
"""
import datetime, glob, json, os, re

import streamlit as st
from fsrs import Card, Rating, Scheduler

from . import db
from .store import ROOT

TIER_SIZE = 1500
DEFAULT_NEW_PER_DAY = 15
# A card due again within this window is shown again in the same session — the
# learning steps (1 and 10 minutes) are meant to be met before you put the phone down.
REQUEUE_WITHIN = datetime.timedelta(minutes=20)

SCHED = Scheduler()

AGAIN, GOOD, EASY = Rating.Again, Rating.Good, Rating.Easy


# ----------------------------------------------------------------------- decks

# Overridable so tests can point at fixture decks.
DECKS = os.environ.get("DONDON_DECKS") or os.path.join(ROOT, "decks")


def _deck_path(lang, tier):
    return os.path.join(DECKS, lang, f"tier{tier}.json")


def tiers(lang):
    """Tier numbers that exist for a language, ascending."""
    out = []
    for p in glob.glob(os.path.join(DECKS, lang, "tier*.json")):
        m = re.search(r"tier(\d+)\.json$", p)
        if m:
            out.append(int(m.group(1)))
    return sorted(out)


@st.cache_data
def deck(lang, tier):
    with open(_deck_path(lang, tier), encoding="utf-8") as fh:
        return json.load(fh)


def all_cards(lang):
    """{card_id: card} across every tier."""
    out = {}
    for t in tiers(lang):
        for c in deck(lang, t)["cards"]:
            out[c["id"]] = {**c, "tier": t}
    return out


# ----------------------------------------------------------------------- state

def _aware(dt):
    # SQLite hands datetimes back without a zone; everything here is UTC.
    return dt if dt.tzinfo else dt.replace(tzinfo=datetime.timezone.utc)


def rows(email, lang):
    cache = st.session_state.setdefault("srs_rows", {})
    if lang not in cache:
        cache[lang] = db.card_rows(email, lang)
    return cache[lang]


def start_tier(lang_settings, lang):
    """Where new cards come from: the chosen starting tier, or 1."""
    ts = tiers(lang)
    t = lang_settings.get("start_tier", ts[0] if ts else 1)
    return t if t in ts else (ts[0] if ts else 1)


def current_tier(email, lang, lang_settings):
    """The first tier, from the starting one up, that still has unintroduced cards."""
    seen = rows(email, lang)
    for t in tiers(lang):
        if t < start_tier(lang_settings, lang):
            continue
        if any(c["id"] not in seen for c in deck(lang, t)["cards"]):
            return t
    return None                                    # every card introduced


def tier_stats(email, lang, tier):
    seen = rows(email, lang)
    ids = [c["id"] for c in deck(lang, tier)["cards"]]
    started = [seen[i] for i in ids if i in seen]
    mature = sum(1 for r in started
                 if json.loads(r["fsrs"]).get("stability") and
                 json.loads(r["fsrs"])["stability"] >= 21)
    return {"total": len(ids), "introduced": len(started), "mature": mature}


def known_words(email, lang):
    """Words you've reviewed at least once — used to steer grammar drills and the
    tutor toward vocabulary you actually have."""
    cards_ = all_cards(lang)
    return {cards_[i]["word"] for i, r in rows(email, lang).items()
            if r["reps"] > 0 and i in cards_}


def queue(email, lang, lang_settings, new_today):
    """Today's session: everything due, then today's remaining new cards."""
    now = db.now()
    cards_ = all_cards(lang)
    seen = rows(email, lang)
    due = sorted((r for r in seen.values()
                  if _aware(r["due"]) <= now and r["card_id"] in cards_),
                 key=lambda r: _aware(r["due"]))
    # A card started from Reading has no answers yet: still new to you.
    out = [{"id": r["card_id"], "new": r["reps"] == 0} for r in due]

    limit = lang_settings.get("new_per_day", DEFAULT_NEW_PER_DAY)
    room = max(limit - new_today, 0)
    t = current_tier(email, lang, lang_settings)
    while room and t is not None:
        for c in deck(lang, t)["cards"]:
            if room == 0:
                break
            if c["id"] not in seen and not any(q["id"] == c["id"] for q in out):
                out.append({"id": c["id"], "new": True})
                room -= 1
        nxt = [x for x in tiers(lang) if x > t]
        t = nxt[0] if room and nxt else None
    return out


def answer(email, lang, card_id, rating, ms, today):
    """Schedule one answer and save it. Returns the card's next due time."""
    seen = rows(email, lang)
    row = seen.get(card_id)
    card = Card.from_dict(json.loads(row["fsrs"])) if row else Card()
    card, _ = SCHED.review_card(card, rating, review_datetime=db.now())
    tier = all_cards(lang)[card_id]["tier"]
    state = json.dumps(card.to_dict())
    reps = (row["reps"] if row else 0) + 1
    introduced = row["introduced"] if row else today
    db.put_card(email, lang, card_id, tier, card.due, reps, state, introduced)
    db.log_review(email, lang, card_id, int(rating), ms)
    seen[card_id] = {"card_id": card_id, "tier": tier, "due": card.due, "reps": reps,
                     "fsrs": state, "introduced": introduced}
    return card.due


def requeue(due):
    return _aware(due) - db.now() <= REQUEUE_WITHIN


# --------------------------------------------------------- words met elsewhere

def _bare(word):
    """Deck headwords carry articles for Spanish nouns ("la casa"); match without."""
    w = word.strip().lower()
    return re.sub(r"^(el|la|los|las|un|una)\s+", "", w)


@st.cache_data
def word_index(lang):
    """{headword: card_id} across every tier, for finding a word met while reading."""
    out = {}
    for t in tiers(lang):
        for c in deck(lang, t)["cards"]:
            out.setdefault(_bare(c["word"]), c["id"])
    return out


def find_card(lang, *forms):
    idx = word_index(lang)
    for f in forms:
        if f and _bare(f) in idx:
            return idx[_bare(f)]
    return None


def introduce(email, lang, card_id, today):
    """Start a card now, out of frequency order — for a word you looked up while
    reading. It joins today's reviews as a fresh card; nothing is answered for you."""
    seen = rows(email, lang)
    if card_id in seen:
        return False
    card = Card()
    tier = all_cards(lang)[card_id]["tier"]
    state = json.dumps(card.to_dict())
    db.put_card(email, lang, card_id, tier, card.due, 0, state, today)
    seen[card_id] = {"card_id": card_id, "tier": tier, "due": card.due, "reps": 0,
                     "fsrs": state, "introduced": today}
    return True
