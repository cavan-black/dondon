"""Progress: where you stand, what's between you and the next level, and how fast
you're getting there. Everything here is read from what the other pages record —
see hub/stats.py for the arithmetic and for what a level asks of you.

Top to bottom it answers, in order: what level am I, what do I still need, when
will I get there, am I keeping it up, what should I work on.
"""
import datetime

import streamlit as st

from hub import basics, db, langs, session, srs, stats, ui
from hub.store import today

L = langs.get(session.lang())
T = L.track
email = session.email()
progress = session.progress()
known = session.known_words()
words = session.words_estimate()
day = today()
rows = list(srs.rows(email, L.code).values()) if srs.tiers(L.code) else []
logs = [session.progress(c)["days"] for c in session.LANGS]
days = progress["days"]

stage = T.current_stage(progress)
n_stages = len(T.stages)
s = stats.standing(words, stage - 1, n_stages)
lv, nxt = s["level"], s["next"]

# ------------------------------------------------------------------ the level
ui.section(L.name, f"level {lv.n} of {len(stats.LEVELS)}")

if nxt:
    need = stats.stages_needed(nxt, n_stages)

    def req(label, have, want, frac, lacking):
        tag = '<span class="tag">focus here</span>' if lacking else ""
        return (f'<div class="req"><div class="top"><span>{label}{tag}</span>'
                f'<span>{have:,} / {want:,}</span></div>{ui.bar(frac)}</div>')

    ui.panel(
        f'<div class="hero">{ui.ring(s["frac"], ui.pct(s["frac"]), "to next")}'
        f'<div class="side"><div class="eyebrow">you are</div>'
        f'<div class="title">{ui.esc(lv.name)}</div>'
        f'<div class="note" style="margin:0">Next: {ui.esc(nxt.name)} — '
        f'{ui.esc(nxt.can.lower())}.</div></div></div>'
        + req("Words known", words, nxt.words, s["words_frac"],
              s["lacking"] == "words")
        + req("Grammar stages finished", stage - 1, need, s["grammar_frac"],
              s["lacking"] == "grammar"))
else:
    ui.panel(f'<div class="hero">{ui.ring(1, "6/6", "top")}<div class="side">'
             f'<div class="eyebrow">you are</div><div class="title">{ui.esc(lv.name)}'
             f'</div><div class="note" style="margin:0">Every level on the path is '
             f'yours. Keep reading and talking.</div></div></div>')

# ---------------------------------------------------------------- the forecast
# Every level still ahead, dated. The pace is yours as measured over the last two
# weeks; the sliders underneath swap in another one to see what it would buy.
words_rate, skills_rate = stats.pace(T, progress, rows, day)
measured = words_rate > 0 and skills_rate > 0
ls = session.lang_settings()
if measured:
    base_w = min(max(5 * round(words_rate * 7 / 5), 5), 350)
    base_s = min(max(round(skills_rate * 7), 1), 14)
else:
    base_w = min(ls.get("new_per_day", srs.DEFAULT_NEW_PER_DAY) * 7, 350)
    base_s = 3
kw, ks = f"fc_words_{L.code}", f"fc_skills_{L.code}"
week_w = st.session_state.get(kw, base_w)
week_s = st.session_state.get(ks, base_s)
chosen = (week_w, week_s) != (base_w, base_s)
if measured and not chosen:
    rate_w, rate_s = words_rate, skills_rate
else:
    rate_w, rate_s = week_w / 7, week_s / 7
fc = stats.forecast(words, T, progress, day, rate_w, rate_s)
ahead = [x for x in fc if not x["held"]]

