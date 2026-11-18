"""Vocab reviews from Dondon's own decks — see hub/srs.py for the scheduling.

The card shows the bare word on the front. The back has the reading (Japanese), the
meaning, and an example sentence, with a speaker button for both. Two buttons, the way this app has
always graded: Again, or Got it. A brand-new card also gets "I know this", for words
you already have from elsewhere.

Cards you miss come back later in the same session (FSRS's 1- and 10-minute learning
steps), so a session ends when every card has been got right once.
"""
import time

import streamlit as st

from hub import audio, langs, session, srs, ui
from hub.store import today

ss = st.session_state
L = langs.get(session.lang())
email = session.email()
ls = session.lang_settings()

if not srs.tiers(L.code):
    ui.card(f'<div class="meaning">No {L.name} decks yet</div><div class="sent-en">'
            f'They\'re generated with <code>tools/make_deck.py</code> and land in '
            f'<code>decks/{L.code}/</code>.</div>')
    st.stop()

key = f"vq_{L.code}"
if key not in ss:
    ss[key] = srs.queue(email, L.code, ls, session.day_log().get("new", 0))
    ss[f"{key}_i"] = 0
    ss[f"{key}_got"] = 0
q, i = ss[key], ss[f"{key}_i"]
cards = srs.all_cards(L.code)


def furigana(s):
    from hub.ja.kana import furigana_html
    return furigana_html(s)


# ----------------------------------------------------------------------------- done
if i >= len(q):
    if not ss.get(f"{key}_saved"):
        ss[f"{key}_saved"] = True
        session.save()
    t = srs.current_tier(email, L.code, ls)
    sub = ""
    if t is not None:
        s = srs.tier_stats(email, L.code, t)
        sub = f"Tier {t}: {s['introduced']} of {s['total']} words started"
    ui.card(f'<div class="word small">{"Done" if q else "Nothing due"}</div>'
            f'<div class="reading">{len(q)} reviews this session</div>'
            f'<div class="sent-en">{sub}</div>')
    if st.button("Check for more", use_container_width=True):
        for k in (key, f"{key}_saved"):
            ss.pop(k, None)
        st.rerun()
    st.page_link("views/grammar.py", label="Next: grammar →")
    st.stop()

# ----------------------------------------------------------------------------- card
item = q[i]
c = cards[item["id"]]
ss.setdefault(f"{key}_shown", time.time())
revealed = ss.get(f"{key}_rev", False)

st.progress(min(i / len(q), 1.0))
st.markdown(f'<div class="meta"><span>{i} / {len(q)}</span><span class="right">'
            f'{"new · " if item["new"] else ""}tier {c["tier"]}</span></div>',
            unsafe_allow_html=True)


def answer(rating):
    if rating != srs.AGAIN:
        ui.swoosh()
    ms = int((time.time() - ss[f"{key}_shown"]) * 1000)
    due = srs.answer(email, L.code, item["id"], rating, ms, today())
    session.log("vocab")
    if item["new"]:
        session.log("new")
    if srs.requeue(due):
        q.append({"id": item["id"], "new": False})
    ss[f"{key}_i"] += 1
    ss[f"{key}_rev"] = False
    ss[f"{key}_shown"] = time.time()
    if ss[f"{key}_i"] % 10 == 0:
        session.save()


if not revealed:
    ui.card(f'<div class="word">{ui.esc(c["word"])}</div>')
    if st.button("Show", type="primary", use_container_width=True):
        ss[f"{key}_rev"] = True
        st.rerun()
else:
    head = (ui.ruby(c["word"], c.get("reading")) if L.has_reading else ui.esc(c["word"]))
    back = [f'<div class="word">{head}</div>']
    if L.has_reading and c.get("reading") and c["reading"] != c["word"]:
        back.append(f'<div class="reading">{ui.esc(c["reading"])}</div>')
    back.append(f'<div class="meaning">{ui.esc(c["meaning"])}</div>')
    if c.get("pos"):
        back.append(f'<div class="sent-en">{ui.esc(c["pos"])}</div>')
    if c.get("sentence"):
        sent = (furigana(c["sentence_furigana"]) if c.get("sentence_furigana")
                else ui.esc(c["sentence"]))
        back += ['<div class="rule"></div>', f'<div class="sent">{sent}</div>',
                 f'<div class="sent-en">{ui.esc(c.get("sentence_en", ""))}</div>']
    ui.card("".join(back))

    voice = audio.find(L.code, c["word"])
    s1, s2 = st.columns(2)
    with s1:
        ui.speak(c.get("reading") or c["word"], L.tts, "word", voice=voice)
    if c.get("sentence"):
        with s2:
            ui.speak(c["sentence"], L.tts, "sentence")
    if voice:
        st.markdown(audio.credit(voice, c["word"]), unsafe_allow_html=True)

    with st.container(key="graders"):
        a, b = st.columns(2)
        if a.button("Again", use_container_width=True, key=f"a{i}"):
            answer(srs.AGAIN)
            st.rerun()
        if b.button("Got it", use_container_width=True, key=f"g{i}"):
            answer(srs.GOOD)
            st.rerun()
    if item["new"] and st.button("I know this already", use_container_width=True,
                                 key=f"e{i}"):
        answer(srs.EASY)
        st.rerun()
