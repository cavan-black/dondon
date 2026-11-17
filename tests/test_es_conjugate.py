import pytest

from hub.es.conjugate import (ALL_CLASSES, BARE_FORMS, COMMAND_FORMS, IRREGULAR, PERSONS,
                              PERSON_FORMS, Verb, conjugate)
from hub.es.lexicon import WORDS

V = {w.written: w for w in WORDS}

# (verb, form, person, canonical answer) — checked against standard conjugation tables.
KNOWN = [
    # ---------------------------------------------------------------- present, regular
    ("hablar", "present", "yo", "hablo"), ("hablar", "present", "tú", "hablas"),
    ("hablar", "present", "él", "habla"), ("hablar", "present", "nosotros", "hablamos"),
    ("hablar", "present", "vosotros", "habláis"), ("hablar", "present", "ellos", "hablan"),
    ("comer", "present", "yo", "como"), ("comer", "present", "vosotros", "coméis"),
    ("comer", "present", "ellos", "comen"), ("vivir", "present", "nosotros", "vivimos"),
    ("vivir", "present", "vosotros", "vivís"), ("vivir", "present", "él", "vive"),
    ("estudiar", "present", "yo", "estudio"), ("leer", "present", "vosotros", "leéis"),
    ("creer", "present", "nosotros", "creemos"),
    # ---------------------------------------------------------------- present, stem change
    ("pensar", "present", "yo", "pienso"), ("pensar", "present", "nosotros", "pensamos"),
    ("pensar", "present", "ellos", "piensan"), ("cerrar", "present", "tú", "cierras"),
    ("empezar", "present", "él", "empieza"), ("entender", "present", "yo", "entiendo"),
    ("perder", "present", "vosotros", "perdéis"), ("preferir", "present", "yo", "prefiero"),
    ("sentir", "present", "ellos", "sienten"), ("sugerir", "present", "tú", "sugieres"),
    ("recomendar", "present", "yo", "recomiendo"), ("querer", "present", "yo", "quiero"),
    ("contar", "present", "yo", "cuento"), ("encontrar", "present", "él", "encuentra"),
    ("recordar", "present", "tú", "recuerdas"), ("volver", "present", "yo", "vuelvo"),
    ("volver", "present", "nosotros", "volvemos"), ("devolver", "present", "él", "devuelve"),
    ("poder", "present", "yo", "puedo"), ("poder", "present", "nosotros", "podemos"),
    ("dormir", "present", "tú", "duermes"), ("dormir", "present", "nosotros", "dormimos"),
    ("morir", "present", "él", "muere"), ("almorzar", "present", "yo", "almuerzo"),
    ("jugar", "present", "yo", "juego"), ("jugar", "present", "nosotros", "jugamos"),
    ("jugar", "present", "ellos", "juegan"), ("pedir", "present", "yo", "pido"),
    ("pedir", "present", "nosotros", "pedimos"), ("servir", "present", "él", "sirve"),
    ("repetir", "present", "tú", "repites"), ("seguir", "present", "yo", "sigo"),
    ("seguir", "present", "tú", "sigues"), ("conseguir", "present", "yo", "consigo"),
    ("elegir", "present", "yo", "elijo"), ("elegir", "present", "él", "elige"),
    ("corregir", "present", "yo", "corrijo"), ("vestir", "present", "ellos", "visten"),
    # ---------------------------------------------------------------- present, irregular
    ("ser", "present", "yo", "soy"), ("ser", "present", "tú", "eres"),
    ("ser", "present", "él", "es"), ("ser", "present", "nosotros", "somos"),
    ("ser", "present", "vosotros", "sois"), ("ser", "present", "ellos", "son"),
    ("estar", "present", "yo", "estoy"), ("estar", "present", "tú", "estás"),
    ("estar", "present", "él", "está"), ("estar", "present", "ellos", "están"),
    ("ir", "present", "yo", "voy"), ("ir", "present", "vosotros", "vais"),
    ("ir", "present", "nosotros", "vamos"), ("haber", "present", "él", "ha"),
    ("haber", "present", "yo", "he"), ("haber", "present", "vosotros", "habéis"),
    ("tener", "present", "yo", "tengo"), ("tener", "present", "tú", "tienes"),
    ("tener", "present", "nosotros", "tenemos"), ("tener", "present", "ellos", "tienen"),
    ("venir", "present", "yo", "vengo"), ("venir", "present", "él", "viene"),
    ("venir", "present", "vosotros", "venís"), ("decir", "present", "yo", "digo"),
    ("decir", "present", "tú", "dices"), ("decir", "present", "nosotros", "decimos"),
    ("oír", "present", "yo", "oigo"), ("oír", "present", "tú", "oyes"),
    ("oír", "present", "nosotros", "oímos"), ("oír", "present", "vosotros", "oís"),
    ("oír", "present", "ellos", "oyen"), ("mantener", "present", "yo", "mantengo"),
    ("mantener", "present", "él", "mantiene"), ("obtener", "present", "ellos", "obtienen"),
    ("prevenir", "present", "tú", "previenes"),
    ("hacer", "present", "yo", "hago"), ("hacer", "present", "tú", "haces"),
    ("poner", "present", "yo", "pongo"), ("suponer", "present", "yo", "supongo"),
    ("salir", "present", "yo", "salgo"), ("traer", "present", "yo", "traigo"),
    ("traer", "present", "vosotros", "traéis"), ("atraer", "present", "yo", "atraigo"),
    ("caer", "present", "yo", "caigo"), ("caer", "present", "él", "cae"),
    ("conocer", "present", "yo", "conozco"), ("conocer", "present", "tú", "conoces"),
    ("parecer", "present", "yo", "parezco"), ("ofrecer", "present", "yo", "ofrezco"),
    ("conducir", "present", "yo", "conduzco"), ("traducir", "present", "yo", "traduzco"),
    ("conducir", "present", "nosotros", "conducimos"),
    ("saber", "present", "yo", "sé"), ("saber", "present", "tú", "sabes"),
    ("ver", "present", "yo", "veo"), ("ver", "present", "vosotros", "veis"),
    ("dar", "present", "yo", "doy"), ("dar", "present", "vosotros", "dais"),
    ("caber", "present", "yo", "quepo"), ("caber", "present", "tú", "cabes"),
    ("valer", "present", "yo", "valgo"), ("coger", "present", "yo", "cojo"),
    ("escoger", "present", "yo", "escojo"), ("proteger", "present", "yo", "protejo"),
    ("dirigir", "present", "yo", "dirijo"), ("exigir", "present", "tú", "exiges"),
    ("construir", "present", "yo", "construyo"), ("construir", "present", "él", "construye"),
    ("construir", "present", "nosotros", "construimos"),
    ("construir", "present", "vosotros", "construís"),
    ("incluir", "present", "ellos", "incluyen"), ("andar", "present", "yo", "ando"),
    # ---------------------------------------------------------------- preterite
    ("hablar", "preterite", "yo", "hablé"), ("hablar", "preterite", "tú", "hablaste"),
    ("hablar", "preterite", "él", "habló"), ("hablar", "preterite", "nosotros", "hablamos"),
    ("hablar", "preterite", "vosotros", "hablasteis"),
    ("hablar", "preterite", "ellos", "hablaron"),
    ("comer", "preterite", "yo", "comí"), ("comer", "preterite", "él", "comió"),
    ("comer", "preterite", "ellos", "comieron"), ("vivir", "preterite", "tú", "viviste"),
    ("buscar", "preterite", "yo", "busqué"), ("buscar", "preterite", "tú", "buscaste"),
    ("tocar", "preterite", "yo", "toqué"), ("llegar", "preterite", "yo", "llegué"),
    ("pagar", "preterite", "yo", "pagué"), ("jugar", "preterite", "yo", "jugué"),
    ("jugar", "preterite", "él", "jugó"), ("empezar", "preterite", "yo", "empecé"),
    ("empezar", "preterite", "él", "empezó"), ("almorzar", "preterite", "yo", "almorcé"),
    ("cruzar", "preterite", "yo", "crucé"), ("pensar", "preterite", "él", "pensó"),
    ("volver", "preterite", "él", "volvió"), ("pedir", "preterite", "yo", "pedí"),
    ("pedir", "preterite", "él", "pidió"), ("pedir", "preterite", "ellos", "pidieron"),
    ("pedir", "preterite", "nosotros", "pedimos"), ("dormir", "preterite", "él", "durmió"),
    ("dormir", "preterite", "ellos", "durmieron"), ("dormir", "preterite", "yo", "dormí"),
    ("morir", "preterite", "él", "murió"), ("sentir", "preterite", "él", "sintió"),
    ("preferir", "preterite", "ellos", "prefirieron"), ("servir", "preterite", "él", "sirvió"),
    ("seguir", "preterite", "él", "siguió"), ("seguir", "preterite", "yo", "seguí"),
    ("elegir", "preterite", "ellos", "eligieron"), ("repetir", "preterite", "él", "repitió"),
    ("leer", "preterite", "yo", "leí"), ("leer", "preterite", "tú", "leíste"),
    ("leer", "preterite", "él", "leyó"), ("leer", "preterite", "nosotros", "leímos"),
    ("leer", "preterite", "ellos", "leyeron"), ("creer", "preterite", "él", "creyó"),
    ("caer", "preterite", "él", "cayó"), ("caer", "preterite", "tú", "caíste"),
    ("oír", "preterite", "yo", "oí"), ("oír", "preterite", "él", "oyó"),
    ("oír", "preterite", "ellos", "oyeron"), ("oír", "preterite", "tú", "oíste"),
    ("construir", "preterite", "yo", "construí"),
    ("construir", "preterite", "tú", "construiste"),
    ("construir", "preterite", "él", "construyó"),
    ("construir", "preterite", "ellos", "construyeron"),
    ("ser", "preterite", "yo", "fui"), ("ser", "preterite", "él", "fue"),
    ("ir", "preterite", "ellos", "fueron"), ("ir", "preterite", "nosotros", "fuimos"),
    ("estar", "preterite", "yo", "estuve"), ("estar", "preterite", "él", "estuvo"),
    ("tener", "preterite", "yo", "tuve"), ("tener", "preterite", "ellos", "tuvieron"),
    ("mantener", "preterite", "él", "mantuvo"), ("andar", "preterite", "yo", "anduve"),
    ("poder", "preterite", "yo", "pude"), ("poder", "preterite", "él", "pudo"),
    ("poner", "preterite", "yo", "puse"), ("poner", "preterite", "él", "puso"),
    ("saber", "preterite", "yo", "supe"), ("querer", "preterite", "yo", "quise"),
    ("querer", "preterite", "él", "quiso"), ("venir", "preterite", "yo", "vine"),
    ("venir", "preterite", "él", "vino"), ("venir", "preterite", "ellos", "vinieron"),
    ("hacer", "preterite", "yo", "hice"), ("hacer", "preterite", "él", "hizo"),
    ("hacer", "preterite", "nosotros", "hicimos"), ("deshacer", "preterite", "él", "deshizo"),
    ("decir", "preterite", "yo", "dije"), ("decir", "preterite", "él", "dijo"),
    ("decir", "preterite", "ellos", "dijeron"), ("traer", "preterite", "yo", "traje"),
    ("traer", "preterite", "ellos", "trajeron"), ("conducir", "preterite", "yo", "conduje"),
    ("conducir", "preterite", "ellos", "condujeron"),
    ("traducir", "preterite", "él", "tradujo"), ("caber", "preterite", "yo", "cupe"),
    ("haber", "preterite", "él", "hubo"), ("dar", "preterite", "yo", "di"),
    ("dar", "preterite", "él", "dio"), ("dar", "preterite", "ellos", "dieron"),
    ("ver", "preterite", "yo", "vi"), ("ver", "preterite", "él", "vio"),
    ("ver", "preterite", "tú", "viste"), ("salir", "preterite", "yo", "salí"),
    ("conocer", "preterite", "él", "conoció"),
    # ---------------------------------------------------------------- imperfect
    ("hablar", "imperfect", "yo", "hablaba"), ("hablar", "imperfect", "nosotros", "hablábamos"),
    ("hablar", "imperfect", "vosotros", "hablabais"), ("comer", "imperfect", "tú", "comías"),
    ("vivir", "imperfect", "nosotros", "vivíamos"), ("pensar", "imperfect", "él", "pensaba"),
    ("ser", "imperfect", "yo", "era"), ("ser", "imperfect", "nosotros", "éramos"),
    ("ir", "imperfect", "él", "iba"), ("ir", "imperfect", "nosotros", "íbamos"),
    ("ver", "imperfect", "yo", "veía"), ("ver", "imperfect", "ellos", "veían"),
    ("leer", "imperfect", "él", "leía"), ("oír", "imperfect", "yo", "oía"),
    # ---------------------------------------------------------------- future / conditional
    ("hablar", "future", "yo", "hablaré"), ("comer", "future", "tú", "comerás"),
    ("vivir", "future", "nosotros", "viviremos"), ("ir", "future", "él", "irá"),
    ("ser", "future", "vosotros", "seréis"), ("oír", "future", "yo", "oiré"),
    ("tener", "future", "yo", "tendré"), ("venir", "future", "él", "vendrá"),
    ("poner", "future", "nosotros", "pondremos"), ("salir", "future", "ellos", "saldrán"),
    ("poder", "future", "yo", "podré"), ("querer", "future", "tú", "querrás"),
    ("saber", "future", "yo", "sabré"), ("haber", "future", "él", "habrá"),
    ("hacer", "future", "yo", "haré"), ("decir", "future", "ellos", "dirán"),
    ("caber", "future", "él", "cabrá"), ("valer", "future", "él", "valdrá"),
    ("mantener", "future", "yo", "mantendré"), ("suponer", "future", "yo", "supondré"),
    ("deshacer", "future", "yo", "desharé"),
    ("hablar", "conditional", "yo", "hablaría"), ("vivir", "conditional", "nosotros", "viviríamos"),
    ("tener", "conditional", "yo", "tendría"), ("hacer", "conditional", "él", "haría"),
    ("decir", "conditional", "tú", "dirías"), ("poder", "conditional", "ellos", "podrían"),
    ("querer", "conditional", "yo", "querría"), ("saber", "conditional", "nosotros", "sabríamos"),
    # ---------------------------------------------------------------- present subjunctive
    ("hablar", "present_subjunctive", "yo", "hable"),
    ("hablar", "present_subjunctive", "vosotros", "habléis"),
    ("comer", "present_subjunctive", "tú", "comas"),
    ("vivir", "present_subjunctive", "nosotros", "vivamos"),
    ("buscar", "present_subjunctive", "yo", "busque"),
    ("llegar", "present_subjunctive", "ellos", "lleguen"),
    ("empezar", "present_subjunctive", "yo", "empiece"),
    ("empezar", "present_subjunctive", "nosotros", "empecemos"),
    ("almorzar", "present_subjunctive", "nosotros", "almorcemos"),
    ("jugar", "present_subjunctive", "yo", "juegue"),
    ("jugar", "present_subjunctive", "nosotros", "juguemos"),
    ("pensar", "present_subjunctive", "tú", "pienses"),
    ("pensar", "present_subjunctive", "nosotros", "pensemos"),
    ("volver", "present_subjunctive", "nosotros", "volvamos"),
    ("volver", "present_subjunctive", "ellos", "vuelvan"),
    ("dormir", "present_subjunctive", "yo", "duerma"),
    ("dormir", "present_subjunctive", "nosotros", "durmamos"),
    ("sentir", "present_subjunctive", "nosotros", "sintamos"),
    ("preferir", "present_subjunctive", "vosotros", "prefiráis"),
    ("pedir", "present_subjunctive", "yo", "pida"),
    ("pedir", "present_subjunctive", "nosotros", "pidamos"),
    ("seguir", "present_subjunctive", "yo", "siga"),
    ("elegir", "present_subjunctive", "él", "elija"),
    ("coger", "present_subjunctive", "yo", "coja"),
    ("conocer", "present_subjunctive", "yo", "conozca"),
    ("conducir", "present_subjunctive", "nosotros", "conduzcamos"),
    ("construir", "present_subjunctive", "yo", "construya"),
    ("hacer", "present_subjunctive", "yo", "haga"),
    ("tener", "present_subjunctive", "nosotros", "tengamos"),
    ("venir", "present_subjunctive", "ellos", "vengan"),
    ("decir", "present_subjunctive", "tú", "digas"),
    ("poner", "present_subjunctive", "él", "ponga"),
    ("salir", "present_subjunctive", "yo", "salga"),
    ("traer", "present_subjunctive", "yo", "traiga"),
    ("oír", "present_subjunctive", "yo", "oiga"),
    ("caber", "present_subjunctive", "yo", "quepa"),
    ("ver", "present_subjunctive", "yo", "vea"),
    ("ver", "present_subjunctive", "vosotros", "veáis"),
    ("ser", "present_subjunctive", "yo", "sea"), ("ser", "present_subjunctive", "nosotros", "seamos"),
    ("estar", "present_subjunctive", "yo", "esté"),
    ("estar", "present_subjunctive", "tú", "estés"),
    ("estar", "present_subjunctive", "nosotros", "estemos"),
    ("ir", "present_subjunctive", "yo", "vaya"), ("ir", "present_subjunctive", "nosotros", "vayamos"),
    ("haber", "present_subjunctive", "él", "haya"),
    ("saber", "present_subjunctive", "yo", "sepa"),
    ("dar", "present_subjunctive", "yo", "dé"), ("dar", "present_subjunctive", "él", "dé"),
    ("dar", "present_subjunctive", "tú", "des"), ("dar", "present_subjunctive", "vosotros", "deis"),
    ("poder", "present_subjunctive", "nosotros", "podamos"),
    ("querer", "present_subjunctive", "yo", "quiera"),
    # ---------------------------------------------------------------- imperfect subjunctive
    ("hablar", "imperfect_subjunctive", "yo", "hablara"),
    ("hablar", "imperfect_subjunctive", "nosotros", "habláramos"),
    ("comer", "imperfect_subjunctive", "nosotros", "comiéramos"),
    ("vivir", "imperfect_subjunctive", "ellos", "vivieran"),
    ("tener", "imperfect_subjunctive", "yo", "tuviera"),
    ("ser", "imperfect_subjunctive", "yo", "fuera"),
    ("ir", "imperfect_subjunctive", "nosotros", "fuéramos"),
    ("decir", "imperfect_subjunctive", "nosotros", "dijéramos"),
    ("pedir", "imperfect_subjunctive", "yo", "pidiera"),
    ("dormir", "imperfect_subjunctive", "él", "durmiera"),
    ("leer", "imperfect_subjunctive", "yo", "leyera"),
    ("dar", "imperfect_subjunctive", "yo", "diera"),
    ("haber", "imperfect_subjunctive", "yo", "hubiera"),
    ("hacer", "imperfect_subjunctive", "tú", "hicieras"),
    ("poder", "imperfect_subjunctive", "yo", "pudiera"),
    ("estar", "imperfect_subjunctive", "él", "estuviera"),
    ("querer", "imperfect_subjunctive", "yo", "quisiera"),
    # ---------------------------------------------------------------- commands
    ("hablar", "imperative", "tú", "habla"), ("hablar", "imperative", "él", "hable"),
    ("hablar", "imperative", "nosotros", "hablemos"),
    ("hablar", "imperative", "vosotros", "hablad"),
    ("hablar", "imperative", "ellos", "hablen"), ("comer", "imperative", "tú", "come"),
    ("vivir", "imperative", "vosotros", "vivid"), ("pensar", "imperative", "tú", "piensa"),
    ("dormir", "imperative", "tú", "duerme"), ("dormir", "imperative", "nosotros", "durmamos"),
    ("pedir", "imperative", "tú", "pide"), ("jugar", "imperative", "tú", "juega"),
    ("leer", "imperative", "tú", "lee"), ("oír", "imperative", "tú", "oye"),
    ("oír", "imperative", "vosotros", "oíd"), ("construir", "imperative", "tú", "construye"),
    ("buscar", "imperative", "él", "busque"),
    ("hacer", "imperative", "tú", "haz"), ("decir", "imperative", "tú", "di"),
    ("ir", "imperative", "tú", "ve"), ("ir", "imperative", "vosotros", "id"),
    ("ir", "imperative", "nosotros", "vamos"), ("ir", "imperative", "él", "vaya"),
    ("poner", "imperative", "tú", "pon"), ("salir", "imperative", "tú", "sal"),
    ("ser", "imperative", "tú", "sé"), ("ser", "imperative", "vosotros", "sed"),
    ("tener", "imperative", "tú", "ten"), ("venir", "imperative", "tú", "ven"),
    ("mantener", "imperative", "tú", "mantén"), ("obtener", "imperative", "tú", "obtén"),
    ("suponer", "imperative", "tú", "supón"), ("proponer", "imperative", "tú", "propón"),
    ("prevenir", "imperative", "tú", "prevén"), ("deshacer", "imperative", "tú", "deshaz"),
    ("estar", "imperative", "tú", "está"), ("estar", "imperative", "él", "esté"),
    ("dar", "imperative", "tú", "da"), ("dar", "imperative", "él", "dé"),
    ("dar", "imperative", "ellos", "den"), ("ver", "imperative", "tú", "ve"),
    ("saber", "imperative", "él", "sepa"), ("hacer", "imperative", "ellos", "hagan"),
    ("decir", "imperative", "nosotros", "digamos"),
    ("hablar", "neg_imperative", "tú", "no hables"),
    ("comer", "neg_imperative", "tú", "no comas"),
    ("hacer", "neg_imperative", "tú", "no hagas"),
    ("decir", "neg_imperative", "tú", "no digas"),
    ("ir", "neg_imperative", "tú", "no vayas"),
    ("ir", "neg_imperative", "nosotros", "no vayamos"),
    ("ser", "neg_imperative", "tú", "no seas"),
    ("tocar", "neg_imperative", "tú", "no toques"),
    ("dormir", "neg_imperative", "ellos", "no duerman"),
    ("dar", "neg_imperative", "él", "no dé"),
    ("hablar", "neg_imperative", "vosotros", "no habléis"),
    # ---------------------------------------------------------------- compound tenses
    ("hablar", "present_perfect", "yo", "he hablado"),
    ("comer", "present_perfect", "tú", "has comido"),
    ("vivir", "present_perfect", "él", "ha vivido"),
    ("hacer", "present_perfect", "nosotros", "hemos hecho"),
    ("decir", "present_perfect", "vosotros", "habéis dicho"),
    ("ver", "present_perfect", "ellos", "han visto"),
    ("escribir", "present_perfect", "yo", "he escrito"),
    ("poner", "present_perfect", "él", "ha puesto"),
    ("volver", "present_perfect", "yo", "he vuelto"),
    ("abrir", "present_perfect", "yo", "he abierto"),
    ("romper", "present_perfect", "yo", "he roto"),
    ("morir", "present_perfect", "él", "ha muerto"),
    ("leer", "present_perfect", "yo", "he leído"),
    ("ir", "present_perfect", "yo", "he ido"), ("ser", "present_perfect", "yo", "he sido"),
    ("hablar", "pluperfect", "yo", "había hablado"),
    ("hacer", "pluperfect", "nosotros", "habíamos hecho"),
    ("decir", "pluperfect", "ellos", "habían dicho"),
    ("hablar", "present_progressive", "yo", "estoy hablando"),
    ("comer", "present_progressive", "tú", "estás comiendo"),
    ("dormir", "present_progressive", "él", "está durmiendo"),
    ("leer", "present_progressive", "nosotros", "estamos leyendo"),
    ("pedir", "present_progressive", "ellos", "están pidiendo"),
    # ---------------------------------------------------------------- gerund / participle
    ("hablar", "gerund", None, "hablando"), ("comer", "gerund", None, "comiendo"),
    ("vivir", "gerund", None, "viviendo"), ("pedir", "gerund", None, "pidiendo"),
    ("dormir", "gerund", None, "durmiendo"), ("morir", "gerund", None, "muriendo"),
    ("sentir", "gerund", None, "sintiendo"), ("decir", "gerund", None, "diciendo"),
    ("venir", "gerund", None, "viniendo"), ("seguir", "gerund", None, "siguiendo"),
    ("leer", "gerund", None, "leyendo"), ("creer", "gerund", None, "creyendo"),
    ("caer", "gerund", None, "cayendo"), ("traer", "gerund", None, "trayendo"),
    ("oír", "gerund", None, "oyendo"), ("construir", "gerund", None, "construyendo"),
    ("ir", "gerund", None, "yendo"), ("poder", "gerund", None, "pudiendo"),
    ("ser", "gerund", None, "siendo"), ("ver", "gerund", None, "viendo"),
    ("hablar", "participle", None, "hablado"), ("comer", "participle", None, "comido"),
    ("vivir", "participle", None, "vivido"), ("hacer", "participle", None, "hecho"),
    ("decir", "participle", None, "dicho"), ("ver", "participle", None, "visto"),
    ("escribir", "participle", None, "escrito"), ("describir", "participle", None, "descrito"),
    ("poner", "participle", None, "puesto"), ("suponer", "participle", None, "supuesto"),
    ("volver", "participle", None, "vuelto"), ("devolver", "participle", None, "devuelto"),
    ("abrir", "participle", None, "abierto"), ("romper", "participle", None, "roto"),
    ("morir", "participle", None, "muerto"), ("cubrir", "participle", None, "cubierto"),
    ("descubrir", "participle", None, "descubierto"),
    ("resolver", "participle", None, "resuelto"), ("deshacer", "participle", None, "deshecho"),
    ("leer", "participle", None, "leído"), ("oír", "participle", None, "oído"),
    ("traer", "participle", None, "traído"), ("caer", "participle", None, "caído"),
    ("construir", "participle", None, "construido"), ("ir", "participle", None, "ido"),
    ("ser", "participle", None, "sido"), ("valer", "participle", None, "valido"),
]


