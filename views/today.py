"""The daily plan: words and rules in, then reading, building, speaking and talking —
each with a target small enough to do every day. Consistency beats volume, and the
streak is there to protect it. Beginners see Basics (the alphabet) first."""
import datetime, json, os

import streamlit as st

from hub import basics, langs, session, srs, stats, tutor, ui
from hub.store import ROOT, now, today

TARGETS = stats.TARGETS

L = langs.get(session.lang())
T = L.track
email = session.email()
progress = session.progress()
log = session.day_log()
known = session.known_words()
words = session.words_estimate()
day = today()

stage = T.current_stage(progress)
grammar_due = len(T.due(progress, day)) + len(T.new_skills(progress))

# A greeting in the language being learned, by the learner's clock.
hour = now().hour
hi = L.greetings[0 if hour < 11 else 1 if hour < 18 else 2]
name = st.session_state.get("name") or ""
who = f", {ui.esc(name.split()[0])}" if name and name != "Owner" else ""
st.markdown(f'<div class="hello"><span class="hi">{hi}{who}</span>'
            f'<span class="on">{day:%A %d %B}</span></div>', unsafe_allow_html=True)

# ------------------------------------------------------------------- the plan
# Each step: (key, icon, name, sub, state, page, fraction done, done?)
plan = []


def add(key, icon, name, sub, n, target, page, unit=""):
    plan.append((key, icon, name, sub, f"{n} / {target}{unit}", page,
                 n / target if target else 0, n >= target))


# Basics first, until it's done or skipped.
b = basics.status(L.code, progress)
if not b["done"]:
    add("basics", "abc", "Basics", ("Hiragana and katakana" if L.code == "ja" else
                                   "Sounds and spelling")
        + (f" · next: {b['next_unit']}" if b.get("next_unit") else ""),
        b["units_done"], b["units_total"], "views/basics.py", " units")

# Vocab: Dondon's decks, plus the owner's own Anki batch for Japanese.
v = log.get("vocab", 0)
if srs.tiers(L.code):
    ls = session.lang_settings()
    waiting = len(srs.queue(email, L.code, ls, log.get("new", 0)))
    t = srs.current_tier(email, L.code, ls)
    if t is None:
        sub = "All tiers started"
    else:
        ts_ = srs.tier_stats(email, L.code, t)
        sub = f"Tier {t} · {ts_['introduced']:,} of {ts_['total']:,} words started"
    plan.append(("vocab", "style", "Vocabulary", sub,
                 f"{waiting} left" if waiting else f"{v} done", "views/vocab.py",
                 v / (v + waiting) if v + waiting else 0, waiting == 0 and v > 0))

if L.code == "ja" and session.is_owner():
    due_path = os.path.join(ROOT, "data", "due.json")
    batch = len(json.load(open(due_path, encoding="utf-8")).get("cards", [])) \
        if os.path.exists(due_path) else 0
    if batch:
        plan.append(("anki", "inbox", "My vocabulary", "Your own deck's batch",
                     f"{batch} cards", "views/anki.py", None, False))

add("grammar", "repeat", "Grammar",
    f"Stage {min(stage, len(T.stages))}: {T.stages.get(stage, 'all stages learned')}"
    f" · {grammar_due} waiting", log.get("grammar", 0), TARGETS["grammar"],
    "views/grammar.py")
add("read", "menu_book", "Read", "Something real at your level", log.get("read", 0),
    TARGETS["read"], "views/read.py")
if tutor.available():
    add("build", "extension", "Build", "Use today's grammar in real sentences",
        log.get("build", 0), TARGETS["build"], "views/build.py")
add("speak", "mic", "Speak", "Listen, repeat, get scored", log.get("speak", 0),
    TARGETS["speak"], "views/speak.py")
if tutor.available():
    add("talk", "forum", "Talk", "A conversation at your level", log.get("talk", 0),
        TARGETS["talk"], "views/talk.py", " turns")

# The Anki batch is the owner's own loop, not part of the daily count.
counted = [p for p in plan if p[6] is not None]
done_n = sum(p[7] for p in counted)
upcoming = next((p for p in counted if not p[7]), None)

