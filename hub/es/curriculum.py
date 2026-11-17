"""Spanish grammar skills, in teaching order. Scheduling lives in hub/grammar.py.

Each skill is a conjugation form (hablar → hablé) or a pattern built from one (comer →
voy a comer), drilled with a person as the cue. Stages follow the order most courses
teach them: the present first, regular before irregular, then the ways to talk about
the future and the past, then commands, then the subjunctive.

Early skills draw only the verbs that show their rule — the regular-present skill never
hands you tener, the stem-changer skill only ever hands you stem-changers — so a
lesson's rule is the whole story for every drill in it. Later tenses draw from every
verb, irregulars included, because by then you are expected to know which is which.

vosotros is left out of the cues by default: most learners aim for Latin American
Spanish, where ustedes does its job. PERSONS_WITH_VOSOTROS is there for anyone learning
Spain's Spanish; the engine conjugates it everywhere.
"""
from ..grammar import Skill, Track
from .conjugate import (ALL_CLASSES, PRESENT_KINDS, PRETERITE_KINDS, Verb, conjugate)

PERSONS = ("yo", "tú", "él", "nosotros", "ellos")
PERSONS_WITH_VOSOTROS = ("yo", "tú", "él", "nosotros", "vosotros", "ellos")
COMMAND_PERSONS = ("tú", "él", "nosotros", "ellos")       # commands have no yo

CUE_LABELS = {
    "yo": "yo", "tú": "tú", "él": "él / ella / usted", "nosotros": "nosotros / nosotras",
    "vosotros": "vosotros / vosotras", "ellos": "ellos / ellas / ustedes",
}
# In a command the person is who you are talking to, never él or ella.
COMMAND_CUE_LABELS = {
    "tú": "tú", "él": "usted", "nosotros": "nosotros (let's)", "vosotros": "vosotros",
    "ellos": "ustedes",
}

ALL = ALL_CLASSES


def classes(present=PRESENT_KINDS, preterite=PRETERITE_KINDS):
    """Verb classes ("<present>/<preterite>") whose present and preterite kinds are
    among those given."""
    return frozenset(c for c in ALL_CLASSES
                     if c.split("/")[0] in present and c.split("/")[1] in preterite)


def _form(f):
    return lambda w, cue: conjugate(w, f, cue)


def _bare(f):
    return lambda w: conjugate(w, f)


_IR = Verb("ir", "to go", irr="ir")
_TENER = Verb("tener", "to have", "ie", irr="tener")


def _ir_a(w, cue):
    return [f"{conjugate(_IR, 'present', cue)[0]} a {w.written}"]


def _tener_que(w, cue):
    return [f"{conjugate(_TENER, 'present', cue)[0]} que {w.written}"]


def P(key, stage, title, shape, build, rule, forms, cls=ALL, cues=PERSONS):
    """A skill with a person cue."""
    return Skill(key, stage, title, shape, cls, build, rule, frozenset(forms), cues)


def B(key, stage, title, shape, build, rule, forms, cls=ALL):
    """A person-less skill (gerund, participle)."""
    return Skill(key, stage, title, shape, cls, build, rule, frozenset(forms))


STAGES = {
    1: "Present tense", 2: "The big irregulars", 3: "Stem-changing verbs",
    4: "Irregular yo", 5: "Plans & obligations", 6: "Right now",
    7: "Preterite", 8: "Irregular preterite", 9: "Imperfect", 10: "Present perfect",
    11: "Pluperfect", 12: "Future", 13: "Conditional", 14: "Commands (tú)",
    15: "Commands (usted, ustedes, nosotros)", 16: "Negative commands",
    17: "Present subjunctive", 18: "Imperfect subjunctive",
}

