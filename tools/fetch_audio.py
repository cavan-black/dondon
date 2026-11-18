"""Find a native speaker saying each word, from Lingua Libre's recordings on
Wikimedia Commons, and write data/audio/<lang>.json.

    python tools/fetch_audio.py ja
    python tools/fetch_audio.py es

WHY: the phone's text-to-speech is clear but sounds synthetic, and gets Japanese
pitch accent wrong often enough to matter. Lingua Libre volunteers record native
speakers saying single words, under free licences (CC0, CC BY, CC BY-SA). The app
plays them straight from Wikimedia: no audio is stored in this repo, only links,
and every recording is credited to its speaker where it plays.

WHAT gets looked up: every word in the decks (decks/<lang>/), the words grammar
drills are built from (hub/<lang>/lexicon.py), and for Japanese the owner's own Anki
words (data/known.json).

HOW: list every file in "Category:Lingua Libre pronunciation-<iso>" once (about
6,000 Japanese and 19,000 Spanish), match titles to words locally, then fetch the
licence and speaker for just the matches, fifty at a time.

MATCHING is deliberately strict, because a wrong recording teaches the wrong sound:
  - Japanese: the word exactly as written. A kana-only recording is used only for a
    word normally written in kana, since kana titles collide across homophones
    with different pitch accents (箸 and 橋 are both はし). A する-verb with no
    recording of its own gets its noun's (練習 for 練習する), marked as such.
  - Spanish: the word, then without its article (la casa -> casa), ignoring case.
Recordings under any licence other than CC0, CC BY or CC BY-SA are skipped. Up to
three speakers are kept per word, so learners hear more than one voice.
"""
import argparse, glob, html, json, os, re, sys, time

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

API = "https://commons.wikimedia.org/w/api.php"
UA = {"User-Agent": "Dondon/1.0 (https://github.com/cavan-black/dondon; language app)"}
ISO = {"ja": "jpn", "es": "spa"}
QID = {"ja": "Q5287", "es": "Q1321"}
FREE = re.compile(r"^(CC0|CC BY(-SA)? [0-9.]+|Public domain)$", re.I)
PER_WORD = 3
VARIETY = re.compile(r"^\(([^)]+)\)\s*")         # "(American Spanish) casa"


def api(**params):
    params.update(format="json", formatversion=2, maxlag=5)
    for attempt in range(5):
        r = requests.get(API, params=params, headers=UA, timeout=60)
        if r.status_code == 200 and "error" not in r.json():
            return r.json()
        time.sleep(2 + 3 * attempt)               # maxlag or a hiccup: back off
    r.raise_for_status()
    raise RuntimeError(r.json().get("error"))


# ---------------------------------------------------------------------- words

def words_for(lang):
    """[(written, reading)] to find recordings for, deduplicated, in a stable order."""
    out = []
    for path in sorted(glob.glob(os.path.join(ROOT, "decks", lang, "tier*.json"))):
        with open(path, encoding="utf-8") as fh:
            out += [(c["word"], c.get("reading", "")) for c in json.load(fh)["cards"]]
    lex = __import__(f"hub.{lang}.lexicon", fromlist=["WORDS"]).WORDS
    out += [(w.written, getattr(w, "kana", "")) for w in lex]
    if lang == "ja":
        known = os.path.join(ROOT, "data", "known.json")
        if os.path.exists(known):
            with open(known, encoding="utf-8") as fh:
                out += [(w, "") for w in json.load(fh).get("words", [])]
        due = os.path.join(ROOT, "data", "due.json")
        if os.path.exists(due):
            with open(due, encoding="utf-8") as fh:
                out += [(c["word"], c.get("reading", "")) for c in json.load(fh).get("cards", [])]
    seen, uniq = set(), []
    for w, r in out:
        if w and w not in seen:
            seen.add(w)
            uniq.append((w, r))
    return uniq


KANA = re.compile(r"^[぀-ヿー]+$")


def candidates(lang, written, reading):
    """Title words to try, best first, each with what the recording will say."""
    if lang == "ja":
        out = [written]
        if reading and reading == written:
            pass
        elif reading and KANA.match(written or ""):
            out.append(reading)
        if written.endswith("する") and len(written) > 2:
            out.append(written[:-2])               # 練習する -> 練習
        return out
    w = written.strip()
    bare = re.sub(r"^(el|la|los|las|un|una)\s+", "", w, flags=re.I)
    return [w] + ([bare] if bare != w else [])


# --------------------------------------------------------------------- commons

