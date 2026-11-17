"""Spanish letters, sounds and stress — the part of Spanish that is spelled the way it
sounds, learned before the words that rely on it.

Units: the five vowels; each letter that sounds different from English (h, j and g,
c qu z, ll and y, ñ, r and rr, b and v, gu and gü); where the stress falls and when
it's written with an accent; and ¿ ¡ with typing accents on a phone.

The main drill is DICTATION: hear a word, type it. A spelling that sounds exactly
right (vaca typed "baca", hola typed "ola") counts — that's your ear working — with a
note on the real spelling. A miss only by accents says so, as in the grammar drills,
but is still a miss: the accent tells you where the stress is. The stress units add
"which syllable is stressed?", with the syllables written out by hand here.

Every word is a common one, with its meaning shown after the answer.
"""
import re

from hub.basics import Item, Unit
from .text import fold, normalize

# (word, meaning)
VOWELS = [("casa", "house"), ("mesa", "table"), ("piso", "flat; floor"),
          ("foto", "photo"), ("luna", "moon"), ("mapa", "map"), ("pelo", "hair"),
          ("vino", "wine"), ("sopa", "soup"), ("uva", "grape"), ("tema", "topic"),
          ("lima", "lime"), ("duda", "doubt"), ("oso", "bear"), ("idea", "idea"),
          ("peso", "weight"), ("mono", "monkey"), ("pila", "battery"), ("nube", "cloud"),
          ("pino", "pine tree")]

H = [("hola", "hello"), ("hoy", "today"), ("hora", "hour"), ("hijo", "son"),
     ("hermano", "brother"), ("hotel", "hotel"), ("huevo", "egg"), ("hambre", "hunger"),
     ("hielo", "ice"), ("historia", "history; story"), ("ahora", "now"),
     ("hacer", "to do, to make"), ("hablar", "to speak"), ("hombre", "man"),
     ("helado", "ice cream"), ("hospital", "hospital"), ("hasta", "until"),
     ("hija", "daughter"), ("humo", "smoke"), ("chico", "boy")]

JG = [("jamón", "ham"), ("jugo", "juice"), ("ojo", "eye"), ("joven", "young"),
      ("julio", "July"), ("jefe", "boss"), ("viaje", "trip"), ("mujer", "woman"),
      ("reloj", "watch"), ("juego", "game"), ("gente", "people"), ("general", "general"),
      ("gigante", "giant"), ("página", "page"), ("girasol", "sunflower"), ("gato", "cat"),
      ("gordo", "fat"), ("agua", "water"), ("lago", "lake"), ("amigo", "friend")]

CQZ = [("cosa", "thing"), ("cuna", "cot, cradle"), ("queso", "cheese"),
       ("quince", "fifteen"), ("aquí", "here"), ("cena", "dinner"), ("cine", "cinema"),
       ("cielo", "sky"), ("cinco", "five"), ("zapato", "shoe"), ("zona", "zone"),
       ("azul", "blue"), ("lápiz", "pencil"), ("plaza", "square"), ("cerveza", "beer"),
       ("taza", "cup"), ("cocina", "kitchen"), ("doce", "twelve"), ("quiero", "I want"),
       ("coche", "car")]

LLY = [("llave", "key"), ("lluvia", "rain"), ("calle", "street"), ("pollo", "chicken"),
       ("silla", "chair"), ("amarillo", "yellow"), ("llamar", "to call"),
       ("llegar", "to arrive"), ("ella", "she"), ("playa", "beach"), ("yo", "I"),
       ("ayer", "yesterday"), ("mayo", "May"), ("ya", "already"),
       ("desayuno", "breakfast"), ("caballo", "horse"), ("muy", "very"), ("rey", "king"),
       ("estrella", "star"), ("llorar", "to cry")]

ENYE = [("niño", "boy, child"), ("niña", "girl"), ("año", "year"),
        ("mañana", "tomorrow; morning"), ("España", "Spain"), ("señor", "sir, Mr"),
        ("señora", "madam, Mrs"), ("baño", "bathroom"), ("sueño", "dream; sleepiness"),
        ("pequeño", "small"), ("montaña", "mountain"), ("compañero", "classmate, colleague"),
        ("otoño", "autumn"), ("araña", "spider"), ("uña", "nail"),
        ("cumpleaños", "birthday"), ("dueño", "owner"), ("enseñar", "to teach"),
        ("castaña", "chestnut"), ("leña", "firewood")]

