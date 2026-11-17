"""The Progress page's arithmetic: levels, pace, activity and the vocab breakdown."""
import datetime, json

from hub import stats, tutor
from hub.ja import curriculum as C

T = C.TRACK
TODAY = datetime.date(2026, 11, 17)


def ago(n):
    return (TODAY - datetime.timedelta(days=n)).isoformat()


def learned_through(stage):
    return {"skills": {s.key: {"box": 2, "seen": 10, "right": 9, "introduced": ago(3)}
                       for s in T.skills if s.stage <= stage}, "days": {}}


# ---------------------------------------------------------------------- levels

def test_levels_are_the_reading_levels():
    assert [lv.name for lv in stats.LEVELS] == [tutor.LEVELS[n][0] for n in sorted(tutor.LEVELS)]
    # The word counts are where the Reading page moves you up a level.
    for lv in stats.LEVELS[1:]:
        assert tutor.level_for(lv.words, 16) == lv.n
        assert tutor.level_for(lv.words - 1, 1) == lv.n - 1


def test_a_level_needs_both_words_and_grammar():
    n = len(T.stages)
    assert stats.standing(0, 0, n)["level"].n == 1
    # Plenty of words but no grammar: still on the first level, and it says why.
    s = stats.standing(2000, 0, n)
    assert s["level"].n == 1 and s["lacking"] == "grammar" and s["words_frac"] == 1.0
    # Plenty of grammar but few words.
    s = stats.standing(100, n, n)
    assert s["level"].n == 1 and s["lacking"] == "words" and s["words_left"] == 50
    # Both.
    need = stats.stages_needed(stats.LEVELS[3], n)
    assert stats.standing(1200, need, n)["level"].n == 4
    assert stats.standing(1200, need - 1, n)["level"].n == 3


def test_top_of_the_path():
    s = stats.standing(9000, len(T.stages), len(T.stages))
    assert s["level"].n == 6 and s["next"] is None and s["frac"] == 1.0


def test_progress_to_next_is_measured_from_the_level_held():
    n = len(T.stages)
    s = stats.standing(325, stats.stages_needed(stats.LEVELS[1], n), n)   # Beginner
    assert s["level"].n == 2 and s["words_frac"] == 0.5 and s["grammar_frac"] == 0.0
    assert s["frac"] == 0.25


# ------------------------------------------------------------------------ pace

def test_pace_counts_only_the_window():
    dates = [ago(0), ago(13), ago(14), ago(40), None]
    assert stats.per_day(dates, TODAY) == 2 / 14


def test_eta():
    assert stats.eta(0, 0, TODAY) == TODAY
    assert stats.eta(10, 0, TODAY) is None
    assert stats.eta(10, 3, TODAY) == TODAY + datetime.timedelta(days=4)


def test_pace_ignores_unanswered_cards_and_unlearned_skills():
    progress = learned_through(1)                      # introduced 3 days ago
    progress["skills"]["x"] = {"box": 1, "introduced": ago(1)}
    rows = [{"reps": 1, "introduced": ago(i % 14)} for i in range(28)]
    rows.append({"reps": 0, "introduced": ago(1)})
    words, skills = stats.pace(T, progress, rows, TODAY)
    assert words == 2
    assert skills == sum(s.stage == 1 for s in T.skills) / 14


def test_forecast_dates_every_level_by_its_slower_half():
    progress = learned_through(1)
    n = len(T.stages)
    f = stats.forecast(100, T, progress, TODAY, 10, 0.5)
    assert [x["level"].n for x in f] == [1, 2, 3, 4, 5, 6]
    assert f[0]["held"] and f[0]["days"] == 0
    # Beginner: 50 words at 10 a day is 5 days; the grammar takes longer.
    left = stats.skills_left(T, progress, stats.stages_needed(stats.LEVELS[1], n))
    assert f[1]["words_left"] == 50 and f[1]["skills_left"] == left
    assert f[1]["days"] == max(5, left * 2) and f[1]["slower"] == "grammar"
    # Later levels are never sooner.
    days = [x["days"] for x in f]
    assert days == sorted(days)
    assert f[-1]["date"] == TODAY + datetime.timedelta(days=days[-1])


def test_forecast_without_a_pace_has_no_date_and_says_which_half():
    f = stats.forecast(100, T, learned_through(1), TODAY, 0, 0.5)
    assert f[1]["date"] is None and f[1]["days"] is None and f[1]["slower"] == "words"
    f = stats.forecast(100, T, learned_through(1), TODAY, 5, 0)
    assert f[1]["date"] is None and f[1]["slower"] == "grammar"
    # A level you already hold needs no pace at all.
    assert stats.forecast(100, T, learned_through(1), TODAY, 0, 0)[0]["held"]


