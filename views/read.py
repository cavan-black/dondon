"""Reading: real things to read, at your level, where every word can be tapped.

Passages come from Wikipedia in the language you're learning — what's trending, what
happened on this day, or a topic you pick — rewritten by Claude at your level, or
from an original short story. Every passage goes into a shared library for your
language and level, so the next learner there can read it for free.

Tap a word for its reading and meaning (and to hear it); tap EN for a sentence's
translation. Words you looked up that are in the Dondon decks can be added to your
vocab straight from the page. Three questions at the end check you got the gist.

You can also paste your own text (an article, lyrics, a manga page you've typed out):
it's glossed exactly as written and never stored.
"""
import json, uuid

import streamlit as st

from hub import db, langs, session, sources, srs, tutor, ui, widgets
from hub.store import today

ss = st.session_state
L = langs.get(session.lang())
progress = session.progress()
ls = session.lang_settings()
reading = progress.setdefault("reading", {"read": []})
known = session.known_words()
MADE_PER_DAY = 6              # new passages per invited learner per day; owner uncapped
PASTE_MAX = 1500

if ss.get("r_lang") != L.code:
    ss.r_passage, ss.r_lang = None, L.code


def fail(msg):
    st.error(msg)
    st.stop()


def auto_level():
    return tutor.level_for(session.words_estimate(), L.track.current_stage(progress))


def can_make():
    if not tutor.available():
        return False, "Needs an ANTHROPIC_API_KEY secret."
    if session.tutor_allowance() <= 0:
        return False, "That's today's tutor allowance used — it resets tomorrow."
    if not session.is_owner() and session.day_log().get("made", 0) >= MADE_PER_DAY:
        return False, "That's today's new passages made — read from the library instead."
    return True, ""


def open_passage(row, data):
    ss.r_passage = {"id": row.get("id"), "data": data, "level": row.get("level"),
                    "topic": row.get("topic"), "source_title": row.get("source_title"),
                    "source_url": row.get("source_url"), "answers": None}
    ss.pop("r_reader", None)


def make(level, choice, custom):
    """Fetch a source (unless it's a story), adapt it, store it, open it."""
    src, topic = None, choice
    with st.spinner("Finding something to read…"):
        try:
            if custom:
                topic = custom
                src = sources.search(L.code, custom)
                if src is None:
                    fail(f"Nothing on {L.name} Wikipedia for “{custom}” — try another "
                         "word, or write it in " + L.name + ".")
            elif choice == "Trending":
                src = sources.trending(L.code)
            elif choice == "On this day":
                src = sources.on_this_day(L.code)
            elif choice in sources.TOPICS[L.code]:
                src = sources.topic(L.code, choice)
            if choice not in ("Story",) and not custom and src is None:
                fail("Couldn't find a good article just now — try another topic.")
        except Exception as exc:     # network trouble shouldn't kill the page
            fail(f"Couldn't reach Wikipedia ({exc.__class__.__name__}) — try again.")
    prof = tutor.profile(L, progress, known)
    with st.spinner("Writing it at your level… (about half a minute)"):
        try:
            p = tutor.adapt(L, prof, level,
                            source_text=src.text if src else None,
                            source_title=src.title if src else None,
                            topic=None if src else "anything fun, surprising or "
                                                   "everyday-relatable")
            session.spend_tutor_call()
        except tutor.TutorError as e:
            fail(str(e))
    row = {"id": f"{L.code}{level}-{uuid.uuid4().hex[:12]}", "lang": L.code,
           "level": level, "topic": topic, "title": p.title,
           "source_title": src.title if src else None,
           "source_url": src.url if src else None, "data": p.model_dump_json(),
           "created_by": session.email()}
    db.put_passage(row)
    session.log("made")
    open_passage(row, p.model_dump())


