"""Native recordings: which titles match which words, and finding them again."""
from hub import audio
from tools import fetch_audio as F


def test_title_words_handle_hyphenated_speakers_and_varieties():
    ja = "File:LL-Q5287 (jpn)-Fukujinzuke-今年.wav"
    assert F.title_words("ja", ja) == ["今年"]
    es = "File:LL-Q1321 (spa)-Noaius Paticus-(American Spanish) Muñoz.wav"
    assert F.title_words("es", es) == ["muñoz"]
    assert "casa" in F.title_words("es", "File:LL-Q1321 (spa)-Some-User-Casa.wav")
    assert F.title_words("ja", "File:LL-Q1321 (spa)-X-casa.wav") == []


def test_japanese_candidates_are_strict():
    # Kanji words don't fall back to their kana: homophones differ in pitch accent.
    assert F.candidates("ja", "橋", "はし") == ["橋"]
    assert F.candidates("ja", "かわいい", "かわいい") == ["かわいい"]
    # A する-verb may use its noun's recording.
    assert F.candidates("ja", "練習する", "れんしゅうする") == ["練習する", "練習"]
    assert F.candidates("ja", "する", "する") == ["する"]


def test_spanish_candidates_drop_the_article():
    assert F.candidates("es", "la casa", "") == ["la casa", "casa"]
    assert F.candidates("es", "hablar", "") == ["hablar"]


def test_only_free_licences():
    for ok in ("CC0", "CC BY 4.0", "CC BY-SA 4.0", "CC BY-SA 3.0", "Public domain"):
        assert F.FREE.match(ok), ok
    for no in ("CC BY-NC 4.0", "CC BY-NC-SA 4.0", "CC BY-ND 4.0", "All rights reserved"):
        assert not F.FREE.match(no), no


def test_find_and_credit(monkeypatch):
    rec = {"url": "u", "page": "p", "speaker": "Ana", "licence": "CC0", "says": "casa",
           "variety": ""}
    audio._index.clear()
    monkeypatch.setattr(audio, "_index", lambda lang: {"casa": [rec, rec], "hablar": [rec]})
    assert audio.find("es", "La Casa") == [rec, rec]
    assert audio.find("es", "nada", "hablar") == [rec]
    assert audio.find("es", "nada") == []
    c = audio.credit([rec, rec], "la casa")
    assert "Ana" in c and "CC0" in c and "says <b>casa</b>" in c and "2 voices" in c
    assert audio.credit([]) == ""


def test_the_shipped_lists_are_well_formed():
    import json, os
    for lang in ("ja", "es"):
        path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "audio",
                            f"{lang}.json")
        words = json.load(open(path, encoding="utf-8"))["words"]
        assert len(words) > 150
        for w, recs in words.items():
            assert 1 <= len(recs) <= F.PER_WORD
            for r in recs:
                assert r["url"].startswith("https://upload.wikimedia.org/") and "?" not in r["url"]
                assert F.FREE.match(r["licence"]) and r["speaker"] and "\n" not in r["speaker"]