R = [("pero", "but"), ("perro", "dog"), ("caro", "expensive"), ("carro", "car (LatAm)"),
     ("cara", "face"), ("para", "for"), ("rojo", "red"), ("rosa", "rose"),
     ("río", "river"), ("ratón", "mouse"), ("tierra", "earth, land"),
     ("guitarra", "guitar"), ("correr", "to run"), ("arroz", "rice"), ("hora", "hour"),
     ("toro", "bull"), ("torre", "tower"), ("flor", "flower"), ("amor", "love"),
     ("comer", "to eat")]

BV = [("beber", "to drink"), ("vivir", "to live"), ("vaso", "glass"), ("bueno", "good"),
      ("vino", "wine"), ("boca", "mouth"), ("vaca", "cow"), ("banco", "bank; bench"),
      ("verde", "green"), ("bien", "well"), ("ventana", "window"), ("bonito", "pretty"),
      ("verano", "summer"), ("árbol", "tree"), ("nuevo", "new"), ("lavar", "to wash"),
      ("cabeza", "head"), ("abuelo", "grandfather"), ("invierno", "winter"),
      ("sábado", "Saturday")]

GU = [("guerra", "war"), ("guitarra", "guitar"), ("guía", "guide"), ("seguir", "to follow"),
      ("hamburguesa", "hamburger"), ("juguete", "toy"), ("pingüino", "penguin"),
      ("vergüenza", "shame, embarrassment"), ("cigüeña", "stork"),
      ("bilingüe", "bilingual"), ("lengua", "tongue; language"), ("antiguo", "old"),
      ("guapo", "good-looking"), ("guisante", "pea"), ("paraguas", "umbrella"),
      ("averiguar", "to find out"), ("agua", "water"), ("pagué", "I paid")]

# (word, syllables, index of the stressed one, meaning)
STRESS = [
    ("casa", ("ca", "sa"), 0, "house"), ("mesas", ("me", "sas"), 0, "tables"),
    ("hablan", ("ha", "blan"), 0, "they speak"), ("joven", ("jo", "ven"), 0, "young"),
    ("comer", ("co", "mer"), 1, "to eat"), ("ciudad", ("ciu", "dad"), 1, "city"),
    ("reloj", ("re", "loj"), 1, "watch"), ("español", ("es", "pa", "ñol"), 2, "Spanish"),
    ("trabajo", ("tra", "ba", "jo"), 1, "work"), ("ventana", ("ven", "ta", "na"), 1, "window"),
    ("azul", ("a", "zul"), 1, "blue"), ("feliz", ("fe", "liz"), 1, "happy"),
    ("amigos", ("a", "mi", "gos"), 1, "friends"), ("examen", ("e", "xa", "men"), 1, "exam"),
    ("pared", ("pa", "red"), 1, "wall"), ("profesor", ("pro", "fe", "sor"), 2, "teacher"),
    ("zapato", ("za", "pa", "to"), 1, "shoe"),
    ("universidad", ("u", "ni", "ver", "si", "dad"), 4, "university"),
    ("caminan", ("ca", "mi", "nan"), 1, "they walk"), ("hotel", ("ho", "tel"), 1, "hotel"),
    ("naranja", ("na", "ran", "ja"), 1, "orange"), ("libertad", ("li", "ber", "tad"), 2, "freedom"),
]

