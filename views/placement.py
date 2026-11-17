"""Find my level: the placement test (hub/placement.py) as one sitting.

Script, then vocab, then grammar, each part ending at its ceiling. Answers aren't
marked as you go — a placement test that teaches you the answers places you too
high — so a part's verdict only shows at the end, with what it changed.
"""
import random

import streamlit as st

from hub import basics as B, langs, placement as P, session, srs, stats, ui
from hub.grammar import check
from hub.store import today

ss = st.session_state
L = langs.get(session.lang())
T = L.track
progress = session.progress()
email = session.email()
ls = session.lang_settings()
day = today()
rng = random.Random()

st.markdown("""<style>
  .st-key-pl_opts .stButton > button {height: auto; min-height: 3.3rem;
      padding: 0.7rem 1rem; text-align: left; justify-content: flex-start;
      font-weight: 500; line-height: 1.35;}
  .st-key-pl_opts .stButton > button p {text-align: left;}
  .parts {display: flex; gap: 0.4rem; margin: 0.2rem 0 0.6rem;}
  .parts span {flex: 1; text-align: center; font-size: 0.7rem; font-weight: 600;
               letter-spacing: 0.06em; text-transform: uppercase; color: var(--muted);
               padding-top: 0.45rem; border-top: 3px solid var(--track);}
  .parts span.on {color: var(--fg); border-color: var(--accent);}
  .parts span.done {border-color: var(--ok);}
</style>""", unsafe_allow_html=True)

if ss.get("pl_lang") != L.code:
    ss.pl, ss.pl_lang = None, L.code

tiers = srs.tiers(L.code)
has_vocab = bool(tiers)
needs_script = not B.status(L.code, progress)["done"]


def parts_bar(now):
    names = (["script"] if needs_script else []) + (["vocab"] if has_vocab else [])         + ["grammar"]
    label = {"script": "Kana" if L.code == "ja" else "Sounds",
             "vocab": "Words", "grammar": "Grammar"}
    at = names.index(now)
    out = "".join(f'<span class="{"done" if k < at else "on" if k == at else ""}">'
                  f'{label[n]}</span>' for k, n in enumerate(names))
    st.markdown(f'<div class="parts">{out}</div>', unsafe_allow_html=True)


def begin():
    ss.pl = {"result": {"script": None, "bands": [], "stages": []}, "phase": None}
    if needs_script:
        start_script()
    elif has_vocab:
        start_vocab()
    else:
        start_grammar()


def start_script():
    ss.pl.update(phase="script", items=P.script_items(L.code, rng), i=0, marks=[])


def start_vocab():
    cards = [(t, srs.deck(L.code, t)["cards"]) for t in tiers]
    ss.pl.update(phase="vocab", bands=P.bands(cards), band=0, scores=[])
    next_band()


def next_band():
    b = ss.pl["bands"][ss.pl["band"]]
    ss.pl.update(items=P.vocab_items(b[1], rng), i=0, marks=[])


def start_grammar():
    ss.pl.update(phase="grammar", stage=min(T.stages))
    next_stage()


def next_stage():
    ss.pl.update(items=P.stage_items(T, ss.pl["stage"], L.words, session.known_words(),
                                     rng), i=0, marks=[])


def after_script():
    marks = ss.pl["marks"]
    score = sum(marks) / len(marks) if marks else 0.0
    ss.pl["result"]["script"] = score
    if L.code == "ja" and score < P.SCRIPT_FLOOR:
        finish()                      # no kana yet: the rest can't be read
    elif has_vocab:
        start_vocab()
    else:
        start_grammar()


def after_band():
    pl = ss.pl
    marks = pl["marks"]
    tier, cards = pl["bands"][pl["band"]]
    known = P.band_known(sum(marks), len(marks))
    pl["scores"].append(known)
    pl["result"]["bands"].append((tier, len(cards), known))
    pl["band"] += 1
    if P.vocab_done(pl["scores"]) or pl["band"] >= len(pl["bands"]):
        start_grammar()
    else:
        next_band()


def after_stage():
    pl = ss.pl
    if P.stage_passed(pl["marks"]):
        pl["result"]["stages"].append(pl["stage"])
        later = [n for n in sorted(T.stages) if n > pl["stage"]]
        if later:
            pl["stage"] = later[0]
            next_stage()
            return
    finish()


def finish():
    rows = list(srs.rows(email, L.code).values()) if has_vocab else []
    before = stats.standing(session.words_estimate(), T.current_stage(progress) - 1,
                            len(T.stages))["level"]
    sizes = {t: len(srs.deck(L.code, t)["cards"]) for t in tiers}
    placed = P.apply(L.code, T, progress, ls, ss.pl["result"], day, rows, sizes)
    session.save()
    session.save_settings()
    st.session_state.pop(f"vq_{L.code}", None)          # rebuild today's vocab queue
    ss.pl.update(phase="done", placed=placed, before=before)


