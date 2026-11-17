"""Where a learner stands and how fast they're moving, worked out from what the app
already records: the day log, the grammar boxes and the vocab cards.

THE PATH is six levels, the same six the Reading page writes for (hub/tutor.py
LEVELS, and the same word counts as tutor.level_for). A level asks for two things:
enough words, and enough of the grammar track. You hold the highest level whose both
halves you've met, so the page can always say which half is holding you back.

PACE is measured, not assumed: words started and skills learned over the last two
weeks. A FORECAST is a pace carried forward to every level still ahead — yours as
measured, or one you choose on the Progress page to see what it would buy. A level
arrives when the slower of its two halves does, and there is no date for a half
with no pace.

Everything here is a pure function of plain data — no Streamlit, no database — so
the pages stay thin and the arithmetic can be tested.
"""
import datetime, json, math
from dataclasses import dataclass

ACTIVITIES = ("vocab", "grammar", "read", "build", "speak", "talk")
LABELS = {"vocab": "Vocabulary", "grammar": "Grammar", "read": "Read", "build": "Build",
          "speak": "Speak", "talk": "Talk"}
# A day's target for each kind of practice. Vocab has none: its target is whatever
# the scheduler says is due.
TARGETS = {"grammar": 20, "read": 1, "build": 5, "speak": 8, "talk": 10}
UNITS = {"vocab": "reviews", "grammar": "drills", "read": "passages",
         "build": "sentences", "speak": "sentences", "talk": "turns"}

PACE_WINDOW = 14            # days of history a pace is measured over
MATURE_DAYS = 21            # FSRS stability at which a card counts as mature


@dataclass(frozen=True)
class Level:
    n: int
    name: str
    words: int              # words known to hold this level
    grammar: float          # share of the grammar stages finished
    can: str                # what it lets you do


LEVELS = (
    Level(1, "First steps", 0, 0.0, "Read the script and sound out words"),
    Level(2, "Beginner", 150, 0.10, "Greetings and simple polite sentences"),
    Level(3, "Elementary", 500, 0.30, "Everyday topics in short sentences"),
    Level(4, "Intermediate", 1200, 0.55, "Hold a simple conversation"),
    Level(5, "Upper intermediate", 2500, 0.80, "Talk through most everyday things"),
    Level(6, "Advanced", 4500, 1.0, "Follow near-native reading and speech"),
)
CONVERSATIONAL = 4          # the level the whole routine is aiming at first


def stages_needed(level, n_stages):
    return round(level.grammar * n_stages)


def _span(have, lo, hi):
    return 1.0 if hi <= lo else min(max((have - lo) / (hi - lo), 0.0), 1.0)


def standing(words, stages_done, n_stages):
    """The level held, the next one, and how far along each half of it you are."""
    held = LEVELS[0]
    for lv in LEVELS:
        if words >= lv.words and stages_done >= stages_needed(lv, n_stages):
            held = lv
        else:
            break
    if held.n == len(LEVELS):
        return {"level": held, "next": None, "words_frac": 1.0, "grammar_frac": 1.0,
                "frac": 1.0, "words_left": 0, "stages_left": 0, "lacking": None}
    nxt = LEVELS[held.n]
    need = stages_needed(nxt, n_stages)
    wf = _span(words, held.words, nxt.words)
    gf = _span(stages_done, stages_needed(held, n_stages), need)
    lacking = None if wf == gf else ("words" if wf < gf else "grammar")
    return {"level": held, "next": nxt, "words_frac": wf, "grammar_frac": gf,
            "frac": (wf + gf) / 2, "words_left": max(nxt.words - words, 0),
            "stages_left": max(need - stages_done, 0), "lacking": lacking}


# ------------------------------------------------------------------------ pace

def _date(d):
    if isinstance(d, datetime.datetime):
        return d.date()
    return datetime.date.fromisoformat(d) if isinstance(d, str) else d


