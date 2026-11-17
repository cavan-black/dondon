"""Spanish conjugation, the deterministic core of the grammar drills.

Every form comes back as a LIST of accepted answers, canonical first. Drilling is strict
about the form but must not mark a learner wrong for something that is also correct —
the -se imperfect subjunctive (hablase) next to the -ra one (hablara), vayamos next to
vamos. Alternates are listed explicitly rather than matched loosely, so a near-miss is
still a miss.

A verb is regular unless its entry says otherwise, and everything predictable is
derived rather than tabled:

  * STEM CHANGES ("boot" verbs) touch the last vowel of the stem when it carries the
    stress — yo, tú, él, ellos — so pensar → pienso but pensamos. -ir stem-changers also
    have a WEAK change (e→i, o→u) in the él/ellos preterite, the gerund and the
    nosotros/vosotros subjunctive: pidió, durmiendo, sintamos. jugar is the one u→ue
    verb and uses the same "ue" marker as o→ue.
  * SPELLING CHANGES keep the consonant's sound when the vowel after it flips between
    a/o/u and e/i: busc-é → busqué, lleg-é → llegué, empez-é → empecé, coj-o (coger),
    sig-o (seguir). They are orthography, not irregularity, so they live in _spell.
  * Vowel stems (le-er, ca-er, o-ír, constru-ir) turn an unstressed i between vowels
    into y (leyó, cayendo, construyeron) and accent it where it stands alone (leíste,
    leído) — except after u, where it stays plain (construiste, construido).
  * -cer/-cir after a vowel take -zco in yo (conozco, conduzco), and the present
    subjunctive is built from the yo form, so it inherits every yo irregularity.

What cannot be derived is in IRREGULAR, keyed by the base verb. Compounds (mantener,
suponer, deshacer, conducir) point at their base and get its irregular pieces with
their own prefix in front: mantuve, supuesto, deshizo, conduje.
"""
from dataclasses import dataclass, field

PERSONS = ("yo", "tú", "él", "nosotros", "vosotros", "ellos")
_STRESSED = {0, 1, 2, 5}          # persons whose stem carries the stress

PERSON_FORMS = ("present", "preterite", "imperfect", "future", "conditional",
                "present_subjunctive", "imperfect_subjunctive", "imperative",
                "neg_imperative", "present_perfect", "pluperfect", "present_progressive")
BARE_FORMS = ("gerund", "participle", "infinitive")
FORMS = PERSON_FORMS + BARE_FORMS
# Commands have no yo.
COMMAND_FORMS = frozenset({"imperative", "neg_imperative"})

# A verb's class is "<present behaviour>/<preterite behaviour>", so a skill can target
# e.g. every verb that is regular in the present, or every strong preterite.
PRESENT_KINDS = ("reg", "stem", "yo", "uir", "core")
PRETERITE_KINDS = ("reg", "shift", "y", "strong")
ALL_CLASSES = frozenset(f"{a}/{b}" for a in PRESENT_KINDS for b in PRETERITE_KINDS)

