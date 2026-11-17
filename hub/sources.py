"""Where reading material comes from: Wikipedia, in the language being learned.

Wikipedia's text is CC BY-SA 4.0, so it may be adapted — rewritten at the learner's
level — as long as the result credits the article and is shared under the same
licence. The Reading page shows that credit on every passage. Nothing here is fetched
from sites whose terms forbid reuse (news sites, NHK Easy and the like); a learner can
still paste those in for themselves, and that text is never stored.

Three ways in:
  trending      what people are reading on that Wikipedia today (the "most read" feed)
  on this day   historical events for today's date (Spanish only — Japanese Wikipedia
                doesn't publish the feed)
  topic         a search: a keyword picked at random from TOPICS, or anything typed

Each returns a Source, or None if nothing usable came back.
"""
import datetime, random, re
from dataclasses import dataclass

import requests

UA = {"User-Agent": "Dondon/1.0 (https://github.com/cavan-black/dondon)"}
TIMEOUT = 15
MAX_CHARS = 3000          # enough for a passage; the adaptation is much shorter
MIN_CHARS = {"ja": 120, "es": 300}   # Japanese packs more into fewer characters


@dataclass
class Source:
    title: str
    url: str
    text: str
    licence: str = "CC BY-SA 4.0"


# Keywords per topic, in the language itself. A topic search picks one at random and
# then one of its top results, so the same topic gives different articles each time.
TOPICS = {
    "ja": {
        "Food": ["ラーメン", "寿司", "和菓子", "カレーライス", "たこ焼き", "お好み焼き",
                 "抹茶", "うどん", "駅弁", "天ぷら", "おにぎり", "納豆", "焼き鳥"],
        "Anime & games": ["スタジオジブリ", "ポケットモンスター", "スーパーマリオ",
                          "ドラゴンボール", "ワンピース (漫画)", "ゼルダの伝説", "初音ミク",
                          "名探偵コナン", "鬼滅の刃", "ドラえもん"],
        "Travel": ["京都", "富士山", "沖縄県", "北海道", "奈良公園", "厳島神社", "白川郷",
                   "東京スカイツリー", "温泉", "新幹線", "大阪城", "屋久島"],
        "Culture": ["花見", "茶道", "相撲", "着物", "祭り", "盆踊り", "書道", "折り紙",
                    "歌舞伎", "七夕", "正月", "銭湯"],
        "Science & nature": ["ニホンザル", "桜", "地震", "台風", "宇宙", "恐竜", "火山",
                             "ロボット", "パンダ", "クジラ"],
        "History": ["江戸時代", "侍", "忍者", "織田信長", "明治維新", "平安時代",
                    "徳川家康", "城", "戦国時代"],
        "Sport & music": ["野球", "サッカー日本代表", "大谷翔平", "柔道", "J-POP",
                          "カラオケ", "マラソン", "スケートボード"],
    },
    "es": {
        "Food": ["paella", "tapas", "tortilla de patatas", "churros", "tacos", "gazpacho",
                 "empanada", "mate (infusión)", "ceviche", "jamón ibérico", "arepa",
                 "dulce de leche"],
        "Travel": ["Machu Picchu", "Sagrada Familia", "Alhambra", "Camino de Santiago",
                   "Cancún", "Buenos Aires", "Islas Galápagos", "Cartagena de Indias",
                   "Ibiza", "Patagonia", "Toledo", "Salar de Uyuni"],
        "Culture": ["flamenco", "Día de Muertos", "La Tomatina", "San Fermín", "tango",
                    "Las Fallas", "siesta", "Semana Santa", "mariachi", "piñata"],
        "Sport & music": ["Real Madrid", "Lionel Messi", "Rafael Nadal", "fútbol",
                          "Shakira", "reguetón", "Bad Bunny", "salsa (música)",
                          "Copa Mundial de Fútbol", "baloncesto"],
        "Science & nature": ["volcán", "colibrí", "selva amazónica", "tortuga marina",
                             "eclipse", "dinosaurio", "terremoto", "jaguar", "Marte",
                             "pulpo"],
        "History": ["Imperio inca", "aztecas", "Cristóbal Colón", "Frida Kahlo",
                    "Don Quijote de la Mancha", "Pablo Picasso", "mayas", "Simón Bolívar"],
        "Film & games": ["Pedro Almodóvar", "Guillermo del Toro", "Coco (película de 2017)",
                         "La casa de papel", "Pokémon", "Minecraft", "Studio Ghibli"],
    },
}