def answer(right):
    ss.pl["marks"].append(bool(right))
    ss.pl["i"] += 1
    if ss.pl["i"] >= len(ss.pl["items"]):
        {"script": after_script, "vocab": after_band, "grammar": after_stage}[ss.pl["phase"]]()


# ---------------------------------------------------------------------- intro
if ss.pl is None:
    st.markdown(f'<div class="hello"><span class="hi">Find your level</span>'
                f'<span class="on">{L.name}</span></div>', unsafe_allow_html=True)
    steps = []
    if needs_script:
        steps.append(("abc", "Kana" if L.code == "ja" else "Sounds",
                      "A dozen hiragana and katakana to type in romaji." if L.code == "ja"
                      else "A dozen words to write down from dictation."))
    if has_vocab:
        steps.append(("style", "Words", "Pick the meaning, most common words first. "
                      "It stops when the words get unfamiliar."))
    steps.append(("repeat", "Grammar", "Conjugate a word into a form, stage by stage, "
                  "until a stage trips you up."))
    rows = "".join(f'<div class="task" style="margin-bottom:0.45rem"><div class="ico">'
                   f'{ui.icon(i)}</div><div class="body"><div class="name">{n}</div>'
                   f'<div class="sub" style="white-space:normal;margin-bottom:0">{d}</div>'
                   f'</div></div>' for i, n, d in steps)
    st.markdown(rows, unsafe_allow_html=True)
    st.caption("About 5 minutes for a beginner, up to 15 if you know a lot. Guessing "
               "places you too high, so pick “I don't know” when you don't. Answers "
               "aren't marked as you go; you'll see the result at the end. It only ever "
               "moves you forward: nothing you've already done here is taken away.")
    if st.button("Start", type="primary", use_container_width=True):
        begin()
        st.rerun()
    if not progress.get("placement") and st.button("Skip it and start from the beginning",
                                                   use_container_width=True):
        P.skip(progress, day)
        session.save()
        st.switch_page("views/today.py")
    st.stop()

pl = ss.pl

# ----------------------------------------------------------------------- done
if pl["phase"] == "done":
    placed, res = pl["placed"], pl["result"]
    n = len(T.stages)
    words = session.words_estimate()
    stage = T.current_stage(progress)
    s = stats.standing(words, stage - 1, n)
    lv = s["level"]
    up = lv.n > pl["before"].n
    ui.panel(f'<div class="hero">{ui.ring(lv.n / len(stats.LEVELS), lv.n, "level")}'
             f'<div class="side"><div class="eyebrow">{"you start at" if up else "you are"}'
             f'</div><div class="title">{ui.esc(lv.name)}</div>'
             f'<div class="note" style="margin:0">{ui.esc(lv.can)}.</div></div></div>')

    changes = []
    if res["script"] is not None:
        pct = round(100 * res["script"])
        if res["script"] >= P.SCRIPT_PASS:
            changes.append(("check_circle", f"{'Kana' if L.code == 'ja' else 'Sounds'}: "
                            f"{pct}%. Basics is marked done; it's still there to review."))
        elif L.code == "ja" and res["script"] < P.SCRIPT_FLOOR:
            changes.append(("abc", f"Kana: {pct}%. Start with Basics: the rest of the "
                            "test needs kana, so it stopped there. Take it again once "
                            "you can read them."))
        else:
            changes.append(("abc", f"{'Kana' if L.code == 'ja' else 'Sounds'}: {pct}%. "
                            "Basics stays on your plan to fill the gaps."))
    if res["bands"]:
        est = sum(round(size * k) for _, size, k in res["bands"])
        t, i = placed.get("start_tier"), placed.get("start_index", 0)
        first = (t - 1) * srs.TIER_SIZE + i + 1 if t else 0
        changes.append(("style", f"Words: about {est:,} of the most common known. New "
                        f"cards start at word {first:,}, in tier {t}; the ones before it "
                        f"are skipped." if t and first > 1 else
                        f"Words: about {est:,} known. New cards start from the most "
                        f"common word." if t else f"Words: about {est:,} known."))
    if res["stages"]:
        top = max(res["stages"])
        changes.append(("repeat", f"Grammar: stages 1–{top} passed, up to "
                        f"{T.stages[top]}. Those skills come back for a check in a week, "
                        f"so a lucky guess gets caught."))
    elif res["script"] is None or res["script"] >= P.SCRIPT_FLOOR or L.code != "ja":
        changes.append(("repeat", f"Grammar: start at stage 1, {T.stages[min(T.stages)]}."))
    if s["next"]:
        changes.append(("trending_up", f"Next: {s['next'].name}. Progress shows what it "
                        f"needs and when you'll get there."))
    st.markdown("".join(
        f'<div class="row" style="align-items:flex-start;margin-top:0.8rem">'
        f'<div style="flex:none;color:var(--accent)">{ui.icon(i)}</div>'
        f'<div style="flex:1;font-size:0.9rem;line-height:1.5;color:var(--fg)">'
        f'{ui.esc(t)}</div></div>' for i, t in changes), unsafe_allow_html=True)
    st.write("")
    if st.button("Go to today's plan", type="primary", use_container_width=True):
        ss.pl = None
        st.switch_page("views/today.py")
    st.stop()

