"""The parts of practice that need judgement rather than a lookup table: grading a
sentence you built, and holding a conversation. Everything here calls Claude; the
grammar drills do not, and work without an API key.

Every call returns a typed object (Pydantic, via structured outputs) so the pages never
parse free text. The learner profile — what grammar is learned, what vocabulary they
have — goes into the system prompt so the tutor speaks at their level, in whichever
language they're on.

Needs an ANTHROPIC_API_KEY secret. Costs: a conversation turn is a few cents at most;
`effort` is low for chat (speed matters, depth does not) and medium for grading. Pages
check session.tutor_allowance() before calling, since invited learners spend the
owner's credit.
"""
import random, re
from typing import List, Literal

import anthropic
import streamlit as st
from pydantic import BaseModel, Field

from .store import secret

MODEL = "claude-opus-5-5"
# A safety-classifier decline is re-run on Anthropic's recommended fallback model
# server-side instead of surfacing as an error mid-lesson.
BETAS = ["server-side-fallback-2026-07-01"]


class TutorError(Exception):
    pass


def available():
    return bool(secret("ANTHROPIC_API_KEY"))


@st.cache_resource
def _client(key):
    return anthropic.Anthropic(api_key=key)


def _ask(system, messages, schema, effort="low", max_tokens=4000):
    try:
        r = _client(secret("ANTHROPIC_API_KEY")).beta.messages.parse(
            model=MODEL, max_tokens=max_tokens, betas=BETAS, fallbacks="default",
            output_config={"effort": effort}, output_format=schema,
            system=system, messages=messages)
    except anthropic.AuthenticationError:
        raise TutorError("ANTHROPIC_API_KEY was rejected.")
    except anthropic.RateLimitError:
        raise TutorError("Rate limited — wait a minute and try again.")
    except anthropic.APIStatusError as e:
        raise TutorError(f"API error {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        raise TutorError("Couldn't reach the API — check the connection.")
    if r.stop_reason == "refusal" or r.parsed_output is None:
        raise TutorError("The tutor declined that one — try rephrasing.")
    return r.parsed_output


# ----------------------------------------------------------------------- the learner

def profile(lang, progress, known):
    """What the tutor should assume you know. Deterministic for a given state, so the
    system prompt is stable across a conversation."""
    T = lang.track
    learned = [s for s in T.skills if T.is_learned(progress, s.key)]
    stage = T.current_stage(progress)
    learning = [s for s in T.skills if s.stage == stage]
    vocab = sorted(known)[:600]
    lines = [
        f"Language being learned: {lang.name}.",
        f"Grammar learned ({len(learned)} of {len(T.skills)} drilled forms): "
        + (", ".join(f"{s.shape} ({s.title})" for s in learned) or "none drilled yet"),
        "Currently learning: " + ", ".join(f"{s.shape} ({s.title})" for s in learning),
        f"Vocabulary studied: {len(known)} words. A sample: " + ", ".join(vocab),
    ]
    return "\n".join(lines)


# ---------------------------------------------------------------- sentence building

class BuildPrompt(BaseModel):
    english: str = Field(description="One natural English sentence to translate.")
    target: str = Field(description="The grammar pattern it practises, as written in the "
                                    "list given, e.g. 〜てもいい or pretérito.")
    hint: str = Field(description="One or two target-language words the learner may not "
                                  "know, as 'word (reading) = meaning', or empty.")


class BuildSet(BaseModel):
    prompts: List[BuildPrompt]


class Grade(BaseModel):
    verdict: Literal["correct", "almost", "wrong"]
    corrected: str = Field(description="The learner's sentence with the fewest changes "
                                       "that make it correct. Same as theirs if correct.")
    natural: str = Field(description="How a native speaker would most naturally say it.")
    reading: str = Field(description="For Japanese, the natural version in hiragana. "
                                     "Empty for other languages.")
    feedback: str = Field(description="One to three short sentences in English: what was "
                                      "wrong and why, or what was good. No preamble.")


BUILD_SYSTEM = """You are a {language} tutor running sentence-building drills on a phone. \
The learner translates short English sentences into {language} to practise grammar \
they have just drilled as conjugation, now inside a real sentence.

About the learner:
{profile}"""

LENIENCY = {
    "ja": "Kana-only answers are fine — do not penalise missing kanji.",
    "es": "A missing accent mark is at worst 'almost' — say which word needs it.",
}


def build_prompts(lang, prof, targets, n=5):
    focus = "\n".join(f"- {s.shape} ({s.title}): {s.rule}" for s in targets)
    ask = (f"Write {n} sentences for the learner to translate into {lang.name}. Each "
           f"must need one of these patterns, spread across them:\n{focus}\n\n"
           "Keep everything else inside grammar they have learned and vocabulary they "
           "know. Make the sentences things a person would really say in daily life, "
           "under 15 words, varied in topic. Mix casual and polite where it fits, and "
           "say which in the sentence, e.g. '(to a friend)'.")
    out = _ask(BUILD_SYSTEM.format(language=lang.name, profile=prof),
               [{"role": "user", "content": ask}], BuildSet)
    return out.prompts[:n]


def grade(lang, prof, prompt, answer):
    ask = (f"English: {prompt.english}\nTarget pattern: {prompt.target}\n"
           f"Learner's {lang.name}: {answer}\n\n"
           "Grade it. 'correct' means grammatical and says what the English says, even "
           "if not the most natural phrasing. 'almost' means one small slip (a particle "
           "or article, a typo, a politeness mismatch). 'wrong' otherwise, or if the "
           "target pattern wasn't used. " + LENIENCY.get(lang.code, ""))
    return _ask(BUILD_SYSTEM.format(language=lang.name, profile=prof),
                [{"role": "user", "content": ask}], Grade, effort="medium")


# --------------------------------------------------------------------- conversation

class Correction(BaseModel):
    needed: bool = Field(description="True only if the learner's last message had a "
                                     "real mistake or something unnatural.")
    corrected: str = Field(description="Their message, fixed. Empty if not needed.")
    note: str = Field(description="One short English sentence on the fix. Empty if "
                                  "not needed.")


class Turn(BaseModel):
    correction: Correction
    reply: str = Field(description="Your next line, in the language being learned, in "
                                   "character.")
    reading: str = Field(description="For Japanese, the reply in kana only. Empty for "
                                     "other languages.")
    english: str = Field(description="English translation of the reply.")


class Debrief(BaseModel):
    summary: str = Field(description="Two sentences in English on how it went.")
    mistakes: List[str] = Field(description="Recurring mistakes, each 'wrong → right: "
                                            "why'. At most four.")
    phrases: List[str] = Field(description="Up to five useful phrases from the "
                                           "conversation worth remembering, as "
                                           "'phrase (reading, for Japanese) — meaning'.")


SCENARIOS = {
    "ja": {
        "Self-introduction": "You meet the learner at a language exchange in Tokyo. Ask "
                             "about their name, where they're from, work, and hobbies.",
        "Café order": "You are a café staff member in Japan. Greet, take the order, ask "
                      "size and for here or to go, and handle payment.",
        "Weekend plans": "You are the learner's Japanese friend. Ask what they did last "
                         "weekend and what they'll do this weekend; suggest meeting up.",
        "Convenience store": "You are a konbini clerk. Ring up items, ask about bags, "
                             "heating the bento, and point card.",
        "Asking directions": "You are a passer-by near a Tokyo station. The learner is "
                             "lost; help them find a place, with left/right/straight "
                             "and landmarks.",
        "Hobbies & likes": "You are a coworker on a lunch break. Talk about what you each "
                           "like — food, music, sport, shows — and why.",
        "Making plans": "You are a friend arranging dinner. Agree on a day, time, place "
                        "and food; handle a scheduling clash.",
        "At the doctor": "You are a clinic doctor. Ask about symptoms, how long, and "
                         "give simple advice.",
        "Hotel check-in": "You are a hotel front desk clerk. Check the learner in, "
                          "explain breakfast and checkout, handle a request.",
        "Free talk": "You are a friendly Japanese conversation partner. Let the learner "
                     "lead; ask follow-up questions about what they bring up.",
    },
    "es": {
        "Self-introduction": "You meet the learner at an intercambio in Madrid. Ask about "
                             "their name, where they're from, work, and hobbies.",
        "Ordering tapas": "You are a waiter at a tapas bar in Seville. Take drinks and "
                          "food orders, recommend something, bring the bill.",
        "Weekend plans": "You are the learner's friend in Mexico City. Ask what they did "
                         "last weekend and what they'll do this one; suggest meeting up.",
        "At the market": "You run a fruit and vegetable stall at a market in Valencia. "
                         "Help them choose, weigh, price, and pay.",
        "Asking directions": "You are a local in Buenos Aires. The learner is lost; help "
                             "them find a place with left/right/straight and landmarks.",
        "Hobbies & likes": "You are a coworker on a coffee break. Talk about what you "
                           "each like — food, music, sport, shows — and why.",
        "Making plans": "You are a friend arranging dinner. Agree on a day, time, place "
                        "and food; handle a scheduling clash.",
        "At the doctor": "You are a doctor at a clinic. Ask about symptoms, how long, "
                         "and give simple advice.",
        "Hotel check-in": "You are a hotel receptionist in Barcelona. Check the learner "
                          "in, explain breakfast and checkout, handle a request.",
        "Free talk": "You are a friendly Spanish conversation partner. Let the learner "
                     "lead; ask follow-up questions about what they bring up.",
    },
}

REGISTERS = {
    "ja": ["casual (friends)", "polite (です/ます)"],
    "es": ["informal (tú)", "formal (usted)"],
}

TALK_SYSTEM = """You are a {language} conversation partner in a speaking practice app.

Scenario: {scenario}
Register: {register}

About the learner:
{profile}

How to talk:
- Stay in character and keep the conversation moving: answer, then ask one thing back.
- One to three short sentences per reply. Pitch it at the learner's level — mostly \
grammar they have learned and words they know, with an occasional new word they can \
guess from context. If they seem lost, simplify.
- If they write English or ask how to say something, give them the {language} to use \
in your reply (briefly, still in character), and carry on.
- Corrections go in the correction field, never in the reply. Only flag real mistakes \
or clearly unnatural phrasing — not missing kanji or accents, not stylistic choices."""


def talk_system(lang, prof, scenario, register):
    return TALK_SYSTEM.format(language=lang.name, scenario=SCENARIOS[lang.code][scenario],
                              register=register, profile=prof)


def talk(system, history):
    """`history` is the conversation as plain text turns, appended to and never
    rewritten — the assistant turns are the JSON the model itself returned."""
    return _ask(system, history, Turn)


def debrief(system, history):
    msgs = history + [{"role": "user", "content":
                       "(The conversation is over. Step out of character and debrief "
                       "the learner.)"}]
    return _ask(system, msgs, Debrief, effort="medium")


def pick_targets(track, progress, k=3):
    """Skills to build sentences around: the ones most recently learned, where
    getting from 'I can conjugate it' to 'I can use it' is the open gap."""
    seen = [s for s in track.skills if track.state(progress, s.key)]
    if not seen:
        return [s for s in track.skills if s.stage == min(track.stages)][:3]
    seen.sort(key=lambda s: (track.state(progress, s.key).get("box", 0), -s.stage))
    recent = seen[:6]
    return random.sample(recent, min(k, len(recent)))


# -------------------------------------------------------------------------- reading

class Token(BaseModel):
    t: str = Field(description="The token exactly as it appears in the sentence.")
    r: str = Field(description="Japanese only: the token's reading in hiragana when it "
                               "contains kanji, else empty. Always empty for Spanish.")
    d: str = Field(description="Dictionary form (verb infinitive / plain form, singular "
                               "noun, masculine singular adjective). Empty for "
                               "punctuation.")
    g: str = Field(description="Short English meaning in this context, e.g. 'went', "
                               "'(topic marker)', 'the cats'. Empty for punctuation.")


class PassageSentence(BaseModel):
    tokens: List[Token]
    en: str = Field(description="Natural English translation of the sentence.")


class Question(BaseModel):
    q: str = Field(description="A comprehension question in English.")
    options: List[str] = Field(description="Exactly three answer options in English.")
    answer: int = Field(description="Index (0-2) of the correct option.")


class Passage(BaseModel):
    title: str = Field(description="A short title in the language being learned.")
    title_en: str
    sentences: List[PassageSentence]
    questions: List[Question] = Field(description="Three questions for an adapted "
                                                  "passage; none for pasted text.")


LEVELS = {
    1: ("First steps", "5-7 very short sentences (at most 8 words). Present tense only, "
        "the most common 300 words, concrete everyday things."),
    2: ("Beginner", "6-8 short sentences (at most 10 words). Present and past, the most "
        "common 800 words, one idea per sentence."),
    3: ("Elementary", "8-10 sentences (at most 14 words). Everyday grammar, the most "
        "common 1,500 words, simple connectors (and, but, because)."),
    4: ("Intermediate", "10-12 sentences (at most 18 words). Natural connectors and "
        "relative clauses; the most common 3,000 words plus topic words."),
    5: ("Upper intermediate", "10-14 sentences of natural, textbook-like prose. Any "
        "common grammar; topic vocabulary is fine."),
    6: ("Advanced", "10-14 sentences, close to native prose; simplify only what is "
        "truly obscure."),
}

LEVEL_NOTES = {
    "ja": {1: "Polite です/ます forms only.", 2: "です/ます forms; simple て-form.",
           3: "です/ます forms; common patterns.", 4: "Mix plain and polite naturally.",
           5: "Plain written style (だ/である) is fine.", 6: ""},
    "es": {1: "Presente only.", 2: "Presente and pretérito.",
           3: "Pretérito and imperfecto; ir a + infinitive.",
           4: "Any indicative tense; occasional subjunctive.", 5: "", 6: ""},
}


def level_for(known_n, stage):
    """A starting level from vocabulary size and grammar stage. The learner can
    always override it on the Reading page."""
    if known_n < 150 and stage <= 2:
        return 1
    for lvl, cap in ((2, 500), (3, 1200), (4, 2500), (5, 4500)):
        if known_n < cap:
            return lvl
    return 6


READ_SYSTEM = """You write graded readers for a {language} learning app. Passages are \
read on a phone: every word can be tapped to see its meaning, so tokenisation and \
glosses must be exact.

Tokenisation:
- Japanese: one token per word as a learner would look it up — a conjugated verb or \
adjective with its endings is ONE token (食べました, 高くない), particles are their own \
tokens, punctuation is its own token. No spaces anywhere.
- Spanish: one token per word; punctuation (including ¿ ¡) is its own token; \
contractions al/del stay one token.
- Joined in order (with spaces between Spanish words), the tokens must give back the \
sentence exactly.

About the learner:
{profile}"""


def _passage_checks(lang, p):
    """Mechanical checks on a passage; returns a list of problems."""
    from .ja.kana import kata_to_hira
    probs = []
    if not p.sentences:
        probs.append("no sentences")
    for i, s in enumerate(p.sentences):
        if not s.tokens:
            probs.append(f"sentence {i} has no tokens")
        for t in s.tokens:
            if lang == "ja" and t.r and not re.fullmatch(r"[ぁ-ゖー]+", kata_to_hira(t.r)):
                probs.append(f"reading {t.r!r} for {t.t!r} isn't kana")
    for q in p.questions:
        if len(q.options) != 3 or not 0 <= q.answer < 3:
            probs.append(f"question {q.q!r} needs 3 options and a valid answer")
    return probs


def adapt(lang, prof, level, source_text=None, source_title=None, topic=None):
    """A graded passage at `level`, adapted from a Wikipedia extract, or an original
    short story when there's no source."""
    name, rule = LEVELS[level]
    note = LEVEL_NOTES.get(lang.code, {}).get(level, "")
    if source_text:
        ask = (f"Rewrite this Wikipedia article as a {name} (level {level}/6) reading "
               f"passage in {lang.name}: {rule} {note}\n\nKeep the interesting facts, "
               "neutral and accurate; leave out what doesn't fit the level. Then write "
               "three comprehension questions.\n\n"
               f"Article: {source_title}\n\n{source_text}")
    else:
        ask = (f"Write an original short story in {lang.name} at {name} level "
               f"(level {level}/6): {rule} {note}\n\nTheme: {topic or 'anything fun'}. "
               "Give it a small twist or a funny ending. Then write three comprehension "
               "questions.")
    out = _ask(READ_SYSTEM.format(language=lang.name, profile=prof),
               [{"role": "user", "content": ask}], Passage, effort="medium",
               max_tokens=16000)
    probs = _passage_checks(lang.code, out)
    if probs:
        raise TutorError("The passage came back malformed (" + "; ".join(probs[:3])
                         + ") — try another.")
    return out


def gloss(lang, prof, text):
    """Tokenise and gloss text the learner pasted, without changing a word of it."""
    ask = ("Tokenise and gloss this text exactly as written — do not correct, simplify "
           "or translate it away. Split it into sentences. No questions.\n\n" + text)
    out = _ask(READ_SYSTEM.format(language=lang.name, profile=prof),
               [{"role": "user", "content": ask}], Passage, effort="medium",
               max_tokens=16000)
    out.questions = []
    probs = _passage_checks(lang.code, out)
    if probs:
        raise TutorError("Couldn't gloss that cleanly (" + "; ".join(probs[:3]) + ").")
    return out


# ------------------------------------------------------------------------ speaking

class ShadowLine(BaseModel):
    text: str = Field(description="The sentence in the language being learned.")
    reading: str = Field(description="Japanese: the whole sentence in hiragana. Empty "
                                     "for other languages.")
    english: str


class ShadowSet(BaseModel):
    lines: List[ShadowLine]


def shadow_lines(lang, prof, level, theme, n=8):
    name, rule = LEVELS[level]
    ask = (f"Write {n} {lang.name} sentences for speaking practice (the learner listens, "
           f"then says each one aloud). Level: {name} — {rule} "
           f"{LEVEL_NOTES.get(lang.code, {}).get(level, '')}\nTheme: {theme}. Make them "
           "things people really say out loud: questions, reactions, requests, small "
           "talk. Vary the rhythm and length within the level.")
    out = _ask(READ_SYSTEM.format(language=lang.name, profile=prof),
               [{"role": "user", "content": ask}], ShadowSet)
    return out.lines[:n]


SHADOW_THEMES = ["greetings and small talk", "at a café or restaurant", "shopping",
                 "travel and directions", "making plans with a friend",
                 "feelings and reactions", "work and school", "hobbies", "at home",
                 "the weather"]