if ahead:
    ui.section("forecast", "a pace you chose" if chosen else
               "your last two weeks' pace" if measured else "the daily plan's pace")
    names = [x["level"].name for x in ahead]
    goal = stats.LEVELS[max(stats.CONVERSATIONAL, ahead[0]["level"].n) - 1].name
    target = st.pills("Level to forecast", names, default=goal,
                      label_visibility="collapsed", key=f"fc_goal_{L.code}") or goal
    t = next(x for x in ahead if x["level"].name == target)

    if t["date"] is None:
        head = ('<div class="eta"><span class="when">No date yet</span></div>'
                f'<div class="note">There is no pace for {t["slower"]} to carry '
                f'forward. Set one below.</div>')
    else:
        left = []
        if t["words_left"]:
            left.append(f'{t["words_left"]:,} more words')
        if t["skills_left"]:
            left.append(f'{t["skills_left"]} more grammar skills')
        last = (f' {"Grammar" if t["slower"] == "grammar" else "Vocab"} arrives last, '
                f'so that is the half to speed up.' if t["slower"] else "")
        head = (f'<div class="eta"><span class="when">{t["date"]:%d %b %Y}</span>'
                f'<span class="in">in {stats.span(t["days"])}</span></div>'
                f'<div class="note">{" and ".join(left) or "Nothing left"}, at '
                f'{rate_w * 7:.0f} new words and {rate_s * 7:.1f} grammar skills a week.'
                f'{last}</div>')
    longest = max((x["days"] or 0 for x in fc), default=0) or 1
    lines = ""
    for x in fc:
        if x["held"]:
            lines += (f'<div class="fc held"><div class="k">{ui.esc(x["level"].name)}'
                      f'</div>{ui.bar(1, "ok")}<div class="n">held</div></div>')
        else:
            when = f'{x["date"]:%b %Y}' if x["date"] else "—"
            lines += (f'<div class="fc{" pick" if x is t else ""}" title="'
                      f'{ui.esc(x["level"].name)}: {stats.span(x["days"])}">'
                      f'<div class="k">{ui.esc(x["level"].name)}</div>'
                      f'{ui.bar((x["days"] or 0) / longest)}<div class="n">{when}</div></div>')
    ui.panel(f'<div class="eyebrow">you reach {ui.esc(target)} around</div>{head}'
             f'<div class="rule" style="margin:1rem 0 0.2rem"></div>{lines}')

    with st.expander("Try a different pace"):
        st.slider("New words a week", 0, 350, base_w, step=5, key=kw)
        st.slider("Grammar skills learned a week", 0, 14, base_s, key=ks)
        if measured:
            st.caption(f"Your last two weeks: {words_rate * 7:.0f} new words and "
                       f"{skills_rate * 7:.1f} grammar skills a week. Put the sliders "
                       f"back there to see your own pace again.")
        else:
            st.caption("There is no measured pace yet, so this starts from your new "
                       "cards per day and three grammar skills a week. It switches to "
                       "your own numbers after a few days of practice here.")
        st.caption(f"{week_w} new words a week is about "
                   f"{stats.vocab_minutes(week_w / 7)} minutes of vocab reviews a day "
                   f"once it settles. A grammar skill counts as learned when you pass "
                   f"it on two separate days.")
    st.caption("A forecast, not a promise: it carries the pace forward in a straight "
               "line and assumes the words and skills stick.")

# The whole path, so the distance to conversation is always in view.
steps = ""
for x in stats.LEVELS:
    cls = "done" if x.n < lv.n else "here" if x.n == lv.n else "todo"
    flag = ('<span class="flag">conversation</span>'
            if x.n == stats.CONVERSATIONAL else "")
    needs = (f'{x.words:,} words · {stats.stages_needed(x, n_stages)} of {n_stages} '
             f'grammar stages' if x.n > 1 else "Where everyone starts")
    if x.n > lv.n and fc[x.n - 1]["date"]:
        needs += f' · around {fc[x.n - 1]["date"]:%b %Y}'
    steps += (f'<div class="step {cls}"><div class="dot">{ui.icon("check") if cls == "done" else x.n}'
              f'</div><div><div class="name">{ui.esc(x.name)}{flag}</div>'
              f'<div class="can">{ui.esc(x.can)}</div>'
              f'<div class="needs">{needs}</div></div></div>')
ui.panel(f'<div class="h">The path</div><div class="path">{steps}</div>')