@pytest.mark.parametrize("verb,form,person,expected", KNOWN)
def test_known_forms(verb, form, person, expected):
    assert conjugate(V[verb], form, person)[0] == expected


def test_accepted_alternates():
    assert conjugate(V["hablar"], "imperfect_subjunctive", "yo") == ["hablara", "hablase"]
    assert conjugate(V["tener"], "imperfect_subjunctive", "nosotros") == [
        "tuviéramos", "tuviésemos"]
    assert conjugate(V["ir"], "imperative", "nosotros") == ["vamos", "vayamos"]
    # Everywhere else, exactly one answer.
    assert conjugate(V["ir"], "neg_imperative", "nosotros") == ["no vayamos"]
    assert conjugate(V["hablar"], "preterite", "él") == ["habló"]


def test_full_tables():
    assert [conjugate(V["ser"], "present", p)[0] for p in PERSONS] == [
        "soy", "eres", "es", "somos", "sois", "son"]
    assert [conjugate(V["estar"], "preterite", p)[0] for p in PERSONS] == [
        "estuve", "estuviste", "estuvo", "estuvimos", "estuvisteis", "estuvieron"]
    assert [conjugate(V["dar"], "present_subjunctive", p)[0] for p in PERSONS] == [
        "dé", "des", "dé", "demos", "deis", "den"]
    assert [conjugate(V["pedir"], "present_subjunctive", p)[0] for p in PERSONS] == [
        "pida", "pidas", "pida", "pidamos", "pidáis", "pidan"]
    assert [conjugate(V["leer"], "preterite", p)[0] for p in PERSONS] == [
        "leí", "leíste", "leyó", "leímos", "leísteis", "leyeron"]


