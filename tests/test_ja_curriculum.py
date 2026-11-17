import datetime

import pytest

from hub import grammar as G
from hub.ja import curriculum as C
from hub.ja.kana import normalize
from hub.ja.lexicon import WORDS

T = C.TRACK

V = {w.written: w for w in WORDS}
TODAY = datetime.date(2026, 11, 17)


def test_every_skill_builds_for_every_eligible_word():
    for s in C.SKILLS:
        pool = T.eligible_words(s, WORDS)
        assert pool, s.key
        for w in pool:
            got = s.build(w)
            assert got and all(got), (s.key, w.written)


@pytest.mark.parametrize("skill,word,answer", [
    ("p.te_kudasai", "書く", "書いてください"), ("p.te_iru", "読む", "読んでる"),
    ("p.te_wa_ikenai", "食べる", "食べちゃだめ"), ("p.te_wa_ikenai", "飲む", "のんじゃいけない"),
    ("p.nakereba", "行く", "行かなければならない"), ("p.nakereba", "行く", "いかなきゃ"),
    ("p.nakereba", "する", "しないといけない"), ("p.nakereba", "来る", "こなくちゃ"),
    ("p.ta_koto_ga_aru", "行く", "行ったことがある"), ("p.mae_ni", "寝る", "寝る前に"),
    ("p.nagara", "歩く", "歩きながら"), ("p.you_to_omou", "買う", "買おうと思う"),
    ("p.sasete_kudasai", "書く", "書かせてください"), ("p.sasete_kudasai", "する", "させてください"),
    ("p.te_shimau", "忘れる", "忘れちゃう"), ("p.te_shimau", "飲む", "飲んじゃう"),
    ("p.te_oku", "買う", "買っとく"), ("p.te_oku", "読む", "読んどく"),
    ("p.sou", "高い", "高そう"), ("p.sou", "いい", "よさそう"), ("p.sou", "静か", "静かそう"),
    ("p.sou", "つまらない", "つまらなさそう"), ("p.sugiru", "食べる", "食べすぎる"),
    ("p.sugiru", "高い", "高すぎる"), ("p.naru", "静か", "静かになる"), ("p.naru", "いい", "よくなる"),
    ("v.masu", "勉強する", "benkyou shimasu"), ("v.te", "行く", "itte"),
])
def test_patterns(skill, word, answer):
    ok, expected, _ = G.check(C.BY_KEY[skill], V[word], None, answer, normalize)
    assert ok, expected


def test_wrong_answers_rejected():
    for skill, word, answer in [("v.te", "行く", "行いて"), ("v.nai", "買う", "買あない"),
                                ("v.potential", "帰る", "帰られる"), ("a.nai", "いい", "いくない"),
                                ("v.caus_passive", "話す", "話さされる")]:
        ok, _, _ = G.check(C.BY_KEY[skill], V[word], None, answer, normalize)
        assert not ok, (skill, word, answer)


def test_stative_words_are_not_drilled_on_odd_forms():
    for key in ("v.potential", "v.imperative", "v.passive", "p.tsumori"):
        pool = {w.written for w in T.eligible_words(C.BY_KEY[key], WORDS)}
        assert "ある" not in pool and "分かる" not in pool


def test_stage_progression():
    p = {"skills": {}, "days": {}}
    assert T.current_stage(p) == 1
    assert [s.stage for s in T.new_skills(p)] == [1, 1, 1]
    stage1 = [s.key for s in C.SKILLS if s.stage == 1]
    T.record(p, TODAY, {k: [True] * 5 for k in stage1})      # tests out of stage 1
    assert all(p["skills"][k]["box"] == 3 for k in stage1)
    assert T.current_stage(p) == 2


def test_failing_drops_to_box_one_and_due_tomorrow():
    p = {"skills": {"v.te": {"box": 4, "seen": 10, "right": 9, "due": "2026-11-17"}},
         "days": {}}
    moves = T.record(p, TODAY, {"v.te": [True, False, False]})
    assert moves["v.te"] == (4, 1)
    assert p["skills"]["v.te"]["due"] == "2026-11-18"


def test_free_practice_leaves_schedule_alone():
    p = {"skills": {"v.te": {"box": 2, "seen": 3, "right": 3, "due": "2026-11-20"}},
         "days": {}}
    T.record(p, TODAY, {"v.te": [False, False]}, schedule=False)
    assert p["skills"]["v.te"]["box"] == 2 and p["skills"]["v.te"]["seen"] == 5


def test_session_introduces_new_skills_with_lessons():
    p = {"skills": {}, "days": {}}
    lessons, items = T.build_session(p, TODAY, WORDS, known=set())
    assert [s.key for s in lessons] == ["v.masu", "v.masu_neg", "v.masu_past"]
    assert len(items) == 15 and {i["skill"] for i in items} == {s.key for s in lessons}
