"""Answer normalisation for Spanish drills, so answers can be checked by string equality.

`normalize` forgives what does not change the form: capitals, stray spaces, the ¡! and
¿? a keyboard adds, and one leading subject pronoun — "yo hablo" is the same answer as
"hablo", since Spanish drops the pronoun anyway.

`fold` strips accents but keeps ñ (año and ano are different words). A phone keyboard
makes accents slow, so when an answer is only wrong by its accents the drill can say
"just the accent" — but it is still a miss: hablo and habló are different tenses.
"""
import unicodedata

_PRONOUNS = frozenset({"yo", "tú", "tu", "él", "el", "ella", "usted", "ud", "vos",
                       "nosotros", "nosotras", "vosotros", "vosotras", "ellos", "ellas",
                       "ustedes", "uds", "vd", "vds"})
_PUNCT = "¡!¿?.,;:…\"'«»“”"
_ACCENTS = {"́", "̀", "̈"}      # acute, grave, diaeresis — not the ñ tilde


def normalize(s):
    s = unicodedata.normalize("NFC", s or "").lower()
    s = " ".join(s.split()).strip(_PUNCT + " ")
    head, _, rest = s.partition(" ")
    if rest and head.rstrip(".,") in _PRONOUNS:
        s = rest.strip(_PUNCT + " ")
    return s


def fold(s):
    d = unicodedata.normalize("NFD", s or "")
    return unicodedata.normalize("NFC", "".join(c for c in d if c not in _ACCENTS))
