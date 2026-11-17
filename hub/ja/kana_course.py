"""Hiragana and katakana, row by row, then reading real words.

Order: the ten hiragana rows, the voiced rows (が ざ だ ば ぱ), the combined sounds
(きゃ…), small っ and long vowels, real words; then katakana the same way, faster —
two rows a unit, since the sounds are already known — then sounds that only
katakana writes (ファ, ティ…) and loanwords with ー.

Two drills per kana: see it and type the romaji, or hear it (and see the romaji)
and pick it from four, where the three wrong ones are look-alikes wherever the
course has any (シ/ツ, ぬ/め, わ/れ/ね). Hepburn and Kunrei spellings are both
accepted (shi/si, tsu/tu, fu/hu, ji/zi), and so is typing the kana itself.

The mnemonics are this app's own, kept to a line.
"""
import re, unicodedata

from hub.basics import Item, Unit
from .kana import kata_to_hira, romaji_to_hiragana
from .lexicon import WORDS


def hira_to_kata(s):
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in s)


# ------------------------------------------------------------------ the kana

# (kana, accepted romaji — Hepburn first, hiragana hint, katakana hint)
ROWS = [
    ("a", [
        ("あ", ("a",), "A cross with a big loop under it: 'ah!' as the knot pulls tight.",
         "ア: an axe head on a handle — 'a'."),
        ("い", ("i",), "Two short strokes side by side, like two eels: 'ee'.",
         "イ: a stroke leaning on a post — an easel, 'i'."),
        ("う", ("u",), "A dash over a curl: someone stubbing a toe — 'oo'.",
         "ウ: a lid on a little hut — 'u'."),
        ("え", ("e",), "A dash, then a zig and a kick: 'eh?'",
         "エ: an I-beam — 'e' for engineer."),
        ("お", ("o",), "Like あ with an extra flick out to the right: 'oh!'",
         "オ: a figure with one arm out — 'oh, over here!'"),
    ]),
    ("ka", [
        ("か", ("ka",), "A blade with a spark beside it: 'ka!'",
         "カ: か without the spark."),
        ("き", ("ki",), "A key: two bars across a stem with a hooked bottom.",
         "キ: the same key, simpler — two bars and a stem."),
        ("く", ("ku",), "An open beak: a cuckoo calling 'ku'.",
         "ク: a cook's hat brim seen from the side."),
        ("け", ("ke",), "A keg on a stand, tap on the side.",
         "ケ: a slanted 'k' with a long tail."),
        ("こ", ("ko",), "Two short coils, one above the other.",
         "コ: a square corner — 'ko'rner."),
    ]),
    ("sa", [
        ("さ", ("sa",), "Like き with one bar fewer: 'sa'.",
         "サ: a saddle with two posts."),
        ("し", ("shi", "si"), "A fish hook: 'she' goes fishing.",
         "シ: two dots on the LEFT, long stroke sweeping UP."),
        ("す", ("su",), "A swing seat on a loop: 'su'.",
         "ス: a stick figure mid-stride — 'su'."),
        ("せ", ("se",), "A mouth open saying 'seh', tongue sticking out.",
         "セ: like せ with the curl tucked in."),
        ("そ", ("so",), "A zigzag of sewing thread: 'so'.",
         "ソ: one dot on top, stroke falling DOWN."),
    ]),
    ("ta", [
        ("た", ("ta",), "A 't' beside a small 'a': 'ta'.",
         "タ: like ク with an extra slash inside — 'ta'."),
        ("ち", ("chi", "ti"), "A backwards '5' — 'chi'.",
         "チ: a cheerleader, arms up — 'chi'."),
        ("つ", ("tsu", "tu"), "A breaking wave: 'tsu'nami.",
         "ツ: two dots on TOP, long stroke falling DOWN."),
        ("て", ("te",), "A bent arm reaching out: 'te' is 'hand'.",
         "テ: a telephone pole — 'te'."),
        ("と", ("to",), "A toe with a thorn stuck in it.",
         "ト: a totem pole with one branch."),
    ]),
    ("na", [
        ("な", ("na",), "A cross and a knot: 'na'.",
         "ナ: a plain cross leaning over — 'na'."),
        ("に", ("ni",), "A post next to two lines: 'ni'.",
         "ニ: two lines — it's the kanji for 'two' (ni)."),
        ("ぬ", ("nu",), "A twist of noodles with a loop at the end.",
         "ヌ: a hook with a slash through it — 'nu'."),
        ("ね", ("ne",), "Like ぬ with a straight back: a cat (neko) curled up.",
         "ネ: a little figure with a hat — 'ne'."),
        ("の", ("no",), "One stroke circling round: a 'no entry' sign.",
         "ノ: a single slash — 'no!'"),
    ]),
    ("ha", [
        ("は", ("ha",), "A tall stroke beside a loop: 'ha!'",
         "ハ: two lines spread apart, like a laugh — 'ha'."),
        ("ひ", ("hi",), "A wide grin: 'hee hee'.",
         "ヒ: a heel kicking left."),
        ("ふ", ("fu", "hu"), "Mount Fuji with puffs of cloud around it.",
         "フ: a hook — blow on it, 'fu'."),
        ("へ", ("he",), "A little hill: 'he'ad up it.",
         "ヘ: the same hill as へ."),
        ("ほ", ("ho",), "Like は with an extra bar on top: 'ho'.",
         "ホ: a cross with feet — 'ho'ly tree."),
    ]),
    ("ma", [
        ("ま", ("ma",), "Two bars on a stem ending in a loop: 'ma'.",
         "マ: a mask hanging from a nail — 'ma'."),
        ("み", ("mi",), "A loop with a long tail and a tick: 'mi'.",
         "ミ: three strokes — 'mi' as in three (mittsu)."),
        ("む", ("mu",), "A cow's face with a flick of an ear: 'moo'.",
         "ム: a cow's nose — 'mu'."),
        ("め", ("me",), "An eye with a lash — 'me' means eye.",
         "メ: an X — mark the 'me'."),
        ("も", ("mo",), "A fish hook with two bars: 'more' fish.",
         "モ: も, straightened out."),
    ]),
    ("ya", [
        ("や", ("ya",), "A yak's horn and a stick: 'ya'.",
         "ヤ: like や with the stick gone."),
        ("ゆ", ("yu",), "A loop with a stroke through it: a fish in a pond, 'yu'.",
         "ユ: a U-turn on its side — 'yu'."),
        ("よ", ("yo",), "A yo-yo hanging from a stick.",
         "ヨ: a backwards E — 'yo'."),
    ]),
    ("ra", [
        ("ら", ("ra", "la"), "A rabbit's ear above a curl: 'ra'.",
         "ラ: a lid over a hook — 'ra'."),
        ("り", ("ri", "li"), "Two reeds by the water: 'ri'.",
         "リ: the same two reeds, straighter."),
        ("る", ("ru", "lu"), "A road that loops back on itself: 'ru'.",
         "ル: two roots, one kicking out — 'ru'."),
        ("れ", ("re", "le"), "A kneeling figure with a straight leg: 're'.",
         "レ: a check mark — 're'ady."),
        ("ろ", ("ro", "lo"), "る without the loop: the road goes straight on.",
         "ロ: a square — a 'ro'om."),
    ]),
    ("wa", [
        ("わ", ("wa",), "Like ね and れ, but ending in a round belly: 'wa'.",
         "ワ: a cup of water — 'wa'."),
        ("を", ("wo", "o"), "A figure bending over a stick. Said 'o'; only used as a "
                            "particle.",
         "ヲ: rare — ヲ shows up in old spellings and on signs."),
        ("ん", ("n", "nn"), "A cursive 'n'.",
         "ン: one dot on the LEFT, stroke sweeping UP."),
    ]),
]