SKILLS = [
    P("es.present_reg", 1, "present", "presente (regular)", _form("present"),
      "Drop -ar/-er/-ir and add: -ar o, as, a, amos, áis, an (hablo, hablamos); "
      "-er o, es, e, emos, éis, en (como); -ir o, es, e, imos, ís, en (vivo, vivimos).",
      ["present"], classes(present=("reg",))),

    P("es.present_core", 2, "present", "presente (ser, estar, ir, tener…)",
      _form("present"),
      "Learn these whole: ser soy, eres, es, somos, son · estar estoy, estás, está, "
      "estamos, están · ir voy, vas, va, vamos, van · tener tengo, tienes, tiene, "
      "tenemos, tienen (venir: vengo, vienes) · decir digo, dices, dice, decimos, dicen · "
      "oír oigo, oyes, oye, oímos, oyen · haber he, has, ha, hemos, han.",
      ["present"], classes(present=("core",))),

    P("es.present_stem", 3, "present", "presente (e→ie, o→ue, e→i)", _form("present"),
      "The stressed stem vowel changes in every person but nosotros/vosotros: e→ie "
      "(pienso, piensas, pensamos), o→ue (puedo, duermo), e→i (pido, sigo), and jugar "
      "u→ue (juego). Endings stay regular.",
      ["present"], classes(present=("stem",))),

    P("es.present_yo", 4, "present", "presente (yo irregular)", _form("present"),
      "Only yo is odd; the rest is regular. -go: hago, pongo, salgo, traigo, caigo, "
      "valgo. Others: doy, sé, veo, quepo. -cer/-cir after a vowel → -zco (conozco, "
      "conduzco). -ger/-gir → -jo (cojo, protejo).",
      ["present"], classes(present=("yo",))),
    P("es.present_uir", 4, "present", "presente (-uir)", _form("present"),
      "-uir verbs add y before the ending, except in nosotros/vosotros: construyo, "
      "construyes, construye, construimos, construyen.",
      ["present"], classes(present=("uir",))),

    P("es.ir_a", 5, "going to", "ir a + inf.", _ir_a,
      "Present of ir + a + infinitive: voy a comer, vamos a salir.",
      ["infinitive"]),
    P("es.tener_que", 5, "have to", "tener que + inf.", _tener_que,
      "Present of tener + que + infinitive: tengo que trabajar, tienen que salir.",
      ["infinitive"]),

    B("es.gerund", 6, "-ing form", "gerundio", _bare("gerund"),
      "-ar → -ando (hablando), -er/-ir → -iendo (comiendo). -ir stem-changers take e→i, "
      "o→u (pidiendo, durmiendo, diciendo, viniendo); a vowel before it makes -yendo "
      "(leyendo, oyendo, construyendo). ir → yendo, poder → pudiendo.",
      ["gerund"]),
    P("es.progressive", 6, "is doing right now", "estar + gerundio",
      _form("present_progressive"),
      "Present of estar + gerund: estoy hablando, están durmiendo.",
      ["present_progressive"]),

    P("es.preterite_reg", 7, "past (completed)", "pretérito (regular)", _form("preterite"),
      "-ar: é, aste, ó, amos, asteis, aron (hablé, habló). -er/-ir: í, iste, ió, imos, "
      "isteis, ieron (comí, vivió). Spelling in yo: -car → -qué (busqué), -gar → -gué "
      "(llegué), -zar → -cé (empecé). -ar/-er stem-changers stay regular (pensé, volvió).",
      ["preterite"], classes(preterite=("reg",))),

    P("es.preterite_shift", 8, "past (completed)", "pretérito (cambios)", _form("preterite"),
      "-ir stem-changers change only in él and ellos: e→i, o→u (pidió, pidieron; durmió, "
      "durmieron; sintió). After a vowel, the i of -ió/-ieron becomes y (leyó, cayeron, "
      "oyó, construyó), and leer-type stems accent the i (leíste, leímos).",
      ["preterite"], classes(preterite=("shift", "y"))),
    P("es.preterite_strong", 8, "past (completed)", "pretérito (irregular)",
      _form("preterite"),
      "Irregular stems take e, iste, o, imos, isteis, ieron — no accents: tuve, estuve, "
      "pude, puse, supe, quise, vine, anduve, cupe, hube, hice (hizo). j-stems end -eron: "
      "dije, dijeron; traje; conduje. ser/ir: fui, fuiste, fue, fuimos, fueron. "
      "dar: di, dio · ver: vi, vio.",
      ["preterite"], classes(preterite=("strong",))),

    P("es.imperfect", 9, "used to / was doing", "imperfecto", _form("imperfect"),
      "-ar: aba, abas, aba, ábamos, abais, aban. -er/-ir: ía, ías, ía, íamos, íais, ían. "
      "No stem changes. Only three irregulars: ser era, ir iba, ver veía.",
      ["imperfect"]),

    B("es.participle", 10, "past participle", "participio", _bare("participle"),
      "-ar → -ado, -er/-ir → -ido (leído, oído, traído take an accent). Irregular: hecho, "
      "dicho, visto, escrito, puesto, vuelto, abierto, roto, muerto, cubierto, "
      "descubierto, resuelto.",
      ["participle"]),
    P("es.present_perfect", 10, "have done", "pretérito perfecto",
      _form("present_perfect"),
      "Present of haber (he, has, ha, hemos, han) + participle: he hablado, han vuelto. "
      "The participle never changes.",
      ["present_perfect"]),

    P("es.pluperfect", 11, "had done", "pluscuamperfecto", _form("pluperfect"),
      "Imperfect of haber (había, habías, había, habíamos, habían) + participle: "
      "había comido, habían dicho.",
      ["pluperfect"]),

    P("es.future", 12, "will", "futuro", _form("future"),
      "Whole infinitive + é, ás, á, emos, éis, án (hablaré, vivirán). Irregular stems: "
      "tendr-, vendr-, pondr-, saldr-, valdr-, podr-, querr-, sabr-, cabr-, habr-, "
      "har-, dir-.",
      ["future"]),

    P("es.conditional", 13, "would", "condicional", _form("conditional"),
      "Future stem + ía, ías, ía, íamos, íais, ían: hablaría, tendría, haría, diría.",
      ["conditional"]),

    P("es.imperative_tu", 14, "command (tú)", "imperativo (tú)", _form("imperative"),
      "Same as the él present: habla, come, piensa, duerme. Irregular: haz, di, ve (ir), "
      "pon, sal, sé (ser), ten, ven.",
      ["imperative"], cues=("tú",)),

    P("es.imperative_formal", 15, "command (usted, ustedes, let's)", "imperativo",
      _form("imperative"),
      "Present subjunctive: yo present minus -o, then -ar → e, -er/-ir → a. usted hable, "
      "ustedes hablen, nosotros hablemos; haga, digan, pongamos. ir: vaya, vayan, "
      "vamos.",
      ["imperative"], cues=("él", "nosotros", "ellos")),

    P("es.neg_imperative", 16, "don't…", "imperativo negativo", _form("neg_imperative"),
      "no + present subjunctive, for tú too: no hables, no comas, no hagas, no vayas; "
      "no hable, no hablemos, no hablen.",
      ["neg_imperative"], cues=COMMAND_PERSONS),

    P("es.present_subjunctive", 17, "present subjunctive", "presente de subjuntivo",
      _form("present_subjunctive"),
      "yo present minus -o, then -ar → e, es, e, emos, éis, en; -er/-ir → a, as, a, amos, "
      "áis, an (hable, coma, tenga, conozca). Stem changes follow the present; -ir ones "
      "also change nosotros (pidamos, durmamos). Irregular: sea, esté, vaya, haya, sepa, "
      "dé, quepa.",
      ["present_subjunctive"]),

    P("es.imperfect_subjunctive", 18, "past subjunctive", "imperfecto de subjuntivo",
      _form("imperfect_subjunctive"),
      "ellos preterite minus -ron, + ra, ras, ra, ´ramos, rais, ran: hablaron → hablara, "
      "habláramos; tuvieron → tuviera; fueron → fuera. The -se set (hablase) is right "
      "too.",
      ["imperfect_subjunctive"]),
]
TRACK = Track(SKILLS, STAGES)
BY_KEY = TRACK.by_key