def title_words(lang, title):
    """The words a recording's title could be naming. Speaker names can contain
    hyphens, so every split point is a candidate: "LL-…-Some-User-casa.wav" offers
    "User-casa" and "casa". A variety label in front is dropped."""
    prefix = f"File:LL-{QID[lang]} ({ISO[lang]})-"
    if not title.startswith(prefix):
        return []
    rest = os.path.splitext(title[len(prefix):])[0]
    out = []
    for i, ch in enumerate(rest):
        if ch == "-":
            word = VARIETY.sub("", rest[i + 1:]).strip()
            if word:
                out.append(word.lower() if lang == "es" else word)
    return out


def all_recordings(lang):
    """{title word (lowercased for Spanish): [file title]} for the whole category."""
    index, cont, n = {}, {}, 0
    while True:
        data = api(action="query", list="categorymembers", cmtype="file", cmlimit=500,
                   cmtitle=f"Category:Lingua Libre pronunciation-{ISO[lang]}", **cont)
        for m in data["query"]["categorymembers"]:
            n += 1
            for key in title_words(lang, m["title"]):
                index.setdefault(key, []).append(m["title"])
        print(f"\r  listed {n:,} recordings", end="", flush=True)
        if "continue" not in data:
            print()
            return index
        cont = data["continue"]


def details(titles):
    """{title: {url, speaker, licence, page, variety}} for free-licence files."""
    out = {}
    titles = list(titles)
    for i in range(0, len(titles), 50):
        data = api(action="query", prop="imageinfo", iiprop="url|extmetadata",
                   iiextmetadatafilter="LicenseShortName|Artist",
                   titles="|".join(titles[i:i + 50]))
        for p in data["query"]["pages"]:
            if not p.get("imageinfo"):
                continue
            ii = p["imageinfo"][0]
            meta = ii.get("extmetadata", {})
            licence = meta.get("LicenseShortName", {}).get("value", "")
            if not FREE.match(licence.strip()):
                continue
            artist = html.unescape(re.sub(r"<[^>]+>", "", meta.get("Artist", {}).get("value", "")))
            m = VARIETY.search(p["title"].split(")-", 1)[-1].split("-", 1)[-1])
            # The Artist field reads "Speaker: X, Recorder: Y" on two lines; credit the voice.
            said = re.search(r"Speaker:\s*(.+)", artist)
            artist = (said.group(1) if said else artist.splitlines()[0] if artist else "").strip()
            out[p["title"]] = {"url": ii["url"].split("?")[0],
                               "page": ii["descriptionurl"].split("?")[0],
                               "speaker": artist or speaker_from(p["title"]),
                               "licence": licence.strip(),
                               "variety": m.group(1) if m else ""}
        print(f"\r  checked {min(i + 50, len(titles)):,} of {len(titles):,} files",
              end="", flush=True)
    print()
    return out


def speaker_from(title):
    return title.split(")-", 1)[-1].rsplit("-", 1)[0]


# ------------------------------------------------------------------------ main

def build(lang):
    words = words_for(lang)
    print(f"{lang}: {len(words):,} words to find")
    index = all_recordings(lang)
    chosen = {}
    for written, reading in words:
        for form in candidates(lang, written, reading):
            hits = index.get(form.lower() if lang == "es" else form)
            if hits:
                chosen[written] = (form, hits)
                break
    files = details({t for _, hits in chosen.values() for t in hits})
    out = {}
    for written, (form, hits) in chosen.items():
        recs = [dict(files[t], says=form) for t in hits if t in files]
        # One per speaker, and unlabelled varieties first (the standard accent).
        seen, keep = set(), []
        for r in sorted(recs, key=lambda r: (bool(r["variety"]), r["speaker"])):
            if r["speaker"] not in seen:
                seen.add(r["speaker"])
                keep.append(r)
        if keep:
            out[written] = keep[:PER_WORD]
    path = os.path.join(ROOT, "data", "audio", f"{lang}.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        json.dump({"source": "Lingua Libre, via Wikimedia Commons",
                   "generated": time.strftime("%Y-%m-%d"), "words": out},
                  fh, ensure_ascii=False, indent=0, sort_keys=True)
    exact = sum(1 for w, recs in out.items() if recs[0]["says"] == w)
    print(f"{lang}: {len(out):,} of {len(words):,} words have a recording "
          f"({exact:,} exact, {len(out) - exact:,} by a close form) -> {os.path.relpath(path, ROOT)}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("langs", nargs="+", choices=sorted(ISO))
    for lang in ap.parse_args().langs:
        build(lang)
