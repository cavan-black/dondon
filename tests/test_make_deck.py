"""The deck generator's mechanical checks and its write → review → drop pipeline,
with Claude stubbed out."""
import pytest

from tools import make_deck as M


def ja(**kw):
    base = dict(rank=1, word="学校", reading="がっこう", meaning="school", pos="noun",
                sentence="学校に行きます。", sentence_furigana="学校[がっこう]に 行[い]きます。",
                sentence_en="I go to school.")
    return M.Card(**{**base, **kw})


def es(**kw):
    base = dict(rank=1, word="la casa", reading="", meaning="house; home", pos="noun (f)",
                sentence="Mi casa es pequeña.", sentence_furigana="",
                sentence_en="My house is small.")
    return M.Card(**{**base, **kw})


def test_good_cards_pass():
    assert M.check("ja", ja()) == ([], [])
    assert M.check("es", es()) == ([], [])


@pytest.mark.parametrize("card,problem", [
    (ja(reading="学校"), "reading must be kana only"),
    (ja(sentence_furigana="学校[がっこう]に行[い]きます。"), "should start with kanji"),
    (ja(sentence_furigana="学校[がっこう]に 行[い]った。"), "doesn't spell the sentence"),
    (ja(sentence_furigana="学校[gakkou]に 行[い]きます。"), "isn't kana"),
    (ja(sentence_furigana="学校に行きます。"), "no furigana"),
    (ja(meaning=""), "empty meaning"),
])
def test_ja_hard_failures(card, problem):
    hard, _ = M.check("ja", card)
    assert any(problem in h for h in hard), hard


def test_soft_flags_go_to_review_not_the_bin():
    hard, soft = M.check("ja", ja(sentence="毎日勉強します。",
                                  sentence_furigana="毎日[まいにち] 勉強[べんきょう]します。"))
    assert not hard and soft
    hard, soft = M.check("es", es(sentence="Vivo en un piso."))
    assert not hard and soft
    # Accents don't defeat the containment check.
    assert M.check("es", es(word="el café", sentence="Tomo un cafe.")) == ([], [])


def test_card_chunk_reviews_fixes_and_drops(tmp_path, monkeypatch):
    words = [{"rank": 1, "lemma": "学校", "reading": "がっこう"},
             {"rank": 2, "lemma": "行く", "reading": "いく"}]
    calls = []

    def fake_ask(system, content, schema, effort="medium"):
        calls.append(schema.__name__)
        if schema is M.CardBatch:
            return M.CardBatch(cards=[ja(), ja(rank=2, word="行く", reading="学校")])
        # Reviewer fixes nothing — so rank 2 still has a kanji reading and is dropped.
        assert "rank 2: reading must be kana only" in content
        return M.ReviewBatch(cards=[M.ReviewedCard(card=ja(), changed=False, issue=""),
                                    M.ReviewedCard(card=ja(rank=2, word="行く",
                                                           reading="学校"),
                                                   changed=False, issue="")])

    monkeypatch.setattr(M, "ask", fake_ask)
    acc, drop = M.card_chunk("ja", str(tmp_path), 0, words)
    assert [c["rank"] for c in acc] == [1] and drop[0][0] == 2
    assert calls == ["CardBatch", "ReviewBatch"]

    # Cached: a second run makes no calls at all.
    calls.clear()
    acc2, _ = M.card_chunk("ja", str(tmp_path), 0, words)
    assert acc2 == acc and calls == []
