"""Answer normalisation, so a drill can be checked by string equality.

Answers arrive from a phone keyboard in whatever the user had switched on: a Japanese
IME (kana or kanji), or plain romaji when typing fast. Everything is folded to hiragana
before comparing, so 「タベタ」, "tabeta" and 「たべた」 all match. Kanji answers are
matched against the kanji spelling of the expected form, not converted.
"""
import re
import unicodedata

# Longest keys first is what makes greedy matching work: "sha" before "sa", "n'" before "n".
_ROMAJI = {
    "kya": "きゃ", "kyu": "きゅ", "kyo": "きょ", "gya": "ぎゃ", "gyu": "ぎゅ", "gyo": "ぎょ",
    "sha": "しゃ", "shu": "しゅ", "sho": "しょ", "she": "しぇ", "sya": "しゃ", "syu": "しゅ",
    "syo": "しょ", "ja": "じゃ", "ju": "じゅ", "jo": "じょ", "je": "じぇ", "jya": "じゃ",
    "jyu": "じゅ", "jyo": "じょ", "zya": "じゃ", "zyu": "じゅ", "zyo": "じょ",
    "cha": "ちゃ", "chu": "ちゅ", "cho": "ちょ", "che": "ちぇ", "tya": "ちゃ", "tyu": "ちゅ",
    "tyo": "ちょ", "nya": "にゃ", "nyu": "にゅ", "nyo": "にょ", "hya": "ひゃ", "hyu": "ひゅ",
    "hyo": "ひょ", "bya": "びゃ", "byu": "びゅ", "byo": "びょ", "pya": "ぴゃ", "pyu": "ぴゅ",
    "pyo": "ぴょ", "mya": "みゃ", "myu": "みゅ", "myo": "みょ", "rya": "りゃ", "ryu": "りゅ",
    "ryo": "りょ", "dya": "ぢゃ", "dyu": "ぢゅ", "dyo": "ぢょ",
    "shi": "し", "chi": "ち", "tsu": "つ", "fu": "ふ", "ji": "じ", "di": "ぢ", "du": "づ",
    "si": "し", "ti": "ち", "tu": "つ", "hu": "ふ", "zi": "じ", "wo": "を", "nn": "ん",
    "n'": "ん", "xtsu": "っ", "xtu": "っ", "ltsu": "っ", "ltu": "っ",
    "xa": "ぁ", "xi": "ぃ", "xu": "ぅ", "xe": "ぇ", "xo": "ぉ",
    "xya": "ゃ", "xyu": "ゅ", "xyo": "ょ",
    "ka": "か", "ki": "き", "ku": "く", "ke": "け", "ko": "こ",
    "ga": "が", "gi": "ぎ", "gu": "ぐ", "ge": "げ", "go": "ご",
    "sa": "さ", "su": "す", "se": "せ", "so": "そ",
    "za": "ざ", "zu": "ず", "ze": "ぜ", "zo": "ぞ",
    "ta": "た", "te": "て", "to": "と", "da": "だ", "de": "で", "do": "ど",
    "na": "な", "ni": "に", "nu": "ぬ", "ne": "ね", "no": "の",
    "ha": "は", "hi": "ひ", "he": "へ", "ho": "ほ",
    "ba": "ば", "bi": "び", "bu": "ぶ", "be": "べ", "bo": "ぼ",
    "pa": "ぱ", "pi": "ぴ", "pu": "ぷ", "pe": "ぺ", "po": "ぽ",
    "ma": "ま", "mi": "み", "mu": "む", "me": "め", "mo": "も",
    "ya": "や", "yu": "ゆ", "yo": "よ",
    "ra": "ら", "ri": "り", "ru": "る", "re": "れ", "ro": "ろ",
    "la": "ら", "li": "り", "lu": "る", "le": "れ", "lo": "ろ",
    "wa": "わ", "a": "あ", "i": "い", "u": "う", "e": "え", "o": "お", "-": "ー",
}
_KEYS = sorted(_ROMAJI, key=len, reverse=True)
_CONSONANTS = set("bcdfghjklmpqrstvwxyz")


def romaji_to_hiragana(s):
    s = s.lower()
    out, i = [], 0
    while i < len(s):
        # A doubled consonant is a small っ: "kitte" -> きって. ("nn" is ん, handled below.)
        # Hepburn writes the っ before ch as t: "matcha" -> まっちゃ.
        doubled = i + 1 < len(s) and s[i] == s[i + 1] and s[i] in _CONSONANTS
        if (doubled and s[i] != "n") or s.startswith("tch", i):
            out.append("っ")
            i += 1
            continue
        for k in _KEYS:
            if s.startswith(k, i):
                out.append(_ROMAJI[k])
                i += len(k)
                break
        else:
            # A lone n before a consonant (or at the end) is ん: "konbanwa", "hon".
            if s[i] == "n":
                out.append("ん")
            else:
                out.append(s[i])
            i += 1
    return "".join(out)


def kata_to_hira(s):
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in s)


_STRIP = re.compile(r"[\s。、．，,.!?！？「」]")


def normalize(s):
    """Fold an answer to the form drills compare in."""
    s = unicodedata.normalize("NFKC", s or "").strip()
    s = _STRIP.sub("", s)
    if re.search(r"[A-Za-z]", s):
        s = romaji_to_hiragana(s)
    return kata_to_hira(s)


# Anki-style furigana, 漢字[かんじ]: the reading attaches to the run of characters
# before it, back to a space or the start. The space is only a delimiter.
_RUBY = re.compile(r"([^ \[\]]+?)\[([^\]]+)\]")


def furigana_html(s):
    import html
    out = _RUBY.sub(lambda m: f"<ruby>{html.escape(m.group(1))}<rt>"
                              f"{html.escape(m.group(2))}</rt></ruby>", s or "")
    return out.replace(" ", "")


def strip_furigana(s):
    return _RUBY.sub(r"\1", s or "").replace(" ", "")


def furigana_reading(s):
    """The whole sentence in kana: each bracketed reading replaces its kanji."""
    return _RUBY.sub(r"\2", s or "").replace(" ", "")
