"""The Basics course: kana checking and data, Spanish sound data, and the unit engine."""
import random, unicodedata

import pytest

from hub import basics as B
from hub.es import sounds as S
from hub.ja import kana_course as K
from hub.ja.kana import kata_to_hira

JA = B.items("ja")
ES = B.items("es")


def ok_ja(item_id, typed):
    return B.check("ja", {"item": item_id, "mode": "type"}, typed)[0]


# ------------------------------------------------------------------- Japanese

@pytest.mark.parametrize("kana,typed", [
    ("し", "shi"), ("し", "si"), ("ち", "chi"), ("ち", "ti"), ("つ", "tsu"), ("つ", "tu"),
    ("ふ", "fu"), ("ふ", "hu"), ("じ", "ji"), ("じ", "zi"), ("ぢ", "ji"), ("ぢ", "di"),
    ("づ", "zu"), ("づ", "du"), ("を", "wo"), ("を", "o"), ("ん", "n"), ("ん", "nn"),
    ("じゃ", "ja"), ("じゃ", "zya"), ("じゃ", "jya"), ("しゃ", "sha"), ("しゃ", "sya"),
    ("ちょ", "cho"), ("ちょ", "tyo"), ("ら", "la"), ("シ", "shi"), ("ツ", "TSU"),
    ("ティ", "ti"), ("ファ", "fa"), ("ウィ", "wi"),
    # the kana itself, either script
    ("か", "か"), ("カ", "か"), ("か", "カ"),
    ("w:がっこう", "gakkou"), ("w:がっこう", "gakkoo"), ("w:がっこう", "gakkō"),
    ("w:コーヒー", "koohii"), ("w:コーヒー", "kōhī"), ("w:コーヒー", "こーひー"),
    ("w:きって", "kitte"), ("w:ちょっと", "chotto"), ("w:せんせい", "sensei"),
    ("w:せんせい", "sensee"), ("w:ファン", "fan"), ("w:カフェ", "kafe"),
    ("w:メニュー", "menyuu"), ("w:サッカー", "sakkaa"), ("w:フォーク", "fooku"),
])
def test_accepted_spellings(kana, typed):
    assert ok_ja(kana, typed), (kana, typed)


@pytest.mark.parametrize("kana,typed", [
    ("し", "su"), ("つ", "su"), ("ぬ", "me"), ("w:きって", "kite"),
    ("w:おばあさん", "obasan"), ("w:コーヒー", "kohi"), ("ン", "so"), ("じゃ", "jo"),
])
def test_rejected_spellings(kana, typed):
    assert not ok_ja(kana, typed)


def test_every_kana_item_has_romaji_that_reads_back():
    for i in JA.values():
        assert i.answers and all(a == a.lower() for a in i.answers), i.id
        if i.id.startswith("w:"):
            continue
        # The canonical romaji must check as right, through the hiragana route too.
        assert K.fold(K.to_hiragana(i.answers[0])) == K.fold(kata_to_hira(i.text)) \
            or i.text in ("ティ", "ディ", "ウォ"), (i.id, i.answers[0])
        # ...and those three are taken by ち, ぢ, を in the shared table, so they are
        # matched from the item's own list instead.
        assert ok_ja(i.id, i.answers[0])


def test_word_romaji_reads_back():
    for i in JA.values():
        if i.id.startswith("w:"):
            assert ok_ja(i.id, i.answers[0]), (i.text, i.answers[0])


def test_all_base_kana_in_both_scripts():
    hira = {i.text for i in JA.values() if len(i.text) == 1 and "ぁ" <= i.text <= "ゖ"}
    kata = {i.text for i in JA.values() if len(i.text) == 1 and "ァ" <= i.text <= "ヺ"}
    assert len(hira) == 46 + 25 and len(kata) == 46 + 25
    assert {K.hira_to_kata(h) for h in hira} == kata


def test_mnemonics_for_every_base_kana():
    for u in B.units("ja"):
        if u.key.split(".")[-1] in {r for r, _ in K.ROWS} or "+" in u.key and u.key.startswith("k."):
            for i in u.items:
                assert i.hint, i.id


def test_options_include_answer_once_and_no_sound_alikes():
    rng = random.Random(1)
    for u in B.units("ja"):
        if "pick" not in u.modes:
            continue
        pool = B._seen_pool("ja", {}, u)
        for i in u.items:
            for _ in range(5):
                opts = K.options(i, pool, B.OPTIONS, rng)
                assert opts.count(i.text) == 1
                assert len(opts) == len(set(opts)) == B.OPTIONS, (i.id, opts)
                folded = [K.fold(kata_to_hira(o)) for o in opts]
                assert len(set(folded)) == len(folded), (i.id, opts)


def test_lookalikes_used_first():
    pool = [i for u in B.units("ja") for i in u.items]
    opts = K.options(JA["シ"], pool, 4, random.Random(0))
    assert {"ツ", "ソ", "ン", "ノ"} & set(opts) and "シ" in opts


def test_ids_unique():
    for code in ("ja", "es"):
        ids = [i.id for u in B.units(code) for i in u.items]
        assert len(ids) == len(set(ids)), code


# -------------------------------------------------------------------- Spanish

ACUTE = set("áéíóú")