def per_day(dates, today, window=PACE_WINDOW):
    """How many of `dates` fall in the last `window` days, per day."""
    start = today - datetime.timedelta(days=window - 1)
    return sum(1 for d in dates if d and start <= _date(d) <= today) / window


def eta(left, rate, today):
    """The date `left` more will be done at `rate` a day; None without a pace."""
    if left <= 0:
        return today
    if rate <= 0:
        return None
    return today + datetime.timedelta(days=math.ceil(left / rate))


def skills_left(track, progress, stages):
    """Skills still unlearned in the first `stages` stages."""
    first = sorted(track.stages)[:stages]
    return sum(1 for s in track.skills
               if s.stage in first and not track.is_learned(progress, s.key))


def pace(track, progress, card_rows, today):
    """(words started a day, grammar skills learned a day) over the last two weeks."""
    words = per_day([r["introduced"] for r in card_rows if r["reps"] > 0], today)
    # Skills placed by the placement test are where you started, not pace.
    skills = per_day([s.get("introduced") for k, s in progress["skills"].items()
                      if track.is_learned(progress, k) and not s.get("placed")], today)
    return words, skills


def placement_words(placement, card_rows):
    """Words the placement test found you know that no card records yet: those in
    the tiers it skipped, plus its estimate for the rest, less the cards started
    there since (each started card is counted by the cards from then on). The
    estimate fades as the deck catches up with it, and never goes below zero."""
    if not placement or placement.get("skipped"):
        return 0
    since = _date(placement["date"])
    t = placement.get("start_tier") or 0
    started = sum(1 for r in card_rows
                  if r["reps"] > 0 and r.get("tier", 0) >= t and _date(r["introduced"]) >= since)
    # (A started card in the start tier may sit above or below the start point;
    # either way it is counted by the cards now, so it comes off the estimate.)
    return placement.get("words_skipped", 0) + max(placement.get("words_other", 0) - started, 0)


def forecast(words, track, progress, today, words_rate, skills_rate):
    """When each level arrives if words and skills keep coming at these daily rates.

    One entry per level: its date (None without the pace it needs), the days from
    now (0 if it's already held), what's still missing, and which half arrives last
    — the one to speed up if the date is too far off.
    """
    n = len(track.stages)
    held = standing(words, track.current_stage(progress) - 1, n)["level"].n
    out = []
    for lv in LEVELS:
        words_left = max(lv.words - words, 0)
        sk_left = skills_left(track, progress, stages_needed(lv, n))
        if lv.n <= held:
            out.append({"level": lv, "held": True, "date": today, "days": 0,
                        "words_left": 0, "skills_left": 0, "slower": None})
            continue
        w, g = eta(words_left, words_rate, today), eta(sk_left, skills_rate, today)
        date = None if None in (w, g) else max(w, g)
        slower = None
        if words_left or sk_left:
            # With no pace on one side, that side is the one in the way.
            slower = ("words" if w is None else "grammar" if g is None else
                      "words" if w > g else "grammar" if g > w else None)
        out.append({"level": lv, "held": False, "date": date,
                    "days": None if date is None else (date - today).days,
                    "words_left": words_left, "skills_left": sk_left, "slower": slower})
    return out


def span(days):
    """A number of days the way you'd say it: "9 days", "7 weeks", "5 months"."""
    if days is None:
        return "no date yet"
    if days <= 0:
        return "today"
    if days < 14:
        return f"{days} day{'' if days == 1 else 's'}"
    if days < 70:
        return f"{round(days / 7)} weeks"
    if days < 700:
        return f"{round(days / 30.4)} months"
    return f"{days / 365.25:.1f} years"


# Roughly what the Account page promises: 15 new cards a day settles at about 20
# minutes of reviews.
MINUTES_PER_NEW_WORD = 20 / 15


def vocab_minutes(words_a_day):
    return round(words_a_day * MINUTES_PER_NEW_WORD)


# -------------------------------------------------------------------- activity

def day_total(entry):
    """Everything practised in one day's log, the alphabet included."""
    return sum(entry.get(k, 0) for k in ACTIVITIES + ("basics",))