# Voiced and half-voiced: hiragana, romaji.
VOICED = [
    ("ga", "The two ticks (゛) voice the sound: k becomes g.",
     [("が", ("ga",)), ("ぎ", ("gi",)), ("ぐ", ("gu",)), ("げ", ("ge",)), ("ご", ("go",))]),
    ("za", "゛ on the s-row gives z — except し, which becomes じ 'ji'.",
     [("ざ", ("za",)), ("じ", ("ji", "zi")), ("ず", ("zu",)), ("ぜ", ("ze",)),
      ("ぞ", ("zo",))]),
    ("da", "゛ on the t-row gives d. ぢ and づ sound just like じ and ず, and are rare.",
     [("だ", ("da",)), ("ぢ", ("ji", "di")), ("づ", ("zu", "du")), ("で", ("de",)),
      ("ど", ("do",))]),
    ("ba", "゛ on the h-row gives b.",
     [("ば", ("ba",)), ("び", ("bi",)), ("ぶ", ("bu",)), ("べ", ("be",)), ("ぼ", ("bo",))]),
    ("pa", "The little circle (゜) on the h-row gives p.",
     [("ぱ", ("pa",)), ("ぴ", ("pi",)), ("ぷ", ("pu",)), ("ぺ", ("pe",)), ("ぽ", ("po",))]),
]

