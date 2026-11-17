"""Basics: the script and sounds, before any words. Kana for Japanese, letters, sounds
and stress for Spanish.

The course is a short line of UNITS (a kana row, a Spanish sound) taken in order.
Each unit opens with a lesson card, then a drill round in the Katsuyou style: every
item in the unit, in each of the unit's drill modes, shuffled, plus a few items from
units already passed. Misses come back at the end of the round, and only first
attempts count. Scoring 90% or more on the unit's own items passes it and opens the
next one.

Items keep a running tally too ("right of seen"), which "Practise all learned" uses
to drill the weakest ones.

Each language's course lives beside its other material — hub/ja/kana_course.py and
hub/es/sounds.py — and supplies the units and how to check a typed answer. This
module does the rest. Progress is progress["basics"] in the learner's per-language
progress, saved by session.save() with everything else.
"""
import importlib, random
from dataclasses import dataclass, field
from typing import Optional, Tuple

PASS = 0.9
REVIEW_IN_UNIT = 4          # earlier items mixed into a unit round
UNIT_ROUND_MAX = 24
REVIEW_ROUND = 20
OPTIONS = 4

COURSES = {"ja": "hub.ja.kana_course", "es": "hub.es.sounds"}


@dataclass(frozen=True)
class Item:
    id: str                 # unique across the course
    text: str               # what is shown: a kana, a word, a phrase
    answers: Tuple[str, ...]  # accepted typed answers, canonical first (romaji, spelling)
    hint: str = ""          # mnemonic or meaning
    speak: str = ""         # what text-to-speech reads; defaults to text
    syllables: Tuple[str, ...] = ()   # Spanish stress drills
    stress: int = -1

    @property
    def say(self):
        return self.speak or self.text


@dataclass(frozen=True)
class Unit:
    key: str
    title: str
    sub: str                # one line under the title, e.g. "あ い う え お"
    intro: str              # the rule, shown on the lesson card
    items: Tuple[Item, ...]
    # Drill modes: "type" (see it, type romaji), "pick" (hear/see romaji, choose the
    # kana), "dictate" (hear it, type it), "stress" (choose the stressed syllable).
    modes: Tuple[str, ...]
    chart: bool = True      # lesson shows every item in a tap-to-hear grid
    sample: Optional[int] = None   # drill only this many items per round (word units)
    extra: dict = field(default_factory=dict)


def course(code):
    return importlib.import_module(COURSES[code])


def units(code):
    return course(code).UNITS


def by_key(code):
    return {u.key: u for u in units(code)}


def items(code):
    return {i.id: i for u in units(code) for i in u.items}


# ----------------------------------------------------------------------- state

def state(progress):
    b = progress.setdefault("basics", {})
    b.setdefault("passed", [])
    b.setdefault("skipped", False)
    b.setdefault("items", {})
    return b


def is_passed(code, progress, key):
    st = state(progress)
    return st["skipped"] or key in st["passed"]


def status(code, progress):
    us = units(code)
    st = state(progress)
    done_n = len(us) if st["skipped"] else sum(u.key in st["passed"] for u in us)
    nxt = next((u for u in us if not is_passed(code, progress, u.key)), None)
    return {"done": nxt is None, "units_done": done_n, "units_total": len(us),
            "next_unit": nxt.title if nxt else None,
            "next_key": nxt.key if nxt else None, "skipped": st["skipped"]}


def skip(code, progress):
    state(progress)["skipped"] = True


def unskip(code, progress):
    state(progress)["skipped"] = False


def unit_states(code, progress):
    """[(unit, "passed" | "current" | "locked")] in course order. Only the first
    unpassed unit is open: each one leans on the ones before it."""
    out, opened = [], False
    for u in units(code):
        if is_passed(code, progress, u.key):
            out.append((u, "passed"))
        elif not opened:
            out.append((u, "current"))
            opened = True
        else:
            out.append((u, "locked"))
    return out


def can_start(code, progress, key):
    return dict((u.key, s) for u, s in unit_states(code, progress))[key] != "locked"


def learned_items(code, progress):
    return [i for u in units(code) if is_passed(code, progress, u.key) for i in u.items]