@pytest.mark.parametrize("words", [S.STRESS, S.ACCENTS])
def test_stress_data_follows_the_rules(words):
    for w, syl, i, _ in words:
        assert "".join(syl) == w, w
        assert 0 <= i < len(syl), w
        accented = [j for j, s in enumerate(syl) if ACUTE & set(s)]
        if not accented:
            assert i == S.default_stress(syl), (w, "unaccented word must follow the rule")
        else:
            assert accented == [i], (w, "the accent marks the stressed syllable")
            hiatus = any(c in "íú" for c in syl[i]) and len(syl) > 1
            assert i != S.default_stress(syl) or hiatus, (w, "accent with no reason")


def test_stress_unit_has_no_accents_and_accent_unit_all_do():
    assert not any(ACUTE & set(w) for w, *_ in S.STRESS)
    assert all(ACUTE & set(w) for w, *_ in S.ACCENTS)


def test_spanish_words_are_lowercase_words_with_meanings():
    for u in B.units("es"):
        for i in u.items:
            assert i.hint, i.id
            if u.key != "punct":
                assert i.text == i.text.lower() or i.text == "España", i.id
                assert unicodedata.normalize("NFC", i.text) == i.text


def dictate(item_id, typed):
    return B.check("es", {"item": item_id, "mode": "dictate"}, typed)


def test_dictation():
    assert dictate("vowels:casa", "Casa")[:2] == (True, False)
    assert dictate("accents:café", "cafe")[:2] == (False, True)           # accent: near miss
    ok, near, _, note = dictate("h:hola", "ola")                           # silent h
    assert ok and note
    assert dictate("bv:vaca", "baca")[0]                                   # b = v
    assert dictate("cqz:zapato", "sapato")[0]                              # seseo
    assert dictate("cqz:queso", "keso")[0]
    assert dictate("lly:llave", "yave")[0]
    assert not dictate("r:perro", "pero")[0]                               # r ≠ rr
    assert not dictate("enye:año", "ano")[0]                               # ñ matters
    assert not dictate("gu:guerra", "gerra")[0]                            # ge = je
    assert dictate("gu:pingüino", "pinguino")[:2] == (False, True)
    assert dictate("punct:¿Cómo estás?", "como estás")[0] is False
    assert dictate("punct:¿Cómo estás?", "cómo estás")[:2] == (True, False)
    assert dictate("punct:¡Hola!", "hola")[:2] == (True, False)


def test_stress_check():
    d = {"item": "accents:café", "mode": "stress"}
    assert B.check("es", d, 1)[0] and not B.check("es", d, 0)[0]


# --------------------------------------------------------------------- engine

def test_status_skip_and_unlock():
    p = {}
    s = B.status("ja", p)
    assert not s["done"] and s["units_done"] == 0 and s["next_key"] == "h.a"
    states = B.unit_states("ja", p)
    assert states[0][1] == "current" and all(st == "locked" for _, st in states[1:])
    assert not B.can_start("ja", p, "h.ka")
    B.skip("ja", p)
    s = B.status("ja", p)
    assert s["done"] and s["skipped"] and s["units_done"] == s["units_total"]
    assert all(st == "passed" for _, st in B.unit_states("ja", p))
    B.unskip("ja", p)
    assert not B.status("ja", p)["done"]


def test_round_and_record_passes_at_90():
    p = {}
    rng = random.Random(3)
    drills = B.build_round("ja", p, "h.a", rng)
    assert len(drills) == 10 and {d["mode"] for d in drills} == {"type", "pick"}
    assert not any(d["review"] for d in drills)       # nothing passed yet to review
    results = [(d["item"], d["unit"], True, d["review"]) for d in drills]
    results[0] = results[0][:2] + (False,) + results[0][3:]
    out = B.record("ja", p, results, "h.a")
    assert out["passed"] and abs(out["unit_pct"] - 0.9) < 1e-9
    assert B.status("ja", p)["next_key"] == "h.ka"

    drills = B.build_round("ja", p, "h.ka", rng)
    reviews = [d for d in drills if d["review"]]
    assert reviews and all(d["unit"] == "h.a" for d in reviews)
    # 8 of 10 on the unit fails it, however well the review items went.
    results = [(d["item"], d["unit"], not d["review"] and i >= 2 or d["review"], d["review"])
               for i, d in enumerate(sorted(drills, key=lambda d: d["review"]))]
    out = B.record("ja", p, results, "h.ka")
    assert not out["passed"] and "h.ka" not in B.state(p)["passed"]
    assert B.state(p)["items"]["あ"][1] >= 2


def test_word_units_sample_and_stress_rounds():
    rng = random.Random(0)
    d = B.build_round("ja", {}, "h.words", rng)
    assert len(d) == 12 and all(x["mode"] == "type" for x in d)
    d = B.build_round("es", {}, "accents", rng)
    assert {x["mode"] for x in d} == {"stress", "dictate"} and len(d) == 20
    assert all(x["options"] == list(range(len(ES[x["item"]].syllables)))
               for x in d if x["mode"] == "stress")


def test_big_units_cap_but_cover_every_sampled_item():
    d = B.build_round("ja", {}, "k.combo", random.Random(5))
    assert len(d) <= B.UNIT_ROUND_MAX
    assert len({x["item"] for x in d}) == 15


def test_review_round_weakest_first():
    p = {}
    B.skip("es", p)
    B.state(p)["items"]["vowels:casa"] = [0, 5]
    d = B.build_review("es", p, random.Random(0), n=5)
    assert len(d) == 5 and "vowels:casa" in {x["item"] for x in d}
