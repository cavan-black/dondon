"""Generate Dondon's vocab decks: 1,500-word tiers in frequency order, with original
meanings and example sentences, for Japanese or Spanish.

    python tools/make_deck.py ja --tiers 1-2 --dry-run     # plan and cost, no calls
    python tools/make_deck.py ja --tiers 1-2 --yes         # generate decks/ja/tier1..2

HOW IT WORKS
1. WORDS. wordfreq's ranked list of the language's most frequent tokens decides which
   words go in and in what order. Raw tokens aren't study words — Japanese comes out
   as tokenizer fragments (なっ, まし, て) and Spanish as inflected forms (fue, tiene)
   — so Claude maps each to the dictionary form a learner studies, dropping particles,
   fragments, names and numbers. First occurrence wins, so 'fue' ranks 'ser' where
   'ser' itself would have. The result is cached as the ranked lemma list; a word's
   rank becomes its permanent card id (ja-00042), so regenerating never reshuffles
   anyone's progress.
2. CARDS. Claude writes each card in batches of 25: meaning, reading and furigana
   (Japanese), article and gender (Spanish nouns), and one example sentence pitched at
   the tier — short and simple in tier 1, richer later.
3. CHECKS. Deterministic checks catch what can be checked mechanically: furigana that
   doesn't spell the sentence, readings with kanji in them, empty fields, and
   sentences that don't seem to contain the word.
4. REVIEW. A second Claude pass reviews every batch, with the check results attached,
   and returns corrected cards. Cards still failing a hard check after review are
   dropped; the next word in frequency order takes their place.

Everything is cached under .deckcache/<lang>/ (gitignored), per batch, so a run that
stops halfway resumes where it left off and never pays for the same batch twice.

The content is ours: the frequency ranking only decides which words are included
(wordfreq's data is CC BY-SA 4.0 and is credited in the README), and every meaning and
sentence is newly written.

Needs ANTHROPIC_API_KEY in the environment, plus `pip install -r tools/requirements.txt`.
"""
import argparse, json, os, re, sys, unicodedata
from concurrent.futures import ThreadPoolExecutor
from typing import List

from pydantic import BaseModel, Field

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)

TIER_SIZE = 1500
LEMMA_CHUNK = 200
CARD_CHUNK = 25
MODEL = "claude-opus-5-5"
BETAS = ["server-side-fallback-2026-07-01"]
NAMES = {"ja": "Japanese", "es": "Spanish"}

# Rough per-call token use, for the --dry-run estimate only. Opus 5.5: $4 / $20 per M.
EST = {"lemma": (3000, 7000), "cards": (2500, 9000), "review": (7000, 9000)}
PRICE_IN, PRICE_OUT = 4 / 1e6, 20 / 1e6


# ---------------------------------------------------------------------- schemas

class Lemma(BaseModel):
    token: str = Field(description="The token exactly as given.")
    lemma: str = Field(description="Dictionary form a learner would study, or empty to "
                                   "drop the token.")
    reading: str = Field(description="Japanese only: the lemma's reading in hiragana. "
                                     "Empty for Spanish.")


class LemmaBatch(BaseModel):
    items: List[Lemma]


class Card(BaseModel):
    rank: int = Field(description="The rank number given for this word, unchanged.")
    word: str = Field(description="The word as it is normally written. Spanish nouns "
                                  "with their article: 'la casa', 'el agua'.")
    reading: str = Field(description="Japanese: the word's reading in hiragana (katakana "
                                     "words: the katakana). Spanish: empty.")
    meaning: str = Field(description="Short English gloss, the senses a learner meets "
                                     "first, separated by '; '. Under 60 characters.")
    pos: str = Field(description="Part of speech in English: noun, verb, i-adjective, "
                                 "na-adjective, adverb, pronoun, particle, expression, "
                                 "etc. Spanish nouns add gender: 'noun (f)'.")
    sentence: str = Field(description="One natural example sentence using the word.")
    sentence_furigana: str = Field(description="Japanese only: the sentence with "
                                               "Anki-style furigana — a space before "
                                               "every kanji run and its reading in "
                                               "brackets: '私[わたし]は 学校[がっこう]に "
                                               "行[い]きます。'. Empty for Spanish.")
    sentence_en: str = Field(description="Natural English translation of the sentence.")


