"""Review the owner's own Anki collection from the phone (Japanese, owner only).

This page NEVER schedules anything. It shows the cards export_due.py put in
data/due.json, records which button was pressed and how long the card took, and writes
that list back to the repo. import_reviews.py then replays those answers through Anki's
own scheduler on the desktop. Keeping the scheduling on one side of the wire is what
makes it safe to review here: the worst a bad session can do is record answers, never
corrupt intervals.

GRADING IS BINARY, the way Migaku does it: you either got it or you didn't. AGAIN sends
Anki's ease 1, GOT IT sends 3 (Good); Hard and Easy are never emitted. If you want the
full scale for a session, do it on the desktop — the collection is the same one.

The deck's audio is not published (see export_due.py). The speaker button reads the word
and sentence with the phone's own Japanese voice instead.
"""
import json, os, time

import streamlit as st

from hub import session, store, ui

DUE = os.path.join(store.ROOT, "data", "due.json")
SAVE_EVERY = 10          # answers between pushes; a crash costs at most this many

AGAIN, GOOD = 1, 3       # Anki ease values; the only two this app ever records
RATINGS = [("Again", AGAIN), ("Got it", GOOD)]


@st.cache_data
def load_due():
    if not os.path.exists(DUE):
        return None
    with open(DUE, encoding="utf-8") as fh:
        return json.load(fh)


due = load_due()
if not due or not due.get("cards"):
    ui.card('<div class="meaning">Nothing due</div>'
            '<div class="sent-en">Run <code>python export_due.py</code> on the laptop, '
            'then push.</div>')
    st.stop()

cards = due["cards"]
ss = st.session_state
ss.setdefault("v_i", 0)
ss.setdefault("v_answers", [])
ss.setdefault("v_revealed", False)
ss.setdefault("v_shown_at", time.time())
ss.setdefault("v_saved_upto", 0)
ss.setdefault("v_save_err", None)


def save(force=False):
    n = len(ss.v_answers)
    if not force and n - ss.v_saved_upto < SAVE_EVERY:
        return
    ok, err = store.write_json("data/reviews.json",
                               {"batch_id": due["batch_id"], "answers": ss.v_answers},
                               f"reviews: {n} answers ({due['batch_id']})")
    ss.v_saved_upto = n if ok else ss.v_saved_upto
    ss.v_save_err = None if ok else err


def answer(rating):
    if rating == GOOD:
        ui.swoosh()
    card = cards[ss.v_i]
    ss.v_answers.append({
        "card_id": card["card_id"],
        "rating": rating,
        "ms": int((time.time() - ss.v_shown_at) * 1000),
        "at": int(time.time()),
    })
    ss.v_i += 1
    ss.v_revealed = False
    ss.v_shown_at = time.time()
    session.log("vocab")
    save()


# ---- finished ----
if ss.v_i >= len(cards):
    if ss.v_saved_upto < len(ss.v_answers):
        save(force=True)
    if not ss.get("v_logged"):
        ss.v_logged = True
        session.save()
    counts = {}
    for a in ss.v_answers:
        counts[a["rating"]] = counts.get(a["rating"], 0) + 1
    got = counts.get(GOOD, 0)
    total = len(ss.v_answers) or 1
    ui.card(f'<div class="word">{round(100 * got / total)}%</div>'
            f'<div class="reading">{got} of {len(ss.v_answers)} on the first pass</div>')
    cols = st.columns(2)
    for col, (label, val) in zip(cols, RATINGS):
        col.metric(label, counts.get(val, 0))
    if ss.v_saved_upto == len(ss.v_answers):
        st.success("Saved. On the laptop: `git pull`, then `python import_reviews.py`.")
    else:
        st.warning(f"Not saved automatically ({ss.v_save_err}). Download this and drop "
                   f"it into `data/reviews.json` on the laptop instead.")
    st.download_button("Download reviews.json",
                       json.dumps({"batch_id": due["batch_id"], "answers": ss.v_answers},
                                  indent=1),
                       file_name="reviews.json", mime="application/json",
                       use_container_width=True)
    st.page_link("views/grammar.py", label="Next: grammar →")
    st.stop()

# ---- one card ----
card = cards[ss.v_i]
done, total = ss.v_i, len(cards)
st.progress(done / total)
saved_note = "" if ss.v_saved_upto >= done else f"{done - ss.v_saved_upto} unsaved"
st.markdown(f'<div class="meta"><span>{done} / {total}</span>'
            f'<span class="right">{saved_note}</span></div>', unsafe_allow_html=True)

# The front is the bare word. Furigana belongs on the back — putting it here would hand
# over the reading, which is most of what the card is asking for.
if not ss.v_revealed:
    ui.card(f'<div class="word">{card["word"]}</div>')
    if st.button("Show", use_container_width=True, type="primary"):
        ss.v_revealed = True
        st.rerun()
else:
    back = [f'<div class="word">{card["word_furigana"] or card["word"]}</div>']
    if card["reading"]:
        back.append(f'<div class="reading">{card["reading"]}</div>')
    back.append(f'<div class="meaning">{card["meaning"]}</div>')
    if card["sentence"]:
        back.append('<div class="rule"></div>')
        back.append(f'<div class="sent">{card["sentence_furigana"] or card["sentence"]}</div>')
        back.append(f'<div class="sent-en">{card["sentence_meaning"]}</div>')
    ui.card("".join(back))

    s1, s2 = st.columns(2)
    with s1:
        ui.speak(card["reading"] or card["word"], label="word")
    if card["sentence"]:
        with s2:
            ui.speak(card["sentence"], label="sentence")

    with st.container(key="graders"):
        for col, (label, val) in zip(st.columns(2), RATINGS):
            if col.button(label, use_container_width=True, key=f"r{val}_{ss.v_i}"):
                answer(val)
                st.rerun()

if ss.v_save_err:
    st.caption(f":material/warning: last save failed: {ss.v_save_err}")
