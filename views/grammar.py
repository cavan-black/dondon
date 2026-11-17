"""Conjugation and pattern drills, Katsuyou-style: a word, a target form, type it.

A right answer moves straight on; a wrong one shows the answer and the rule, and the
item comes back once at the end of the round. Only the FIRST attempt counts toward the
schedule — getting it right after being shown is recall of the last ten seconds, not
of the rule.

Japanese answers can be kana, kanji or romaji (hub/ja/kana.py). Spanish answers may
start with the subject pronoun; an answer that is right except for an accent is
still a miss, but says so (hub/es/text.py). "I was right" exists for the IME picking
different kanji, or a typo you'd never make out loud — it is on your honour.
"""
import streamlit as st

from hub import grammar as G, langs, session, ui
from hub.store import today

ss = st.session_state
L = langs.get(session.lang())
T = L.track
progress = session.progress()
day = today()
known = session.known_words()
WORDS = L.words

# A round belongs to the language it was started in.
if ss.get("g_lang") != L.code:
    ss.g_mode, ss.g_lang = None, L.code


def start(lessons, items, schedule=True):
    ss.g_mode = "lesson" if lessons else "drill"
    ss.g_lessons, ss.g_lesson_i = lessons, 0
    ss.g_items, ss.g_i = items, 0
    ss.g_results = {}
    ss.g_schedule = schedule
    ss.g_feedback = None
    ss.g_flash = None
    ss.g_saved = False


def reading_of(skill, word, cue):
    if not L.has_reading:
        return ""
    w = type(word)(word.kana, word.kana, word.cls, word.meaning)
    return skill.answers(w, cue)[0]


def word_html(w):
    if L.has_reading:
        head = ui.ruby(w.label(), w.kana if w.cls != "na" else "")
    else:
        head = ui.esc(w.label())
    return (f'<div class="word small">{head}</div>'
            f'<div class="reading">{ui.esc(w.meaning)}</div>')


def chips(skills):
    return " ".join(f'<span class="chip">{ui.esc(s.shape)}</span>' for s in skills)


# ----------------------------------------------------------------------- start screen
if ss.g_mode is None:
    stage = T.current_stage(progress)
    due = T.due(progress, day)
    fresh = T.new_skills(progress)
    st.markdown(f'<div class="meta"><span>{L.name} stage {min(stage, len(T.stages))}'
                f'</span><span class="right">{T.stages.get(stage, "everything learned")}'
                f'</span></div>', unsafe_allow_html=True)
    lines = []
    if fresh:
        lines.append("New: " + chips(fresh))
    if due:
        lines.append("Due: " + chips(due))
    ui.card("<br>".join(lines) or '<div class="sent-en">Nothing new or due — today\'s '
            'round drills your weakest skills.</div>', tight=True)

    if st.button("Start today's round", type="primary", use_container_width=True):
        start(*T.build_session(progress, day, WORDS, known))
        st.rerun()

    pending = [s for s in T.skills if s.stage == stage and not T.is_learned(progress, s.key)]
    if pending:
        if st.button(f"Test out of stage {stage} ({len(pending)} skills, 4 each)",
                     use_container_width=True):
            start([], T.stage_test(progress, WORDS, known))
            st.rerun()
        st.caption("Already know these? Score 90%+ on a skill you haven't drilled here "
                   "and it's marked learned straight away.")

    with st.expander("Free practice"):
        opts = {f"{s.shape} · {s.title}": s for s in T.unlocked(progress)}
        picked = st.multiselect("Skills", list(opts), label_visibility="collapsed",
                                placeholder="Pick forms to drill")
        if picked and st.button("Drill these", use_container_width=True):
            _, items = T.build_session(progress, day, WORDS, known,
                                       only=[opts[p] for p in picked])
            start([], items, schedule=False)
            st.rerun()
        st.caption("Free practice counts toward stats but doesn't move the schedule.")
    st.stop()

# --------------------------------------------------------------------------- lessons
if ss.g_mode == "lesson":
    skill = ss.g_lessons[ss.g_lesson_i]
    st.markdown(f'<div class="meta"><span>new skill {ss.g_lesson_i + 1} / '
                f'{len(ss.g_lessons)}</span><span class="right">stage {skill.stage}</span>'
                f'</div>', unsafe_allow_html=True)
    examples, seen = [], set()
    for w in T.eligible_words(skill, WORDS):
        if w.cls in seen:
            continue
        seen.add(w.cls)
        cue = skill.cues[len(seen) % len(skill.cues)]
        who = f"({ui.esc(L.cue_label(cue, skill))}) " if cue else ""
        examples.append(f'<div class="sent">{who}{ui.esc(w.label())} → '
                        f'<b>{ui.esc(skill.answers(w, cue)[0])}</b></div>')
        if len(examples) == 4:
            break
    ui.card(f'<div class="target"><div class="jp">{ui.esc(skill.shape)}</div>'
            f'<div class="en">{ui.esc(skill.title)}</div></div>'
            f'<div class="why" style="text-align:center">{ui.esc(skill.rule)}</div>'
            f'<div class="rule"></div>{"".join(examples)}')
    if st.button("Got it", type="primary", use_container_width=True):
        ss.g_lesson_i += 1
        if ss.g_lesson_i >= len(ss.g_lessons):
            ss.g_mode = "drill"
        st.rerun()
    st.stop()

