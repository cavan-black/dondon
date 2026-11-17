"""Reading and speaking: the speech scorer, Wikipedia text cleaning, the level
picker, passage checks, and adding a looked-up word to your vocab."""
import os

import pytest

from hub import speech, sources, tutor


# ------------------------------------------------------------------- speech scoring

def test_japanese_matches_kanji_or_kana():
    targets = ["学校に行きます。", "がっこうにいきます。"]
    assert speech.score("ja", targets, ["学校に行きます"])[0] == 1.0
    assert speech.score("ja", targets, ["がっこうにいきます"])[0] == 1.0
    # Katakana from the recogniser folds to hiragana.
    assert speech.score("ja", ["コーヒーをください"], ["こーひーをください"])[0] == 1.0


def test_best_alternative_wins():
    r, _, heard = speech.score("ja", ["ありがとう"], ["ありがと", "ありがとう"])
    assert r == 1.0 and heard == "ありがとう"


def test_spanish_ignores_accents_case_and_punctuation():
    assert speech.score("es", ["¿Dónde está la estación?"],
                        ["donde esta la estacion"])[0] == 1.0
    # ñ is a different letter, not an accent.
    assert speech.ratio("es", "año", "ano") < 1.0


def test_partial_is_partial():
    r = speech.ratio("es", "quiero un café con leche", "quiero un café")
    assert speech.CLOSE <= r < speech.GOOD
    assert speech.verdict(r)[0] == "mid"
    assert speech.verdict(0.2)[0] == "no" and speech.verdict(0.95)[0] == "ok"


def test_diff_marks_missed_words_with_accents_kept():
    out = speech.diff_html("es", "¿Dónde está la estación de tren?", "donde esta la estacion")
    assert "Dónde" in out and "estación" in out
    assert "wavy\">de<" in out and "wavy\">tren<" in out


def test_empty_heard_scores_zero():
    assert speech.ratio("ja", "こんにちは", "") == 0.0


# ------------------------------------------------------------------------ sources

def test_clean_drops_headings_and_back_matter():
    raw = ("ラーメンは料理である。\n\n== 歴史 ==\n明治時代に広まった。\n"
           "== 脚注 ==\n出典など\n")
    out = sources.clean(raw)
    assert "歴史" not in out and "明治時代" in out and "出典" not in out


def test_clean_cuts_long_text_at_a_sentence():
    raw = "Una frase corta. " * 400
    out = sources.clean(raw)
    assert len(out) <= sources.MAX_CHARS and out.rstrip().endswith(".")


def test_every_topic_has_keywords():
    for lang, topics in sources.TOPICS.items():
        assert len(topics) >= 6
        for name, words in topics.items():
            assert len(words) >= 6, (lang, name)
    assert not sources.has_on_this_day("ja") and sources.has_on_this_day("es")


# ------------------------------------------------------------------- levels/checks

@pytest.mark.parametrize("known,stage,level", [
    (0, 1, 1), (100, 2, 1), (100, 4, 2), (499, 3, 2), (860, 5, 3),
    (2000, 6, 4), (4000, 9, 5), (9000, 12, 6)])
def test_level_for(known, stage, level):
    assert tutor.level_for(known, stage) == level


def _passage(reading="がっこう", options=3, answer=0):
    T = tutor
    return T.Passage(title="t", title_en="t", sentences=[T.PassageSentence(
        tokens=[T.Token(t="学校", r=reading, d="学校", g="school"),
                T.Token(t="。", r="", d="", g="")], en="School.")],
        questions=[T.Question(q="?", options=["a", "b", "c"][:options], answer=answer)])


def test_passage_checks():
    assert tutor._passage_checks("ja", _passage()) == []
    assert tutor._passage_checks("ja", _passage(reading="ガッコウ")) == []
    assert any("isn't kana" in p for p in tutor._passage_checks("ja", _passage("gakkou")))
    assert any("3 options" in p for p in tutor._passage_checks("ja", _passage(options=2)))
    assert any("3 options" in p for p in tutor._passage_checks("ja", _passage(answer=3)))


# --------------------------------------------------------------- word → vocab

@pytest.fixture
def fixture_srs(tmp_path, monkeypatch):
    from hub import db, srs
    fixtures = os.path.join(os.path.dirname(__file__), "fixtures", "decks")
    monkeypatch.setattr(srs, "DECKS", fixtures)
    url = "sqlite:///" + str(tmp_path / "t.db").replace("\\", "/")
    eng = db.engine.__wrapped__(url) if hasattr(db.engine, "__wrapped__") else None
    if eng is None:
        pytest.skip("engine isn't wrapped")
    monkeypatch.setattr(db, "engine", lambda url_=None: eng)
    import streamlit as st
    st.session_state.clear() if hasattr(st.session_state, "clear") else None
    srs.word_index.clear()
    srs.deck.clear()
    return srs


def test_find_card_strips_spanish_articles():
    from hub import srs
    assert srs._bare("La casa") == "casa" and srs._bare("el perro") == "perro"
    assert srs._bare("casa") == "casa"


def test_introduce_makes_an_unanswered_due_card(fixture_srs, monkeypatch):
    srs = fixture_srs
    import datetime
    store = {}
    monkeypatch.setattr(srs, "rows", lambda email, lang: store)
    cid = srs.find_card("ja", "行く")
    assert cid
    assert srs.introduce("a@b", "ja", cid, datetime.date(2026, 1, 1))
    assert store[cid]["reps"] == 0
    assert not srs.introduce("a@b", "ja", cid, datetime.date(2026, 1, 1))   # once only
    q = srs.queue("a@b", "ja", {}, 0)
    assert q[0] == {"id": cid, "new": True}      # due now, and still new to you