def accuracy(progress, item_id):
    right, seen = state(progress)["items"].get(item_id, (0, 0))
    return right / seen if seen else 0.0


# ---------------------------------------------------------------------- drills

def _drill(code, unit, item, mode, pool, rng, review=False):
    d = {"unit": unit.key, "item": item.id, "mode": mode, "review": review}
    if mode == "pick":
        d["options"] = course(code).options(item, pool, OPTIONS, rng)
    elif mode == "stress":
        d["options"] = list(range(len(item.syllables)))
    return d


def _seen_pool(code, progress, unit):
    """Items a learner has met by this unit: distractors come only from these."""
    out = []
    for u in units(code):
        out.extend(u.items)
        if u.key == unit.key:
            break
    return out


def build_round(code, progress, unit_key, rng=None):
    rng = rng or random.Random()
    unit = by_key(code)[unit_key]
    pool = _seen_pool(code, progress, unit)
    chosen = list(unit.items)
    if unit.sample and len(chosen) > unit.sample:
        chosen = rng.sample(chosen, unit.sample)
    drills = [_drill(code, unit, i, m, pool, rng) for i in chosen for m in unit.modes
              if m != "stress" or i.syllables]
    if len(drills) > UNIT_ROUND_MAX:
        # Keep every item at least once, then fill up with the rest.
        rng.shuffle(drills)
        first, rest, seen = [], [], set()
        for d in drills:
            (rest if d["item"] in seen else first).append(d)
            seen.add(d["item"])
        drills = (first + rest)[:max(UNIT_ROUND_MAX, len(first))]
    earlier = [(u, i) for u in units(code) if u.key != unit.key
               and is_passed(code, progress, u.key) for i in u.items]
    for u, i in rng.sample(earlier, min(REVIEW_IN_UNIT, len(earlier))):
        drills.append(_drill(code, u, i, u.modes[0], _seen_pool(code, progress, u), rng,
                             review=True))
    rng.shuffle(drills)
    return drills


def build_review(code, progress, rng=None, n=REVIEW_ROUND):
    """Learned items, weakest first, with a little randomness so it isn't the same
    twenty every time."""
    rng = rng or random.Random()
    pairs = [(u, i) for u in units(code) if is_passed(code, progress, u.key)
             for i in u.items]
    # Never-drilled items (a skipped course) sit between poor and good ones.
    tally = state(progress)["items"]
    pairs.sort(key=lambda p: (accuracy(progress, p[1].id) if p[1].id in tally else 0.6,
                              rng.random()))
    drills = []
    for u, i in pairs[:n]:
        modes = [m for m in u.modes if m != "stress" or i.syllables]
        drills.append(_drill(code, u, i, rng.choice(modes),
                             _seen_pool(code, progress, u), rng, review=True))
    rng.shuffle(drills)
    return drills


def check(code, drill, answer):
    """Returns (ok, near, expected, note). `answer` is typed text for type/dictate
    and the chosen option for pick/stress. `near` marks a miss that was nearly right
    (an accent); `note` explains a hit that was spelled differently."""
    item = items(code)[drill["item"]]
    mode = drill["mode"]
    if mode == "pick":
        return answer == item.text, False, item.text, ""
    if mode == "stress":
        return answer == item.stress, False, item.syllables[item.stress], ""
    return course(code).check(item, mode, answer)


def record(code, progress, results, unit_key=None):
    """Fold a finished round in. `results` is [(item_id, unit_key, ok, review)] for
    first attempts only. Returns {"pct", "unit_pct", "passed"}: the unit passes when
    its own items scored PASS or better."""
    st = state(progress)
    for item_id, _, ok, _ in results:
        right, seen = st["items"].get(item_id, (0, 0))
        st["items"][item_id] = [right + bool(ok), seen + 1]
    marks = [ok for *_, ok, _ in results]
    own = [ok for _, u, ok, review in results if u == unit_key and not review]
    unit_pct = sum(own) / len(own) if own else 0.0
    passed = bool(unit_key) and bool(own) and unit_pct >= PASS
    if passed and unit_key not in st["passed"]:
        st["passed"].append(unit_key)
    return {"pct": sum(marks) / len(marks) if marks else 0.0, "unit_pct": unit_pct,
            "passed": passed}