# ----------------------------------------------------------------- the numbers
ui.section("at a glance")
states = stats.card_states(rows)
since = db.now() - datetime.timedelta(days=30)
answered, passed = db.review_summary(email, L.code, since) if rows else (0, 0)
acc = stats.grammar_accuracy(progress)
acc7 = stats.recent_accuracy(days, day)
learned = sum(T.is_learned(progress, k.key) for k in T.skills)
ui.tiles([
    (session.streak(), "day streak", f"best {stats.best_streak(logs)}"),
    (stats.days_active(logs), "days practised"),
    (f"{words:,}", "words known", f"{states['mature']:,} mature" if rows else ""),
    (f"{round(100 * passed / answered)}%" if answered else "—", "vocab recall",
     f"{answered:,} answers, 30 days" if answered else "no reviews yet"),
    (f"{round(100 * acc)}%" if acc is not None else "—", "grammar accuracy",
     f"{round(100 * acc7)}% this week" if acc7 is not None else "first attempts"),
    (f"{learned}/{len(T.skills)}", "grammar learned",
     f"stage {min(stage, n_stages)} of {n_stages}"),
])

# ------------------------------------------------------------------- activity
hist = stats.history(logs, day, 14)
top = max(n for _, n in hist) or 1
cols = "".join(
    f'<div class="c" title="{d:%a %d %b}: {n} answers">'
    f'<span class="n">{n if n == top and n else ""}</span>'
    f'<i style="height:{round(84 * n / top)}%"></i></div>' for d, n in hist)
axis = "".join(f'<span class="{"now" if d == day else ""}">{f"{d:%a}"[0]}</span>'
               for d, _ in hist)
total = sum(n for _, n in hist)
active = sum(1 for _, n in hist if n)
ui.panel(f'<div class="h">Last 14 days</div><div class="note">{total:,} answers '
         f'across {active} of 14 days — every review, drill, sentence and turn.</div>'
         f'<div class="cols">{cols}</div><div class="axis">{axis}</div>')

# This week against the daily targets: the short bars are what to do next.
bal = stats.week_balance(days, day)
lines = ""
for k in stats.ACTIVITIES:
    done, want = bal[k]
    if want is None:
        continue
    lines += (f'<div class="row"><div class="k">{stats.LABELS[k]}</div>'
              f'{ui.bar(done / want, "ok" if done >= want else "")}'
              f'<div class="n">{done:,} / {want:,} {stats.UNITS[k]}</div></div>')
ui.panel(f'<div class="h">This week\'s balance</div><div class="note">The last 7 days '
         f'against a week of daily targets, on top of {bal["vocab"][0]:,} vocab '
         f'reviews. The short bars are what to do next.</div>{lines}')

# What the schedule has waiting, so a heavy day is never a surprise.
soon = stats.coming_up(rows, T, progress, day)
peak = max(c + g for _, c, g in soon) or 1
cols = "".join(
    f'<div class="c" title="{d:%a %d %b}: {c} cards, {g} grammar skills">'
    f'<span class="n">{c + g or ""}</span>'
    f'<i class="b" style="height:{round(84 * g / peak)}%"></i>'
    f'<i style="height:{round(84 * c / peak)}%"></i></div>' for d, c, g in soon)
axis = "".join(f'<span class="{"now" if d == day else ""}">'
               f'{"Today" if d == day else f"{d:%a}"}</span>' for d, _, _ in soon)
ui.panel(f'<div class="h">Coming up</div><div class="note">'
         + ("Reviews falling due over the next 7 days." if any(c + g for _, c, g in soon)
            else "Nothing scheduled yet. Reviews appear here once you've started "
                 "cards and grammar skills.")
         + f'</div><div class="cols">{cols}</div>'
         f'<div class="axis">{axis}</div><div class="legend">'
         f'<span><b style="background:var(--viz-1)"></b>Vocab cards</span>'
         f'<span><b style="background:var(--viz-2)"></b>Grammar skills</span></div>')

