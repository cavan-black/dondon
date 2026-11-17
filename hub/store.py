"""Secrets, the learner's date, and the repo as storage for the owner's Anki loop.

The Anki batch (data/due.json) and its answers (data/reviews.json) travel through the
repo, committed via the GitHub contents API with a GH_PAT secret, because the laptop
on the other end reads them with git. Reads go to the API too when a token is set, so
the phone sees the latest commit before Streamlit has redeployed.

Learners' own data never goes here — the repo is public. That lives in hub/db.py.
"""
import base64, datetime, json, os
import requests
import streamlit as st

REPO = "cavan-black/dondon"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = f"https://api.github.com/repos/{REPO}/contents/"


def secret(name):
    try:
        v = st.secrets.get(name)
    except Exception:
        v = None          # no secrets.toml at all, e.g. running locally
    return v or os.environ.get(name)


def _headers():
    return {"Authorization": f"token {secret('GH_PAT')}",
            "Accept": "application/vnd.github+json"}


def read_json(path, default=None):
    """Latest committed copy of a repo file, or the deployed copy, or `default`."""
    if secret("GH_PAT"):
        try:
            r = requests.get(API + path, headers=_headers(), timeout=15)
            if r.status_code == 200:
                return json.loads(base64.b64decode(r.json()["content"]).decode("utf-8"))
        except Exception:
            pass
    local = os.path.join(ROOT, path)
    if os.path.exists(local):
        with open(local, encoding="utf-8") as fh:
            return json.load(fh)
    return default


def write_json(path, data, message):
    """Commit `data` to `path`. Returns (ok, error)."""
    if not secret("GH_PAT"):
        return False, "no GH_PAT secret"
    body = base64.b64encode(json.dumps(data, ensure_ascii=False, indent=1)
                            .encode("utf-8")).decode()
    # Two tries: a 409 means the file moved under us (another tab saved), so fetch the
    # new sha and write again. Last write wins, which is fine for one person's stats.
    err = None
    for _ in range(2):
        try:
            r = requests.get(API + path, headers=_headers(), timeout=15)
            sha = r.json().get("sha") if r.status_code == 200 else None
            payload = {"message": message, "content": body, "branch": "main"}
            if sha:
                payload["sha"] = sha
            r2 = requests.put(API + path, headers=_headers(), json=payload, timeout=20)
            if r2.status_code in (200, 201):
                return True, None
            err = f"GitHub {r2.status_code}: {r2.text[:150]}"
            if r2.status_code != 409:
                break
        except Exception as exc:
            err = str(exc)
            break
    return False, err


def now():
    """The learner's clock, not the server's — Community Cloud runs in UTC, and a
    day's study should roll over at the learner's midnight. The browser reports its
    zone."""
    try:
        from zoneinfo import ZoneInfo
        tz = st.context.timezone
        if tz:
            return datetime.datetime.now(ZoneInfo(tz))
    except Exception:
        pass
    return datetime.datetime.now()


def today():
    return now().date()
