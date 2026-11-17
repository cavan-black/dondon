"""The placement test: one short sitting that finds where a new learner stands, so
nobody starts at あいうえお who can already hold a conversation.

It has three parts, each stopping as soon as it finds the ceiling:

  SCRIPT    a dozen items from across the Basics course (kana to type, or Spanish
            words to write down from dictation). 90% skips Basics. For Japanese,
            under half ends the test there: without kana the rest can't be read.
  VOCAB     the decks in bands of 500 words, most common first. Five words a band,
            each with four meanings to pick from and "I don't know". A band's score
            is corrected for guessing, and the test moves on until two bands in a
            row come out mostly unknown. Needs the decks; skipped without them.
  GRAMMAR   the grammar track stage by stage, four to six drills a stage, the same
            drills as the Grammar page. A stage passes at 75%; the first stage that
            doesn't ends the test.

What it changes, all of it only ever upwards (a retake never takes anything away):

  - Basics is marked skipped.
  - Every skill in a passed stage goes to box 3, as if tested out on the Grammar
    page: due again in a week, so the schedule checks the placement rather than
    trusting it. They're flagged "placed" so the forecast doesn't count them as
    pace.
  - New vocab starts at the first band of 500 that isn't mostly known, even part
    way into a tier.
  - progress["placement"] remembers the estimate of words known that the decks
    don't record (see stats.placement_words), so the level holds from day one.

Pure functions only; views/placement.py drives it.
"""
import datetime, math, random

from . import basics as B
from .grammar import INTERVALS, LEARNED_BOX

SCRIPT_ITEMS = 12
SCRIPT_PASS = 0.9
SCRIPT_FLOOR = 0.5          # Japanese: below this, the rest of the test is unreadable
BAND = 500
PER_BAND = 5
CHOICES = 4
KNOWN_BAND = 0.85           # a band this well known counts as done for start_tier
STOP_BAND = 0.3             # two bands in a row below this ends the vocab part
STAGE_MIN, STAGE_MAX = 4, 6
STAGE_PASS = 0.75
PLACED_BOX = 3


# ---------------------------------------------------------------------- script

def script_items(code, rng=None, n=SCRIPT_ITEMS):
    """One item from each of `n` units spread evenly across the course, easiest to
    hardest. Typed where the unit can be typed, dictated otherwise."""
    rng = rng or random.Random()
    us = B.units(code)
    picks = [us[round(i * (len(us) - 1) / max(n - 1, 1))] for i in range(min(n, len(us)))]
    out = []
    for u in picks:
        mode = "type" if "type" in u.modes else "dictate"
        out.append(B._drill(code, u, rng.choice(u.items), mode, [], rng))
    return out


# ----------------------------------------------------------------------- vocab

def bands(deck_cards):
    """[(tier, [cards])] in rank order, BAND cards each. `deck_cards` is
    [(tier, cards)] with each tier's cards already in rank order."""
    out = []
    for tier, cards in deck_cards:
        for i in range(0, len(cards), BAND):
            out.append((tier, cards[i:i + BAND]))
    return out


def vocab_items(cards, rng=None, k=PER_BAND):
    """`k` words from a band, each with its meaning and CHOICES - 1 others from the
    same band, so the wrong answers are as common as the right one."""
    rng = rng or random.Random()
    chosen = rng.sample(cards, min(k, len(cards)))
    out = []
    for c in chosen:
        others = list({x["meaning"] for x in cards
                       if x["meaning"] != c["meaning"] and x["id"] != c["id"]})
        options = rng.sample(others, min(CHOICES - 1, len(others))) + [c["meaning"]]
        rng.shuffle(options)
        out.append({"id": c["id"], "word": c["word"], "reading": c.get("reading", ""),
                    "options": options, "answer": c["meaning"]})
    return out


def band_known(right, n, choices=CHOICES):
    """The share of a band known, from `right` of `n`, less what guessing explains."""
    if not n:
        return 0.0
    chance = 1 / choices
    return max((right / n - chance) / (1 - chance), 0.0)


def vocab_done(scores):
    """Stop once two bands in a row are mostly unknown."""
    return len(scores) >= 2 and all(s < STOP_BAND for s in scores[-2:])