# ---------------------------------------------------------------------- vocab
ui.section("vocab", f"{words:,} words known")
tiers = srs.tiers(L.code)
if tiers:
    body = ""
    for t in tiers:
        ids = {c["id"] for c in srs.deck(L.code, t)["cards"]}
        st_ = stats.card_states([r for r in rows if r["card_id"] in ids])
        size = len(ids) or 1
        started = sum(st_.values())
        seg = "".join(
            f'<i title="{st_[k]:,} {k}" style="width:{100 * st_[k] / size:.2f}%;'
            f'background:var(--seq-{i})"></i>'
            for i, k in ((3, "mature"), (2, "young"), (1, "learning")) if st_[k])
        body += (f'<div class="req"><div class="top"><span>Tier {t} · words '
                 f'{(t - 1) * srs.TIER_SIZE + 1:,}–{t * srs.TIER_SIZE:,}</span>'
                 f'<span>{started:,} / {len(ids):,} started</span></div>'
                 f'<div class="stack">{seg}</div></div>')
    ui.panel(f'<div class="h">The ladder</div><div class="note">Most common words '
             f'first. A tier opens once every word in the one before is started.</div>'
             f'{body}<div class="legend">'
             f'<span><b style="background:var(--seq-3)"></b>Mature (3 weeks+)</span>'
             f'<span><b style="background:var(--seq-2)"></b>Young</span>'
             f'<span><b style="background:var(--seq-1)"></b>Learning</span>'
             f'<span><b style="background:var(--track)"></b>Not started</span></div>')
else:
    ui.panel(f'<div class="h">The ladder</div><div class="note">No {L.name} decks have '
             f'been generated yet, so the count above is the words from your own '
             f'collection.</div>')

# -------------------------------------------------------------------- grammar
ui.section("grammar", f"{learned} of {len(T.skills)} skills learned")
weak = stats.weakest(T, progress)
if weak:
    lines = "".join(
        f'<div class="row"><div class="k" style="width:auto;flex:1">'
        f'{ui.esc(k.shape)} <span style="color:var(--muted)">· {ui.esc(k.title)}</span>'
        f'</div><div class="n" style="width:auto">{round(100 * a)}%</div></div>'
        for k, a in weak)
    ui.panel(f'<div class="h">Work on these</div><div class="note">Your lowest '
             f'first-attempt accuracy. Pick them under Free practice on the Grammar '
             f'page.</div>{lines}')

body = ""
for i, (n, name, done, total, status) in enumerate(stats.stage_rows(T, progress)):
    body += (f'<div class="stage {status}{" first" if i == 0 else ""}">'
             f'<div class="no">{ui.icon("check") if status == "done" else n}</div>'
             f'<div class="body"><div class="name">{ui.esc(name)}</div>'
             + (ui.bar(done / total, "thin") if status == "current" and total else "")
             + f'</div><div class="n">{done}/{total}</div></div>')
ui.panel(f'<div class="h">The roadmap</div><div class="note">A stage opens once '
         f'everything before it is learned: passed on two separate days, or aced the '
         f'first time.</div>{body}')

with st.expander("Every form on the roadmap"):
    for n, name in T.stages.items():
        chips = " ".join(
            f'<span class="chip {"done" if T.is_learned(progress, k.key) else "on" if T.state(progress, k.key) else ""}">'
            f'{ui.esc(k.shape)}</span>' for k in T.skills if k.stage == n)
        st.markdown(f"**{n}. {name}**  \n{chips}", unsafe_allow_html=True)
    st.caption("Green is learned, blue is in progress.")

# --------------------------------------------------------------------- basics
b = basics.status(L.code, progress)
ui.section("basics", "skipped" if b["skipped"] else
           f"{b['units_done']} of {b['units_total']} units")
ui.panel(f'<div class="h">{"Kana" if L.code == "ja" else "Sounds and spelling"}</div>'
         f'<div class="note">'
         + ("You skipped the alphabet — it's still there on the Basics page."
            if b["skipped"] else "All units passed." if b["done"] else
            f"Next unit: {ui.esc(b['next_unit'])}.")
         + f'</div><div class="req">{ui.bar(b["units_done"] / b["units_total"], "ok" if b["done"] else "")}</div>')

if st.session_state.get("save_err"):
    st.caption(f":material/warning: progress not saved: {st.session_state.save_err}")