def test_commands_have_no_yo():
    for form in COMMAND_FORMS:
        with pytest.raises(ValueError):
            conjugate(V["hablar"], form, "yo")


def test_every_word_conjugates_every_eligible_form():
    for w in WORDS:
        for form in PERSON_FORMS:
            if form in w.skip:
                continue
            for p in PERSONS:
                if form in COMMAND_FORMS and p == "yo":
                    continue
                got = conjugate(w, form, p)
                assert got and all(a and a == a.strip() for a in got), (w.written, form, p)
                assert len(got) == len(set(got)), (w.written, form, p)
        for form in BARE_FORMS:
            if form not in w.skip:
                assert conjugate(w, form)[0], (w.written, form)


def test_lexicon_well_formed():
    assert len(WORDS) >= 150
    assert len({w.written for w in WORDS}) == len(WORDS), "duplicate verb"
    for w in WORDS:
        assert w.written[-2:] in ("ar", "er", "ir", "ír"), w.written
        assert w.meaning.startswith("to "), w.written
        assert w.change in ("", "ie", "ue", "i"), w.written
        assert not w.irr or (w.irr in IRREGULAR and w.written.endswith(w.irr)), w.written
        assert w.cls in ALL_CLASSES, w.written
        assert isinstance(w.skip, frozenset)
        assert w.label() == w.written
        # e→i only exists in -ir verbs.
        assert w.change != "i" or w.written.endswith("ir"), w.written


