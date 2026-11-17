"""Japanese conjugation, the deterministic core of the grammar drills.

Every function returns a LIST of accepted answers, canonical first. Katsuyou-style
drilling is strict about the form but should not mark a learner wrong for a spelling
or register that is also correct — 食べれる next to 食べられる, 書かせられる next to
書かされる, ではない next to じゃない. Alternates are listed explicitly rather than
matched loosely, so a near-miss is still a miss.

Words are conjugated on both spellings (kanji and kana) and the results unioned, so
either kind of answer is accepted. Conjugation only ever touches the okurigana at the
end, which is the same in both spellings — the exceptions are 来る, whose kanji keeps
its shape while its reading changes, and いい, which conjugates from よい.
"""
from dataclasses import dataclass, field

A = dict(う="わ", く="か", ぐ="が", す="さ", つ="た", ぬ="な", ぶ="ば", む="ま", る="ら")
I = dict(う="い", く="き", ぐ="ぎ", す="し", つ="ち", ぬ="に", ぶ="び", む="み", る="り")
E = dict(う="え", く="け", ぐ="げ", す="せ", つ="て", ぬ="ね", ぶ="べ", む="め", る="れ")
O = dict(う="お", く="こ", ぐ="ご", す="そ", つ="と", ぬ="の", ぶ="ぼ", む="も", る="ろ")
TE = dict(う="って", つ="って", る="って", む="んで", ぶ="んで", ぬ="んで",
          く="いて", ぐ="いで", す="して")

VERB_CLASSES = {"godan", "ichidan", "suru", "kuru"}
ADJ_CLASSES = {"i", "na"}


@dataclass(frozen=True)
class Word:
    written: str            # 食べる / 静か (na-adjectives without な)
    kana: str
    cls: str                # godan | ichidan | suru | kuru | i | na
    meaning: str
    skip: frozenset = field(default_factory=frozenset)   # forms that sound wrong for it

    @property
    def is_verb(self):
        return self.cls in VERB_CLASSES

    def label(self):
        return self.written + ("(な)" if self.cls == "na" else "")


# ---------------------------------------------------------------- verbs, one spelling

def _uniq(xs):
    seen, out = set(), []
    for x in xs:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _is_iku(s):
    return s.endswith("行く") or s.endswith("いく")


def _kuru(s):
    """Split 来る/くる into prefix and a function giving the stem for a reading."""
    pre = s[:-2]
    if s.endswith("来る"):
        return lambda reading: pre + "来"
    return lambda reading: pre + reading


def _verb_pieces(s, cls):
    """The handful of stems everything else is built from."""
    if cls == "suru":
        pre = s[:-2]
        return dict(stem=pre + "し", nai=pre + "し", te=pre + "して",
                    vol=pre + "しよう", ba=pre + "すれば")
    if cls == "kuru":
        k = _kuru(s)
        return dict(stem=k("き"), nai=k("こ"), te=k("き") + "て",
                    vol=k("こ") + "よう", ba=k("く") + "れば")
    if cls == "ichidan":
        st = s[:-1]
        return dict(stem=st, nai=st, te=st + "て", vol=st + "よう", ba=st + "れば")
    # godan
    st, e = s[:-1], s[-1]
    te = st + ("って" if _is_iku(s) else TE[e])
    return dict(stem=st + I[e], nai=st + A[e], te=te, vol=st + O[e] + "う",
                ba=st + E[e] + "ば", e_base=st + E[e])


def _verb(s, cls, form):
    p = _verb_pieces(s, cls)
    pre = s[:-2]
    is_aru = cls == "godan" and s in ("ある", "有る")
    te = p["te"]
    ta = te[:-1] + ("た" if te.endswith("て") else "だ")
    if form == "dict":
        return [s]
    if form == "stem":
        return [p["stem"]]
    if form == "te":
        return [te]
    if form == "ta":
        return [ta]
    if form == "tara":
        return [ta + "ら"]
    if form == "masu":
        return [p["stem"] + "ます"]
    if form == "masu_neg":
        return [p["stem"] + "ません"]
    if form == "masu_past":
        return [p["stem"] + "ました"]
    if form == "masu_neg_past":
        return [p["stem"] + "ませんでした"]
    if form == "vol_polite":
        return [p["stem"] + "ましょう"]
    if form == "tai":
        return [p["stem"] + "たい"]
    if form == "tai_neg":
        return [p["stem"] + "たくない"]
    if form in ("nai", "nakatta", "nakereba"):
        tail = {"nai": "ない", "nakatta": "なかった", "nakereba": "なければ"}[form]
        return [tail] if is_aru else [p["nai"] + tail]
    if form == "vol":
        return [p["vol"]]
    if form == "ba":
        return [p["ba"]]
    if form == "prohibitive":
        return [s + "な"]

    if form == "potential":
        if cls == "godan":
            return [p["e_base"] + "る"]
        if cls == "ichidan":
            return [s[:-1] + "られる", s[:-1] + "れる"]      # ら抜き is everyday speech
        if cls == "suru":
            return [pre + "できる"]
        k = _kuru(s)
        return [k("こ") + "られる", k("こ") + "れる"]
    if form == "passive":
        if cls == "godan":
            return [p["nai"] + "れる"]
        if cls == "suru":
            return [pre + "される"]
        return [p["nai"] + "られる"]
    if form == "causative":
        if cls == "godan":
            return [p["nai"] + "せる"]
        if cls == "suru":
            return [pre + "させる"]
        return [p["nai"] + "させる"]
    if form == "caus_passive":
        if cls == "godan":
            long = p["nai"] + "せられる"
            # The contracted される form exists for every godan verb except す-verbs,
            # where it would read 話さされる.
            return [long] if s.endswith("す") else [p["nai"] + "される", long]
        if cls == "suru":
            return [pre + "させられる"]
        return [p["nai"] + "させられる"]
    if form == "imperative":
        if cls == "godan":
            return [p["e_base"]]
        if cls == "ichidan":
            return [s[:-1] + "ろ", s[:-1] + "よ"]
        if cls == "suru":
            return [pre + "しろ", pre + "せよ"]
        return [_kuru(s)("こ") + "い"]
    raise KeyError(f"no verb form {form!r}")