def test_faster_pace_is_never_later():
    slow = stats.forecast(0, T, {"skills": {}, "days": {}}, TODAY, 5, 0.2)
    fast = stats.forecast(0, T, {"skills": {}, "days": {}}, TODAY, 20, 1)
    assert all(a["days"] >= b["days"] for a, b in zip(slow, fast))
    assert fast[3]["days"] == max(60, round(stats.skills_left(
        T, {"skills": {}, "days": {}}, stats.stages_needed(stats.LEVELS[3], len(T.stages)))))


def test_span_reads_like_speech():
    assert [stats.span(d) for d in (None, 0, 1, 9, 14, 60, 150, 800)] ==         ["no date yet", "today", "1 day", "9 days", "2 weeks", "9 weeks", "5 months",
         "2.2 years"]
    assert stats.vocab_minutes(15) == 20


# -------------------------------------------------------------------- activity

def test_history_merges_languages_and_ignores_bookkeeping():
    ja = {ago(0): {"vocab": 5, "new": 5, "api": 9, "grammar_right": 3}, ago(2): {"grammar": 4}}
    es = {ago(0): {"talk": 2}}
    h = stats.history([ja, es], TODAY, 3)
    assert [n for _, n in h] == [4, 0, 7] and h[-1][0] == TODAY


def test_streaks_and_days():
    days = {ago(n): {"vocab": 1} for n in (0, 1, 2, 5, 6, 7, 8)}
    days[ago(3)] = {"api": 4}                      # tutor calls alone aren't practice
    assert stats.best_streak([days]) == 4
    assert stats.days_active([days]) == 7
    assert stats.best_streak([{}]) == 0


def test_week_balance_and_accuracy():
    days = {ago(0): {"grammar": 10, "grammar_right": 8, "vocab": 30},
            ago(6): {"grammar": 10, "grammar_right": 6, "talk": 5},
            ago(7): {"grammar": 100, "grammar_right": 0}}
    bal = stats.week_balance(days, TODAY)
    assert bal["grammar"] == (20, stats.TARGETS["grammar"] * 7)
    assert bal["vocab"] == (30, None) and bal["talk"][0] == 5
    assert stats.recent_accuracy(days, TODAY) == 0.7
    assert stats.recent_accuracy({}, TODAY) is None


# ----------------------------------------------------------------------- vocab

def row(reps, state, stability, due=None):
    return {"reps": reps, "due": due or datetime.datetime(2026, 11, 18, 9),
            "fsrs": json.dumps({"state": state, "stability": stability})}


def test_card_states():
    rows = [row(0, 1, None), row(1, 1, 0.4), row(5, 3, 2.0), row(4, 2, 9.0),
            row(9, 2, 21.0), row(9, 2, 80.0)]
    assert stats.card_states(rows) == {"learning": 2, "young": 1, "mature": 2}


def test_coming_up_puts_overdue_on_today():
    rows = [row(1, 2, 5, datetime.datetime(2026, 11, 10, 9)),
            row(1, 2, 5, datetime.datetime(2026, 11, 17, 23)),
            row(1, 2, 5, datetime.datetime(2026, 11, 19, 1)),
            row(1, 2, 5, datetime.datetime(2027, 1, 1, 1))]
    progress = {"skills": {"a": {"due": ago(4)}, "b": {"due": ago(-2)}, "c": {}}}
    out = stats.coming_up(rows, T, progress, TODAY)
    assert len(out) == 7 and out[0] == (TODAY, 2, 1)
    assert out[2][1:] == (1, 1) and sum(c for _, c, _ in out) == 3


# --------------------------------------------------------------------- grammar

def test_grammar_accuracy_and_weakest():
    progress = {"skills": {}, "days": {}}
    assert stats.grammar_accuracy(progress) is None and stats.weakest(T, progress) == []
    a, b, c = T.skills[:3]
    progress["skills"] = {a.key: {"seen": 10, "right": 9}, b.key: {"seen": 10, "right": 4},
                          c.key: {"seen": 2, "right": 0}}       # too few to judge
    assert stats.grammar_accuracy(progress) == 13 / 22
    assert [(s.key, acc) for s, acc in stats.weakest(T, progress)] == [(b.key, 0.4)]


def test_stage_rows():
    rows = stats.stage_rows(T, learned_through(2))
    assert [r[4] for r in rows[:4]] == ["done", "done", "current", "locked"]
    assert rows[0][2] == rows[0][3] and rows[2][2] == 0
    assert stats.skills_left(T, learned_through(2), 3) == rows[2][3]
