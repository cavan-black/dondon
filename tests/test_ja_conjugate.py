"""Conjugation is the one thing the drills must never get wrong — a drill that marks a
correct answer wrong teaches the wrong form. These cases cover every class, every form,
and the irregulars that rule-based conjugators usually trip on.

Run:  python -m pytest tests
"""
import pytest

from hub.ja.conjugate import Word, conjugate, kana_of
from hub.ja.kana import normalize
from hub.ja.lexicon import WORDS

V = {w.written: w for w in WORDS}

CASES = [
    # word, form, canonical answer
    ("書く", "masu", "書きます"), ("書く", "nai", "書かない"), ("書く", "te", "書いて"),
    ("書く", "ta", "書いた"), ("書く", "potential", "書ける"), ("書く", "passive", "書かれる"),
    ("書く", "causative", "書かせる"), ("書く", "caus_passive", "書かされる"),
    ("書く", "imperative", "書け"), ("書く", "vol", "書こう"), ("書く", "ba", "書けば"),
    ("書く", "tara", "書いたら"), ("書く", "prohibitive", "書くな"),
    ("書く", "masu_neg_past", "書きませんでした"), ("書く", "tai_neg", "書きたくない"),
    ("行く", "te", "行って"), ("行く", "ta", "行った"), ("行く", "tara", "行ったら"),
    ("泳ぐ", "te", "泳いで"), ("泳ぐ", "ta", "泳いだ"),
    ("話す", "te", "話して"), ("話す", "caus_passive", "話させられる"),
    ("待つ", "te", "待って"), ("待つ", "nai", "待たない"), ("待つ", "masu", "待ちます"),
    ("死ぬ", "te", "死んで"), ("遊ぶ", "te", "遊んで"), ("読む", "ta", "読んだ"),
    ("買う", "nai", "買わない"), ("買う", "te", "買って"), ("買う", "passive", "買われる"),
    ("帰る", "nai", "帰らない"), ("帰る", "te", "帰って"), ("帰る", "potential", "帰れる"),
    ("変える", "nai", "変えない"), ("変える", "te", "変えて"),
    ("ある", "nai", "ない"), ("ある", "nakatta", "なかった"), ("ある", "te", "あって"),
    ("食べる", "masu", "食べます"), ("食べる", "nai", "食べない"), ("食べる", "te", "食べて"),
    ("食べる", "potential", "食べられる"), ("食べる", "passive", "食べられる"),
    ("食べる", "causative", "食べさせる"), ("食べる", "caus_passive", "食べさせられる"),
    ("食べる", "imperative", "食べろ"), ("食べる", "vol", "食べよう"), ("食べる", "ba", "食べれば"),
    ("する", "masu", "します"), ("する", "nai", "しない"), ("する", "te", "して"),
    ("する", "potential", "できる"), ("する", "passive", "される"), ("する", "causative", "させる"),
    ("する", "imperative", "しろ"), ("する", "vol", "しよう"), ("する", "ba", "すれば"),
    ("勉強する", "potential", "勉強できる"), ("勉強する", "te", "勉強して"),
    ("来る", "masu", "来ます"), ("来る", "nai", "来ない"), ("来る", "te", "来て"),
    ("来る", "potential", "来られる"), ("来る", "imperative", "来い"), ("来る", "vol", "来よう"),
    ("来る", "ba", "来れば"), ("来る", "caus_passive", "来させられる"),
    ("高い", "nai", "高くない"), ("高い", "ta", "高かった"), ("高い", "nakatta", "高くなかった"),
    ("高い", "te", "高くて"), ("高い", "adverb", "高く"), ("高い", "ba", "高ければ"),
    ("高い", "masu_neg", "高くないです"),
    ("いい", "nai", "よくない"), ("いい", "ta", "よかった"), ("いい", "masu", "いいです"),
    ("かっこいい", "ta", "かっこよかった"),
    ("静か", "nai", "静かじゃない"), ("静か", "ta", "静かだった"), ("静か", "te", "静かで"),
    ("静か", "adverb", "静かに"), ("静か", "masu_neg_past", "静かじゃなかったです"),
]


@pytest.mark.parametrize("word,form,expected", CASES)
def test_canonical(word, form, expected):
    assert conjugate(V[word], form)[0] == expected


KANA = [
    ("来る", "nai", "こない"), ("来る", "masu", "きます"), ("来る", "potential", "こられる"),
    ("来る", "ba", "くれば"), ("勉強する", "masu", "べんきょうします"), ("行く", "te", "いって"),
]


@pytest.mark.parametrize("word,form,expected", KANA)
def test_kana_reading(word, form, expected):
    assert kana_of(V[word], form) == expected


def test_alternates_accepted():
    assert "食べれる" in conjugate(V["食べる"], "potential")
    assert "書かせられる" in conjugate(V["書く"], "caus_passive")
    assert "話さされる" not in conjugate(V["話す"], "caus_passive")
    assert "静かではない" in conjugate(V["静か"], "nai")
    assert "高くありません" in conjugate(V["高い"], "masu_neg")
    assert "こない" in conjugate(V["来る"], "nai")      # kana spelling of 来ない


def test_every_word_conjugates_every_form():
    forms = ["dict", "stem", "masu", "masu_neg", "masu_past", "masu_neg_past", "nai", "ta",
             "nakatta", "te", "tara", "ba", "nakereba"]
    verb_only = ["tai", "tai_neg", "vol", "vol_polite", "potential", "passive", "causative",
                 "caus_passive", "imperative", "prohibitive"]
    for w in WORDS:
        for f in forms + (verb_only if w.is_verb else ["adverb"]):
            got = conjugate(w, f)
            assert got and all(got), (w.written, f)


def test_lexicon_is_well_formed():
    seen = set()
    for w in WORDS:
        assert (w.written, w.cls) not in seen, w.written
        seen.add((w.written, w.cls))
        if w.is_verb:
            assert w.kana[-1] in "うくぐすつぬぶむる", w.written
        if w.cls == "ichidan":
            assert w.kana[-2] in "いきぎしじちにひびぴみりえけげせぜてでねへべぺめれ", w.written
        if w.cls == "i":
            assert w.kana.endswith("い"), w.written


@pytest.mark.parametrize("typed,expected", [
    ("tabeta", "たべた"), ("TABETA", "たべた"), ("itte", "いって"), ("kitte", "きって"),
    ("benkyou shimasu", "べんきょうします"), ("konbanwa", "こんばんわ"), ("hon", "ほん"),
    ("shinbun", "しんぶん"), ("kan'i", "かんい"), ("ジュース", "じゅーす"), ("食べた。", "食べた"),
    ("chotto", "ちょっと"), ("matcha", "まっちゃ"),
])
def test_normalize(typed, expected):
    assert normalize(typed) == expected
