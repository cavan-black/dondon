"""What differs between the languages, in one place. Pages ask this module rather than
importing a language's package directly, so adding a third language means one entry
here plus its hub/<code>/ package and decks/<code>/ files."""
import importlib
from dataclasses import dataclass


@dataclass(frozen=True)
class Lang:
    code: str
    name: str
    native: str
    tts: str                 # BCP 47 tag for the phone's text-to-speech
    placeholder: str         # answer box hint in drills
    has_reading: bool        # Japanese shows kana readings; Spanish has none
    greetings: tuple         # morning, afternoon, evening

    @property
    def curriculum(self):
        return importlib.import_module(f"hub.{self.code}.curriculum")

    @property
    def track(self):
        return self.curriculum.TRACK

    @property
    def words(self):
        return importlib.import_module(f"hub.{self.code}.lexicon").WORDS

    def normalize(self, s):
        if self.code == "ja":
            return importlib.import_module("hub.ja.kana").normalize(s)
        return importlib.import_module(f"hub.{self.code}.text").normalize(s)

    @property
    def fold(self):
        """Strips what a near-miss may differ by (accents), or None."""
        if self.code == "ja":
            return None
        return importlib.import_module(f"hub.{self.code}.text").fold

    def cue_label(self, cue, skill=None):
        """How to show a cue. Commands are addressed to usted/ustedes, never to él,
        so command skills use their own labels."""
        if cue is None:
            return ""
        labels = getattr(self.curriculum, "CUE_LABELS", {})
        if skill is not None and "imperative" in skill.key:
            labels = getattr(self.curriculum, "COMMAND_CUE_LABELS", labels)
        return labels.get(cue, cue)


LANGS = {
    "ja": Lang("ja", "Japanese", "日本語", "ja-JP",
               "type it — kana, kanji or romaji", True,
               ("おはよう", "こんにちは", "こんばんは")),
    "es": Lang("es", "Spanish", "Español", "es-ES",
               "escríbelo", False,
               ("Buenos días", "Buenas tardes", "Buenas noches")),
}


def get(code):
    return LANGS[code]
