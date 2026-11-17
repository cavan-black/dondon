# Dondon

*どんどん: steadily, more and more, keep going.*

A phone-first app for the whole daily routine of learning Japanese or Spanish, from
first words to conversation. It's free for an invited group, and your progress follows
your Google account across phone, tablet and computer.

| Page | What it does |
|---|---|
| **Today** | Language switch, today's ring, your level, the week, and the day's plan. Tap a step to do it |
| **Progress** | Your level and what the next one needs, the date you'll reach it at your pace, and the statistics |
| **Basics** | The alphabet: hiragana and katakana, or Spanish sounds, spelling and stress. Skippable |
| **Vocabulary** | Reviews from Dondon's own decks: 1,500-word tiers in frequency order, scheduled with FSRS |
| **Grammar** | Katsuyou-style drills: a word, a form (and for Spanish a person), type it. Staged, on a spaced schedule |
| **Read** | Wikipedia articles and short stories rewritten at your level. Tap any word for its meaning |
| **Build** | Translate sentences that need the grammar you just drilled; Claude grades them and shows the natural version |
| **Speak** | Listen to a sentence, say it back, and see how much the phone's speech recognition understood |
| **Talk** | Role-play conversations pitched at your level, with corrections and a debrief. Answer by voice with the microphone |
| **Find my level** | The placement test: kana, words and grammar, so you start in the right place |
| **Profile & settings** | Starting tier, new cards per day, invites (owner), sign out |
| **My vocabulary** | Owner only: review your own Anki collection from the phone (the original purpose of this repo) |

The order is the method. Words come in through the decks and rules through the
drills. Reading shows them in real use. You then produce both, first in single
sentences, then out loud, then in conversation, because producing the language is
what turns knowing it into speaking it. A little of each every day beats a lot of
one.

## Getting around

Dondon draws its own bar across the top of every page: the mark (back to Today from
anywhere), Today, Progress, a Practice menu with every exercise, and your profile at
the top right: who's signed in, your level, Profile & settings, Find my level, and
sign out. On a phone Today and Progress shrink to icons so it fits on one line.

## Finding your level

New learners are offered a placement test before anything else. It's one sitting
in up to three parts, each stopping at your ceiling:

- **Kana / Sounds:** a dozen items from across Basics. 90% marks Basics done. For
  Japanese, under half ends the test there, since the rest needs kana.
- **Words:** the decks in bands of 500, most common first: five words a band, pick
  the meaning or "I don't know". Scores are corrected for guessing, and it stops
  after two bands in a row come out mostly unknown.
- **Grammar:** the grammar track stage by stage, four to six drills each. A stage
  passes at 75%; the first one that doesn't ends the test.

Answers aren't marked as you go. At the end it shows your level and what changed:
Basics skipped, passed grammar stages marked learned (they come back for a check in
a week, so a lucky guess gets caught), and new vocabulary starting at the first band
of 500 that isn't mostly known, even part-way into a tier. The words it found you
know count toward your level until the cards catch up. A retake only ever moves you
forward. It can be retaken from the profile menu or Progress.

## The look

