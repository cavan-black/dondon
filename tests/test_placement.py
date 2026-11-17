"""The placement test: what it asks, how it scores, and what it changes."""
import datetime, random

import pytest

from hub import basics as B, placement as P, stats
from hub.es import curriculum as ES
from hub.es.lexicon import WORDS as ES_WORDS
from hub.ja import curriculum as JA
from hub.ja.lexicon import WORDS as JA_WORDS

TODAY = datetime.date(2026, 11, 17)


def fresh():
    return {"skills": {}, "days": {}}


def cards(n, start=0):
    return [{"id": f"c{start + i}", "word": f"w{start + i}", "meaning": f"m{start + i}"}
            for i in range(n)]


# ---------------------------------------------------------------------- script

@pytest.mark.parametrize("code", ["ja", "es"])
def test_script_items_span_the_course_and_can_be_answered(code):
    items = P.script_items(code, random.Random(1))
    units = [u.key for u in B.units(code)]
    assert len(items) == P.SCRIPT_ITEMS
    assert items[0]["unit"] == units[0] and items[-1]["unit"] == units[-1]
    for d in items:
        item = B.items(code)[d["item"]]
        assert d["mode"] in ("type", "dictate")
        assert B.check(code, d, item.answers[0])[0], item.id


# ----------------------------------------------------------------------- vocab

def test_bands_split_tiers_in_rank_order():
    bs = P.bands([(1, cards(1500)), (2, cards(700, 1500))])
    assert [(t, len(c)) for t, c in bs] == [(1, 500), (1, 500), (1, 500), (2, 500), (2, 200)]
    assert bs[3][1][0]["id"] == "c1500"


def test_vocab_items_offer_the_answer_among_same_band_meanings():
    band = cards(500)
    for q in P.vocab_items(band, random.Random(2)):
        assert q["answer"] in q["options"] and len(set(q["options"])) == P.CHOICES
        assert all(o.startswith("m") for o in q["options"])


def test_guessing_is_corrected_for():
    assert P.band_known(5, 5) == 1.0
    assert P.band_known(0, 5) == 0.0
    assert P.band_known(1, 4) == 0.0              # a quarter right is pure chance
    assert P.band_known(4, 5) == pytest.approx((0.8 - 0.25) / 0.75)


def test_vocab_stops_after_two_weak_bands():
    assert not P.vocab_done([0.9, 0.1])
    assert P.vocab_done([0.9, 0.1, 0.2])
    assert not P.vocab_done([0.1, 0.9])


SIZES = {1: 1500, 2: 1500, 3: 1500}


def test_start_point_is_the_first_band_not_mostly_known():
    # Two bands known, the third not: start a thousand words into tier 1.
    assert P.start_point(SIZES, [(1, 1.0), (1, 0.9), (1, 0.5)]) == (1, 1000)
    # A whole tier known: the next tier from its top.
    assert P.start_point(SIZES, [(1, 1.0), (1, 0.9), (1, 0.86), (2, 0.5)]) == (2, 0)
    assert P.start_point(SIZES, [(1, 0.5), (1, 1.0)]) == (1, 0)
    # Every tested band known, the rest untested: start where the testing stopped.
    assert P.start_point(SIZES, [(1, 1.0)] * 3 + [(2, 1.0)]) == (2, 500)
    # A short last tier, all known: nothing new left there.
    assert P.start_point({1: 1500, 2: 200}, [(1, 1.0)] * 3 + [(2, 1.0)]) == (2, 200)


# --------------------------------------------------------------------- grammar

@pytest.mark.parametrize("track,words", [(JA.TRACK, JA_WORDS), (ES.TRACK, ES_WORDS)])
def test_every_stage_gets_four_to_six_answerable_drills(track, words):
    for n in track.stages:
        items = P.stage_items(track, n, words, set(), random.Random(n))
        assert P.STAGE_MIN <= len(items) <= P.STAGE_MAX
        for it in items:
            sk = track.by_key[it["skill"]]
            assert sk.stage == n and sk.answers(it["word"], it.get("cue"))


def test_stage_pass_mark():
    assert P.stage_passed([True, True, True, False])
    assert not P.stage_passed([True, True, False, False])
    assert not P.stage_passed([True] * 4 + [False] * 2)        # 4/6 < 75%
    assert P.stage_passed([True] * 5 + [False])
    assert not P.stage_passed([])


# ----------------------------------------------------------------------- apply