def start_point(tier_sizes, band_scores):
    """Where new cards should start: (tier, index of the first card). Bands are
    walked in rank order and every band mostly known from the top is passed over;
    the first that isn't, or the first untested one, is where new cards begin.
    `tier_sizes` is {tier: cards} in tier order; `band_scores` is [(tier, known)]
    for the bands tested, in order."""
    tested = {}
    for tier, known in band_scores:
        tested.setdefault(tier, []).append(known)
    last = None
    for t, size in tier_sizes.items():
        lead = 0
        for known in tested.get(t, []):
            if known < KNOWN_BAND:
                break
            lead += 1
        skip = min(lead * BAND, size)
        if skip < size:
            return t, skip
        last = (t, skip)
    return last


# --------------------------------------------------------------------- grammar

def stage_items(track, stage, words, known, rng=None):
    """Four to six drills on a stage's skills: each skill at least once (a sample of
    them if there are more than six), then repeats up to four."""
    rng = rng or random.Random()
    skills = [s for s in track.skills if s.stage == stage]
    picked = rng.sample(skills, STAGE_MAX) if len(skills) > STAGE_MAX else list(skills)
    while len(picked) < STAGE_MIN:
        picked.append(rng.choice(skills))
    items = [track.item(s, words, known) for s in picked]
    rng.shuffle(items)
    return items


def stage_passed(marks):
    return bool(marks) and sum(marks) >= math.ceil(STAGE_PASS * len(marks))


# ----------------------------------------------------------------------- apply

def apply(code, track, progress, lang_settings, result, today, card_rows=(), tier_sizes=None):
    """Fold a finished test into the learner's state. `result` holds "script" (a
    score or None), "bands" ([(tier, size, known)]) and "stages" (passed stage
    numbers). Returns the placement record it saved."""
    # Basics
    if result.get("script") is not None and result["script"] >= SCRIPT_PASS:
        B.skip(code, progress)

    # Grammar: passed stages to box 3, never lower.
    due = (today + datetime.timedelta(days=INTERVALS[PLACED_BOX])).isoformat()
    for s in track.skills:
        if s.stage in result.get("stages", ()):
            st = progress["skills"].setdefault(s.key, {})
            if st.get("box", 0) < PLACED_BOX:
                st.update(box=PLACED_BOX, due=due, placed=True)
                st.setdefault("introduced", today.isoformat())

    # Vocab: where new cards start, and the words known that cards won't show.
    placed = {"date": today.isoformat(), "script": result.get("script"),
              "stages": sorted(result.get("stages", ())), "words_skipped": 0,
              "words_other": 0, "start_tier": None}
    bs = result.get("bands", [])
    if tier_sizes and bs:
        tiers = list(tier_sizes)
        t, i = start_point(tier_sizes, [(tier, known) for tier, _, known in bs])
        here = (lang_settings.get("start_tier", tiers[0]), lang_settings.get("start_index", 0))
        if (t, i) > here:
            lang_settings["start_tier"], lang_settings["start_index"] = t, i
        t, i = lang_settings.get("start_tier", tiers[0]), lang_settings.get("start_index", 0)
        started = {}
        for r in card_rows:
            if r["reps"] > 0:
                started[r["tier"]] = started.get(r["tier"], 0) + 1
        # Bands before the start point won't come up as new cards; the rest will.
        below = above = 0
        pos = {}
        for tier, size, known in bs:
            at = pos.get(tier, 0)
            pos[tier] = at + size
            if tier < t or (tier == t and at < i):
                below += round(size * known)
            else:
                above += round(size * known)
        # Words already reviewed here are counted by the cards; don't count them twice.
        placed["words_skipped"] = max(below - sum(n for k, n in started.items() if k <= t), 0)
        placed["words_other"] = max(above - sum(n for k, n in started.items() if k > t), 0)
        placed["start_tier"], placed["start_index"] = t, i
    progress["placement"] = placed
    return placed


def skip(progress, today):
    """Start from the beginning without taking the test."""
    progress["placement"] = {"date": today.isoformat(), "skipped": True}
