"""Basics: kana for Japanese, letters, sounds and stress for Spanish — the course is in
hub/basics.py, with the content in hub/ja/kana_course.py and hub/es/sounds.py.

A unit is a lesson card (a chart you can tap to hear), then a drill round in the
grammar page's style: right answers move straight on, misses show the answer and come
back once at the end, and only first attempts count. 90% on the unit's own items
passes it and opens the next.
"""
import json

import streamlit as st

from hub import basics as B, langs, session, ui

ss = st.session_state
L = langs.get(session.lang())
C = B.course(L.code)
progress = session.progress()
UNITS = B.by_key(L.code)
ITEMS = B.items(L.code)

st.markdown("""<style>
  .st-key-b_opts .stButton > button {height: 4.2rem; font-size: 1.9rem; font-weight: 500;}
  .st-key-b_syl .stButton > button {font-size: 1.3rem;}
  .unit {display: flex; justify-content: space-between; align-items: center; gap: .6rem;
         padding: .55rem .2rem; border-bottom: 1px solid var(--line);}
  .unit .t {color: var(--fg); font-weight: 600; font-size: .95rem;}
  .unit .s {color: var(--muted); font-size: .85rem;}
  .unit.locked .t, .unit.locked .s {opacity: .45;}
</style>""", unsafe_allow_html=True)

if ss.get("b_lang") != L.code:
    ss.b_mode, ss.b_lang = None, L.code


def start(drills, unit_key=None, lesson=True):
    ss.b_unit = unit_key
    ss.b_mode = "lesson" if (unit_key and lesson) else "drill"
    ss.b_items, ss.b_i = drills, 0
    ss.b_results = []
    ss.b_feedback = ss.b_flash = None
    ss.b_saved = False
    ss.b_ended = False          # "End round" — a part-round can't pass a unit