def _api(lang, **params):
    r = requests.get(f"https://{lang}.wikipedia.org/w/api.php", headers=UA,
                     timeout=TIMEOUT,
                     params={"action": "query", "format": "json", "formatversion": 2,
                             **params})
    r.raise_for_status()
    return r.json()


def _url(lang, title):
    return f"https://{lang}.wikipedia.org/wiki/" + title.replace(" ", "_")


def clean(text):
    """Plain-text extract → prose: drop section headings and the reference-ish tail."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"=+\s*.*?\s*=+", line):
            # Stop at the usual back matter; skip other headings.
            if re.search(r"脚注|参考文献|関連項目|外部リンク|Referencias|Véase también|"
                         r"Enlaces externos|Bibliografía|Notas", line):
                break
            continue
        out.append(line)
    text = "\n".join(out)
    if len(text) <= MAX_CHARS:
        return text
    cut = text[:MAX_CHARS]
    end = max(cut.rfind("。"), cut.rfind(". "), cut.rfind("\n"))
    return cut[:end + 1] if end > MAX_CHARS // 2 else cut


def article(lang, title):
    """The opening ~3,000 characters of an article as plain text."""
    j = _api(lang, prop="extracts|pageprops", titles=title, explaintext=1,
             exsectionformat="wiki", redirects=1, ppprop="disambiguation")
    pages = j.get("query", {}).get("pages", [])
    if not pages or pages[0].get("missing") or "pageprops" in pages[0]:
        return None
    p = pages[0]
    text = clean(p.get("extract", ""))
    if len(text) < MIN_CHARS.get(lang, 200):
        return None
    return Source(p["title"], _url(lang, p["title"]), text)


def search(lang, query, rng=random):
    """One of the top results for `query`, at random, skipping stubs and
    disambiguation pages."""
    j = _api(lang, generator="search", gsrsearch=query, gsrlimit=10, gsrnamespace=0,
             prop="extracts|pageprops", exintro=1, explaintext=1, exlimit=10,
             ppprop="disambiguation")
    pages = [p for p in j.get("query", {}).get("pages", [])
             if "pageprops" not in p and len(p.get("extract", "")) >= 60]
    # The best match first, then a random pick among the rest for variety.
    pages.sort(key=lambda p: p.get("index", 99))
    order = pages[:1] + rng.sample(pages[1:], len(pages[1:])) if pages else []
    if rng.random() < 0.5:
        order = order[1:] + order[:1]
    for p in order[:4]:
        src = article(lang, p["title"])
        if src:
            return src
    return None


def topic(lang, name, rng=random):
    return search(lang, rng.choice(TOPICS[lang][name]), rng)


def _feed(lang, path):
    r = requests.get(f"https://{lang}.wikipedia.org/api/rest_v1/feed/{path}",
                     headers=UA, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()


def trending(lang, rng=random, day=None):
    """A random pick from yesterday's most-read articles (today's list isn't
    published until the day is over)."""
    d = (day or datetime.date.today()) - datetime.timedelta(days=1)
    arts = _feed(lang, f"featured/{d:%Y/%m/%d}").get("mostread", {}).get("articles", [])
    arts = [a for a in arts if a.get("type") == "standard"]
    for a in rng.sample(arts[:30], min(len(arts), 30))[:6]:
        src = article(lang, a["titles"]["normalized"])
        if src:
            return src
    return None


def has_on_this_day(lang):
    return lang != "ja"


def on_this_day(lang, rng=random, day=None):
    d = day or datetime.date.today()
    events = _feed(lang, f"onthisday/events/{d:%m/%d}").get("events", [])
    rng.shuffle(events)
    for e in events[:8]:
        for p in e.get("pages", [])[:2]:
            src = article(lang, p["titles"]["normalized"])
            if src:
                src.text = f"{e.get('year')}: {e.get('text', '')}\n\n{src.text}"
                return src
    return None