_ENDINGS = {
    ("present", "ar"): ("o", "as", "a", "amos", "áis", "an"),
    ("present", "er"): ("o", "es", "e", "emos", "éis", "en"),
    ("present", "ir"): ("o", "es", "e", "imos", "ís", "en"),
    ("preterite", "ar"): ("é", "aste", "ó", "amos", "asteis", "aron"),
    ("preterite", "er"): ("í", "iste", "ió", "imos", "isteis", "ieron"),
    ("preterite", "ir"): ("í", "iste", "ió", "imos", "isteis", "ieron"),
    ("imperfect", "ar"): ("aba", "abas", "aba", "ábamos", "abais", "aban"),
    ("imperfect", "er"): ("ía", "ías", "ía", "íamos", "íais", "ían"),
    ("imperfect", "ir"): ("ía", "ías", "ía", "íamos", "íais", "ían"),
    ("subj", "ar"): ("e", "es", "e", "emos", "éis", "en"),
    ("subj", "er"): ("a", "as", "a", "amos", "áis", "an"),
    ("subj", "ir"): ("a", "as", "a", "amos", "áis", "an"),
}
_FUTURE = ("é", "ás", "á", "emos", "éis", "án")
_CONDITIONAL = ("ía", "ías", "ía", "íamos", "íais", "ían")
_STRONG = ("e", "iste", "o", "imos", "isteis", "ieron")   # tuve, tuvo: no accents
_HABER_PRESENT = ("he", "has", "ha", "hemos", "habéis", "han")
_HABER_IMPERFECT = ("había", "habías", "había", "habíamos", "habíais", "habían")
_ESTAR_PRESENT = ("estoy", "estás", "está", "estamos", "estáis", "están")
_FUI = ("fui", "fuiste", "fue", "fuimos", "fuisteis", "fueron")

_ACUTE = str.maketrans("aeiou", "áéíóú")
_PLAIN = str.maketrans("áéíóú", "aeiou")
_VOWELS = "aeiouáéíóú"

# Only what cannot be derived. Keys: present (full table), yo (present yo only — the
# subjunctive follows it), preterite (full table), pret_stem (strong preterite stem),
# pret3 (él preterite when the stem's spelling shifts: hizo), imperfect (full table),
# fut (future/conditional stem), subj (full table), subj_stem, imp_tu, imp_nos
# (accepted nosotros commands), gerund, part.
IRREGULAR = {
    "ser": dict(present=["soy", "eres", "es", "somos", "sois", "son"], preterite=_FUI,
                imperfect=["era", "eras", "era", "éramos", "erais", "eran"],
                subj_stem="se", imp_tu="sé"),
    "ir": dict(present=["voy", "vas", "va", "vamos", "vais", "van"], preterite=_FUI,
               imperfect=["iba", "ibas", "iba", "íbamos", "ibais", "iban"],
               subj_stem="vay", imp_tu="ve", imp_nos=["vamos", "vayamos"], gerund="yendo"),
    "estar": dict(present=list(_ESTAR_PRESENT), pret_stem="estuv",
                  subj=["esté", "estés", "esté", "estemos", "estéis", "estén"]),
    "haber": dict(present=list(_HABER_PRESENT), pret_stem="hub", fut="habr",
                  subj_stem="hay"),
    "tener": dict(yo="tengo", pret_stem="tuv", fut="tendr", imp_tu="ten"),
    "venir": dict(yo="vengo", pret_stem="vin", fut="vendr", imp_tu="ven"),
    "decir": dict(yo="digo", pret_stem="dij", fut="dir", imp_tu="di", part="dicho"),
    "hacer": dict(yo="hago", pret_stem="hic", pret3="hizo", fut="har", imp_tu="haz",
                  part="hecho"),
    "poder": dict(pret_stem="pud", fut="podr", gerund="pudiendo"),
    "poner": dict(yo="pongo", pret_stem="pus", fut="pondr", imp_tu="pon", part="puesto"),
    "querer": dict(pret_stem="quis", fut="querr"),
    "saber": dict(yo="sé", pret_stem="sup", fut="sabr", subj_stem="sep"),
    "salir": dict(yo="salgo", fut="saldr", imp_tu="sal"),
    "valer": dict(yo="valgo", fut="valdr"),
    "caber": dict(yo="quepo", pret_stem="cup", fut="cabr"),
    "traer": dict(yo="traigo", pret_stem="traj"),
    "caer": dict(yo="caigo"),
    "andar": dict(pret_stem="anduv"),
    "ducir": dict(pret_stem="duj"),                       # conducir, traducir, producir
    # Monosyllables take no written accent: dais, veis, di, dio, vi, vio.
    "dar": dict(present=["doy", "das", "da", "damos", "dais", "dan"],
                preterite=["di", "diste", "dio", "dimos", "disteis", "dieron"],
                subj=["dé", "des", "dé", "demos", "deis", "den"]),
    "ver": dict(present=["veo", "ves", "ve", "vemos", "veis", "ven"],
                preterite=["vi", "viste", "vio", "vimos", "visteis", "vieron"],
                imperfect=["veía", "veías", "veía", "veíamos", "veíais", "veían"],
                part="visto"),
    "oír": dict(present=["oigo", "oyes", "oye", "oímos", "oís", "oyen"]),
}
# The present-tense heavyweights: irregular in more than the yo form.
CORE = frozenset({"ser", "ir", "estar", "haber", "tener", "venir", "decir", "oír"})