def history(day_logs, today, n):
    """[(date, total)] for the last `n` days, oldest first. `day_logs` is one
    progress["days"] per language; a day counts whichever language it was in."""
    out = []
    for back in range(n - 1, -1, -1):
        d = today - datetime.timedelta(days=back)
        out.append((d, sum(day_total(days.get(d.isoformat(), {})) for days in day_logs)))
    return out


def days_active(day_logs):
    return len({d for days in day_logs for d, e in days.items() if day_total(e)})


def best_streak(day_logs):
    """The longest run of consecutive days with any practice."""
    active = sorted(datetime.date.fromisoformat(d)
                    for d in {d for days in day_logs for d, e in days.items()
                              if day_total(e)})
    best = run = 0
    prev = None
    for d in active:
        run = run + 1 if prev and (d - prev).days == 1 else 1
        best, prev = max(best, run), d
    return best


def week_balance(days, today, span=7):
    """For each kind of practice, what was done in the last `span` days and what a
    week of daily targets comes to. Vocab has no target: (done, None)."""
    out = {}
    for k in ACTIVITIES:
        done = sum(days.get((today - datetime.timedelta(days=b)).isoformat(), {})
                   .get(k, 0) for b in range(span))
        out[k] = (done, TARGETS[k] * span if k in TARGETS else None)
    return out


def recent_accuracy(days, today, span=7):
    """First-attempt grammar accuracy over the last `span` days, or None."""
    seen = right = 0
    for b in range(span):
        e = days.get((today - datetime.timedelta(days=b)).isoformat(), {})
        seen += e.get("grammar", 0)
        right += e.get("grammar_right", 0)
    return right / seen if seen else None


# ----------------------------------------------------------------------- vocab

def card_states(card_rows):
    """Started cards by how well they're held: learning (still in the first steps or
    relearning), young (reviewing, under three weeks), mature."""
    out = {"learning": 0, "young": 0, "mature": 0}
    for r in card_rows:
        if r["reps"] == 0:
            continue
        f = json.loads(r["fsrs"])
        if f.get("state", 1) != 2:
            out["learning"] += 1
        elif (f.get("stability") or 0) >= MATURE_DAYS:
            out["mature"] += 1
        else:
            out["young"] += 1
    return out


def coming_up(card_rows, track, progress, today, n=7):
    """[(date, cards due, grammar skills due)] for today and the next `n - 1` days.
    Anything already overdue lands on today."""
    cards = [max(_date(r["due"]), today) for r in card_rows]
    skills = [max(_date(s["due"]), today) for s in progress["skills"].values()
              if s.get("due")]
    out = []
    for i in range(n):
        d = today + datetime.timedelta(days=i)
        out.append((d, cards.count(d), skills.count(d)))
    return out


# --------------------------------------------------------------------- grammar

def grammar_accuracy(progress):
    """All-time first-attempt accuracy across every drilled skill, or None."""
    seen = sum(s.get("seen", 0) for s in progress["skills"].values())
    right = sum(s.get("right", 0) for s in progress["skills"].values())
    return right / seen if seen else None


def weakest(track, progress, k=3, min_seen=4, below=0.8):
    """The drilled skills with the lowest accuracy, worst first."""
    pool = [(track.accuracy(progress, s.key), s) for s in track.skills
            if track.state(progress, s.key).get("seen", 0) >= min_seen]
    return [(s, a) for a, s in sorted(pool, key=lambda p: p[0]) if a < below][:k]


def stage_rows(track, progress):
    """[(number, name, learned, total, "done" | "current" | "locked")]."""
    cur = track.current_stage(progress)
    out = []
    for n, name in sorted(track.stages.items()):
        skills = [s for s in track.skills if s.stage == n]
        done = sum(track.is_learned(progress, s.key) for s in skills)
        out.append((n, name, done, len(skills),
                    "done" if n < cur else "current" if n == cur else "locked"))
    return out