class CardBatch(BaseModel):
    cards: List[Card]


class ReviewedCard(BaseModel):
    card: Card
    changed: bool
    issue: str = Field(description="What was wrong, if changed. Empty otherwise.")


class ReviewBatch(BaseModel):
    cards: List[ReviewedCard]


# ---------------------------------------------------------------------- prompts

LEMMA_SYSTEM = {
    "ja": """You turn tokens from a Japanese word-frequency list into a vocabulary \
list for learners. The tokens come from a morphological tokenizer, so many are \
fragments: conjugation pieces (なっ, まし, れ), particles (の, に, は), auxiliaries \
(です, ます, た), suffixes (的, 者). For each token give the dictionary-form word a \
learner would study, written the way it is normally written (kanji where usual), with \
its hiragana reading. なっ → なる; 人 → 人 (ひと); いい → いい.

Drop (empty lemma): particles, auxiliaries and copulas, bare conjugation endings, \
single kana that aren't words, numbers, symbols, Latin letters, proper nouns (names of \
people, places, companies, works), and pure suffixes or prefixes. Keep: nouns, verbs, \
adjectives, adverbs, pronouns, demonstratives (これ, その), conjunctions, common \
interjections and set expressions, katakana loanwords, counters that are words.""",
    "es": """You turn tokens from a Spanish word-frequency list into a vocabulary list \
for learners. Tokens are inflected forms: give the dictionary form a learner studies — \
the infinitive for verbs (fue → ser or ir, choose the more frequent reading; tiene → \
tener), masculine singular for adjectives (buenas → bueno), singular for nouns (casas \
→ casa, without article).

Drop (empty lemma): proper nouns (people, places, brands), numbers, abbreviations, \
English or other foreign words, and non-words. Keep everything a learner should study, \
including prepositions, pronouns, conjunctions, articles and common interjections.""",
}

LEVEL = {
    1: "a complete beginner: 4–8 words, present or simple past, only very common words",
    2: "an advanced beginner: up to 10 words, everyday grammar, common words",
    3: "a lower-intermediate learner: up to 12 words, any common grammar",
    4: "an intermediate learner: up to 15 words, natural everyday language",
}

CARD_SYSTEM = """You write vocabulary flashcards for {language} learners. Every card \
is original: never copy example sentences from dictionaries, textbooks or other decks.

The example sentence must use the card's word (inflected as needed), sound like \
something a native speaker would really say, and suit {level}. Keep the rest of the \
sentence to words more common than the card's word, so the card teaches one new thing.

Meanings are short glosses, not definitions. Give the most common senses first.{extra}"""

CARD_EXTRA = {
    "ja": " Write the word in its usual written form (kanji if it's normally written \
in kanji, kana if it's normally kana). In sentence_furigana every kanji run gets its \
reading in brackets with a space before the run; kana and punctuation have no \
brackets. Readings in hiragana.",
    "es": " Use neutral international Spanish. Nouns carry their article in `word` and \
gender in `pos`.",
}

REVIEW_SYSTEM = """You are a meticulous native-speaker editor checking {language} \
vocabulary flashcards for learners at the level of {level}. For each card check: the \
meaning is right and gives the most common senses; the reading is right (Japanese); \
the sentence is natural, correct, uses the card's word, and suits the level; the \
translation is accurate; the furigana is correct and correctly formatted (Japanese). \
Automated checks have flagged some cards — their notes are attached; fix what they \
point to. Return every card, corrected where needed, keeping each rank unchanged."""


# ---------------------------------------------------------------------- checks

KANA = re.compile(r"^[぀-ゟ゠-ヿー・ 　]+$")
KANJI = re.compile(r"[一-鿿々]")
RUBY = re.compile(r"([^ \[\]]+?)\[([^\]]+)\]")


