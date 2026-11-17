"""The grammar track, independent of language: what to learn, in what order, and what
to drill today. Each language supplies its skills (hub/ja/curriculum.py,
hub/es/curriculum.py); this module schedules them.

A SKILL is one transformation you can be tested on: a conjugation form (食べる → 食べ
ました, hablar → hablé) or a pattern built from one (食べる → 食べてもいい). Skills are
grouped into STAGES in roughly the order textbooks teach them, so each stage leans on
the one before.

A skill may take a CUE — something the prompt has to specify besides the word, such
as the grammatical person in Spanish ("nosotros"). Japanese skills have no cues. The
cue for each drill is picked at random alongside the word.

Scheduling is spaced repetition at the level of the skill, not the word: the word in
each drill is random, which is the point — you are proving you can apply the rule to
anything, not that you remember one answer. After a session a skill moves up a box if
you got at least 80% of it, back to box 1 if not. A skill counts as learned at box 2,
which means passing it on two separate days, and a stage opens once everything before
it is learned. Scoring 90%+ on a skill the first time it is drilled jumps it straight
to box 3 — someone who already knows a form tests out in one session instead of
grinding through it.
"""
import datetime, random
from dataclasses import dataclass
from typing import Callable, Optional, Tuple

INTERVALS = {1: 1, 2: 3, 3: 7, 4: 14, 5: 30, 6: 60}     # box -> days until due
LEARNED_BOX = 2
NEW_PER_SESSION = 3
SESSION_SIZE = 20


@dataclass(frozen=True)
class Skill:
    key: str
    stage: int
    title: str              # what it means, in English
    shape: str              # the form as textbooks write it: 〜ます, pretérito
    classes: frozenset      # word classes it applies to
    build: Callable         # (word) or (word, cue) -> [accepted answers], canonical first
    rule: str               # how to form it — shown in the lesson and on every miss
    forms: frozenset        # underlying forms, checked against Word.skip
    cues: Tuple = (None,)   # e.g. the six Spanish persons; (None,) for no cue

    def answers(self, word, cue=None):
        return self.build(word) if cue is None else self.build(word, cue)


class Track:
    def __init__(self, skills, stages):
        self.skills = list(skills)
        self.stages = dict(stages)
        self.by_key = {s.key: s for s in self.skills}
        assert len(self.by_key) == len(self.skills), "duplicate skill key"

    # ------------------------------------------------------------------ state

    @staticmethod
    def state(progress, key):
        return progress["skills"].get(key) or {}

    def is_learned(self, progress, key):
        return self.state(progress, key).get("box", 0) >= LEARNED_BOX

    def current_stage(self, progress):
        """The lowest stage with anything not yet learned."""
        for n in sorted(self.stages):
            if not all(self.is_learned(progress, s.key) for s in self.skills if s.stage == n):
                return n
        return max(self.stages) + 1

    def unlocked(self, progress):
        top = self.current_stage(progress)
        return [s for s in self.skills if s.stage <= top]

    def due(self, progress, today):
        t = today.isoformat()
        return [s for s in self.skills if self.state(progress, s.key).get("due") and
                self.state(progress, s.key)["due"] <= t]

    def new_skills(self, progress, limit=NEW_PER_SESSION):
        return [s for s in self.unlocked(progress) if not self.state(progress, s.key)][:limit]

    def accuracy(self, progress, key):
        s = self.state(progress, key)
        return s.get("right", 0) / s["seen"] if s.get("seen") else 0.0

    # --------------------------------------------------------------- sessions

    @staticmethod
    def eligible_words(skill, words):
        return [w for w in words if w.cls in skill.classes and not (skill.forms & w.skip)]

    def item(self, skill, words, known):
        """One drill: a word for the skill (mostly words you know from your vocab,
        but not only — a rule only sticks once it survives words you haven't met)
        and a cue."""
        pool = self.eligible_words(skill, words)
        mine = [w for w in pool if w.written in known or getattr(w, "kana", None) in known]
        w = random.choice(mine) if mine and random.random() < 0.7 else random.choice(pool)
        return {"skill": skill.key, "word": w, "cue": random.choice(skill.cues)}

    def build_session(self, progress, today, words, known, only=None, size=SESSION_SIZE):
        """Return (lessons, items). Lessons are skills seen for the first time today.

        `only` restricts to chosen skills — free practice, which records stats but
        leaves the schedule alone.
        """
        if only:
            chosen, lessons = [(s, size // len(only) or 1) for s in only], []
        else:
            fresh = self.new_skills(progress)
            overdue = sorted(self.due(progress, today),
                             key=lambda s: (self.state(progress, s.key)["due"],
                                            self.state(progress, s.key).get("box", 0)))
            chosen = [(s, 5) for s in fresh] + [(s, 3) for s in overdue]
            lessons = fresh
            if not chosen:
                # Nothing new or due: practise the weakest of what is unlocked.
                pool = [s for s in self.unlocked(progress) if self.state(progress, s.key)]
                pool.sort(key=lambda s: self.accuracy(progress, s.key))
                chosen = [(s, 3) for s in pool[:7]]

        items = []
        for skill, n in chosen:
            for _ in range(min(n, size - len(items))):
                items.append(self.item(skill, words, known))
            if len(items) >= size:
                break
        random.shuffle(items)
        return lessons, items

    def stage_test(self, progress, words, known, per_skill=4):
        stage = self.current_stage(progress)
        pending = [s for s in self.skills
                   if s.stage == stage and not self.is_learned(progress, s.key)]
        items = [self.item(s, words, known) for s in pending for _ in range(per_skill)]
        random.shuffle(items)
        return items

    @staticmethod
    def record(progress, today, results, schedule=True):
        """Fold a finished session into progress. `results` maps skill key -> list of
        first-attempt booleans. Returns {key: (old_box, new_box)} for the summary."""
        moves = {}
        for key, marks in results.items():
            if not marks:
                continue
            s = progress["skills"].setdefault(key, {})
            first_time = not s.get("seen")
            s["seen"] = s.get("seen", 0) + len(marks)
            s["right"] = s.get("right", 0) + sum(marks)
            if not schedule:
                continue
            rate = sum(marks) / len(marks)
            old = s.get("box", 0)
            if first_time and rate >= 0.9 and len(marks) >= 4:
                new = 3                                    # tested out
            elif rate >= 0.8:
                new = min(old + 1, max(INTERVALS))
            else:
                new = 1
            s["box"] = new
            s["due"] = (today + datetime.timedelta(days=INTERVALS[new])).isoformat()
            s.setdefault("introduced", today.isoformat())
            moves[key] = (old, new)
        return moves


def check(skill, word, cue, answer, normalize, fold=None):
    """Returns (ok, expected, near). `near` is True when the answer only differs from
    an accepted one by what `fold` strips — accents, in Spanish — so the miss can say
    so rather than look like a wrong form."""
    expected = skill.answers(word, cue)
    a = normalize(answer)
    if any(a == normalize(e) for e in expected):
        return True, expected, False
    near = bool(fold) and any(fold(a) == fold(normalize(e)) for e in expected)
    return False, expected, near
