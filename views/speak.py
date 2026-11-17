"""Speaking practice: shadowing, scored by your phone's speech recognition.

Listen to a sentence (at speed, or slowed down), say it back into the microphone,
and see how much the
phone understood: the parts it didn't catch are underlined. Speech recognition is a
rough judge — it rewards being understood, which is the point — so treat the score as
"would a stranger get it", not a pronunciation grade.

Sentences come from the example sentences of words you're learning (free), or a new
set written for your level around a theme (one tutor call). "Ears first" hides the
text until you've had a go, so you shadow what you heard instead of reading aloud.

For free conversation out loud, use the microphone on the Talk page.
"""
import random

import streamlit as st

from hub import langs, session, speech, srs, tutor, ui, widgets
from hub.ja.kana import furigana_html, furigana_reading

ss = st.session_state
L = langs.get(session.lang())
progress = session.progress()
known = session.known_words()
SET_SIZE = 8

if ss.get("sp_lang") != L.code:
    ss.sp_lines, ss.sp_lang = None, L.code


def vocab_lines():
    """Example sentences from cards you've answered at least once."""
    if not srs.tiers(L.code):
        return []
    cards = srs.all_cards(L.code)
    out = []
    for cid, r in srs.rows(session.email(), L.code).items():
        c = cards.get(cid)
        if r["reps"] > 0 and c and c.get("sentence"):
            out.append({"text": c["sentence"],
                        "reading": furigana_reading(c.get("sentence_furigana"))
                        if L.has_reading else "",
                        "html": furigana_html(c["sentence_furigana"])
                        if L.has_reading and c.get("sentence_furigana") else None,
                        "english": c.get("sentence_en", "")})
    return out


def begin(lines):
    ss.sp_lines, ss.sp_i = lines, 0
    ss.sp_best, ss.sp_last, ss.sp_saved = {}, {}, False


# ------------------------------------------------------------------ start screen
if ss.sp_lines is None:
    st.markdown(f'<div class="meta"><span>{L.name} speak</span>'
                f'<span class="right">listen · repeat · get scored</span></div>',
                unsafe_allow_html=True)
    ss.sp_ears = st.toggle("Ears first (hide the text until you've tried)",
                           value=ss.get("sp_ears", False))
    ss.sp_slow = st.toggle("Slower voice", value=ss.get("sp_slow", False))

    mine = vocab_lines()
    if len(mine) >= 4:
        if st.button(f"From my vocab ({len(mine)} sentences)", type="primary",
                     use_container_width=True):
            begin(random.sample(mine, min(SET_SIZE, len(mine))))
            st.rerun()
    else:
        st.caption("Once you've reviewed a few vocab cards, their example sentences "
                   "show up here for free practice.")

    if tutor.available():
        theme = st.pills("Theme", tutor.SHADOW_THEMES, default=tutor.SHADOW_THEMES[0],
                         label_visibility="collapsed")
        lvl = ss.get("sp_level") or tutor.level_for(session.words_estimate(),
                                                    L.track.current_stage(progress))
        if st.button(f"New set · level {lvl}", use_container_width=True):
            if session.tutor_allowance() <= 0:
                st.warning("That's today's tutor allowance used — it resets tomorrow.")
                st.stop()
            with st.spinner("Writing sentences…"):
                try:
                    got = tutor.shadow_lines(L, tutor.profile(L, progress, known), lvl,
                                             theme or random.choice(tutor.SHADOW_THEMES),
                                             SET_SIZE)
                    session.spend_tutor_call()
                except tutor.TutorError as e:
                    st.error(str(e))
                    st.stop()
            begin([{"text": x.text, "reading": x.reading, "html": None,
                    "english": x.english} for x in got])
            st.rerun()
    st.caption("Works in Chrome and Safari (iPhone too). The first time, allow the "
               "microphone when the browser asks.")
    st.stop()


# --------------------------------------------------------------------------- done
lines, i = ss.sp_lines, ss.sp_i
if i >= len(lines):
    scores = list(ss.sp_best.values())
    if not ss.sp_saved:
        ss.sp_saved = True
        session.log("speak", len(scores))
        session.save()
    if scores:
        avg = round(100 * sum(scores) / len(scores))
        ui.card(f'<div class="word">{avg}%</div><div class="reading">understood, on '
                f'average, over {len(scores)} sentences</div>')
    else:
        ui.card('<div class="word small">Done</div><div class="reading">nothing said '
                'out loud this time</div>')
    if st.button("Another set", type="primary", use_container_width=True):
        ss.sp_lines = None
        st.rerun()
    st.page_link("views/talk.py", label="Next: talk out loud →")
    st.stop()


# ----------------------------------------------------------------------- a line
line = lines[i]
st.progress(i / len(lines))
st.markdown(f'<div class="meta"><span>{i + 1} / {len(lines)}</span>'
            f'<span class="right">{"best " + str(round(100 * ss.sp_best[i])) + "%" if i in ss.sp_best else ""}'
            f'</span></div>', unsafe_allow_html=True)

tried = i in ss.sp_last
hide = ss.get("sp_ears") and not tried
if hide:
    ui.card('<div class="sent-en">Listen, then say what you heard.</div>', tight=True)
else:
    body = line["html"] or ui.esc(line["text"])
    sub = (f'<div class="reading" style="font-size:1rem">{ui.esc(line["reading"])}</div>'
           if line["reading"] and not line["html"] else "")
    ui.card(f'<div class="sent" style="font-size:1.5rem">{body}</div>{sub}'
            f'<div class="sent-en">{ui.esc(line["english"])}</div>', tight=True)

rate = 0.7 if ss.get("sp_slow") else 0.95
c1, c2 = st.columns(2)
with c1:
    ui.speak(line["text"], L.tts, "listen", rate=rate)
with c2:
    ui.speak(line["text"], L.tts, "slow", rate=0.55, icon="slow_motion_video")

heard = widgets.mic(L.tts, "Say it", key=f"sp_mic_{i}")
if heard:
    alts = [heard["text"]] + [a for a in heard.get("alts", []) if a != heard["text"]]
    r, tgt, said = speech.score(L.code, [line["text"], line["reading"]], alts)
    ss.sp_last[i] = {"r": r, "target": tgt, "said": said}
    ss.sp_best[i] = max(r, ss.sp_best.get(i, 0.0))
    st.rerun()

if tried:
    last = ss.sp_last[i]
    cls, msg = speech.verdict(last["r"])
    st.markdown(f'<div class="verdict {cls}">{msg} · {round(100 * last["r"])}%</div>',
                unsafe_allow_html=True)
    ui.card(f'<div class="why">Heard: {ui.esc(last["said"])}</div>'
            f'<div class="sent" style="font-size:1.15rem;text-align:left">'
            f'{speech.diff_html(L.code, last["target"], last["said"])}</div>', tight=True)

if st.button("Next" if tried else "Skip", type="primary" if tried else "secondary",
             use_container_width=True):
    ss.sp_i += 1
    st.rerun()
