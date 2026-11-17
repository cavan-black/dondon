"""The Spanish verbs conjugation drills are built from.

Kept as code because drilling needs what a verb DOES, and the infinitive alone does not
say: pensar is e→ie but pesar is regular, contar is o→ue but montar is not, pedir is
e→i but medir's neighbour vivir is regular. So every stem change and irregularity here
is set by hand; spelling changes (busqué, cojo, sigo) and the y of leyó are derived
from the infinitive by hub/es/conjugate.py, because those really are predictable.

Left out on purpose: reflexive verbs (levantarse — the pronoun is a separate drill),
gustar-type verbs (me gusta — the subject is the thing liked), weather verbs (llueve —
only one person exists), and verbs whose written accents moved in the 2010 spelling
reform (huir: hui/huí, reír: rio/rió), where a drill would have to pick a side.

`skip` holds forms that are grammatical but unnatural for that word — the command of
poder, the progressive of estar — a drill never asks for them.
"""
from .conjugate import Verb

_CMD = frozenset({"imperative", "neg_imperative"})
_PROG = frozenset({"present_progressive"})
# haber is drilled as the auxiliary (he, has, ha); its commands, progressive and
# perfects (he habido) are not things a learner says.
_AUX = _CMD | _PROG | {"present_perfect", "pluperfect", "infinitive"}


def _v(written, meaning, change="", irr="", part="", skip=()):
    return Verb(written, meaning, change, irr, part, frozenset(skip))