ACCENTS = [
    ("café", ("ca", "fé"), 1, "coffee"), ("canción", ("can", "ción"), 1, "song"),
    ("teléfono", ("te", "lé", "fo", "no"), 1, "telephone"), ("árbol", ("ár", "bol"), 0, "tree"),
    ("lápiz", ("lá", "piz"), 0, "pencil"), ("música", ("mú", "si", "ca"), 0, "music"),
    ("sábado", ("sá", "ba", "do"), 0, "Saturday"), ("también", ("tam", "bién"), 1, "also"),
    ("avión", ("a", "vión"), 1, "plane"), ("difícil", ("di", "fí", "cil"), 1, "difficult"),
    ("fácil", ("fá", "cil"), 0, "easy"), ("inglés", ("in", "glés"), 1, "English"),
    ("médico", ("mé", "di", "co"), 0, "doctor"), ("número", ("nú", "me", "ro"), 0, "number"),
    ("país", ("pa", "ís"), 1, "country"), ("día", ("dí", "a"), 0, "day"),
    ("tío", ("tí", "o"), 0, "uncle"), ("están", ("es", "tán"), 1, "they are"),
    ("mamá", ("ma", "má"), 1, "mum"), ("azúcar", ("a", "zú", "car"), 1, "sugar"),
    ("rápido", ("rá", "pi", "do"), 0, "fast"), ("plátano", ("plá", "ta", "no"), 0, "banana"),
    ("autobús", ("au", "to", "bús"), 2, "bus"), ("miércoles", ("miér", "co", "les"), 0, "Wednesday"),
]

PHRASES = [("¡Hola!", "Hi!"), ("¿Qué tal?", "How's it going?"),
           ("¿Cómo estás?", "How are you?"), ("¿Dónde está?", "Where is it?"),
           ("¡Qué bien!", "Great!"), ("Buenos días", "Good morning"),
           ("¿Cuánto cuesta?", "How much is it?"), ("Muchas gracias", "Thanks a lot"),
           ("De nada", "You're welcome"), ("¿Por qué?", "Why?"),
           ("Lo siento", "I'm sorry"), ("Por favor", "Please"),
           ("¡Hasta luego!", "See you later!"), ("¿Qué hora es?", "What time is it?"),
           ("¿Cómo te llamas?", "What's your name?"), ("Mucho gusto", "Nice to meet you")]


# --------------------------------------------------------------------- checking

def default_stress(syllables):
    """Ends in a vowel, n or s: second-to-last syllable. Anything else: the last."""
    if len(syllables) == 1:
        return 0
    last = fold(syllables[-1])[-1]
    return len(syllables) - 2 if last in "aeiouns" else len(syllables) - 1


def sound_key(s):
    """What a word sounds like, roughly, in Latin American Spanish: h is silent,
    b and v are one sound, ll and y are one sound, z and soft c sound like s, and so
    on. Two spellings with the same key are heard the same."""
    s = normalize(s)
    s = re.sub(r"gü(?=[ei])", "gw", s)           # pingüino: the u is heard
    s = fold(s)
    s = re.sub(r"(?<!c)h", "", s)
    s = s.replace("v", "b").replace("ll", "y")
    s = re.sub(r"y\b", "i", s)
    s = re.sub(r"gu(?=[ei])", "G", s)             # guerra: the u is silent
    s = re.sub(r"g(?=[ei])", "j", s).replace("G", "g")
    s = re.sub(r"c(?=[ei])", "s", s).replace("z", "s")
    s = s.replace("qu", "k")
    s = re.sub(r"c(?!h)", "k", s)
    return s


def check(item, mode, typed):
    """Dictation: the spelling, with credit for a spelling that sounds the same."""
    want = item.text
    a, e = normalize(typed), normalize(want)
    if a == e:
        return True, False, want, ""
    if fold(a) == fold(e):
        return False, True, want, ""
    if a and sound_key(a) == sound_key(e):
        return True, False, want, f"Sounds just right — it's spelled {want}"
    return False, False, want, ""


def options(item, pool, k, rng):          # Spanish has no pick-the-letter drill
    return [item.text]


# ------------------------------------------------------------------------ units

def _items(key, words):
    return tuple(Item(id=f"{key}:{w}", text=w, answers=(w,), hint=m) for w, m in words)


def _stress_items(key, words):
    return tuple(Item(id=f"{key}:{w}", text=w, answers=(w,), hint=m, syllables=s, stress=i)
                 for w, s, i, m in words)