def fold(s):
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def check(lang, c):
    """Returns (hard, soft): hard problems drop the card; soft ones go to review."""
    hard, soft = [], []
    for f in ("word", "meaning", "sentence", "sentence_en", "pos"):
        if not getattr(c, f).strip():
            hard.append(f"empty {f}")
    if len(c.meaning) > 80:
        soft.append("meaning too long")
    if lang == "ja":
        if not c.reading or not KANA.match(c.reading):
            hard.append("reading must be kana only")
        bases = RUBY.findall(c.sentence_furigana)
        if RUBY.sub(r"\1", c.sentence_furigana).replace(" ", "") != c.sentence.replace(" ", ""):
            hard.append("furigana doesn't spell the sentence")
        for base, rt in bases:
            if not KANJI.search(base) or KANA.match(base[0]):
                hard.append(f"furigana base '{base}' should start with kanji")
            if not KANA.match(rt):
                hard.append(f"furigana reading '{rt}' isn't kana")
        if KANJI.search(c.sentence) and not bases:
            hard.append("sentence has kanji but no furigana")
        stem = c.word[:-1] if len(c.word) > 1 else c.word
        if c.word not in c.sentence and stem not in c.sentence:
            soft.append("sentence may not contain the word")
        if len(c.sentence) > 45:
            soft.append("sentence long")
    else:
        head = fold(c.word.split()[-1])
        if fold(head[:4]) not in fold(c.sentence):
            soft.append("sentence may not contain the word (fine for irregular forms)")
        if len(c.sentence) > 110:
            soft.append("sentence long")
    return hard, soft


# ---------------------------------------------------------------------- calls

def client():
    import anthropic
    return anthropic.Anthropic()


def ask(system, content, schema, effort="medium"):
    r = client().beta.messages.parse(
        model=MODEL, max_tokens=16000, betas=BETAS, fallbacks="default",
        output_config={"effort": effort}, output_format=schema, system=system,
        messages=[{"role": "user", "content": content}])
    if r.stop_reason == "refusal" or r.parsed_output is None:
        raise RuntimeError(f"no usable output (stop_reason={r.stop_reason})")
    return r.parsed_output


def cached(path, make):
    """Return the JSON at `path`, or make it, write it, and return it."""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    data = make()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    os.replace(tmp, path)
    return data


# ---------------------------------------------------------------------- stages

def candidates(lang, n=60000):
    from wordfreq import top_n_list
    out = []
    for t in top_n_list(lang, n):
        if lang == "ja" and re.search(r"[぀-ヿ一-鿿]", t) \
                and not re.search(r"[0-9A-Za-z０-９]", t):
            out.append(t)
        elif lang == "es" and re.fullmatch(r"[a-záéíóúüñ]+", t):
            out.append(t)
    return out


def lemma_chunk(lang, cache, i, tokens):
    def make():
        out = ask(LEMMA_SYSTEM[lang], "Tokens, in frequency order:\n" + "\n".join(tokens),
                  LemmaBatch, effort="low")
        return [x.model_dump() for x in out.items]
    return cached(os.path.join(cache, "lemmas", f"{i:04d}.json"), make)


def ranked_lemmas(lang, cache, need, workers):
    """The ordered, de-duplicated study words, enough for `need` cards plus margin."""
    toks = candidates(lang)
    chunks = [toks[i:i + LEMMA_CHUNK] for i in range(0, len(toks), LEMMA_CHUNK)]
    out, seen, done = [], set(), 0
    with ThreadPoolExecutor(workers) as pool:
        while len(out) < need and done < len(chunks):
            batch = list(range(done, min(done + workers, len(chunks))))
            results = list(pool.map(lambda i: lemma_chunk(lang, cache, i, chunks[i]), batch))
            for res in results:
                for x in res:
                    lem = x["lemma"].strip()
                    key = (lem, x.get("reading", "").strip())
                    if lem and key not in seen:
                        seen.add(key)
                        out.append({"lemma": lem, "reading": x.get("reading", "").strip()})
            done = batch[-1] + 1
            print(f"  lemmas: {len(out)} from {done} chunks", flush=True)
    return out


def tier_of(rank):
    return (rank - 1) // TIER_SIZE + 1