# ------------------------------------------------------------ adjectives, one spelling

def _i_base(s):
    # いい (and compounds like かっこいい) conjugate from the older よい.
    return s[:-2] + "よ" if s.endswith("いい") else s[:-1]


def _i_adj(s, form):
    b = _i_base(s)
    table = {
        "dict": [s],
        "masu": [s + "です"],
        "masu_neg": [b + "くないです", b + "くありません"],
        "masu_past": [b + "かったです"],
        "masu_neg_past": [b + "くなかったです", b + "くありませんでした"],
        "nai": [b + "くない"],
        "ta": [b + "かった"],
        "nakatta": [b + "くなかった"],
        "te": [b + "くて"],
        "adverb": [b + "く"],
        "ba": [b + "ければ"],
        "tara": [b + "かったら"],
        "nakereba": [b + "くなければ"],
        "stem": [b],
    }
    return table[form]


def _na_adj(s, form):
    table = {
        "dict": [s + "だ", s],
        "masu": [s + "です"],
        "masu_neg": [s + "じゃないです", s + "じゃありません", s + "ではありません",
                     s + "ではないです"],
        "masu_past": [s + "でした"],
        "masu_neg_past": [s + "じゃなかったです", s + "じゃありませんでした",
                          s + "ではありませんでした", s + "ではなかったです"],
        "nai": [s + "じゃない", s + "ではない"],
        "ta": [s + "だった"],
        "nakatta": [s + "じゃなかった", s + "ではなかった"],
        "te": [s + "で"],
        "adverb": [s + "に"],
        "ba": [s + "なら", s + "ならば"],
        "tara": [s + "だったら"],
        "nakereba": [s + "じゃなければ", s + "でなければ"],
        "stem": [s],
    }
    return table[form]


# ------------------------------------------------------------------------- public API

def conjugate(word, form):
    """All accepted spellings of `word` in `form`, the kanji spelling's canonical first."""
    out = []
    for s in (word.written, word.kana):
        if word.cls == "i":
            out += _i_adj(s, form)
        elif word.cls == "na":
            out += _na_adj(s, form)
        else:
            out += _verb(s, word.cls, form)
    return _uniq(out)


def kana_of(word, form):
    """Canonical answer in kana only — the reading to show under a kanji answer."""
    w = Word(word.kana, word.kana, word.cls, word.meaning)
    return conjugate(w, form)[0]


# Each form names the Japanese grammar term too, so the label matches what textbooks
# and videos call it.
FORM_NAMES = {
    "masu": ("polite", "〜ます"),
    "masu_neg": ("polite negative", "〜ません"),
    "masu_past": ("polite past", "〜ました"),
    "masu_neg_past": ("polite past negative", "〜ませんでした"),
    "nai": ("plain negative", "〜ない"),
    "ta": ("plain past", "〜た"),
    "nakatta": ("plain past negative", "〜なかった"),
    "te": ("te-form", "〜て"),
    "tai": ("want to", "〜たい"),
    "tai_neg": ("don't want to", "〜たくない"),
    "vol": ("volitional", "〜よう"),
    "vol_polite": ("let's", "〜ましょう"),
    "potential": ("potential", "〜られる"),
    "passive": ("passive", "〜られる"),
    "causative": ("causative", "〜させる"),
    "caus_passive": ("causative-passive", "〜させられる"),
    "imperative": ("imperative", "〜ろ"),
    "prohibitive": ("prohibitive", "〜な"),
    "ba": ("conditional", "〜ば"),
    "tara": ("conditional", "〜たら"),
    "adverb": ("adverb", "〜く / 〜に"),
}