UNITS = [
    Unit("vowels", "The five vowels", "a e i o u",
         "Five vowels, and each has one sound only, always short and clean — never the "
         "'ay' or 'oh-oo' glide of English. a as in 'father', e as in 'bed', i as in "
         "'machine', o as in 'more', u as in 'food'. Spanish is spelled the way it's "
         "said: hear a word and you can write it.",
         _items("vowels", VOWELS), ("dictate",), sample=12),
    Unit("h", "H is silent", "hola · hoy · ahora",
         "H is never pronounced: hola is 'ola', ahora is 'a-ora'. Only ch makes a sound "
         "— 'ch' as in 'church'.",
         _items("h", H), ("dictate",), sample=12),
    Unit("jg", "J, and G before e and i", "jamón · gente · gato",
         "J is a breathy h from the back of the throat, like the 'ch' in Scottish "
         "'loch'. G before e or i sounds the same (gente, página). Before a, o, u, or a "
         "consonant, g is hard as in 'go' (gato, gordo, agua).",
         _items("jg", JG), ("dictate",), sample=12),
    Unit("cqz", "C, QU and Z", "casa · queso · cena · zapato",
         "C is a hard k before a, o, u (casa, cosa); qu is that same k before e and i "
         "(queso, aquí) and the u is silent. C before e or i, and z everywhere, is an s "
         "in Latin America and a soft 'th' in most of Spain (cena, zapato). Ch is "
         "'ch' as in 'church'.",
         _items("cqz", CQZ), ("dictate",), sample=12),
    Unit("lly", "LL and Y", "llave · playa · yo",
         "Ll and y are the same sound for most speakers — like the y in 'yes', often "
         "closer to 'j' or, in Argentina, 'sh'. Y on its own or at the end of a word is "
         "the vowel i: y ('and'), muy, hoy.",
         _items("lly", LLY), ("dictate",), sample=12),
    Unit("enye", "Ñ", "niño · año · España",
         "Ñ is 'ny', like the middle of 'canyon'. It's its own letter: año (year) and "
         "ano are different words, so the tilde always matters.",
         _items("enye", ENYE), ("dictate",), sample=12),
    Unit("r", "R and RR", "pero · perro",
         "A single r between vowels is one quick tap of the tongue, like the tt in "
         "American 'butter' (pero, cara). Rr — and r at the start of a word — is a "
         "trill, several taps (perro, rojo). pero means 'but'; perro means 'dog'.",
         _items("r", R), ("dictate",), sample=12),
    Unit("bv", "B and V", "beber · vivir · vaca",
         "B and v are the same sound: a b at the start or after m/n, and a softer b, "
         "lips barely touching, between vowels. There's no English 'v'. Spelling just "
         "has to be learned with the word.",
         _items("bv", BV), ("dictate",), sample=12),
    Unit("gu", "GU and GÜ", "guitarra · pingüino",
         "Before e and i, a silent u keeps g hard: guerra, guitarra ('gee-TA-rra', not "
         "'gwi'). When that u should be heard, it gets two dots: pingüino, vergüenza. "
         "Before a and o, gu is just 'gw': agua, antiguo.",
         _items("gu", GU), ("dictate",), sample=12),
    Unit("stress", "Where the stress falls", "CA·sa · co·MER",
         "Two rules, no exceptions without an accent mark: a word ending in a vowel, n "
         "or s is stressed on the second-to-last syllable (CA-sa, HA-blan); any other "
         "ending stresses the last syllable (co-MER, ciu-DAD, es-pa-ÑOL).",
         _stress_items("stress", STRESS), ("stress", "dictate"), chart=True, sample=10),
    Unit("accents", "Written accents", "ca·FÉ · ÁR·bol",
         "An accent mark means 'the stress is here', and is written when the stress "
         "breaks the two rules: café (ends in a vowel, but stressed last), árbol (ends "
         "in l, but stressed first), teléfono. It also splits a vowel pair: dí-a, "
         "pa-ís. On a phone, hold a vowel down to get á é í ó ú.",
         _stress_items("accents", ACCENTS), ("stress", "dictate"), chart=True, sample=10),
    Unit("punct", "¿ ¡ and typing Spanish", "¿Qué tal? · ¡Hola!",
         "Questions and exclamations open with an upside-down mark as well as closing "
         "with one: ¿Qué tal? ¡Hola! On a phone keyboard, hold ? or ! for ¿ and ¡, and "
         "hold n for ñ. Add a Spanish keyboard in your phone's settings and it will "
         "suggest accents for you. The drills don't mark you down for leaving off ¿ ¡.",
         _items("punct", PHRASES), ("dictate",), chart=True, sample=10),
]

TTS = "es-ES"
LETTERS = "spelling"