# Combined sounds: an i-column kana plus a small ゃ ゅ ょ. Romaji stems per base.
_COMBO_STEMS = {"き": ("ky",), "ぎ": ("gy",), "し": ("sh", "sy"), "じ": ("j", "zy", "jy"),
                "ち": ("ch", "ty", "cy"), "に": ("ny",), "ひ": ("hy",), "び": ("by",),
                "ぴ": ("py",), "み": ("my",), "り": ("ry", "ly")}
_SMALL = {"ゃ": "a", "ゅ": "u", "ょ": "o"}


def _combos(bases):
    out = []
    for b in bases:
        for small, v in _SMALL.items():
            out.append((b + small, tuple(s + v for s in _COMBO_STEMS[b])))
    return out


COMBOS_1 = _combos("きしちにひ")
COMBOS_2 = _combos("みりぎじびぴ")

# Sounds only katakana writes, for loanwords.
FOREIGN = [("ファ", ("fa",)), ("フィ", ("fi",)), ("フェ", ("fe",)), ("フォ", ("fo",)),
           ("ティ", ("ti",)), ("ディ", ("di",)), ("チェ", ("che",)), ("シェ", ("she",)),
           ("ジェ", ("je",)), ("ウィ", ("wi",)), ("ウェ", ("we",)), ("ウォ", ("wo",))]


# ------------------------------------------------------------------ the words

# Small っ and long vowels, in hiragana: (word, Hepburn the way it's spelled, meaning).
SOKUON = [
    ("きって", "stamp"), ("がっこう", "school"), ("ちょっと", "a little"),
    ("いっしょ", "together"), ("きっぷ", "ticket"), ("ざっし", "magazine"),
    ("まっすぐ", "straight ahead"), ("おかあさん", "mother"), ("おにいさん", "older brother"),
    ("おばあさん", "grandmother"), ("せんせい", "teacher"), ("とうきょう", "Tokyo"),
    ("ゆうびん", "post, mail"), ("ひこうき", "aeroplane"), ("りょうり", "cooking"),
    ("ぎゅうにゅう", "milk"), ("えいが", "film"), ("とけい", "clock"),
    ("おおきい", "big"), ("くうこう", "airport"),
]