# ------------------------------------------------------------------- the hero
# Today's ring, the level you hold and how far the next one is, and the week.
s = stats.standing(words, stage - 1, len(T.stages))
lv, nxt = s["level"], s["next"]
if nxt:
    # The date for the next level at the last two weeks' pace, when there is one.
    cards_ = list(srs.rows(email, L.code).values()) if srs.tiers(L.code) else []
    ahead = stats.forecast(words, T, progress, day,
                           *stats.pace(T, progress, cards_, day))[nxt.n - 1]
    right = (f"in {stats.span(ahead['days'])}" if ahead["date"] else
             f"{words:,} words · stage {min(stage, len(T.stages))}")
    under = (f'<span>{ui.pct(s["frac"])} to {ui.esc(nxt.name)}</span>'
             f'<span>{right}</span>')
else:
    under = f'<span>Top of the path</span><span>{words:,} words</span>'

streak = session.streak()
logs = [session.progress(c)["days"] for c in session.LANGS]
monday = day - datetime.timedelta(days=day.weekday())
week = ""
for i, letter in enumerate("MTWTFSS"):
    d = monday + datetime.timedelta(days=i)
    on = any(stats.day_total(days.get(d.isoformat(), {})) for days in logs)
    week += (f'<div class="d{" on" if on else ""}{" now" if d == day else ""}">'
             f'<i></i>{letter}</div>')
week += f'<div class="streak">{ui.icon("local_fire_department", fill=True)} {streak} day{"" if streak == 1 else "s"}</div>'

ui.panel(
    f'<div class="hero">{ui.ring(done_n / len(counted), f"{done_n}/{len(counted)}", "today")}'
    f'<div class="side"><div class="eyebrow">level {lv.n} of '
    f'{len(stats.LEVELS)}</div><div class="title">{ui.esc(lv.name)}</div>'
    f'{ui.bar(s["frac"])}<div class="under">{under}</div></div></div>'
    f'<div class="week">{week}</div>')

if not progress.get("placement"):
    # New here: find the right starting point before anything else.
    if st.button("Find your level · about 5 minutes", type="primary",
                 use_container_width=True, icon=":material/my_location:"):
        st.switch_page("views/placement.py")
elif upcoming:
    if st.button(f"{'Continue' if done_n or any(log.values()) else 'Start'} · "
                 f"{upcoming[2]}", type="primary", use_container_width=True):
        st.switch_page(upcoming[5])
else:
    st.markdown(f'<div class="verdict ok">{ui.icon("check_circle")} Everything done for '
                f'today</div>', unsafe_allow_html=True)

# ------------------------------------------------------------------- the plan
ui.section("today's plan", f"{done_n} of {len(counted)} done")
for key, icon, name, sub, state, page, frac, done in plan:
    ui.task(key, icon, name, sub, state, page, frac, done,
            nxt=upcoming is not None and key == upcoming[0])
ui.task("progress", "trending_up", "Progress", "Your path, pace and statistics",
        "", "views/progress.py")

with st.expander("How this gets you speaking"):
    st.markdown("""
**Basics** is the alphabet — hiragana and katakana, or Spanish sounds and
spelling. Skip it if you have it already.

**Vocabulary** brings the words in: 1,500-word tiers, most common words first. Finish
starting one tier and the next opens.

**Grammar** turns the rules into reflexes. You get a word and a form and you type it
until conjugating takes no thought. Skills come back on a spaced schedule, and a
stage opens once the one before it sticks. If you already know a form, ace it the
first time and it skips ahead.

**Read** is where words stop being flashcards: real topics — what's trending,
history, food, games — rewritten at your level. Tap any word you don't know, and
add it to your vocab from there.

**Build** is where conjugating turns into speaking. You translate sentences that
need what you just drilled, using words you know, and get graded on whether it's
right and how a native speaker would put it.

**Speak** trains your mouth: hear a sentence, say it back, and the phone tells you
how much of it it understood.

**Talk** is the actual goal. Role-plays at your level, with a correction after
anything you get wrong. Tap the microphone to answer out loud, and the speaker to
hear replies and
shadow them.

Do a little of each every day. Ten minutes of each beats an hour of one.
""")

if st.session_state.get("save_err"):
    st.caption(f":material/warning: progress not saved: {st.session_state.save_err}")
