"""Settings that follow the learner across devices, and the owner's invite list."""
import streamlit as st

from hub import db, langs, session, srs

L = langs.get(session.lang())
ls = session.lang_settings()

st.markdown(f'<div class="meta"><span>signed in</span><span class="right">'
            f'{session.email()}</span></div>', unsafe_allow_html=True)

st.subheader(f"{L.name} vocab")
ts = srs.tiers(L.code)
if ts:
    start = st.selectbox(
        "Start new cards at", ts, index=ts.index(srs.start_tier(ls, L.code)),
        format_func=lambda t: f"Tier {t} — words {(t - 1) * srs.TIER_SIZE + 1:,}"
                              f"–{t * srs.TIER_SIZE:,}",
        help="Already know the most common words? Start higher. Earlier tiers are "
             "skipped, not deleted — move back down any time.")
    per_day = st.slider("New cards per day", 0, 50,
                        ls.get("new_per_day", srs.DEFAULT_NEW_PER_DAY), step=5,
                        help="Each new card means about ten reviews over the next "
                             "month. 15 a day is roughly 20 minutes of reviews once it "
                             "settles.")
    if (start, per_day) != (srs.start_tier(ls, L.code),
                            ls.get("new_per_day", srs.DEFAULT_NEW_PER_DAY)):
        if start != srs.start_tier(ls, L.code):
            ls.pop("start_index", None)                 # a new tier starts at its top
        ls["start_tier"], ls["new_per_day"] = start, per_day
        session.save_settings()
        st.session_state.pop(f"vq_{L.code}", None)     # rebuild today's queue
        st.toast("Saved")
else:
    st.caption(f"No {L.name} decks generated yet.")

if session.is_owner():
    st.subheader("Invites")
    st.caption("Only invited Google accounts can sign in. Everyone shares your API key, "
               f"capped at {session.DAILY_TUTOR_CALLS} tutor calls each per day.")
    with st.form("invite", clear_on_submit=True, border=False):
        new = st.text_input("Email", placeholder="friend@gmail.com",
                            label_visibility="collapsed")
        if st.form_submit_button("Invite", use_container_width=True) and "@" in new:
            db.invite(new, session.email())
            st.toast(f"Invited {new.strip().lower()}")
    for e in db.invited():
        a, b = st.columns([4, 1])
        a.markdown(e)
        if b.button("Remove", key=f"rm_{e}"):
            db.uninvite(e)
            st.rerun()

try:
    signed_in_with_google = "auth" in st.secrets and st.user.is_logged_in
except Exception:
    signed_in_with_google = False
if signed_in_with_google and st.button("Sign out", use_container_width=True):
    st.logout()