@dataclass(frozen=True)
class Verb:
    written: str                 # the infinitive: hablar, oír
    meaning: str                 # "to speak"
    change: str = ""             # stem change: "ie" | "ue" (also jugar's u→ue) | "i"
    irr: str = ""                # IRREGULAR key this verb (or its base) is under
    part: str = ""               # irregular past participle not covered by `irr`
    skip: frozenset = field(default_factory=frozenset)   # forms never drilled

    def label(self):
        return self.written

    # ---------------------------------------------------------------- derived shape

    @property
    def inf(self):
        """The infinitive without the accent of oír, which future endings attach to."""
        return self.written.translate(_PLAIN)

    @property
    def ending(self):
        return self.inf[-2:]

    @property
    def stem(self):
        return self.inf[:-2]

    @property
    def prefix(self):
        return self.written[:-len(self.irr)] if self.irr else ""

    @property
    def table(self):
        return IRREGULAR.get(self.irr, {})

    @property
    def uir(self):
        """construir-type: -uir where the u is pronounced (not seguir, delinquir)."""
        return self.inf.endswith("uir") and not self.inf.endswith(("guir", "quir"))

    @property
    def vowel_stem(self):
        return self.ending != "ar" and (self.stem[-1:] in ("a", "e", "o") or self.uir)

    @property
    def zc(self):
        t = self.table
        return (self.ending in ("er", "ir") and self.stem[-1:] == "c"
                and self.stem[-2:-1] in _VOWELS and "yo" not in t and "present" not in t)

    @property
    def sound(self):
        """Which consonant spelling must be preserved before a changing vowel."""
        i = self.inf
        if i.endswith("car"):
            return "k"
        if i.endswith("gar"):
            return "g"
        if i.endswith("zar"):
            return "z"
        if i.endswith("guir"):
            return "gu"
        if i.endswith(("cer", "cir")):
            return "c"
        if i.endswith(("ger", "gir")):
            return "j"
        return None

    @property
    def cls(self):
        """"<present>/<preterite>": how the verb behaves in the two tenses where
        irregularity is taught separately. See PRESENT_KINDS / PRETERITE_KINDS."""
        t = self.table
        base = self.irr
        if base in CORE:
            pres = "core"
        elif "yo" in t or "present" in t or self.zc or (
                self.sound == "j" and not self.change):
            pres = "yo"
        elif self.uir:
            pres = "uir"
        elif self.change:
            pres = "stem"
        else:
            pres = "reg"
        if "pret_stem" in t or "preterite" in t:
            pret = "strong"
        elif self.change and self.ending == "ir":
            pret = "shift"
        elif self.vowel_stem:
            pret = "y"
        else:
            pret = "reg"
        return f"{pres}/{pret}"


# -------------------------------------------------------------------- building blocks

def _uniq(xs):
    return list(dict.fromkeys(xs))


def _shift(stem, change, weak=False):
    """Apply a stem change to the stem's last vowel (ignoring the silent u of gu/qu).
    weak=True gives the -ir verbs' e→i / o→u."""
    for i in range(len(stem) - 1, -1, -1):
        c = stem[i]
        if c not in "aeiou" or (c == "u" and i and stem[i - 1] in "gq"):
            continue
        if change in ("ie", "i"):
            assert c == "e", (stem, change)
            new = "i" if weak or change == "i" else "ie"
        elif change == "ue":
            assert c in "ou", (stem, change)
            new = "u" if weak else "ue"
        else:
            raise ValueError(change)
        return stem[:i] + new + stem[i + 1:]
    raise ValueError(f"no vowel in {stem!r}")