# -------------------------------------------------------------------- a question
items, i = pl["items"], pl["i"]
parts_bar(pl["phase"])
if pl["phase"] == "vocab":
    tier, cards = pl["bands"][pl["band"]]
    first = (pl["band"]) * P.BAND + 1
    right = f"words {first:,}–{first + len(cards) - 1:,}"
elif pl["phase"] == "grammar":
    right = f"stage {pl['stage']} · {T.stages[pl['stage']]}"
else:
    right = f"{i + 1} of {len(items)}"
st.markdown(f'<div class="meta"><span>{pl["phase"] if pl["phase"] != "script" else "basics"}'
            f'</span><span class="right">{ui.esc(right)}</span></div>',
            unsafe_allow_html=True)
st.progress(i / len(items))

q = items[i]
key = f"pl_{pl['phase']}_{pl.get('band', 0)}_{pl.get('stage', 0)}_{i}"

if pl["phase"] == "script":
    item = B.items(L.code)[q["item"]]
    if q["mode"] == "type":
        ui.card(f'<div class="word">{ui.esc(item.text)}</div>'
                f'<div class="target"><div class="en">type how it reads</div></div>')
    else:
        ui.card(f'<div class="word small">{ui.icon("volume_up")}</div><div class="target">'
                f'<div class="en">listen, then type what you hear</div></div>', tight=True)
        a, b = st.columns(2)
        with a:
            ui.speak(item.say, L.tts, "play", rate=0.9)
        with b:
            ui.speak(item.say, L.tts, "slowly", rate=0.55, icon="slow_motion_video")
    with st.form(key, clear_on_submit=True, border=False):
        typed = st.text_input("answer", label_visibility="collapsed",
                              placeholder="romaji" if L.code == "ja" else "escríbelo")
        sent = st.form_submit_button("Next", use_container_width=True, type="primary")
    ui.focus_input()
    if sent:
        ok = bool(typed.strip()) and B.check(L.code, q, typed.strip())[0]
        answer(ok)
        st.rerun()
    if st.button("I don't know", use_container_width=True, key=key + "_x"):
        answer(False)
        st.rerun()

elif pl["phase"] == "vocab":
    ui.card(f'<div class="word small">{ui.esc(q["word"])}</div>'
            f'<div class="target"><div class="en">what does it mean?</div></div>',
            tight=True)
    with st.container(key="pl_opts"):
        for j, opt in enumerate(q["options"]):
            if st.button(opt, key=f"{key}_{j}", use_container_width=True):
                answer(opt == q["answer"])
                st.rerun()
    if st.button("I don't know", key=key + "_x", use_container_width=True):
        answer(False)
        st.rerun()

else:
    skill, word, cue = T.by_key[q["skill"]], q["word"], q.get("cue")
    head = (ui.ruby(word.label(), word.kana if word.cls != "na" else "")
            if L.has_reading else ui.esc(word.label()))
    who = (f'<div class="answer" style="font-size:1.3rem">'
           f'{ui.esc(L.cue_label(cue, skill))}</div>' if cue else "")
    ui.card(f'<div class="word small">{head}</div>'
            f'<div class="reading">{ui.esc(word.meaning)}</div>'
            f'<div class="target">{who}<div class="jp">{ui.esc(skill.shape)}</div>'
            f'<div class="en">{ui.esc(skill.title)}</div></div>')
    with st.form(key, clear_on_submit=True, border=False):
        typed = st.text_input("answer", label_visibility="collapsed",
                              placeholder=L.placeholder)
        sent = st.form_submit_button("Next", use_container_width=True, type="primary")
    ui.focus_input()
    if sent:
        ok = bool(typed.strip()) and check(skill, word, cue, typed, L.normalize, L.fold)[0]
        answer(ok)
        st.rerun()
    if st.button("I haven't learned this", use_container_width=True, key=key + "_x"):
        answer(False)
        st.rerun()

st.write("")
if st.button("Stop here and see my level", use_container_width=True, key=key + "_end"):
    finish()
    st.rerun()
