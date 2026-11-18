"""Native speakers saying words: recordings from Lingua Libre on Wikimedia Commons,
found by tools/fetch_audio.py and listed in data/audio/<lang>.json.

Only links and credits live in the repo; the browser plays each file straight from
upload.wikimedia.org. A word with no recording falls back to the phone's voice.
Each recording is CC0, CC BY or CC BY-SA, so wherever one plays its speaker and
licence are shown with a link to the file's page (credit()).
"""
import json, os, re

import streamlit as st

from .store import ROOT


@st.cache_data
def _index(lang):
    path = os.path.join(ROOT, "data", "audio", f"{lang}.json")
    if not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8") as fh:
        words = json.load(fh).get("words", {})
    # Spanish matches ignore case; keep both spellings so either finds it.
    out = dict(words)
    for w, recs in words.items():
        out.setdefault(w.lower(), recs)
    return out


def _bare(word):
    return re.sub(r"^(el|la|los|las|un|una)\s+", "", word.strip(), flags=re.I)


def find(lang, *forms):
    """The recordings of the first of `forms` that has any (a list, best first),
    or []. Pass the word as written first, then any looser forms."""
    idx = _index(lang)
    for f in forms:
        if not f:
            continue
        for key in (f, f.lower(), _bare(f), _bare(f).lower()):
            if key in idx:
                return idx[key]
    return []


def credit(recs, word=None):
    """The small print under a recording: whose voice, which licence, a link."""
    if not recs:
        return ""
    r = recs[0]
    says = (f' · the recording says <b>{r["says"]}</b>'
            if word and r.get("says") and r["says"] != word else "")
    more = f" · {len(recs)} voices, tap again" if len(recs) > 1 else ""
    return (f'<div class="credit">Voice: <a href="{r["page"]}" target="_blank" '
            f'rel="noopener">{r["speaker"]}</a> · {r["licence"]}{says}{more}</div>')