The mark is two beats, the second bigger: どん、どん. Indigo (#8b9dff) is the
working colour for progress, links and buttons; persimmon (#ff9466) is kept for
what matters most on a screen, such as the forecast and the half to focus on. Green,
red and amber only ever mean right, wrong and nearly. Headings and numbers are set in
Bricolage Grotesque, text in Inter, Japanese in Zen Kaku Gothic New. Everything lives
in `hub/ui.py`; the mark is `assets/mark.svg`. Icons are Material Symbols Rounded,
the set Streamlit's own widgets use; there are no emoji in the interface.

Things animate once as they arrive (panels rise, bars and rings fill to their
value) and then hold still. A right answer swooshes: the card lights green and flies
off as the next slides in. With "reduce motion" switched on in the phone's
settings, nothing moves.

## Progress

The path has six levels, the same six the Reading page writes for: First steps,
Beginner, Elementary, Intermediate, Upper intermediate, Advanced. A level asks for
two things, enough words and enough of the grammar track, and you hold the highest
level whose both halves you've met. Intermediate (1,200 words and a little over half
the grammar stages) is where conversation starts, and it's marked on the path.

| Level | Words known | Grammar stages finished |
|---|---|---|
| Beginner | 150 | 10% |
| Elementary | 500 | 30% |
| Intermediate | 1,200 | 55% |
| Upper intermediate | 2,500 | 80% |
| Advanced | 4,500 | all |

The Progress page shows which half is holding you back, and a forecast: the date
you reach each level still ahead if the last two weeks' pace holds (new words
started and grammar skills learned). Pick a level to see what's left and which half
arrives last. "Try a different pace" swaps in words and skills a week of your
choosing, to see what a faster or slower routine would buy. Until there's a measured
pace it starts from your new cards per day and three skills a week. It's a straight
line carried forward, not a promise.
Below that: streak, recall on vocab reviews over 30 days, first-attempt grammar
accuracy, the last 14 days of practice, this week against the daily targets, what
falls due over the next 7 days, each vocab tier by how well its words are held, the
grammar roadmap, and the three forms you get wrong most.

## Basics

Japanese: hiragana one row at a time, then the voiced sounds, combined sounds, small
っ and long vowels, real words, and the same again for katakana with loanwords. You
see the kana and type the romaji (Hepburn or Kunrei), or see the romaji and pick the
kana from four look-alikes. Spanish: the vowels, the letters that differ from
English, stress and written accents, and ¿ ¡. Mostly dictation: hear a word, type
it. A unit passes at 90% first time; anyone who already knows it can skip the lot.

## Reading

Pick a topic, or what's trending today, or what happened on this day, or type
anything. Dondon fetches a Wikipedia article in the language you're learning and
Claude rewrites it at your level, from six levels between "first steps" and
"advanced". Or it writes an original short story. Tap a word to see its reading,
dictionary form and meaning; tap EN for a sentence's translation; the speaker
button reads it aloud.
Words you looked up that are in the decks can be added to your vocab from the page.
Three questions at the end check you got the gist.

Every passage goes into a shared library for its language and level, so one
learner making it stocks it for everyone. Adapted Wikipedia text keeps its
CC BY-SA 4.0 licence and credits its article. Text you paste in yourself is glossed
word by word and never stored. Invited learners can make 6 new passages a day; the
library is unlimited.

## Speaking

The speaker buttons use the phone's own text-to-speech, so there are no audio files and no
licensing question. **Speak** is shadowing: hear a sentence, tap the microphone, say it back,
and see which parts the phone's speech recognition caught. The sentences come from
the example sentences of words you've learned, or a new set at your level. **Talk**
takes your spoken answers too. Recognition works in Chrome and Safari, iPhone
included; it scores whether you were understood, which isn't the same as perfect
pronunciation.

## Vocab decks

Tier 1 is the 1,500 most common words, tier 2 the next 1,500, and so on. New cards
come from your current tier in frequency order. Once every card in it has been
started, new cards flow from the next tier, and reviews of earlier tiers carry on.
On Account you can start at a higher tier if you already know the basics.

