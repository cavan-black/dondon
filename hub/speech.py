"""How close what the phone heard was to what you meant to say.

Speech recognition is a rough judge of pronunciation — it guesses the most likely
words, so a slightly off vowel can still come back right, and a homophone written
with different kanji can come back "wrong". So the score is a similarity, not a
verdict, and it compares against every alternative the recogniser offered.

Japanese is compared character by character (after folding katakana into hiragana),
against both the written sentence and its kana reading, since the recogniser may
write a word in kanji or kana. Spanish is compared word by word with accents and
case folded — the recogniser adds accents itself, and they're not what's being
practised here.
"""
import difflib, html, re, unicodedata

from .ja.kana import kata_to_hira

_JA_DROP = re.compile(r"[\s、。，．,.!?！？「」『』（）()…・〜~ー-]")
_ES_WORD = re.compile(r"[a-zñü0-9]+")

GOOD, CLOSE = 0.85, 0.6


def _fold_es(s):
    s = unicodedata.normalize("NFD", s.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn" or c == "̃")
    return unicodedata.normalize("NFC", s)


def units(lang, s):
    """What gets compared: kana-folded characters for Japanese, words for Spanish."""
    if lang == "ja":
        return list(_JA_DROP.sub("", kata_to_hira(unicodedata.normalize("NFKC", s))))
    return _ES_WORD.findall(_fold_es(s))


def ratio(lang, target, heard):
    a, b = units(lang, target), units(lang, heard)
    if not a or not b:
        return 0.0
    return difflib.SequenceMatcher(None, a, b, autojunk=False).ratio()


def score(lang, targets, heard_alts):
    """Best similarity between any form of the target (written, reading) and any
    alternative heard. Returns (score, best target, best heard)."""
    best = (0.0, targets[0], heard_alts[0] if heard_alts else "")
    for t in targets:
        if not t:
            continue
        for h in heard_alts:
            r = ratio(lang, t, h)
            if r > best[0]:
                best = (r, t, h)
    return best


def verdict(r):
    if r >= GOOD:
        return "ok", "Clear"
    if r >= CLOSE:
        return "mid", "Close — listen and try once more"
    return "no", "Not quite — listen again, slower"


def diff_html(lang, target, heard):
    """The target with the parts the recogniser didn't hear dimmed and struck."""
    a, b = units(lang, target), units(lang, heard)
    sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
    hit = set()
    for blk in sm.get_matching_blocks():
        hit.update(range(blk.a, blk.a + blk.size))
    sep = "" if lang == "ja" else " "
    shown = a
    if lang != "ja":
        # Same words, as written — accents and capitals back.
        orig = re.findall(r"[^\W_]+", target)
        if len(orig) == len(a):
            shown = orig
    out = []
    for i, u in enumerate(shown):
        u = html.escape(u)
        out.append(u if i in hit else
                   f'<span style="color:var(--no-text);text-decoration:underline wavy">{u}</span>')
    return sep.join(out)