# Katakana loanwords: (word, meaning). Long vowels written with ー.
LOANWORDS = [
    ("コーヒー", "coffee"), ("テレビ", "television"), ("パン", "bread"),
    ("カメラ", "camera"), ("ホテル", "hotel"), ("タクシー", "taxi"), ("バス", "bus"),
    ("ビール", "beer"), ("ジュース", "juice"), ("ケーキ", "cake"), ("アイス", "ice cream"),
    ("ゲーム", "game"), ("スマホ", "smartphone"), ("パソコン", "computer"),
    ("メール", "email"), ("ノート", "notebook"), ("ペン", "pen"), ("テスト", "test"),
    ("スポーツ", "sport"), ("サッカー", "football"), ("テニス", "tennis"),
    ("ピアノ", "piano"), ("ギター", "guitar"), ("アニメ", "anime"), ("マンガ", "manga"),
    ("レストラン", "restaurant"), ("メニュー", "menu"), ("トイレ", "toilet"),
    ("エレベーター", "lift, elevator"), ("デパート", "department store"),
    ("コンビニ", "convenience store"), ("スーパー", "supermarket"),
    ("アパート", "flat, apartment"), ("ベッド", "bed"), ("シャツ", "shirt"),
    ("ドア", "door"), ("ラーメン", "ramen"), ("チョコレート", "chocolate"),
    ("アメリカ", "America"), ("フランス", "France"), ("カフェ", "café"),
    ("ファン", "fan"), ("フォーク", "fork"), ("チェック", "check"),
]


# ------------------------------------------------------------- romaji <-> kana

_HEPBURN = {}           # hiragana -> canonical Hepburn, built from the course data
for _, row in ROWS:
    for k, rs, *_ in row:
        _HEPBURN[k] = rs[0]
for _, _, row in VOICED:
    for k, rs in row:
        _HEPBURN[k] = rs[0]
for k, rs in _combos(_COMBO_STEMS):
    _HEPBURN[k] = rs[0]
for k, rs in FOREIGN:
    _HEPBURN[kata_to_hira(k)] = rs[0]
_HEPBURN.update({"ぁ": "a", "ぃ": "i", "ぅ": "u", "ぇ": "e", "ぉ": "o", "を": "o"})

_VOWEL_KANA = {"a": "あ", "i": "い", "u": "う", "e": "え", "o": "お"}


def to_romaji(word):
    """Hepburn as the word is spelled: がっこう → gakkou, コーヒー → koohii."""
    h = kata_to_hira(word)
    out, i = [], 0
    while i < len(h):
        two = h[i:i + 2]
        if two in _HEPBURN and len(two) == 2:
            r, i = _HEPBURN[two], i + 2
        elif h[i] == "っ":
            nxt = to_romaji(h[i + 1:])[:1] if i + 1 < len(h) else ""
            r = "t" if to_romaji(h[i + 1:]).startswith("ch") else nxt
            i += 1
        elif h[i] == "ー":
            r = out[-1][-1] if out else ""
            i += 1
        elif h[i] == "ん":
            nxt = h[i + 1:i + 2]
            r = "n'" if nxt and (nxt in "あいうえおやゆよ") else "n"
            i += 1
        else:
            r, i = _HEPBURN.get(h[i], h[i]), i + 1
        out.append(r)
    return "".join(out)


_MACRONS = str.maketrans({"ā": "aa", "ī": "ii", "ū": "uu", "ē": "ee", "ō": "ou",
                          "â": "aa", "î": "ii", "û": "uu", "ê": "ee", "ô": "ou"})
# Foreign-sound spellings the shared romaji table doesn't carry. ("ti"/"di" stay
# ち/ぢ there — those are taken by Kunrei — and are matched by the item's own list.)
_FOREIGN_ROMAJI = [("fa", "ふぁ"), ("fi", "ふぃ"), ("fe", "ふぇ"), ("fo", "ふぉ"),
                   ("wi", "うぃ"), ("we", "うぇ")]


def to_hiragana(typed):
    s = unicodedata.normalize("NFC", typed or "").strip().lower().translate(_MACRONS)
    s = re.sub(r"[\s。、．，,.!?！？「」]", "", s)
    if re.search(r"[a-z]", s):
        for r, k in _FOREIGN_ROMAJI:
            s = s.replace(r, k)
        s = romaji_to_hiragana(s)       # reads "n'" as ん
    return kata_to_hira(s.replace("'", ""))