Grading is two buttons: **Again** or **Got it**. A brand-new card also gets **I know
this already**, which skips the learning steps and checks it again in about a week.
Scheduling is [FSRS](https://github.com/open-spaced-repetition/py-fsrs), the
algorithm modern Anki uses.

### Making decks

```
pip install -r tools/requirements.txt
set ANTHROPIC_API_KEY=...
python tools/make_deck.py ja --tiers 1-2 --dry-run     # plan + cost estimate
python tools/make_deck.py ja --tiers 1-2 --yes         # writes decks/ja/tier1.json, tier2.json
```

[wordfreq](https://github.com/rspeer/wordfreq) decides which words go in and in what
order (its data is CC BY-SA 4.0; thanks to Robyn Speer and the sources it credits).
Claude turns the raw tokens into dictionary words, then writes every card: meaning,
reading and furigana for Japanese, article and gender for Spanish, and an original
example sentence pitched at the tier. Mechanical checks catch broken furigana,
non-kana readings and missing fields. A second Claude pass reviews every batch, and
anything still failing is dropped and replaced by the next word. Every API result is
cached in `.deckcache/`, so an interrupted run resumes without paying twice. A word's
frequency rank is its permanent card id, so regenerating a deck never scrambles
anyone's progress.

## Grammar track

Each **skill** is one transformation: a form (食べる → 食べました, hablar → hablé) or a
pattern built on one (食べてもいい, voy a comer). Spaced repetition runs per skill and the
word in each drill is random, so you're proving you can apply the rule to any word.
About 70% of drill words come from your own vocab.

- ≥80% on a skill in a round moves it up a box; less sends it back to tomorrow.
- A skill is *learned* once it has passed on two separate days. A stage opens once
  everything before it is learned.
- 90%+ the first time a skill is drilled marks it learned at once, and **Test out of
  stage N** does that for a whole stage.
- Japanese answers can be kana, kanji or romaji. Spanish answers can include the
  pronoun. An accent-only miss is still a miss, but it says "just the accent".
- Only first attempts count. Misses come back at the end of the round for practice.

The conjugation engines are deterministic and tested (`python -m pytest tests`).
Claude never grades drills.

## Setup

Deploy `streamlit_app.py` on Streamlit Community Cloud from this repo, with these
secrets:

```toml
OWNER_EMAIL = "you@gmail.com"          # you: unlimited tutor, invite list, Anki page
ANTHROPIC_API_KEY = "sk-ant-..."       # turns on Build and Talk
DATABASE_URL = "postgresql://..."      # Neon or Supabase free tier
GH_PAT = "..."                         # owner's Anki loop only (repo scope)

[auth]                                 # Google sign-in
redirect_uri = "https://<your-app>.streamlit.app/oauth2callback"
cookie_secret = "<long random string>"
client_id = "<from Google Cloud console>"
client_secret = "<from Google Cloud console>"
server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"
```

- **Google sign-in:** in Google Cloud console, create an OAuth client ID (type "Web
  application") and add the `redirect_uri` above as an authorised redirect URI.
- **Invites:** only `OWNER_EMAIL` and the addresses on the Account page's invite list
  can sign in. Learners share your API key, capped at 120 tutor calls each per day.
- **Without `[auth]`:** the app runs as a single user (the owner) behind `APP_PIN`,
  the way it used to.
- **Without `DATABASE_URL`:** progress goes to a local SQLite file. That's fine on a
  laptop, but Streamlit Cloud wipes it on every restart.

## The owner's Anki loop

The Anki page reviews your own Anki collection. It never schedules anything:

```
python export_due.py                 # writes data/due.json and data/known.json
git add -A && git commit -m batch && git push
# review on the phone, then:
git pull
.venv/Scripts/python import_reviews.py     # Anki must be CLOSED
```

`import_reviews.py` replays the phone's answers through Anki's own scheduler
(`build_answer`/`answer_card`), so intervals are always Anki's work. It backs the
collection up to `backups/` first. It needs `python -m venv .venv &&
.venv/Scripts/python -m pip install anki`.

## What's public

The repo is public. It holds code, the decks, and the owner's Anki batch files:
a day's slice of card text, review timings, and the bare list of words studied.
Learners' progress and the reading library live only in the database. Tutor
conversations, pasted text and anything said into the microphone are never saved.
Credentials live only in Streamlit's secrets store.

Kaishi 1.5k ships with no licence and its audio comes from assorted sources, so none
of its audio is published here. The local `media/` copy is gitignored.