def test_classification_spot_checks():
    """Hand classification: the look-alikes that conjugate apart."""
    assert V["pensar"].change == "ie" and V["contar"].change == "ue"
    assert V["pedir"].change == "i" and V["jugar"].change == "ue"
    assert V["vivir"].change == "" and V["comer"].change == ""
    assert V["hablar"].cls == "reg/reg" and V["buscar"].cls == "reg/reg"
    assert V["pensar"].cls == "stem/reg" and V["pedir"].cls == "stem/shift"
    assert V["conocer"].cls == "yo/reg" and V["hacer"].cls == "yo/strong"
    assert V["ser"].cls == "core/strong" and V["leer"].cls == "reg/y"
    assert V["construir"].cls == "uir/y" and V["andar"].cls == "reg/strong"


def test_every_irregular_named_in_the_brief_is_in_the_lexicon():
    for v in ("ser", "estar", "ir", "haber", "tener", "venir", "decir", "hacer", "poder",
              "poner", "querer", "saber", "salir", "dar", "ver", "traer", "caber", "andar",
              "conducir", "traducir", "oír", "conocer", "valer", "leer", "creer",
              "construir", "seguir", "coger"):
        assert v in V, v


def test_compound_follows_its_base():
    mantener = Verb("mantener", "to maintain", "ie", irr="tener")
    assert conjugate(mantener, "preterite", "yo") == ["mantuve"]
    assert conjugate(mantener, "present_subjunctive", "ellos") == ["mantengan"]