def _spell(stem, ending, sound):
    front = ending[:1] in ("e", "é", "i", "í")
    if sound == "k" and front and stem.endswith("c"):
        stem = stem[:-1] + "qu"
    elif sound == "g" and front and stem.endswith("g"):
        stem = stem + "u"
    elif sound == "z" and front and stem.endswith("z"):
        stem = stem[:-1] + "c"
    elif sound == "c" and not front and stem.endswith("c"):
        stem = stem[:-1] + "z"
    elif sound == "j" and not front and stem.endswith("g"):
        stem = stem[:-1] + "j"
    elif sound == "gu" and not front and stem.endswith("gu"):
        stem = stem[:-1]
    return stem + ending


def _attach(v, stem, ending):
    """stem + ending, with the vowel-stem y/í rules and the spelling changes."""
    if v.vowel_stem and stem and ending[:1] == "i" and (
            stem[-1] in "aeo" or (stem[-1] == "u" and v.uir)):
        if len(ending) > 1 and ending[1] in _VOWELS:
            return stem + "y" + ending[1:]                  # leyó, construyendo
        if stem[-1] in "aeo":
            return stem + "í" + ending[1:]                  # leíste, oído
        return stem + ending                                # construiste
    return _spell(stem, ending, v.sound)


def _pre(v, x):
    """An IRREGULAR entry with the compound's prefix put back on."""
    if isinstance(x, (list, tuple)):
        return [v.prefix + s for s in x]
    return v.prefix + x


def _yo_override(v):
    t = v.table
    if "yo" in t:
        return _pre(v, t["yo"])
    if v.zc:
        return v.stem[:-1] + "zco"
    return None


# ------------------------------------------------------------------------- tenses

def _present(v):
    t = v.table
    if "present" in t:
        return _pre(v, t["present"])
    out = []
    for p, e in enumerate(_ENDINGS[("present", v.ending)]):
        stem = _shift(v.stem, v.change) if v.change and p in _STRESSED else v.stem
        if v.uir and e[0] in "oae":
            out.append(stem + "y" + e)                      # construyo, construyen
        else:
            out.append(_attach(v, stem, e))
    yo = _yo_override(v)
    if yo:
        out[0] = yo
    return out


def _subjunctive(v):
    t = v.table
    ends = _ENDINGS[("subj", v.ending)]
    if "subj" in t:
        return _pre(v, t["subj"])
    if "subj_stem" in t:
        return [_pre(v, t["subj_stem"]) + e for e in ends]
    if "present" in t or _yo_override(v) or v.uir:
        stem = _present(v)[0][:-1]                          # hag-o → hag-a, conozc-a
        return [stem + e for e in ends]
    out = []
    for p, e in enumerate(ends):
        if v.change and p in _STRESSED:
            stem = _shift(v.stem, v.change)
        elif v.change and v.ending == "ir":
            stem = _shift(v.stem, v.change, weak=True)      # pidamos, durmamos
        else:
            stem = v.stem
        out.append(_attach(v, stem, e))
    return out


def _preterite(v):
    t = v.table
    if "preterite" in t:
        return _pre(v, t["preterite"])
    if "pret_stem" in t:
        s = _pre(v, t["pret_stem"])
        ends = list(_STRONG)
        if s.endswith("j"):
            ends[5] = "eron"                                # dijeron, trajeron
        out = [s + e for e in ends]
        if "pret3" in t:
            out[2] = _pre(v, t["pret3"])
        return out
    out = []
    for p, e in enumerate(_ENDINGS[("preterite", v.ending)]):
        weak = v.change and v.ending == "ir" and p in (2, 5)
        stem = _shift(v.stem, v.change, weak=True) if weak else v.stem
        out.append(_attach(v, stem, e))
    return out


