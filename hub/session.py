"""Who is using the app, which language they're on, and their progress for it.

SIGN-IN is Google, through Streamlit's built-in st.login (an [auth] section in the
secrets). Access is invite-only: the owner (OWNER_EMAIL) and anyone they've invited
from the Account page. The app spends the owner's API credit, so an open door would
be an open wallet.

Until [auth] is configured the app runs as a single user — the owner — behind the
old APP_PIN gate, so an existing deploy keeps working while sign-in is set up.

Progress is loaded from the database once per session and per language, changed in
memory, and written back by save() at natural break points (end of a round, every few
turns). Card reviews are written straight away — see hub/srs.py.
"""
import datetime

import streamlit as st

from . import db, ui
from .store import secret, today

LANGS = ("ja", "es")
DEFAULT_LANG = "ja"


def _auth_configured():
    try:
        return "auth" in st.secrets
    except Exception:
        return False


def _owner():
    return (secret("OWNER_EMAIL") or "owner@local").lower()


def _pin_gate():
    pin = secret("APP_PIN")
    if not pin or st.session_state.get("unlocked"):
        return
    st.markdown('<div class="meta"><span>locked</span></div>', unsafe_allow_html=True)
    entered = st.text_input("PIN", type="password", label_visibility="collapsed",
                            placeholder="PIN")
    if entered:
        if entered == pin:
            st.session_state["unlocked"] = True
            st.rerun()
        else:
            st.error("Nope.")
    st.stop()


def sign_in():
    """Stop the page unless someone allowed is signed in. Returns their email."""
    ss = st.session_state
    if "email" in ss:
        return ss.email
    if not _auth_configured():
        _pin_gate()
        email, name = _owner(), "Owner"
    else:
        if not st.user.is_logged_in:
            st.markdown(f'<div class="card">{ui.brand(big=True)}'
                        '<div class="reading">steadily onward</div>'
                        '<div class="sent-en">Daily vocab, grammar, sentence building and '
                        'conversation — Japanese and Spanish.</div></div>',
                        unsafe_allow_html=True)
            if st.button("Sign in with Google", type="primary", use_container_width=True):
                st.login()
            st.stop()
        email, name = st.user.email.lower(), st.user.get("name") or st.user.email
        if email != _owner() and not db.is_invited(email):
            st.markdown(f'<div class="card"><div class="meaning">Not invited yet</div>'
                        f'<div class="sent-en">{email} isn\'t on the list. Ask whoever '
                        f'sent you the link to invite you.</div></div>',
                        unsafe_allow_html=True)
            if st.button("Sign out", use_container_width=True):
                st.logout()
            st.stop()
    db.ensure_user(email, name)
    ss.email, ss.name = email, name
    return email


def email():
    return st.session_state.email


def is_owner():
    return email() == _owner()


# -------------------------------------------------------------------- settings

def settings():
    ss = st.session_state
    if "settings" not in ss:
        ss.settings = db.get_settings(email())
    return ss.settings


def save_settings():
    db.put_settings(email(), settings())


def lang():
    return settings().get("lang", DEFAULT_LANG)


def set_lang(code):
    settings()["lang"] = code
    save_settings()


def lang_settings(code=None):
    """Per-language settings: starting tier, new cards per day, and so on."""
    return settings().setdefault("by_lang", {}).setdefault(code or lang(), {})


# -------------------------------------------------------------------- progress

def progress(code=None):
    code = code or lang()
    cache = st.session_state.setdefault("progress", {})
    if code not in cache:
        p = db.get_progress(email(), code)
        p.setdefault("skills", {})
        p.setdefault("days", {})
        cache[code] = p
    return cache[code]


def day_log(d=None, code=None):
    return progress(code)["days"].setdefault((d or today()).isoformat(), {})


def log(kind, n=1):
    """Count `n` units of today's `kind` of practice (vocab, grammar, build, talk)."""
    entry = day_log()
    entry[kind] = entry.get(kind, 0) + n


def save(code=None):
    try:
        db.put_progress(email(), code or lang(), progress(code))
        st.session_state.save_err = None
    except Exception as exc:          # a dropped connection shouldn't kill the page
        st.session_state.save_err = str(exc)


def streak():
    """Consecutive days, ending today or yesterday, with practice in any language."""
    def active(d):
        return any(any(progress(c)["days"].get(d.isoformat(), {}).values())
                   for c in LANGS)
    d = today()
    if not active(d):
        d -= datetime.timedelta(days=1)
    n = 0
    while active(d):
        n += 1
        d -= datetime.timedelta(days=1)
    return n


def known_words(code=None):
    """Words this learner has reviewed in Dondon's decks — plus, for the owner's
    Japanese, the words in their own Anki collection (data/known.json, written by
    export_due.py)."""
    from . import srs
    from .store import read_json
    code = code or lang()
    cache = st.session_state.setdefault("known", {})
    if code not in cache:
        words = set(srs.known_words(email(), code))
        if code == "ja" and is_owner():
            words |= set((read_json("data/known.json", default={}) or {}).get("words", []))
        cache[code] = words
    return cache[code]


def words_estimate(code=None):
    """How many words you know, for levels and the forecast: the words reviewed
    here, plus what the placement test found that the cards don't show yet. For the
    owner's Japanese the Anki collection counts too, whichever is larger."""
    from . import srs, stats
    code = code or lang()
    known = known_words(code)
    rows = list(srs.rows(email(), code).values()) if srs.tiers(code) else []
    mine = sum(1 for r in rows if r["reps"] > 0)
    return max(len(known), mine + stats.placement_words(progress(code).get("placement"), rows))


# ---------------------------------------------------------------- API spending

DAILY_TUTOR_CALLS = 120     # per learner per day; the owner is not capped


def tutor_allowance():
    """How many tutor calls are left today. Build and Talk spend the owner's API
    credit, so each invited learner gets a generous but finite daily budget."""
    if is_owner():
        return 10 ** 6
    used = sum(day_log(code=c).get("api", 0) for c in LANGS)
    return max(DAILY_TUTOR_CALLS - used, 0)


def spend_tutor_call():
    log("api")