def chart(unit):
    """Every item in a grid; tap one to hear it. One frame for the whole grid —
    a ui.speak per tile would be dozens of frames."""
    tiles = [{"t": i.text, "r": i.answers[0] if L.code == "ja" else "",
              "h": i.hint, "s": i.say} for i in unit.items]
    wide = any(len(i.text) > 3 for i in unit.items)
    rows = -(-len(tiles) // (2 if wide else 5))
    height = rows * (64 if wide else 92) + 8
    st.iframe(f"""
      <style>
        html,body{{margin:0;background:transparent;font-family:-apple-system,
          'Hiragino Sans','Noto Sans JP',sans-serif;overflow:hidden}}
        .g{{display:grid;grid-template-columns:repeat({2 if wide else 5},1fr);gap:6px}}
        .c{{background:#13151c;border:1px solid #252938;border-radius:12px;
            color:#eceef5;text-align:center;padding:6px 2px;cursor:pointer;
            user-select:none}}
        .c:active{{border-color:#8b9dff}}
        .k{{font-size:{22 if wide else 30}px;line-height:1.3}}
        .r{{font-size:12px;color:#8d94a8}}
      </style>
      <div class="g" id="g"></div>
      <script>
        const T = {json.dumps(tiles)};
        const g = document.getElementById('g');
        T.forEach(x => {{
          const d = document.createElement('div'); d.className = 'c';
          d.innerHTML = '<div class="k"></div><div class="r"></div>';
          d.children[0].textContent = x.t;
          d.children[1].textContent = x.r || x.h;
          d.onclick = () => {{
            const u = new SpeechSynthesisUtterance(x.s); u.lang = '{L.tts}'; u.rate = 0.8;
            const v = speechSynthesis.getVoices().find(v => v.lang.startsWith('{L.tts[:2]}'));
            if (v) u.voice = v;
            speechSynthesis.cancel(); speechSynthesis.speak(u);
          }};
          g.appendChild(d);
        }});
      </script>""", height=height)


# ----------------------------------------------------------------------- start screen
if ss.b_mode is None:
    stat = B.status(L.code, progress)
    st.markdown(f'<div class="meta"><span>{L.name} basics</span><span class="right">'
                f'{stat["units_done"]} of {stat["units_total"]} units</span></div>',
                unsafe_allow_html=True)
    st.progress(stat["units_done"] / stat["units_total"])

    if stat["skipped"]:
        ui.card('<div class="meaning">Skipped</div><div class="sent-en">You marked the '
                'basics as known. Every unit is open for practice.</div>', tight=True)
    elif stat["done"]:
        ui.card(f'<div class="meaning">{ui.icon("check_circle")} Basics done</div>'
                '<div class="sent-en">Keep them '
                'fresh with a review now and then.</div>', tight=True)
    else:
        nxt = UNITS[stat["next_key"]]
        ui.card(f'<div class="sent-en">Next up</div><div class="meaning">'
                f'{ui.esc(nxt.title)}</div><div class="reading">{ui.esc(nxt.sub)}</div>',
                tight=True)
        if st.button("Start next unit", type="primary", use_container_width=True):
            start(B.build_round(L.code, progress, nxt.key), nxt.key)
            st.rerun()

    if B.learned_items(L.code, progress):
        if st.button("Practise all learned", use_container_width=True):
            start(B.build_review(L.code, progress))
            st.rerun()

    rows = []
    for u, state_ in B.unit_states(L.code, progress):
        mark = ui.icon({"passed": "check_circle", "current": "play_arrow",
                        "locked": "lock"}[state_], fill=state_ != "locked")
        rows.append(f'<div class="unit{" locked" if state_ == "locked" else ""}"><div>'
                    f'<div class="t">{ui.esc(u.title)}</div><div class="s">'
                    f'{ui.esc(u.sub)}</div></div><div>{mark}</div></div>')
    with st.expander("All units", expanded=not stat["done"]):
        st.markdown("".join(rows), unsafe_allow_html=True)
        open_ = [u for u, s in B.unit_states(L.code, progress) if s != "locked"]
        if len(open_) > 1:
            pick = st.selectbox("Redo a unit", [u.key for u in open_],
                                format_func=lambda k: UNITS[k].title,
                                index=len(open_) - 1)
            if st.button("Open this unit", use_container_width=True):
                start(B.build_round(L.code, progress, pick), pick)
                st.rerun()

    if stat["skipped"]:
        if st.button("Take the course after all", use_container_width=True):
            B.unskip(L.code, progress)
            session.save()
            st.rerun()
    elif not stat["done"]:
        what = "kana" if L.code == "ja" else "Spanish sounds"
        if st.button(f"I already know my {what} — skip Basics", use_container_width=True):
            B.skip(L.code, progress)
            session.save()
            st.rerun()
    st.stop()

# --------------------------------------------------------------------------- lesson
if ss.b_mode == "lesson":
    u = UNITS[ss.b_unit]
    st.markdown(f'<div class="meta"><span>lesson</span><span class="right">'
                f'{ui.esc(u.title)}</span></div>', unsafe_allow_html=True)
    ui.card(f'<div class="target"><div class="jp">{ui.esc(u.sub)}</div>'
            f'<div class="en">{ui.esc(u.title)}</div></div>'
            f'<div class="why">{ui.esc(u.intro)}</div>', tight=True)
    if u.chart:
        st.caption("Tap any tile to hear it.")
        chart(u)
    else:
        sample = u.items[:6]
        ui.card("".join(f'<div class="sent">{ui.esc(i.text)} '
                        f'<span class="sent-en">{ui.esc(i.answers[0])} · '
                        f'{ui.esc(i.hint)}</span></div>' for i in sample), tight=True)
    if any(i.hint for i in u.items) and L.code == "ja" and u.chart:
        with st.expander("Memory hooks"):
            st.markdown("  \n".join(f"**{i.text}** {i.answers[0]} — {i.hint}"
                                    for i in u.items if i.hint))
    if st.button("Start the drill", type="primary", use_container_width=True):
        ss.b_mode = "drill"
        st.rerun()
    if st.button("Back", use_container_width=True):
        ss.b_mode = None
        st.rerun()
    st.stop()

# ----------------------------------------------------------------------------- done
if ss.b_i >= len(ss.b_items):
    if not ss.b_saved:
        ss.b_saved = True
        ss.b_outcome = B.record(L.code, progress, ss.b_results,
                                None if ss.b_ended else ss.b_unit)
        session.log("basics", len(ss.b_results))
        session.save()
    out = ss.b_outcome
    marks = [r[2] for r in ss.b_results]
    ui.card(f'<div class="word">{round(100 * out["pct"])}%</div>'
            f'<div class="reading">{sum(marks)} of {len(marks)} first time</div>')
    nxt = B.status(L.code, progress)
    if ss.b_unit:
        u = UNITS[ss.b_unit]
        if out["passed"]:
            st.success(f"{u.title} passed", icon=":material/check_circle:")
        elif ss.b_ended:
            st.info(f"Round ended early — finish a whole round of {u.title} to pass it.")
        else:
            st.info(f"{round(100 * out['unit_pct'])}% on {u.title} — "
                    f"{round(100 * B.PASS)}% passes it. Another go?")
    if ss.get("save_err"):
        st.caption(f":material/warning: progress not saved: {ss.save_err}")
    if ss.b_unit and not out["passed"]:
        if st.button("Try again", type="primary", use_container_width=True):
            start(B.build_round(L.code, progress, ss.b_unit), ss.b_unit, lesson=False)
            st.rerun()
    elif not nxt["done"]:
        if st.button(f"Next: {nxt['next_unit']}", type="primary", use_container_width=True):
            start(B.build_round(L.code, progress, nxt["next_key"]), nxt["next_key"])
            st.rerun()
    if st.button("Back to Basics", use_container_width=True):
        ss.b_mode = None
        st.rerun()
    st.stop()

# ----------------------------------------------------------------------------- drill
d = ss.b_items[ss.b_i]
item = ITEMS[d["item"]]
st.progress(min(ss.b_i / len(ss.b_items), 1.0))
st.markdown(f'<div class="meta"><span>{ss.b_i} / {len(ss.b_items)}</span>'
            f'<span class="right">{"review" if d["review"] else ""}'
            f'{" · retry" if d.get("retry") else ""}</span></div>', unsafe_allow_html=True)
if ss.b_flash:
    st.markdown(f'<div class="verdict ok">{ui.icon("check")} {ui.esc(ss.b_flash)}</div>',
                unsafe_allow_html=True)


def mark(ok):
    if not d.get("retry"):
        ss.b_results.append((item.id, d["unit"], ok, d["review"]))


def advance(flash=None):
    ss.b_i += 1
    ss.b_feedback = None
    ss.b_flash = flash


def answered(answer, shown):
    ok, near, expected, note = B.check(L.code, d, answer)
    if ok and not note:
        mark(True)
        ui.swoosh()
        advance(f"{item.text} · {item.answers[0]}" if L.code == "ja" else item.text)
        return
    mark(ok)
    if not ok and not d.get("retry"):
        ss.b_items.append({**d, "retry": True})
    ss.b_feedback = {"shown": shown, "ok": ok, "near": near, "note": note}


fb = ss.b_feedback
mode = d["mode"]
if fb is None:
    if mode == "type":
        ui.card(f'<div class="word">{ui.esc(item.text)}</div>'
                f'<div class="target"><div class="en">type how it reads</div></div>')
    elif mode == "pick":
        ui.card(f'<div class="word small">{ui.esc(item.answers[0])}</div>'
                f'<div class="target"><div class="en">which one is it?</div></div>',
                tight=True)
        ui.speak(item.say, L.tts, rate=0.8)
    elif mode == "dictate":
        ui.card(f'<div class="word small">{ui.icon("volume_up")}</div>'
                '<div class="target"><div class="en">'
                'listen, then type what you hear</div></div>', tight=True)
        a, b = st.columns(2)
        with a:
            ui.speak(item.say, L.tts, "play", rate=0.9)
        with b:
            ui.speak(item.say, L.tts, "slowly", rate=0.55, icon="slow_motion_video")
    else:                                                          # stress
        ui.card(f'<div class="word small">{ui.esc(item.text)}</div>'
                f'<div class="target"><div class="en">which syllable is stressed?'
                f'</div></div>', tight=True)

    if mode in ("type", "dictate"):
        with st.form(f"bf{ss.b_i}", clear_on_submit=True, border=False):
            typed = st.text_input("answer", label_visibility="collapsed",
                                  placeholder=("romaji or kana" if L.code == "ja"
                                               else "escríbelo"))
            sent = st.form_submit_button("Check", use_container_width=True, type="primary")
        ui.focus_input()
        if sent and typed.strip():
            answered(typed.strip(), typed.strip())
            st.rerun()
        if st.button("Show me", use_container_width=True):
            mark(False)
            if not d.get("retry"):
                ss.b_items.append({**d, "retry": True})
            ss.b_feedback = {"shown": "", "ok": False, "near": False, "note": ""}
            st.rerun()
    elif mode == "pick":
        with st.container(key="b_opts"):
            opts = d["options"]
            for row in range(0, len(opts), 2):
                cols = st.columns(2)
                for j, opt in enumerate(opts[row:row + 2]):
                    if cols[j].button(opt, key=f"b_o{ss.b_i}_{row + j}",
                                      use_container_width=True):
                        answered(opt, opt)
                        st.rerun()
    else:
        with st.container(key="b_syl"):
            cols = st.columns(len(item.syllables))
            for j, syl in enumerate(item.syllables):
                if cols[j].button(syl, key=f"b_s{ss.b_i}_{j}", use_container_width=True):
                    answered(j, syl)
                    st.rerun()
else:
    if fb["ok"]:
        verdict = f'<div class="verdict ok">{ui.icon("check")} {ui.esc(fb["note"])}</div>'
    elif fb["near"]:
        verdict = (f'<div class="verdict mid">≈ {ui.esc(fb["shown"])} — just the accent'
                   f'</div>')
    elif fb["shown"]:
        verdict = f'<div class="verdict no">{ui.icon("close")} {ui.esc(fb["shown"])}</div>'
    else:
        verdict = ""
    if mode == "stress":
        body = " · ".join(f"<b>{ui.esc(s.upper())}</b>" if j == item.stress else ui.esc(s)
                          for j, s in enumerate(item.syllables))
    elif L.code == "ja":
        body = f'{ui.esc(item.text)} <span class="reading">{ui.esc(item.answers[0])}</span>'
    else:
        body = ui.esc(item.text)
    ui.card(verdict + f'<div class="answer">{body}</div>' +
            (f'<div class="sent-en">{ui.esc(item.hint)}</div>' if item.hint else ""),
            tight=True)
    ui.speak(item.say, L.tts)
    c1, c2 = st.columns(2)
    if fb["shown"] and not fb["ok"] and mode in ("type", "dictate") and \
            c1.button("I was right", use_container_width=True):
        if not d.get("retry"):
            ss.b_results[-1] = (item.id, d["unit"], True, d["review"])
            ss.b_items.pop()
        advance(fb["shown"])
        st.rerun()
    if c2.button("Next", type="primary", use_container_width=True):
        advance()
        st.rerun()

if st.button("End round", use_container_width=True):
    ss.b_items = ss.b_items[:ss.b_i]
    ss.b_feedback = None
    ss.b_ended = True
    st.rerun()