def _imperfect(v):
    t = v.table
    if "imperfect" in t:
        return _pre(v, t["imperfect"])
    return [_attach(v, v.stem, e) for e in _ENDINGS[("imperfect", v.ending)]]


def _future_stem(v):
    t = v.table
    return _pre(v, t["fut"]) if "fut" in t else v.inf


def _imperfect_subjunctive(v):
    """From the ellos preterite: hablaron → habla- + ra / se."""
    base = _preterite(v)[5][:-3]
    accented = base[:-1] + base[-1].translate(_ACUTE)       # habláramos, tuviéramos
    out = []
    for p in range(6):
        b = accented if p == 3 else base
        tails = [("ra", "se"), ("ras", "ses"), ("ra", "se"), ("ramos", "semos"),
                 ("rais", "seis"), ("ran", "sen")][p]
        out.append([b + tails[0], b + tails[1]])
    return out


def gerund(v):
    t = v.table
    if "gerund" in t:
        return _pre(v, t["gerund"])
    if v.ending == "ar":
        return v.stem + "ando"
    stem = _shift(v.stem, v.change, weak=True) if v.change and v.ending == "ir" else v.stem
    return _attach(v, stem, "iendo")


def participle(v):
    t = v.table
    if v.part:
        return v.part
    if "part" in t:
        return _pre(v, t["part"])
    if v.ending == "ar":
        return v.stem + "ado"
    return _attach(v, v.stem, "ido")


def _imperative(v, p):
    t = v.table
    if p == 1:
        if "imp_tu" in t:
            imp = t["imp_tu"]
            if v.prefix and imp in ("ten", "pon", "ven"):
                imp = imp[0] + imp[1].translate(_ACUTE) + imp[2]   # mantén, supón
            return [v.prefix + imp]
        return [_present(v)[2]]
    if p == 4:
        return [v.written[:-1] + "d"]                       # hablad, id, oíd
    if p == 3 and "imp_nos" in t:
        return _pre(v, t["imp_nos"])
    return [_subjunctive(v)[p]]


def conjugate(verb, form, person=None):
    """Accepted answers for `verb` in `form` (and `person`, one of PERSONS, for the
    personal forms), canonical first."""
    if form in BARE_FORMS:
        if person is not None:
            raise ValueError(f"{form} takes no person")
        if form == "gerund":
            return [gerund(verb)]
        if form == "participle":
            return [participle(verb)]
        return [verb.written]
    if form not in PERSON_FORMS:
        raise ValueError(f"unknown form {form!r}")
    p = PERSONS.index(person)
    if form in COMMAND_FORMS and p == 0:
        raise ValueError("commands have no yo form")
    if form == "present":
        return [_present(verb)[p]]
    if form == "preterite":
        return [_preterite(verb)[p]]
    if form == "imperfect":
        return [_imperfect(verb)[p]]
    if form == "future":
        return [_future_stem(verb) + _FUTURE[p]]
    if form == "conditional":
        return [_future_stem(verb) + _CONDITIONAL[p]]
    if form == "present_subjunctive":
        return [_subjunctive(verb)[p]]
    if form == "imperfect_subjunctive":
        return _imperfect_subjunctive(verb)[p]
    if form == "imperative":
        return _uniq(_imperative(verb, p))
    if form == "neg_imperative":
        return ["no " + _subjunctive(verb)[p]]               # no vayamos, never no vamos
    if form == "present_perfect":
        return [f"{_HABER_PRESENT[p]} {participle(verb)}"]
    if form == "pluperfect":
        return [f"{_HABER_IMPERFECT[p]} {participle(verb)}"]
    return [f"{_ESTAR_PRESENT[p]} {gerund(verb)}"]           # present_progressive