def card_chunk(lang, cache, j, words):
    """Write, check, review and re-check one batch. Returns accepted cards as dicts."""
    tier = tier_of(words[0]["rank"])
    level = LEVEL.get(tier, LEVEL[4])
    listing = "\n".join(f"{w['rank']}. {w['lemma']}" + (f" ({w['reading']})" if w['reading'] else "")
                        for w in words)

    def write():
        out = ask(CARD_SYSTEM.format(language=NAMES[lang], level=level,
                                     extra=CARD_EXTRA[lang]),
                  f"Write one card for each word:\n{listing}", CardBatch)
        return [c.model_dump() for c in out.cards]
    drafts = [Card(**c) for c in cached(os.path.join(cache, "cards", f"{j:04d}.json"), write)]

    notes = []
    for c in drafts:
        hard, soft = check(lang, c)
        if hard or soft:
            notes.append(f"rank {c.rank}: " + "; ".join(hard + soft))

    def review():
        body = json.dumps([c.model_dump() for c in drafts], ensure_ascii=False, indent=0)
        msg = (f"Cards:\n{body}\n\nAutomated check notes:\n" + ("\n".join(notes) or "none"))
        out = ask(REVIEW_SYSTEM.format(language=NAMES[lang], level=level), msg, ReviewBatch)
        return [x.model_dump() for x in out.cards]
    reviewed = cached(os.path.join(cache, "review", f"{j:04d}.json"), review)

    wanted = {w["rank"] for w in words}
    accepted, dropped = [], []
    for x in reviewed:
        c = Card(**x["card"])
        hard, _ = check(lang, c)
        if c.rank not in wanted or hard:
            dropped.append((c.rank, c.word, hard or ["unexpected rank"]))
            continue
        wanted.discard(c.rank)
        accepted.append(c.model_dump())
    return accepted, dropped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("lang", choices=sorted(NAMES))
    ap.add_argument("--tiers", default="1", help="e.g. 1, 1-4")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true", help="plan and estimate cost only")
    ap.add_argument("--yes", action="store_true", help="actually spend API credit")
    a = ap.parse_args()

    lo, _, hi = a.tiers.partition("-")
    tiers = list(range(int(lo), int(hi or lo) + 1))
    need_cards = max(tiers) * TIER_SIZE
    cache = os.path.join(ROOT, ".deckcache", a.lang)

    # Estimate: ~1.6 tokens per kept lemma, ~3% of cards dropped.
    lemma_calls = int(need_cards * 1.6 * 1.1 / LEMMA_CHUNK) + 1
    card_calls = int(need_cards * 1.05 / CARD_CHUNK) + 1
    cost = (lemma_calls * (EST["lemma"][0] * PRICE_IN + EST["lemma"][1] * PRICE_OUT) +
            card_calls * sum(EST[k][0] * PRICE_IN + EST[k][1] * PRICE_OUT
                             for k in ("cards", "review")))
    print(f"{NAMES[a.lang]} tiers {tiers[0]}–{tiers[-1]}: {need_cards} cards, about "
          f"{lemma_calls} lemma calls + {card_calls} card batches × 2 calls, roughly "
          f"${cost:.0f} on {MODEL} at list price, before cached batches.")
    if a.dry_run or not a.yes:
        if not a.dry_run:
            print("Nothing spent. Re-run with --yes to generate.")
        return

    lemmas = ranked_lemmas(a.lang, cache, int(need_cards * 1.08), a.workers)
    for r, w in enumerate(lemmas, 1):
        w["rank"] = r

    accepted, dropped, j = [], [], 0
    chunks = [lemmas[i:i + CARD_CHUNK] for i in range(0, len(lemmas), CARD_CHUNK)]
    with ThreadPoolExecutor(a.workers) as pool:
        while len(accepted) < need_cards and j < len(chunks):
            batch = list(range(j, min(j + a.workers, len(chunks))))
            for acc, drop in pool.map(lambda k: card_chunk(a.lang, cache, k, chunks[k]), batch):
                accepted += acc
                dropped += drop
            j = batch[-1] + 1
            print(f"  cards: {len(accepted)} accepted, {len(dropped)} dropped", flush=True)

    accepted.sort(key=lambda c: c["rank"])
    out_dir = os.path.join(ROOT, "decks", a.lang)
    os.makedirs(out_dir, exist_ok=True)
    for t in tiers:
        part = accepted[(t - 1) * TIER_SIZE:t * TIER_SIZE]
        deck = {"lang": a.lang, "tier": t, "count": len(part),
                "cards": [{"id": f"{a.lang}-{c['rank']:05d}", **c} for c in part]}
        path = os.path.join(out_dir, f"tier{t}.json")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(deck, fh, ensure_ascii=False, indent=1)
        print(f"wrote {path}: {len(part)} cards")
    for rank, word, why in dropped[:40]:
        print(f"  dropped {rank} {word}: {'; '.join(why)}")


if __name__ == "__main__":
    main()
