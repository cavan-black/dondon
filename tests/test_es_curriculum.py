import datetime

import pytest

from hub import grammar
from hub.es import curriculum as C
from hub.es.lexicon import WORDS
from hub.es.text import fold, normalize

V = {w.written: w for w in WORDS}
TODAY = datetime.date(2026, 11, 17)
T = C.TRACK


def test_every_skill_builds_for_every_eligible_word_and_cue():
    for s in C.SKILLS:
        pool = T.eligible_words(s, WORDS)
        assert pool, s.key
        for w in pool:
            for cue in s.cues:
                got = s.answers(w, cue)
                assert got and all(got), (s.key, w.written, cue)


def test_skills_are_well_formed():
    assert set(s.stage for s in C.SKILLS) == set(C.STAGES)
    for s in C.SKILLS:
        assert s.rule and s.title and s.shape, s.key
        for cue in s.cues:
            assert cue is None or cue in C.CUE_LABELS, (s.key, cue)
        if s.key.startswith("es.imperative") or s.key == "es.neg_imperative":
            assert "yo" not in s.cues
            assert all(c in C.COMMAND_CUE_LABELS for c in s.cues)
    assert "vosotros" not in C.PERSONS and "vosotros" in C.PERSONS_WITH_VOSOTROS


def test_early_skills_only_draw_the_verbs_their_rule_covers():
    pool = lambda key: {w.written for w in T.eligible_words(C.BY_KEY[key], WORDS)}
    reg = pool("es.present_reg")
    assert "hablar" in reg and "comer" in reg and "vivir" in reg
    assert not reg & {"tener", "pensar", "hacer", "conocer", "ser", "construir"}
    stem = pool("es.present_stem")
    assert {"pensar", "contar", "pedir", "jugar", "dormir"} <= stem
    assert "hablar" not in stem and "tener" not in stem
    assert {"hacer", "conocer", "saber", "dar", "ver"} <= pool("es.present_yo")
    assert {"ser", "estar", "ir", "tener"} <= pool("es.present_core")
    pret = pool("es.preterite_reg")
    assert {"hablar", "buscar", "pensar", "volver"} <= pret
    assert not pret & {"pedir", "leer", "tener", "ir", "hacer", "dar"}
    assert {"pedir", "dormir", "leer", "oír"} <= pool("es.preterite_shift")
    assert {"tener", "hacer", "ser", "dar", "conducir"} <= pool("es.preterite_strong")


def test_odd_forms_are_never_drilled():
    cmd = {w.written for w in T.eligible_words(C.BY_KEY["es.imperative_tu"], WORDS)}
    assert "poder" not in cmd and "haber" not in cmd
    prog = {w.written for w in T.eligible_words(C.BY_KEY["es.progressive"], WORDS)}
    assert "estar" not in prog
    perf = {w.written for w in T.eligible_words(C.BY_KEY["es.present_perfect"], WORDS)}
    assert "haber" not in perf


@pytest.mark.parametrize("skill,word,cue,answer", [
    ("es.present_reg", "hablar", "yo", "hablo"),
    ("es.present_reg", "hablar", "yo", "Yo hablo"),
    ("es.present_reg", "comer", "ellos", "ellos comen."),
    ("es.present_stem", "pensar", "nosotros", "pensamos"),
    ("es.ir_a", "comer", "yo", "voy a comer"),
    ("es.ir_a", "comer", "nosotros", "Nosotros vamos a comer"),
    ("es.tener_que", "trabajar", "tú", "tienes que trabajar"),
    ("es.progressive", "dormir", "él", "está durmiendo"),
    ("es.gerund", "leer", None, "leyendo"),
    ("es.participle", "escribir", None, "escrito"),
    ("es.preterite_strong", "hacer", "él", "hizo"),
    ("es.imperative_tu", "hablar", "tú", "¡Habla!"),
    ("es.imperative_formal", "ir", "nosotros", "vamos"),
    ("es.imperative_formal", "ir", "nosotros", "vayamos"),
    ("es.neg_imperative", "decir", "tú", "¡No digas!"),
    ("es.imperfect_subjunctive", "tener", "yo", "tuviese"),
    ("es.imperfect_subjunctive", "tener", "nosotros", "tuviéramos"),
])
def test_accepts(skill, word, cue, answer):
    ok, expected, _ = grammar.check(C.BY_KEY[skill], V[word], cue, answer, normalize, fold)
    assert ok, expected


@pytest.mark.parametrize("skill,word,cue,answer", [
    ("es.preterite_reg", "hablar", "yo", "hable"),        # accent only
    ("es.preterite_strong", "hacer", "él", "hico"),
    ("es.neg_imperative", "comer", "tú", "no come"),
    ("es.present_stem", "pensar", "nosotros", "piensamos"),
    ("es.imperative_formal", "ir", "nosotros", "no vamos"),
])
def test_rejects(skill, word, cue, answer):
    ok, _, _ = grammar.check(C.BY_KEY[skill], V[word], cue, answer, normalize, fold)
    assert not ok


def test_accent_only_miss_is_near():
    ok, expected, near = grammar.check(C.BY_KEY["es.preterite_reg"], V["hablar"], "yo",
                                       "hable", normalize, fold)
    assert not ok and near and expected == ["hablé"]
    ok, _, near = grammar.check(C.BY_KEY["es.preterite_reg"], V["hablar"], "yo",
                                "hablo", normalize, fold)
    assert not ok and not near


def test_normalize():
    assert normalize("Yo hablo") == "hablo"
    assert normalize("  yo   hablo  ") == "hablo"
    assert normalize("¡Habla!") == "habla"
    assert normalize("¿Hablas?") == "hablas"
    assert normalize("Ud. habla") == "habla"
    assert normalize("tu hablas") == "hablas"
    assert normalize("ellas no hablan") == "no hablan"
    assert normalize("yo") == "yo"                     # a lone word is never stripped
    assert normalize("él") == "él"
    assert normalize("HABLÓ") == "habló"
    assert normalize("hablo") != normalize("habló")
    # NFD input (some keyboards) compares equal to NFC.
    assert normalize("habló") == normalize("habló")


def test_fold():
    assert fold("habló") == "hablo" == fold("hablo")
    assert fold("ESTÁS") == "ESTAS"
    assert fold("año") == "año" and fold("año") != fold("ano")
    assert fold("pingüino") == "pinguino"


def test_stage_progression_test_out():
    p = {"skills": {}, "days": {}}
    assert T.current_stage(p) == 1
    stage1 = [s.key for s in C.SKILLS if s.stage == 1]
    moves = T.record(p, TODAY, {k: [True] * 5 for k in stage1})
    assert all(new == 3 for _, new in moves.values())
    assert T.current_stage(p) == 2
    assert {s.key for s in T.unlocked(p)} == {s.key for s in C.SKILLS if s.stage <= 2}


def test_session_items_are_valid():
    p = {"skills": {}, "days": {}}
    lessons, items = T.build_session(p, TODAY, WORDS, known=set())
    assert lessons and items
    for it in items:
        s = C.BY_KEY[it["skill"]]
        assert it["cue"] in s.cues
        assert s.answers(it["word"], it["cue"])