# ----------------------------------------------------------------------------- done
if ss.g_i >= len(ss.g_items):
    if not ss.g_saved:
        ss.g_saved = True
        ss.g_moves = T.record(progress, day, ss.g_results, schedule=ss.g_schedule)
        n = sum(len(v) for v in ss.g_results.values())
        session.log("grammar", n)
        session.log("grammar_right", sum(sum(v) for v in ss.g_results.values()))
        session.save()
    marks = [m for v in ss.g_results.values() for m in v]
    pct = round(100 * sum(marks) / len(marks)) if marks else 0
    ui.card(f'<div class="word">{pct}%</div>'
            f'<div class="reading">{sum(marks)} of {len(marks)} first time</div>')
    rows = []
    for key, marks_ in ss.g_results.items():
        s = T.by_key[key]
        old, new = ss.g_moves.get(key, (None, None))
        tag = ""
        if new is not None:
            tag = (" · learned :material/check_circle:" if new >= G.LEARNED_BOX > old else
                   f" · back in {G.INTERVALS[new]}d")
        rows.append(f"**{s.shape}** {s.title} — {sum(marks_)}/{len(marks_)}{tag}")
    st.markdown("  \n".join(rows))
    if ss.get("save_err"):
        st.caption(f":material/warning: progress not saved: {ss.save_err}")
    c1, c2 = st.columns(2)
    if c1.button("Another round", use_container_width=True):
        ss.g_mode = None
        st.rerun()
    with c2:
        st.page_link("views/build.py", label="Next: build sentences →")
    st.stop()

# ----------------------------------------------------------------------------- drill
item = ss.g_items[ss.g_i]
skill, word, cue = T.by_key[item["skill"]], item["word"], item.get("cue")
st.progress(min(ss.g_i / len(ss.g_items), 1.0))
st.markdown(f'<div class="meta"><span>{ss.g_i} / {len(ss.g_items)}</span>'
            f'<span class="right">{"retry" if item.get("retry") else ""}</span></div>',
            unsafe_allow_html=True)

if ss.g_flash:
    st.markdown(f'<div class="verdict ok">{ui.icon("check")} {ui.esc(ss.g_flash)}</div>',
                unsafe_allow_html=True)

who = (f'<div class="answer" style="font-size:1.3rem">{ui.esc(L.cue_label(cue, skill))}</div>'
       if cue else "")
ui.card(word_html(word) + f'<div class="target">{who}<div class="jp">'
        f'{ui.esc(skill.shape)}</div><div class="en">{ui.esc(skill.title)}</div></div>')


def mark(right):
    if not item.get("retry"):
        ss.g_results.setdefault(skill.key, []).append(right)


def miss(typed, expected, near=False):
    mark(False)
    ss.g_flash = None
    ss.g_feedback = {"typed": typed, "expected": expected, "near": near}
    if not item.get("retry"):
        ss.g_items.append({**item, "retry": True})


def advance():
    ss.g_i += 1
    ss.g_feedback = None


fb = ss.g_feedback
if fb is None:
    with st.form(f"f{ss.g_i}", clear_on_submit=True, border=False):
        typed = st.text_input("answer", label_visibility="collapsed",
                              placeholder=L.placeholder)
        sent = st.form_submit_button("Check", use_container_width=True, type="primary")
    ui.focus_input()
    if sent and typed.strip():
        ok, expected, near = G.check(skill, word, cue, typed, L.normalize, L.fold)
        if ok:
            mark(True)
            ss.g_flash = expected[0]
            advance()
        else:
            miss(typed.strip(), expected, near)
        st.rerun()
    if st.button("Show me", use_container_width=True):
        miss("", skill.answers(word, cue))
        st.rerun()
else:
    exp = fb["expected"]
    reading = reading_of(skill, word, cue)
    extra = [e for e in exp[1:] if L.normalize(e) != L.normalize(reading)][:3]
    verdict = ""
    if fb["typed"]:
        verdict = (f'<div class="verdict mid">≈ {ui.esc(fb["typed"])} — just the accent'
                   f'</div>' if fb.get("near") else
                   f'<div class="verdict no">{ui.icon("close")} {ui.esc(fb["typed"])}</div>')
    ui.card(verdict +
            f'<div class="answer">{ui.ruby(exp[0], reading)}</div>' +
            (f'<div class="sent-en">also: {", ".join(ui.esc(e) for e in extra)}</div>'
             if extra else "") +
            f'<div class="why">{ui.esc(skill.rule)}</div>', tight=True)
    ui.speak(reading or exp[0], L.tts)
    c1, c2 = st.columns(2)
    if fb["typed"] and c1.button("I was right", use_container_width=True):
        # Undo the miss and the retry it queued.
        if not item.get("retry"):
            ss.g_results[skill.key][-1] = True
            ss.g_items.pop()
        ss.g_flash = fb["typed"]
        advance()
        st.rerun()
    if c2.button("Next", type="primary", use_container_width=True):
        ss.g_flash = None
        advance()
        st.rerun()

if st.button("End round", use_container_width=True):
    ss.g_items = ss.g_items[:ss.g_i]
    ss.g_feedback = None
    st.rerun()