WORDS = [
    # ------------------------------------------------------------ regular -ar
    _v("hablar", "to speak"), _v("trabajar", "to work"), _v("estudiar", "to study"),
    _v("tomar", "to take, drink"), _v("llamar", "to call"), _v("llevar", "to carry, wear"),
    _v("mirar", "to look at"), _v("escuchar", "to listen to"), _v("comprar", "to buy"),
    _v("necesitar", "to need", skip=_CMD), _v("ayudar", "to help"),
    _v("viajar", "to travel"), _v("cocinar", "to cook"), _v("bailar", "to dance"),
    _v("cantar", "to sing"), _v("caminar", "to walk"), _v("esperar", "to wait, hope"),
    _v("ganar", "to win, earn"), _v("gastar", "to spend"), _v("lavar", "to wash"),
    _v("limpiar", "to clean"), _v("usar", "to use"), _v("terminar", "to finish"),
    _v("entrar", "to enter"), _v("preguntar", "to ask"), _v("contestar", "to answer"),
    _v("enseñar", "to teach, show"), _v("olvidar", "to forget"),
    _v("preparar", "to prepare"), _v("regresar", "to return"),
    _v("descansar", "to rest"), _v("nadar", "to swim"), _v("cambiar", "to change"),
    _v("dejar", "to leave, let"), _v("pasar", "to pass, spend (time)"),
    _v("visitar", "to visit"), _v("cenar", "to have dinner"),
    _v("desayunar", "to have breakfast"), _v("invitar", "to invite"),
    _v("manejar", "to drive"), _v("mandar", "to send, order"),
    _v("alquilar", "to rent"), _v("arreglar", "to fix"), _v("bajar", "to go down"),
    _v("aceptar", "to accept"), _v("tratar", "to try, treat"), _v("amar", "to love"),
    _v("crear", "to create"),
    # -car / -gar / -zar: regular, with a spelling change before e (busqué, llegue)
    _v("buscar", "to look for"), _v("tocar", "to touch, play (an instrument)"),
    _v("sacar", "to take out"), _v("practicar", "to practise"),
    _v("explicar", "to explain"), _v("llegar", "to arrive"), _v("pagar", "to pay"),
    _v("apagar", "to turn off"), _v("cruzar", "to cross"),
    _v("organizar", "to organise"), _v("utilizar", "to use"),
    # ------------------------------------------------------------ regular -er
    _v("comer", "to eat"), _v("beber", "to drink"), _v("aprender", "to learn"),
    _v("comprender", "to understand"), _v("correr", "to run"), _v("vender", "to sell"),
    _v("deber", "to owe, must", skip=_CMD | _PROG), _v("meter", "to put in"),
    _v("prometer", "to promise"), _v("responder", "to reply"), _v("temer", "to fear"),
    _v("barrer", "to sweep"), _v("esconder", "to hide"),
    _v("sorprender", "to surprise"), _v("romper", "to break", part="roto"),
    # vowel stems: leyó, leído
    _v("leer", "to read"), _v("creer", "to believe"), _v("poseer", "to own", skip=_CMD),
    # ------------------------------------------------------------ regular -ir
    _v("vivir", "to live"), _v("recibir", "to receive"), _v("decidir", "to decide"),
    _v("subir", "to go up"), _v("compartir", "to share"), _v("asistir", "to attend"),
    _v("permitir", "to allow"), _v("discutir", "to argue, discuss"),
    _v("sufrir", "to suffer"), _v("añadir", "to add"), _v("partir", "to leave, split"),
    _v("cumplir", "to fulfil"), _v("insistir", "to insist"), _v("abrir", "to open",
                                                                part="abierto"),
    _v("escribir", "to write", part="escrito"),
    _v("describir", "to describe", part="descrito"),
    _v("cubrir", "to cover", part="cubierto"),
    _v("descubrir", "to discover", part="descubierto"),
    _v("existir", "to exist", skip=_CMD),
    # ------------------------------------------------------------ e → ie
    _v("pensar", "to think", "ie"), _v("cerrar", "to close", "ie"),
    _v("empezar", "to begin", "ie"), _v("comenzar", "to begin", "ie"),
    _v("despertar", "to wake (someone)", "ie"),
    _v("recomendar", "to recommend", "ie"), _v("calentar", "to heat", "ie"),
    _v("negar", "to deny", "ie"), _v("entender", "to understand", "ie"),
    _v("perder", "to lose", "ie"), _v("encender", "to light, turn on", "ie"),
    _v("defender", "to defend", "ie"),
    _v("preferir", "to prefer", "ie"), _v("sentir", "to feel, be sorry", "ie"),
    _v("mentir", "to lie", "ie"), _v("sugerir", "to suggest", "ie"),
    _v("divertir", "to amuse", "ie"), _v("convertir", "to convert", "ie"),
    _v("advertir", "to warn", "ie"),
    # ------------------------------------------------------------ o → ue (and jugar)
    _v("contar", "to count, tell", "ue"), _v("encontrar", "to find", "ue"),
    _v("recordar", "to remember", "ue"), _v("probar", "to try, taste", "ue"),
    _v("mostrar", "to show", "ue"), _v("demostrar", "to demonstrate", "ue"),
    _v("volar", "to fly", "ue"), _v("soñar", "to dream", "ue"),
    _v("almorzar", "to have lunch", "ue"), _v("colgar", "to hang (up)", "ue"),
    _v("jugar", "to play (a game)", "ue"),
    _v("volver", "to return", "ue", part="vuelto"),
    _v("devolver", "to give back", "ue", part="devuelto"),
    _v("resolver", "to solve", "ue", part="resuelto"),
    _v("mover", "to move", "ue"), _v("morder", "to bite", "ue"),
    _v("dormir", "to sleep", "ue"),
    _v("morir", "to die", "ue", part="muerto", skip=_CMD),
    # ------------------------------------------------------------ e → i (all -ir)
    _v("pedir", "to ask for, order", "i"), _v("servir", "to serve", "i"),
    _v("repetir", "to repeat", "i"), _v("medir", "to measure", "i"),
    _v("vestir", "to dress (someone)", "i"), _v("competir", "to compete", "i"),
    _v("impedir", "to prevent", "i"), _v("seguir", "to follow, continue", "i"),
    _v("conseguir", "to get, manage", "i"), _v("elegir", "to choose", "i"),
    _v("corregir", "to correct", "i"),
    # ------------------------------------------------------------ irregular yo only
    _v("hacer", "to do, make", irr="hacer"), _v("deshacer", "to undo", irr="hacer"),
    _v("poner", "to put", irr="poner"), _v("componer", "to compose", irr="poner"),
    _v("proponer", "to propose", irr="poner"), _v("suponer", "to suppose", irr="poner"),
    _v("salir", "to go out, leave", irr="salir"), _v("traer", "to bring", irr="traer"),
    _v("atraer", "to attract", irr="traer"), _v("distraer", "to distract", irr="traer"),
    _v("caer", "to fall", irr="caer"),
    _v("saber", "to know (facts)", irr="saber", skip=_PROG),
    _v("caber", "to fit", irr="caber", skip=_CMD | _PROG),
    _v("valer", "to be worth", irr="valer", skip=_CMD | _PROG),
    _v("dar", "to give", irr="dar"), _v("ver", "to see", irr="ver"),
    # -cer / -cir after a vowel: -zco
    _v("conocer", "to know (people, places)"), _v("parecer", "to seem", skip=_CMD),
    _v("ofrecer", "to offer"), _v("agradecer", "to thank for"),
    _v("nacer", "to be born", skip=_CMD), _v("crecer", "to grow"),
    _v("obedecer", "to obey"), _v("merecer", "to deserve", skip=_CMD),
    _v("aparecer", "to appear"), _v("desaparecer", "to disappear"),
    _v("establecer", "to establish"),
    _v("conducir", "to drive", irr="ducir"), _v("traducir", "to translate", irr="ducir"),
    _v("producir", "to produce", irr="ducir"), _v("reducir", "to reduce", irr="ducir"),
    _v("introducir", "to introduce", irr="ducir"),
    # -ger / -gir: cojo, protejo
    _v("coger", "to take, catch"), _v("escoger", "to choose"),
    _v("recoger", "to pick up"), _v("proteger", "to protect"),
    _v("dirigir", "to direct"), _v("exigir", "to demand"),
    # ------------------------------------------------------------ -uir: construyo
    _v("construir", "to build"), _v("destruir", "to destroy"),
    _v("incluir", "to include"), _v("contribuir", "to contribute"),
    _v("distribuir", "to distribute"), _v("sustituir", "to replace"),
    _v("concluir", "to conclude"),
    # ------------------------------------------------------------ strong preterite only
    _v("andar", "to walk", irr="andar"),
    # ------------------------------------------------------------ the big irregulars
    _v("ser", "to be (what)", irr="ser"),
    _v("estar", "to be (how, where)", irr="estar", skip=_PROG),
    _v("ir", "to go", irr="ir"),
    _v("haber", "to have (auxiliary)", irr="haber", skip=_AUX),
    _v("tener", "to have", "ie", irr="tener"),
    _v("mantener", "to maintain", "ie", irr="tener"),
    _v("obtener", "to obtain", "ie", irr="tener"),
    _v("contener", "to contain", "ie", irr="tener", skip=_CMD),
    _v("detener", "to stop, arrest", "ie", irr="tener"),
    _v("venir", "to come", "ie", irr="venir"),
    _v("prevenir", "to prevent", "ie", irr="venir"),
    _v("decir", "to say, tell", "i", irr="decir"),
    _v("oír", "to hear", irr="oír"),
    _v("poder", "to be able to", "ue", irr="poder", skip=_CMD | _PROG),
    _v("querer", "to want, love", "ie", irr="querer", skip={"imperative"}),
]