_EQUIV = str.maketrans({"を": "お", "ぢ": "じ", "づ": "ず"})
_VOWEL_OF = {}
for k, r in _HEPBURN.items():
    if r and r[-1] in _VOWEL_KANA:
        _VOWEL_OF[k[-1]] = _VOWEL_KANA[r[-1]]
_VOWEL_OF.update({"ゃ": "あ", "ゅ": "う", "ょ": "お"})


def fold(h):
    """Spellings that read the same: を/お, ぢ/じ, づ/ず, a ー or a doubled vowel, and
    long o and e written おう/えい (がっこう = gakkoo = gakkō)."""
    out = []
    for ch in h.translate(_EQUIV):
        prev = out[-1] if out else ""
        if ch == "ー" and prev:
            ch = _VOWEL_OF.get(prev, "ー")
        elif ch == "う" and _VOWEL_OF.get(prev) == "お":
            ch = "お"
        elif ch == "い" and _VOWEL_OF.get(prev) == "え":
            ch = "え"
        out.append(ch)
    return "".join(out)


def check(item, mode, typed):
    """A typed reading of a kana or word: romaji (either system) or the kana."""
    t = (typed or "").strip().lower()
    ok = t in item.answers or (bool(t) and fold(to_hiragana(t)) == fold(kata_to_hira(item.text)))
    return ok, False, item.answers[0], ""


# ------------------------------------------------------------------ look-alikes

_LOOKALIKE_GROUPS = [
    "あおめぬ", "いりこ", "うつらち", "きさちま", "けはほ", "こにい", "しつもし",
    "ぬめねの", "ねれわ", "るろら", "はほま", "くへて", "そてろ", "たなに", "むすお",
    "ゆよる", "ぱばは", "ぴびひ", "ぷぶふ", "ぺべへ", "ぽぼほ",
    "シツソンノ", "クケタワウフ", "スヌラフ", "ナメチテ", "コユロヨエ", "ニヒミ",
    "ハルソ", "マムアヤ", "オホキ", "チテナ", "セヤサ", "ワウクフ", "レル",
    "パバハ", "ピビヒ", "プブフ", "ペベヘ", "ポボホ",
]
LOOKALIKES = {}
for g in _LOOKALIKE_GROUPS:
    for c in g:
        LOOKALIKES.setdefault(c, []).extend(x for x in g if x != c)


def options(item, pool, k, rng):
    """The kana and k-1 wrong ones: look-alikes first, then the same unit's
    neighbours, then anything met so far — never two that read the same."""
    same_script = [i.text for i in pool if _script(i.text) == _script(item.text)]
    look = [x for x in LOOKALIKES.get(item.text, []) if x in same_script]
    rng.shuffle(look)
    others = [x for x in same_script if x not in look]
    rng.shuffle(others)
    # Same length first (a combo among combos) before falling back to anything.
    others.sort(key=lambda x: len(x) != len(item.text))
    picked, seen = [], {fold(kata_to_hira(item.text))}
    for x in look + others:
        f = fold(kata_to_hira(x))
        if f in seen:
            continue
        picked.append(x)
        seen.add(f)
        if len(picked) == k - 1:
            break
    out = picked + [item.text]
    rng.shuffle(out)
    return out


def _script(s):
    return "kata" if any("ァ" <= c <= "ヺ" for c in s) else "hira"


# ------------------------------------------------------------------ the units

def _kana_items(rows, kata=False):
    out = []
    for k, rs, *hints in rows:
        text = hira_to_kata(k) if kata else k
        hint = (hints[1] if kata else hints[0]) if hints else ""
        out.append(Item(id=text, text=text, answers=tuple(rs), hint=hint))
    return tuple(out)


def _word_items(words, prefix):
    return tuple(Item(id=f"{prefix}:{w}", text=w, answers=(to_romaji(w),), hint=m)
                 for w, m in words)