# =============================================================== library / start
if ss.r_passage is None:
    lvl_auto = auto_level()
    choice = ls.get("read_level", "auto")
    opts = ["auto"] + list(tutor.LEVELS)
    picked = st.segmented_control(
        "Level", opts, default=choice if choice in opts else "auto",
        format_func=lambda v: f"auto ({lvl_auto})" if v == "auto" else str(v))
    if picked and picked != choice:
        ls["read_level"] = picked
        session.save_settings()
    level = lvl_auto if (picked or choice) == "auto" else int(picked or choice)
    name, rule = tutor.LEVELS[level]
    st.markdown(f'<div class="meta"><span>{L.name} reading · level {level}</span>'
                f'<span class="right">{name}</span></div>', unsafe_allow_html=True)
    st.caption(rule)

    # ---- something new
    ok, why = can_make()
    topics = ["Trending"] + (["On this day"] if sources.has_on_this_day(L.code) else []) \
        + ["Story"] + list(sources.TOPICS[L.code])
    icons = {"Trending": ":material/local_fire_department: ",
             "On this day": ":material/event: ", "Story": ":material/auto_stories: "}
    pick = st.pills("Topic", topics, default="Trending", label_visibility="collapsed",
                    format_func=lambda t: icons.get(t, "") + t)
    custom = st.text_input("or any topic", placeholder="…or any topic (e.g. cats, Messi)",
                           label_visibility="collapsed").strip()
    if st.button("New passage", type="primary", use_container_width=True, disabled=not ok):
        make(level, pick or "Story", custom)
        st.rerun()
    if not ok:
        st.caption(why)

    # ---- the shared library
    rows = db.library(L.code, level)
    unread = [r for r in rows if r["id"] not in reading["read"]]
    done = [r for r in rows if r["id"] in reading["read"]]
    st.markdown(f'<div class="meta"><span>library · level {level}</span>'
                f'<span class="right">{len(unread)} unread · {len(done)} read</span></div>',
                unsafe_allow_html=True)
    if not rows:
        st.caption("Nothing at this level yet — make the first one.")
    for r in unread[:12] + done[:4]:
        mark = ":material/check: " if r["id"] in reading["read"] else ""
        src = f" · from {r['source_title']}" if r.get("source_title") else " · story"
        if st.button(f"{mark}{r['title']}", key=f"lib_{r['id']}", use_container_width=True,
                     help=f"{r.get('topic') or ''}{src}"):
            full = db.get_passage(r["id"])
            open_passage(full, json.loads(full["data"]))
            st.rerun()

    # ---- your own text
    with st.expander("Paste your own text"):
        st.caption(f"Anything in {L.name} up to {PASTE_MAX} characters — it's glossed "
                   "word by word exactly as written, and not saved anywhere.")
        txt = st.text_area("Text", label_visibility="collapsed", max_chars=PASTE_MAX,
                           height=150)
        if st.button("Gloss it", use_container_width=True, disabled=not ok or not txt.strip()):
            with st.spinner("Glossing…"):
                try:
                    p = tutor.gloss(L, tutor.profile(L, progress, known), txt.strip())
                    session.spend_tutor_call()
                except tutor.TutorError as e:
                    fail(str(e))
            open_passage({"topic": "pasted"}, p.model_dump())
            st.rerun()
    st.stop()


# ======================================================================= reading
P = ss.r_passage
data = P["data"]
if st.button("← Library"):
    ss.r_passage = None
    st.rerun()

st.markdown(f'<div class="meta"><span>{ui.esc(P.get("topic") or L.name)}</span>'
            f'<span class="right">{"level " + str(P["level"]) if P.get("level") else ""}'
            f'</span></div>', unsafe_allow_html=True)
st.markdown(f'<div class="word small" style="text-align:left;font-size:1.7rem">'
            f'{ui.esc(data["title"])}</div><div class="sent-en" style="text-align:left">'
            f'{ui.esc(data.get("title_en", ""))}</div>', unsafe_allow_html=True)

tapped = widgets.reader(data, L.tts, furigana=(P.get("level") or 3) <= 3, key="r_reader")

if P.get("source_url"):
    st.caption(f"Adapted from [{P['source_title']}]({P['source_url']}) on Wikipedia, "
               "CC BY-SA 4.0. This adaptation is shared under the same licence.")

# ---- words you looked up
if tapped:
    st.markdown('<div class="meta"><span>words you looked up</span></div>',
                unsafe_allow_html=True)
    email, day = session.email(), today()
    started = srs.rows(email, L.code) if srs.tiers(L.code) else {}
    seen = set()
    for si, ti in tapped:
        try:
            t = data["sentences"][si]["tokens"][ti]
        except (IndexError, KeyError):
            continue
        head = t.get("d") or t["t"]
        if head in seen:
            continue
        seen.add(head)
        # The reading belongs to the form in the text, so it goes with that form.
        seen_as = t["t"] + (f" ({t['r']})" if t.get("r") and t["r"] != t["t"] else "")
        shown = f" · {seen_as}" if seen_as != head else ""
        c1, c2 = st.columns([3, 1], vertical_alignment="center")
        c1.markdown(f"**{ui.esc(head)}**{ui.esc(shown)} — {ui.esc(t.get('g', ''))}")
        cid = srs.find_card(L.code, t.get("d"), t["t"]) if srs.tiers(L.code) else None
        if cid and cid in started:
            c2.caption(":material/check: in vocab")
        elif cid:
            if c2.button("＋ vocab", key=f"add_{cid}"):
                srs.introduce(email, L.code, cid, day)
                st.toast(f"{head} added — it'll come up in Vocabulary today.")
                st.rerun()

# ---- did you get it?
qs = data.get("questions") or []
if qs:
    st.markdown('<div class="meta"><span>did you get it?</span></div>',
                unsafe_allow_html=True)
    with st.form("r_quiz", border=False):
        picks = [st.radio(q["q"], q["options"], index=None, key=f"q{i}")
                 for i, q in enumerate(qs)]
        checked = st.form_submit_button("Check", use_container_width=True, type="primary")
    if checked:
        P["answers"] = [q["options"].index(p) if p in q["options"] else None
                        for q, p in zip(qs, picks)]
    if P.get("answers") is not None:
        right = sum(a == q["answer"] for a, q in zip(P["answers"], qs))
        ui.card(f'<div class="word small">{right} / {len(qs)}</div>' +
                "".join(f'<div class="why">{ui.icon("check" if a == q["answer"] else "close")} '
                        f'{ui.esc(q["q"])} — {ui.esc(q["options"][q["answer"]])}</div>'
                        for a, q in zip(P["answers"], qs)), tight=True)

finished = P.get("answers") is not None or not qs
if st.button("Done reading" if finished else "Done (skip the questions)",
             type="primary" if finished else "secondary", use_container_width=True):
    if P.get("id") and P["id"] not in reading["read"]:
        reading["read"].append(P["id"])
    session.log("read")
    session.save()
    ss.r_passage = None
    st.rerun()
