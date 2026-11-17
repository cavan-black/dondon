"""Japanese grammar skills, in teaching order. Scheduling lives in hub/grammar.py.

Each skill is a conjugation form (食べる → 食べました) or a pattern built from one
(食べる → 食べてもいい). Stages follow roughly the order textbooks teach them, so each
leans on the one before — you cannot build 〜てもいい before you can make the て-form.
"""
from ..grammar import Skill, Track
from .conjugate import ADJ_CLASSES, VERB_CLASSES, Word, conjugate

VERBS = frozenset(VERB_CLASSES)
ADJS = frozenset(ADJ_CLASSES)


def _form(f):
    return lambda w: conjugate(w, f)


def _plus(f, *tails):
    return lambda w: [a + t for t in tails for a in conjugate(w, f)]


def _contract(te_answers, tails):
    """て→ちゃ / で→じゃ, the way 〜てはいけない and 〜てしまう are actually said."""
    out = []
    for a in te_answers:
        head = a[:-1] + ("ちゃ" if a.endswith("て") else "じゃ")
        out += [head + t for t in tails]
    return out


def _te_wa_ikenai(w):
    te = conjugate(w, "te")
    return ([a + "はいけない" for a in te] + [a + "はいけません" for a in te] +
            [a + "はだめ" for a in te] + _contract(te, ["いけない", "だめ"]))


def _te_shimau(w):
    te = conjugate(w, "te")
    return [a + "しまう" for a in te] + _contract(te, ["う"])


def _te_oku(w):
    te = conjugate(w, "te")
    # 書いておく -> 書いとく, 読んでおく -> 読んどく
    return [a + "おく" for a in te] + [a[:-1] + ("とく" if a.endswith("て") else "どく")
                                      for a in te]


def _nakereba(w):
    nai = conjugate(w, "nai")
    out = [a[:-2] + "なければならない" for a in nai]
    out += [a[:-2] + "なければいけない" for a in nai]
    out += [a[:-2] + "なければなりません" for a in nai]
    out += [a[:-2] + "なきゃ" for a in nai] + [a[:-2] + "なくちゃ" for a in nai]
    out += [a + "といけない" for a in nai]
    return out


def _sou(w):
    """Looks like: 高そう, 静かそう, よさそう, なさそう (ない/いい take さ)."""
    out = []
    for s in (w.written, w.kana):
        if w.cls == "na":
            out.append(s + "そう")
        elif s.endswith("いい"):
            out.append(s[:-2] + "よさそう")
        elif s.endswith("ない"):
            out += [s[:-1] + "そう", s[:-1] + "さそう"]   # つまらなそう / つまらなさそう
        else:
            out.append(s[:-1] + "そう")
    return list(dict.fromkeys(out))


def _sugiru(w):
    if w.is_verb:
        return _plus("stem", "すぎる")(w)
    out = []
    for s in (w.written, w.kana):
        if w.cls == "na":
            out.append(s + "すぎる")
        elif s.endswith("いい"):
            out.append(s[:-2] + "よすぎる")
        else:
            out.append(s[:-1] + "すぎる")
    return list(dict.fromkeys(out))


def _vol_omou(w):
    return [a + t for t in ("とおもう", "と思う", "と思っている", "と思います")
            for a in conjugate(w, "vol")]


def _causative_te_kudasai(w):
    return [a[:-1] + "てください" for a in conjugate(w, "causative")]


def V(key, stage, title, jp, build, rule, forms, classes=VERBS):
    return Skill(key, stage, title, jp, classes, build, rule, frozenset(forms))


def A(key, stage, title, jp, build, rule, forms, classes=ADJS):
    return Skill(key, stage, title, jp, classes, build, rule, frozenset(forms))


STAGES = {
    1: "Polite verbs", 2: "Plain negative & past", 3: "The て-form",
    4: "Adjectives", 5: "Wanting & suggesting", 6: "Permission & prohibition",
    7: "Obligation & advice", 8: "Experience & sequence", 9: "Intention",
    10: "Potential", 11: "Conditionals", 12: "Commands", 13: "Passive",
    14: "Causative", 15: "Causative-passive", 16: "Nuance",
}