def _lexicon_words(n=40):
    """Plain-hiragana dictionary forms from the drill lexicon — real words the
    grammar drills will use later."""
    out, seen = [], {w for w, _ in SOKUON}
    for w in WORDS:
        if w.kana not in seen and len(w.kana) <= 5 and \
                all(c in _HEPBURN or c in "っん" for c in w.kana):
            seen.add(w.kana)
            out.append((w.kana, w.meaning))
    # The lexicon is grouped by word class; take an even spread, not the first n.
    step = max(len(out) / n, 1)
    return [out[int(i * step)] for i in range(min(n, len(out)))]


_ROW_NAMES = {"a": "あ row", "ka": "か row", "sa": "さ row", "ta": "た row",
              "na": "な row", "ha": "は row", "ma": "ま row", "ya": "や row",
              "ra": "ら row", "wa": "わ, を, ん"}
_ROW_NOTES = {
    "a": "The five vowels. Every other kana is a consonant plus one of these, and "
         "they never change: a as in 'father', i as in 'machine', u as in 'food' "
         "(lips relaxed), e as in 'bed', o as in 'more' without the r.",
    "sa": "し is 'shi', not 'si'.",
    "ta": "ち is 'chi' and つ is 'tsu' — the row doesn't keep its t.",
    "ha": "ふ is between 'fu' and 'hu': blow gently, lips not touching. "
          "は is read 'wa' when it is the topic particle.",
    "ya": "Only three: yi and ye aren't used.",
    "ra": "The Japanese r is a light tap of the tongue, between r, l and d.",
    "wa": "を is read 'o' and only appears as a particle. ん is the only kana that's "
          "a consonant on its own.",
}


def _row_units(kata=False):
    out = []
    script = "Katakana" if kata else "Hiragana"
    for name, row in ROWS:
        items = _kana_items(row, kata)
        out.append(Unit(
            key=f"{'k' if kata else 'h'}.{name}",
            title=f"{script}: {(hira_to_kata(_ROW_NAMES[name]) if kata else _ROW_NAMES[name])}",
            sub=" ".join(i.text for i in items),
            intro=_ROW_NOTES.get(name, "Tap a kana to hear it, then drill the row."),
            items=items, modes=("type", "pick")))
    return out


def _pairs(us, script):
    """Katakana two rows a unit: the sounds are known, only the shapes are new."""
    out = []
    for a, b in zip(us[0::2], us[1::2] + [None]):
        group = (a,) if b is None else (a, b)
        out.append(Unit(
            key="+".join(u.key for u in group),
            title=f"{script}: " + " + ".join(u.title.split(": ")[1] for u in group),
            sub=" ".join(u.sub for u in group),
            intro="Same sounds as hiragana, new shapes. Katakana writes loanwords, "
                  "foreign names and emphasis. " + " ".join(
                      _ROW_NOTES[u.key.split(".")[1]] for u in group
                      if u.key.split(".")[1] in ("sa", "ta", "wa")),
            items=sum((u.items for u in group), ()), modes=("type", "pick")))
    return out


def _voiced_units(kata=False):
    script = "Katakana" if kata else "Hiragana"
    conv = hira_to_kata if kata else (lambda s: s)
    if kata:
        items = tuple(Item(id=conv(k), text=conv(k), answers=rs)
                      for _, _, row in VOICED for k, rs in row)
        return [Unit(key="k.voiced", title=f"{script}: ゛ and ゜",
                     sub="ガ ザ ダ バ パ", intro="The same ゛ and ゜ marks as hiragana: "
                     "k→g, s→z, t→d, h→b, and h→p with the circle.",
                     items=items, modes=("type", "pick"), sample=15)]
    out = []
    for (n1, i1, r1), (n2, i2, r2) in [(VOICED[0], VOICED[1]), (VOICED[2], VOICED[3])]:
        out.append(Unit(key=f"h.{n1}+{n2}", title=f"{script}: {r1[0][0]} and {r2[0][0]} rows",
                        sub=" ".join(k for k, _ in r1 + r2), intro=f"{i1} {i2}",
                        items=tuple(Item(id=k, text=k, answers=rs) for k, rs in r1 + r2),
                        modes=("type", "pick")))
    n, i, r = VOICED[4]
    out.append(Unit(key="h.pa", title=f"{script}: ぱ row", sub=" ".join(k for k, _ in r),
                    intro=i, items=tuple(Item(id=k, text=k, answers=rs) for k, rs in r),
                    modes=("type", "pick")))
    return out