def test_apply_places_grammar_basics_and_vocab():
    T = JA.TRACK
    progress, ls = fresh(), {}
    res = {"script": 1.0, "stages": [1, 2],
           "bands": [(1, 500, 1.0), (1, 500, 0.9), (1, 500, 0.86), (2, 500, 0.4), (2, 500, 0.1)]}
    placed = P.apply("ja", T, progress, ls, res, TODAY, [], SIZES)
    assert B.status("ja", progress)["done"]
    assert T.current_stage(progress) == 3
    for s in T.skills:
        st = progress["skills"].get(s.key, {})
        if s.stage <= 2:
            assert st["box"] == P.PLACED_BOX and st["placed"]
            assert st["due"] == (TODAY + datetime.timedelta(days=7)).isoformat()
        else:
            assert not st
    assert (ls["start_tier"], ls["start_index"]) == (2, 0) == (placed["start_tier"],
                                                               placed["start_index"])
    assert placed["words_skipped"] == 500 + 450 + 430
    assert placed["words_other"] == 200 + 50
    assert progress["placement"] is placed


def test_apply_starts_part_way_into_a_tier():
    ls = {}
    placed = P.apply("ja", JA.TRACK, fresh(), ls,
                     {"bands": [(1, 500, 1.0), (1, 500, 1.0), (1, 500, 0.2), (2, 500, 0.0)]},
                     TODAY, [], SIZES)
    assert (ls["start_tier"], ls["start_index"]) == (1, 1000)
    assert placed["words_skipped"] == 1000 and placed["words_other"] == 100


def test_apply_never_moves_anything_back():
    T = JA.TRACK
    key = next(s.key for s in T.skills if s.stage == 1)
    progress = fresh()
    progress["skills"][key] = {"box": 5, "due": "2027-01-01"}
    ls = {"start_tier": 3}
    P.apply("ja", T, progress, ls, {"script": 0.2, "stages": [1], "bands": [(1, 500, 0.1)]},
            TODAY, [], SIZES)
    assert progress["skills"][key] == {"box": 5, "due": "2027-01-01"}
    assert ls["start_tier"] == 3
    assert not B.status("ja", progress)["done"]


def test_words_already_reviewed_are_not_counted_twice():
    rows = [{"reps": 2, "tier": 1, "introduced": TODAY}] * 300 + \
           [{"reps": 0, "tier": 1, "introduced": TODAY}] * 50
    placed = P.apply("ja", JA.TRACK, fresh(), {}, {"bands": [(1, 500, 1.0)] * 3},
                     TODAY, rows, SIZES)
    assert placed["words_skipped"] == 1500 - 300 and placed["start_tier"] == 2


def test_placed_skills_are_not_pace_and_placed_words_fade():
    T = JA.TRACK
    progress = fresh()
    placed = P.apply("ja", T, progress, {}, {"stages": [1, 2, 3],
                                               "bands": [(1, 500, 1.0), (2, 500, 0.6)]},
                     TODAY, [], {1: 500, 2: 1500})
    assert stats.pace(T, progress, [], TODAY)[1] == 0
    assert stats.placement_words(placed, []) == 500 + 300
    later = TODAY + datetime.timedelta(days=3)
    rows = [{"reps": 1, "tier": 2, "introduced": later}] * 120
    assert stats.placement_words(placed, rows) == 500 + 180
    rows *= 3
    assert stats.placement_words(placed, rows) == 500


def test_skipping_records_it_and_counts_nothing():
    progress = fresh()
    P.skip(progress, TODAY)
    assert progress["placement"]["skipped"]
    assert stats.placement_words(progress["placement"], []) == 0


def test_new_cards_skip_what_placement_found_known(monkeypatch):
    from hub import srs
    decks = {1: {"cards": cards(1500)}, 2: {"cards": cards(1500, 1500)}}
    monkeypatch.setattr(srs, "tiers", lambda lang: [1, 2])
    monkeypatch.setattr(srs, "deck", lambda lang, t: decks[t])
    monkeypatch.setattr(srs, "all_cards", lambda lang: {c["id"]: {**c, "tier": t}
                                                         for t, d in decks.items()
                                                         for c in d["cards"]})
    monkeypatch.setattr(srs, "rows", lambda email, lang: {})
    ls = {"start_tier": 1, "start_index": 1000, "new_per_day": 3}
    q = srs.queue("a@b", "ja", ls, 0)
    assert [x["id"] for x in q] == ["c1000", "c1001", "c1002"]
    assert srs.current_tier("a@b", "ja", ls) == 1
    # Later tiers start from their top.
    ls = {"start_tier": 1, "start_index": 1500, "new_per_day": 2}
    assert [x["id"] for x in srs.queue("a@b", "ja", ls, 0)] == ["c1500", "c1501"]
