"""Conversation practice — the point of everything else.

Pick a scenario and a register; the tutor stays in character and pitches its replies
at what you have learned (it is told your grammar progress and your vocabulary).
Mistakes are corrected under your message, never in the reply, so the conversation
keeps going. At the end, a debrief: recurring mistakes and phrases worth keeping.

To practise SPEAKING rather than typing, tap the microphone and answer out loud — what the phone
hears is sent as your reply — and use the speaker to hear each reply and say it back
(shadowing) before you answer.

Nothing said here is saved. Only the count of turns goes into progress.
"""
import streamlit as st

from hub import langs, session, tutor, ui, widgets

ss = st.session_state
L = langs.get(session.lang())
if not tutor.available():
    ui.card('<div class="meaning">Needs an API key</div><div class="sent-en">Add '
            'ANTHROPIC_API_KEY to the app\'s secrets to turn on conversation.</div>')
    st.stop()

progress = session.progress()
if ss.get("t_lang") != L.code:
    ss.t_system, ss.t_lang = None, L.code
SAVE_EVERY = 5


def fail(e):
    st.error(str(e))
    st.stop()


def out_of_calls():
    if session.tutor_allowance() > 0:
        return False
    st.warning("That's today's tutor allowance used — it resets tomorrow.")
    return True


# ----------------------------------------------------------------------- set up
if ss.t_system is None:
    st.markdown(f'<div class="meta"><span>{L.name} talk</span></div>',
                unsafe_allow_html=True)
    scenarios = tutor.SCENARIOS[L.code]
    scenario = st.selectbox("Scenario", list(scenarios))
    register = st.radio("Register", tutor.REGISTERS[L.code], horizontal=True, index=1)
    st.caption(scenarios[scenario])
    if st.button("Start", type="primary", use_container_width=True) and not out_of_calls():
        prof = tutor.profile(L, progress, session.known_words())
        system = tutor.talk_system(L, prof, scenario, register)
        start = {"role": "user", "content": "(Start the conversation with your first "
                                            "line. Leave the correction empty.)"}
        with st.spinner("…"):
            try:
                turn = tutor.talk(system, [start])
                session.spend_tutor_call()
            except tutor.TutorError as e:
                fail(e)
        ss.t_system = system
        # The API transcript only ever grows; display state is kept beside it.
        ss.t_history = [start, {"role": "assistant", "content": turn.model_dump_json()}]
        ss.t_view = [{"ai": turn}]
        ss.t_unsaved, ss.t_debrief = 0, None
        st.rerun()
    st.stop()

# -------------------------------------------------------------------- transcript
show_en = st.toggle("English", value=False)
for i, entry in enumerate(ss.t_view):
    if "ai" in entry:
        t = entry["ai"]
        with st.chat_message("assistant", avatar=":material/forum:"):
            st.markdown(f'<div style="font-size:1.25rem;line-height:1.8">'
                        f'{ui.esc(t.reply)}</div>', unsafe_allow_html=True)
            if show_en:
                st.caption(f"{t.reading}  \n{t.english}" if t.reading else t.english)
            if i == len(ss.t_view) - 1:
                ui.speak(t.reply, L.tts)
    else:
        with st.chat_message("user", avatar=":material/person:"):
            st.markdown(ui.esc(entry["me"]))
            c = entry.get("fix")
            if c and c.needed:
                st.markdown(f'<div class="why">{ui.icon("edit")} {ui.esc(c.corrected)}<br>'
                            f'{ui.esc(c.note)}</div>', unsafe_allow_html=True)

if ss.t_debrief:
    d = ss.t_debrief
    ui.card(f'<div class="why">{ui.esc(d.summary)}</div>' +
            "".join(f'<div class="why">{ui.icon("edit")} {ui.esc(m)}</div>' for m in d.mistakes) +
            ('<div class="rule"></div>' if d.phrases else "") +
            "".join(f'<div class="sent" style="text-align:left;font-size:1rem">'
                    f'{ui.esc(p)}</div>' for p in d.phrases), tight=True)
    if st.button("New conversation", type="primary", use_container_width=True):
        ss.t_system = None
        st.rerun()
    st.stop()

heard = widgets.mic(L.tts, "Answer out loud", key="t_mic")
said = (st.chat_input(f"{L.native}… (or English if you're stuck)")
        or (heard["text"] if heard else None))
if said and not out_of_calls():
    ss.t_history.append({"role": "user", "content": said})
    ss.t_view.append({"me": said})
    with st.spinner("…"):
        try:
            turn = tutor.talk(ss.t_system, ss.t_history)
            session.spend_tutor_call()
        except tutor.TutorError as e:
            # Leave the transcript well-formed: drop the unanswered message so the
            # next attempt doesn't send two user turns in a row.
            ss.t_history.pop()
            ss.t_view.pop()
            fail(e)
    ss.t_history.append({"role": "assistant", "content": turn.model_dump_json()})
    ss.t_view[-1]["fix"] = turn.correction
    ss.t_view.append({"ai": turn})
    session.log("talk")
    ss.t_unsaved += 1
    if ss.t_unsaved >= SAVE_EVERY:
        ss.t_unsaved = 0
        session.save()
    st.rerun()

turns = sum(1 for e in ss.t_view if "me" in e)
if turns and st.button(f"End & debrief ({turns} turns)", use_container_width=True):
    if not out_of_calls():
        with st.spinner("Looking back over it…"):
            try:
                ss.t_debrief = tutor.debrief(ss.t_system, ss.t_history)
                session.spend_tutor_call()
            except tutor.TutorError as e:
                fail(e)
        session.save()
        st.rerun()