_COMBO_NOTE = ("An i-sound kana plus a small ゃ ゅ ょ makes one syllable: き + ゃ = "
               "kya, not ki-ya. The small kana is written half size.")


def _combo_units(kata=False):
    conv = hira_to_kata if kata else (lambda s: s)
    script = "Katakana" if kata else "Hiragana"
    if kata:
        items = tuple(Item(id=conv(k), text=conv(k), answers=rs)
                      for k, rs in COMBOS_1 + COMBOS_2)
        return [Unit(key="k.combo", title=f"{script}: キャ, シュ, チョ…", sub="キャ シュ チョ ニャ リョ",
                     intro=_COMBO_NOTE.replace("き", "キ").replace("ゃ ゅ ょ", "ャ ュ ョ"),
                     items=items, modes=("type", "pick"), sample=15)]
    return [
        Unit(key="h.combo1", title="Hiragana: きゃ, しゃ, ちゃ…", sub="きゃ しゃ ちゃ にゃ ひゃ",
             intro=_COMBO_NOTE, items=_kana_items([(k, rs) for k, rs in COMBOS_1]),
             modes=("type", "pick"), sample=10),
        Unit(key="h.combo2", title="Hiragana: みゃ, りゃ, じゃ…", sub="みゃ りゃ ぎゃ じゃ びゃ ぴゃ",
             intro=_COMBO_NOTE + " じゃ じゅ じょ are 'ja ju jo'.",
             items=_kana_items([(k, rs) for k, rs in COMBOS_2]),
             modes=("type", "pick"), sample=10),
    ]


UNITS = (
    _row_units()
    + _voiced_units()
    + _combo_units()
    + [Unit(key="h.sokuon", title="Small っ and long vowels", sub="きって · がっこう · おかあさん",
            intro="A small っ is a beat of silence that doubles the next consonant: "
                  "きって is 'kit-te'. A vowel written twice is held twice as long: "
                  "おかあさん is 'okaasan'. Long o is usually written おう (がっこう, "
                  "'gakkou' or 'gakkō'), and long e often えい (せんせい).",
            items=_word_items(SOKUON, "w"), modes=("type",), chart=True, sample=12),
       Unit(key="h.words", title="Reading real words", sub="Hiragana words you'll drill later",
            intro="Real words, in hiragana. Type how each one reads. You don't need the "
                  "meanings yet — they're shown after each answer.",
            items=_word_items(_lexicon_words(), "w"), modes=("type",), chart=False,
            sample=12)]
    + _pairs(_row_units(kata=True), "Katakana")
    + _voiced_units(kata=True)
    + _combo_units(kata=True)
    + [Unit(key="k.foreign", title="Katakana-only sounds", sub="ファ ティ ウィ チェ",
            intro="Loanwords need sounds Japanese didn't have, so katakana adds small "
                  "vowels: フ + ァ = fa, テ + ィ = ti (as in 'tea'), ウ + ィ = wi.",
            items=tuple(Item(id=k, text=k, answers=rs) for k, rs in FOREIGN),
            modes=("type", "pick")),
       Unit(key="k.words", title="Loanwords and ー", sub="コーヒー · テレビ · パン",
            intro="In katakana a long vowel is a dash, ー: コーヒー is 'koohii' (coffee). "
                  "Say it aloud and the English word usually jumps out.",
            items=_word_items(LOANWORDS, "w"), modes=("type",), chart=False, sample=12)]
)

TTS = "ja-JP"
LETTERS = "romaji"
