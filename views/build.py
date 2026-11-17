"""Sentence building: the step between conjugating a word and holding a conversation.

You get English sentences that need the grammar you have been drilling, built from
vocabulary you know, and translate them. Claude grades each one — right, nearly, or
wrong — and shows the smallest fix to what you wrote alongside how a native speaker
would say it. Seeing both matters: the fix teaches the rule you broke, the natural
version teaches what to aim for.
"""
import streamlit as st

from hub import langs, session, tutor, ui

ss = st.session_state
L = langs.get(session.lang())
if not tutor.available():
    ui.card('<div class="meaning">Needs an API key</div><div class="sent-en">Add '
            'ANTHROPIC_API_KEY to the app\'s secrets to turn on sentence building.</div>')
    st.stop()

progress = session.progress()
if ss.get("b_lang") != L.code:
    ss.b_set, ss.b_lang = None, L.code


def out_of_calls():
    if session.tutor_allowance() > 0:
        return False
    st.warning("That's today's tutor allowance used — it resets tomorrow.")
    return True


def new_set():
    if out_of_calls():
        return
    targets = tutor.pick_targets(L.track, progress)
    with st.spinner("Writing sentences for you…"):
        try:
            prof = tutor.profile(L, progress, session.known_words())
            ss.b_set = tutor.build_prompts(L, prof, targets)
            session.spend_tutor_call()
            ss.b_prof = prof
            ss.b_i, ss.b_grades, ss.b_saved = 0, [], False
        except tutor.TutorError as e:
            st.error(str(e))


if ss.b_set is None:
    st.markdown(f'<div class="meta"><span>{L.name} build</span></div>',
                unsafe_allow_html=True)
    ui.card(f'<div class="sent-en">Five sentences that need the grammar you\'ve been '
            f'drilling. Translate each into {L.name}.</div>', tight=True)
    if st.button("Start", type="primary", use_container_width=True):
        new_set()
        st.rerun()
    st.stop()

prompts = ss.b_set

# ----------------------------------------------------------------------------- done
if ss.b_i >= len(prompts):
    if not ss.b_saved:
        ss.b_saved = True
        session.log("build", len(ss.b_grades))
        session.save()
    score = {"correct": 1, "almost": 0.5, "wrong": 0}
    total = sum(score[g.verdict] for g in ss.b_grades)
    ui.card(f'<div class="word">{total:g} / {len(prompts)}</div>'
            f'<div class="reading">sentences built</div>')
    for p, g in zip(prompts, ss.b_grades):
        st.markdown(f"**{p.english}**  \n{g.natural}")
    c1, c2 = st.columns(2)
    if c1.button("Five more", use_container_width=True):
        new_set()
        st.rerun()
    with c2:
        st.page_link("views/talk.py", label="Next: talk →")
    st.stop()

# ------------------------------------------------------------------------- sentence
p = prompts[ss.b_i]
st.progress(ss.b_i / len(prompts))
st.markdown(f'<div class="meta"><span>{ss.b_i + 1} / {len(prompts)}</span>'
            f'<span class="right">{ui.esc(p.target)}</span></div>', unsafe_allow_html=True)
ui.card(f'<div class="meaning">{ui.esc(p.english)}</div>' +
        (f'<div class="sent-en">{ui.esc(p.hint)}</div>' if p.hint else ""))

graded = len(ss.b_grades) > ss.b_i
if not graded:
    with st.form(f"b{ss.b_i}", border=False):
        typed = st.text_area(L.name, label_visibility="collapsed", height=90,
                             placeholder=f"{L.native}…")
        sent = st.form_submit_button("Check", type="primary", use_container_width=True)
    if sent and typed.strip() and not out_of_calls():
        with st.spinner("Checking…"):
            try:
                g = tutor.grade(L, ss.b_prof, p, typed.strip())
                session.spend_tutor_call()
                ss.b_grades.append(g)
                ss.b_typed = typed.strip()
            except tutor.TutorError as e:
                st.error(str(e))
                st.stop()
        st.rerun()
else:
    g = ss.b_grades[ss.b_i]
    cls, word = {"correct": ("ok", "Correct"), "almost": ("mid", "Almost"),
                 "wrong": ("no", "Not quite")}[g.verdict]
    word = (ui.icon("check") if cls == "ok" else ui.icon("close") if cls == "no"
            else "≈") + " " + word
    parts = [f'<div class="verdict {cls}">{word}</div>',
             f'<div class="sent-en">you: {ui.esc(ss.b_typed)}</div>']
    if g.verdict != "correct" and g.corrected != ss.b_typed:
        parts.append(f'<div class="sent">{ui.esc(g.corrected)}</div>')
    parts += ['<div class="rule"></div>',
              '<div class="sent-en">natural</div>'
              f'<div class="sent">{ui.esc(g.natural)}</div>' +
              (f'<div class="sent-en">{ui.esc(g.reading)}</div>' if g.reading else ""),
              f'<div class="why">{ui.esc(g.feedback)}</div>']
    ui.card("".join(parts), tight=True)
    ui.speak(g.natural, L.tts, "hear it")
    if st.button("Next", type="primary", use_container_width=True):
        ss.b_i += 1
        st.rerun()