_GODAN = "Godan: change the final u-sound"
SKILLS = [
    V("v.masu", 1, "polite", "〜ます", _form("masu"),
      f"{_GODAN} to its i-sound + ます (書く→書きます). Ichidan: drop る + ます. "
      "する→します, 来る→来ます.", ["masu"]),
    V("v.masu_neg", 1, "polite negative", "〜ません", _form("masu_neg"),
      "ます-stem + ません (書きません, 食べません).", ["masu_neg"]),
    V("v.masu_past", 1, "polite past", "〜ました", _form("masu_past"),
      "ます-stem + ました.", ["masu_past"]),
    V("v.masu_neg_past", 1, "polite past negative", "〜ませんでした", _form("masu_neg_past"),
      "ます-stem + ませんでした.", ["masu_neg_past"]),

    V("v.nai", 2, "plain negative", "〜ない", _form("nai"),
      f"{_GODAN} to its a-sound + ない; う becomes わ (買う→買わない). Ichidan: drop る + "
      "ない. する→しない, 来る→来(こ)ない, ある→ない.", ["nai"]),
    V("v.ta", 2, "plain past", "〜た", _form("ta"),
      "Same sound changes as the て-form, with た/だ: う・つ・る→った, む・ぶ・ぬ→んだ, "
      "く→いた, ぐ→いだ, す→した. 行く→行った. Ichidan: drop る + た.", ["ta"]),
    V("v.nakatta", 2, "plain past negative", "〜なかった", _form("nakatta"),
      "ない-form, with ない → なかった.", ["nakatta"]),

    V("v.te", 3, "te-form", "〜て", _form("te"),
      "う・つ・る→って, む・ぶ・ぬ→んで, く→いて, ぐ→いで, す→して. 行く→行って "
      "is the exception. Ichidan: drop る + て. する→して, 来る→来て.", ["te"]),
    V("p.te_kudasai", 3, "please do", "〜てください", _plus("te", "ください"),
      "て-form + ください.", ["te"]),
    V("p.te_iru", 3, "is doing / state", "〜ている", _plus("te", "いる", "る"),
      "て-form + いる. Spoken: 〜てる.", ["te"]),

    A("a.masu_neg", 4, "polite negative", "〜くないです", _form("masu_neg"),
      "い-adj: drop い + くないです (or くありません). いい→よくないです. "
      "な-adj: + じゃないです / じゃありません.", ["masu_neg"]),
    A("a.nai", 4, "plain negative", "〜くない", _form("nai"),
      "い-adj: drop い + くない (いい→よくない). な-adj: + じゃない.", ["nai"]),
    A("a.ta", 4, "plain past", "〜かった", _form("ta"),
      "い-adj: drop い + かった (いい→よかった). な-adj: + だった.", ["ta"]),
    A("a.nakatta", 4, "plain past negative", "〜くなかった", _form("nakatta"),
      "い-adj: drop い + くなかった. な-adj: + じゃなかった.", ["nakatta"]),
    A("a.masu_past", 4, "polite past", "〜かったです", _form("masu_past"),
      "い-adj: drop い + かったです. な-adj: + でした.", ["masu_past"]),
    A("a.te", 4, "te-form (and...)", "〜くて", _form("te"),
      "い-adj: drop い + くて (いい→よくて). な-adj: + で.", ["te"]),
    A("a.adverb", 4, "adverb", "〜く / 〜に", _form("adverb"),
      "い-adj: drop い + く (早く). な-adj: + に (静かに).", ["adverb"]),
    A("p.naru", 4, "become", "〜くなる", _plus("adverb", "なる"),
      "Adverb form + なる: 高くなる, 静かになる, よくなる.", ["adverb"]),

    V("v.tai", 5, "want to", "〜たい", _form("tai"), "ます-stem + たい.", ["tai"]),
    V("v.tai_neg", 5, "don't want to", "〜たくない", _form("tai_neg"),
      "ます-stem + たくない (たい conjugates like an い-adjective).", ["tai_neg"]),
    V("v.vol_polite", 5, "let's", "〜ましょう", _form("vol_polite"),
      "ます-stem + ましょう.", ["vol_polite"]),
    V("p.mashou_ka", 5, "shall I / shall we?", "〜ましょうか", _plus("stem", "ましょうか"),
      "ます-stem + ましょうか.", ["vol_polite"]),

    V("p.te_mo_ii", 6, "may / it's OK to", "〜てもいい", _plus("te", "もいい", "もいいです"),
      "て-form + もいい.", ["te"]),
    V("p.te_wa_ikenai", 6, "must not", "〜てはいけない", _te_wa_ikenai,
      "て-form + はいけない. Spoken: 〜ちゃだめ / 〜じゃだめ.", ["te"]),
    V("p.nai_de_kudasai", 6, "please don't", "〜ないでください", _plus("nai", "でください"),
      "ない-form + でください.", ["nai"]),

    V("p.nakereba", 7, "must / have to", "〜なければならない", _nakereba,
      "ない-form, drop い, + ければならない (行かなければならない). Spoken: "
      "〜なきゃ, 〜なくちゃ, 〜ないといけない.", ["nai"]),
    V("p.ta_hou_ga_ii", 7, "you'd better", "〜たほうがいい",
      _plus("ta", "ほうがいい", "方がいい", "ほうがいいです"),
      "た-form + ほうがいい.", ["ta"]),
    V("p.nai_hou_ga_ii", 7, "you'd better not", "〜ないほうがいい",
      _plus("nai", "ほうがいい", "方がいい", "ほうがいいです"),
      "ない-form + ほうがいい.", ["nai"]),

    V("p.ta_koto_ga_aru", 8, "have done before", "〜たことがある",
      _plus("ta", "ことがある", "ことがあります", "事がある"),
      "た-form + ことがある.", ["ta"]),
    V("p.te_kara", 8, "after doing", "〜てから", _plus("te", "から"),
      "て-form + から.", ["te"]),
    V("p.mae_ni", 8, "before doing", "〜まえに", _plus("dict", "まえに", "前に"),
      "Dictionary form + まえに — always the dictionary form, even about the past.",
      ["vol"]),
    V("p.nagara", 8, "while doing", "〜ながら", _plus("stem", "ながら"),
      "ます-stem + ながら.", ["vol"]),

    V("v.vol", 9, "let's (plain) / volitional", "〜よう", _form("vol"),
      f"{_GODAN} to its o-sound + う (書こう, 飲もう). Ichidan: drop る + よう. "
      "する→しよう, 来る→来(こ)よう.", ["vol"]),
    V("p.you_to_omou", 9, "I'm thinking of doing", "〜ようと思う", _vol_omou,
      "Volitional + と思う.", ["vol"]),
    V("p.tsumori", 9, "intend to", "〜つもり",
      _plus("dict", "つもり", "つもりだ", "つもりです"),
      "Dictionary form + つもり.", ["vol"]),

    V("v.potential", 10, "can do", "〜られる", _form("potential"),
      f"{_GODAN} to its e-sound + る (書ける). Ichidan: drop る + られる (spoken "
      "〜れる). する→できる, 来る→来(こ)られる.", ["potential"]),
    V("p.koto_ga_dekiru", 10, "be able to (formal)", "〜ことができる",
      _plus("dict", "ことができる", "ことができます"),
      "Dictionary form + ことができる.", ["potential"]),

    V("v.ba", 11, "if (〜ば)", "〜ば", _form("ba"),
      f"{_GODAN} to its e-sound + ば (書けば). Ichidan: drop る + れば. "
      "する→すれば, 来る→来(く)れば.", ["ba"]),
    V("v.tara", 11, "if / when (〜たら)", "〜たら", _form("tara"),
      "た-form + ら.", ["tara"]),
    A("a.ba", 11, "if (〜ければ)", "〜ければ", _form("ba"),
      "い-adj: drop い + ければ (いい→よければ). な-adj: + なら.", ["ba"]),
    A("a.tara", 11, "if (〜かったら)", "〜かったら", _form("tara"),
      "い-adj: drop い + かったら. な-adj: + だったら.", ["tara"]),

    V("v.imperative", 12, "command", "〜ろ / 〜え", _form("imperative"),
      f"{_GODAN} to its e-sound (書け, 待て). Ichidan: drop る + ろ. する→しろ, "
      "来る→来(こ)い. Blunt — you'll hear it more than say it.", ["imperative"]),
    V("v.prohibitive", 12, "don't! (blunt)", "〜な", _form("prohibitive"),
      "Dictionary form + な.", ["prohibitive"]),

    V("v.passive", 13, "passive", "〜られる", _form("passive"),
      "Godan: ない-stem + れる (書かれる, 買われる). Ichidan: drop る + られる. "
      "する→される, 来る→来(こ)られる.", ["passive"]),

    V("v.causative", 14, "make / let do", "〜させる", _form("causative"),
      "Godan: ない-stem + せる (書かせる). Ichidan: drop る + させる. する→させる, "
      "来る→来(こ)させる.", ["causative"]),
    V("p.sasete_kudasai", 14, "please let me", "〜させてください", _causative_te_kudasai,
      "Causative, as an ichidan verb in て-form, + ください (書かせてください).",
      ["causative"]),

    V("v.caus_passive", 15, "be made to do", "〜させられる", _form("caus_passive"),
      "Godan: ない-stem + される (書かされる), or + せられる. す-verbs only take "
      "せられる (話させられる). Ichidan: drop る + させられる. する→させられる.",
      ["caus_passive"]),

    V("p.te_shimau", 16, "end up doing / do completely", "〜てしまう", _te_shimau,
      "て-form + しまう. Spoken: 〜ちゃう / 〜じゃう.", ["te"]),
    V("p.te_miru", 16, "try doing", "〜てみる", _plus("te", "みる"),
      "て-form + みる.", ["te"]),
    V("p.te_oku", 16, "do in advance", "〜ておく", _te_oku,
      "て-form + おく. Spoken: 〜とく / 〜どく.", ["te"]),
    A("p.sou", 16, "looks like", "〜そう", _sou,
      "い-adj: drop い + そう (高そう). な-adj: + そう. いい→よさそう.", ["stem"]),
    Skill("p.sugiru", 16, "too much", "〜すぎる", VERBS | ADJS, _sugiru,
          "Verb ます-stem / い-adj minus い / な-adj, + すぎる (食べすぎる, 高すぎる).",
          frozenset({"stem"})),
    V("p.yasui", 16, "easy to do", "〜やすい", _plus("stem", "やすい"),
      "ます-stem + やすい. Its opposite is 〜にくい.", ["stem"]),
]
TRACK = Track(SKILLS, STAGES)
BY_KEY = TRACK.by_key
