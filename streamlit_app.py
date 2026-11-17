"""Dondon (どんどん, "steadily onward"): one phone app for the whole daily routine of
learning a language — Japanese or Spanish.

  Today     the plan for the day and how far along you are
  Progress  your level, what the next one needs, your pace, and the statistics
  Basics    the alphabet: kana for Japanese, sounds and spelling for Spanish
  Vocab     reviews from the Dondon decks: 1,500-word tiers in frequency order
  Grammar   Katsuyou-style conjugation and pattern drills on a spaced schedule
  Read      Wikipedia and stories rewritten at your level; tap any word
  Build     translate sentences that need the grammar you just drilled; Claude grades
  Speak     listen, repeat, and get scored by the phone's speech recognition
  Talk      role-play conversations pitched at your level, with corrections
  Account   language, deck placement, invites (owner), sign out

The order is the method: words in, rules in, then both out — first into single
sentences, then into conversation, which is where speaking actually comes from.

The owner also gets "Anki": the original purpose of this repo, reviewing their own
Anki collection from the phone (views/anki.py).
"""
import streamlit as st

from hub import session, ui

st.set_page_config(page_title="Dondon", page_icon="assets/icon.png", layout="centered",
                   initial_sidebar_state="collapsed")
ui.setup()
session.sign_in()

page = st.Page
you = []
if session.is_owner() and session.lang() == "ja":
    you.append(page("views/anki.py", title="Anki", icon=":material/inbox:", url_path="anki"))
you.append(page("views/account.py", title="Account", icon=":material/person:", url_path="account"))
pages = {
    "": [page("views/today.py", title="Today", icon=":material/home:", default=True),
         page("views/progress.py", title="Progress", icon=":material/trending_up:", url_path="progress")],
    "Learn": [page("views/basics.py", title="Basics", icon=":material/abc:", url_path="basics"),
              page("views/vocab.py", title="Vocab", icon=":material/style:", url_path="vocab"),
              page("views/grammar.py", title="Grammar", icon=":material/repeat:", url_path="grammar")],
    "Use": [page("views/read.py", title="Read", icon=":material/menu_book:", url_path="read"),
            page("views/build.py", title="Build", icon=":material/extension:", url_path="build"),
            page("views/speak.py", title="Speak", icon=":material/mic:", url_path="speak"),
            page("views/talk.py", title="Talk", icon=":material/forum:", url_path="talk")],
    "You": you,
}
st.navigation(pages, position="top").run()
