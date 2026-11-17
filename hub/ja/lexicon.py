"""The words conjugation drills are built from.

Kept as code rather than pulled from the Anki deck because drilling needs a word's
CLASS (godan, ichidan, i-adjective...) and Kaishi carries no part-of-speech field.
Classifying by shape is unreliable — 帰る and 変える look alike and conjugate apart —
so every entry here is classified by hand. Drills prefer the entries you also know from
Anki (data/known.json), so the conjugation practice uses your own vocabulary first.

`skip` holds forms that are grammatical but unnatural for that word (the passive of
ある, the imperative of わかる); a drill never asks for them.
"""
from .conjugate import Word

_STATIVE = frozenset({"potential", "passive", "causative", "caus_passive", "imperative",
                      "prohibitive", "vol", "vol_polite", "tai", "tai_neg"})

_G = "godan"
_R = "ichidan"

_RAW = [
    # godan, う
    ("会う", "あう", _G, "to meet"), ("買う", "かう", _G, "to buy"),
    ("言う", "いう", _G, "to say"), ("使う", "つかう", _G, "to use"),
    ("歌う", "うたう", _G, "to sing"), ("洗う", "あらう", _G, "to wash"),
    ("習う", "ならう", _G, "to learn"), ("手伝う", "てつだう", _G, "to help"),
    ("思う", "おもう", _G, "to think"), ("笑う", "わらう", _G, "to laugh"),
    ("払う", "はらう", _G, "to pay"), ("拾う", "ひろう", _G, "to pick up"),
    ("吸う", "すう", _G, "to inhale, smoke"), ("向かう", "むかう", _G, "to head toward"),
    # godan, く / ぐ
    ("書く", "かく", _G, "to write"), ("聞く", "きく", _G, "to listen, ask"),
    ("歩く", "あるく", _G, "to walk"), ("働く", "はたらく", _G, "to work"),
    ("行く", "いく", _G, "to go"), ("着く", "つく", _G, "to arrive"),
    ("置く", "おく", _G, "to put"), ("引く", "ひく", _G, "to pull"),
    ("泣く", "なく", _G, "to cry"), ("履く", "はく", _G, "to wear (shoes)"),
    ("磨く", "みがく", _G, "to brush, polish"), ("動く", "うごく", _G, "to move"),
    ("急ぐ", "いそぐ", _G, "to hurry"), ("泳ぐ", "およぐ", _G, "to swim"),
    ("脱ぐ", "ぬぐ", _G, "to take off (clothes)"), ("騒ぐ", "さわぐ", _G, "to make noise"),
    # godan, す
    ("話す", "はなす", _G, "to speak"), ("貸す", "かす", _G, "to lend"),
    ("返す", "かえす", _G, "to give back"), ("出す", "だす", _G, "to take out, submit"),
    ("消す", "けす", _G, "to turn off, erase"), ("探す", "さがす", _G, "to look for"),
    ("押す", "おす", _G, "to push"), ("渡す", "わたす", _G, "to hand over"),
    ("直す", "なおす", _G, "to fix"), ("起こす", "おこす", _G, "to wake (someone)"),
    # godan, つ / ぬ / ぶ / む
    ("待つ", "まつ", _G, "to wait"), ("持つ", "もつ", _G, "to hold, have"),
    ("立つ", "たつ", _G, "to stand"), ("勝つ", "かつ", _G, "to win"),
    ("死ぬ", "しぬ", _G, "to die"),
    ("遊ぶ", "あそぶ", _G, "to play, hang out"), ("呼ぶ", "よぶ", _G, "to call"),
    ("飛ぶ", "とぶ", _G, "to fly"), ("選ぶ", "えらぶ", _G, "to choose"),
    ("運ぶ", "はこぶ", _G, "to carry"), ("学ぶ", "まなぶ", _G, "to study"),
    ("読む", "よむ", _G, "to read"), ("飲む", "のむ", _G, "to drink"),
    ("住む", "すむ", _G, "to live (somewhere)"), ("休む", "やすむ", _G, "to rest"),
    ("頼む", "たのむ", _G, "to ask (a favour)"), ("楽しむ", "たのしむ", _G, "to enjoy"),
    ("進む", "すすむ", _G, "to advance"),
    # godan, る — the ones that look ichidan are the ones worth drilling
    ("帰る", "かえる", _G, "to go home"), ("入る", "はいる", _G, "to enter"),
    ("走る", "はしる", _G, "to run"), ("知る", "しる", _G, "to come to know"),
    ("切る", "きる", _G, "to cut"), ("作る", "つくる", _G, "to make"),
    ("乗る", "のる", _G, "to ride"), ("取る", "とる", _G, "to take"),
    ("終わる", "おわる", _G, "to end"), ("座る", "すわる", _G, "to sit"),
    ("送る", "おくる", _G, "to send"), ("売る", "うる", _G, "to sell"),
    ("頑張る", "がんばる", _G, "to do one's best"), ("困る", "こまる", _G, "to be troubled"),
    ("曲がる", "まがる", _G, "to turn"), ("触る", "さわる", _G, "to touch"),
    ("守る", "まもる", _G, "to protect, keep"), ("戻る", "もどる", _G, "to return"),
    ("喋る", "しゃべる", _G, "to chat"), ("集まる", "あつまる", _G, "to gather"),
    ("登る", "のぼる", _G, "to climb"), ("泊まる", "とまる", _G, "to stay overnight"),
    ("怒る", "おこる", _G, "to get angry"), ("謝る", "あやまる", _G, "to apologise"),
    ("減る", "へる", _G, "to decrease"), ("滑る", "すべる", _G, "to slip, ski"),
    ("分かる", "わかる", _G, "to understand", _STATIVE),
    ("ある", "ある", _G, "to exist (things)", _STATIVE),
    # ichidan
    ("食べる", "たべる", _R, "to eat"), ("見る", "みる", _R, "to see"),
    ("寝る", "ねる", _R, "to sleep"), ("起きる", "おきる", _R, "to get up"),
    ("着る", "きる", _R, "to wear"), ("教える", "おしえる", _R, "to teach"),
    ("開ける", "あける", _R, "to open"), ("閉める", "しめる", _R, "to close"),
    ("始める", "はじめる", _R, "to begin"), ("出る", "でる", _R, "to leave, go out"),
    ("借りる", "かりる", _R, "to borrow"), ("忘れる", "わすれる", _R, "to forget"),
    ("覚える", "おぼえる", _R, "to memorise"), ("考える", "かんがえる", _R, "to think about"),
    ("答える", "こたえる", _R, "to answer"), ("決める", "きめる", _R, "to decide"),
    ("続ける", "つづける", _R, "to continue"), ("調べる", "しらべる", _R, "to look up"),
    ("浴びる", "あびる", _R, "to shower"), ("降りる", "おりる", _R, "to get off"),
    ("着替える", "きがえる", _R, "to change clothes"), ("生きる", "いきる", _R, "to live"),
    ("信じる", "しんじる", _R, "to believe"), ("疲れる", "つかれる", _R, "to get tired"),
    ("遅れる", "おくれる", _R, "to be late"), ("入れる", "いれる", _R, "to put in"),
    ("止める", "やめる", _R, "to quit"), ("捨てる", "すてる", _R, "to throw away"),
    ("見せる", "みせる", _R, "to show"), ("集める", "あつめる", _R, "to collect"),
    ("伝える", "つたえる", _R, "to convey"), ("変える", "かえる", _R, "to change"),
    ("比べる", "くらべる", _R, "to compare"), ("落ちる", "おちる", _R, "to fall"),
    ("慣れる", "なれる", _R, "to get used to"), ("逃げる", "にげる", _R, "to run away"),
    ("投げる", "なげる", _R, "to throw"), ("受ける", "うける", _R, "to receive, take (a test)"),
    ("褒める", "ほめる", _R, "to praise"), ("間違える", "まちがえる", _R, "to make a mistake"),
    ("迎える", "むかえる", _R, "to welcome, pick up"), ("並べる", "ならべる", _R, "to line up"),
    ("いる", "いる", _R, "to exist (living things)", frozenset({"passive", "causative",
                                                                 "caus_passive"})),
    ("できる", "できる", _R, "to be able to", _STATIVE),
    # irregular
    ("する", "する", "suru", "to do"), ("来る", "くる", "kuru", "to come"),
    ("勉強する", "べんきょうする", "suru", "to study"),
    ("運動する", "うんどうする", "suru", "to exercise"),
    ("料理する", "りょうりする", "suru", "to cook"),
    ("掃除する", "そうじする", "suru", "to clean"),
    ("洗濯する", "せんたくする", "suru", "to do laundry"),
    ("電話する", "でんわする", "suru", "to phone"),
    ("結婚する", "けっこんする", "suru", "to marry"),
    ("練習する", "れんしゅうする", "suru", "to practise"),
    ("説明する", "せつめいする", "suru", "to explain"),
    ("心配する", "しんぱいする", "suru", "to worry"),
    ("準備する", "じゅんびする", "suru", "to prepare"),
    ("散歩する", "さんぽする", "suru", "to take a walk"),
    ("旅行する", "りょこうする", "suru", "to travel"),
    ("質問する", "しつもんする", "suru", "to ask a question"),
    ("約束する", "やくそくする", "suru", "to promise"),
    ("紹介する", "しょうかいする", "suru", "to introduce"),
    ("連絡する", "れんらくする", "suru", "to contact"),
    ("予約する", "よやくする", "suru", "to reserve"),
    # i-adjectives
    ("高い", "たかい", "i", "expensive, tall"), ("安い", "やすい", "i", "cheap"),
    ("大きい", "おおきい", "i", "big"), ("小さい", "ちいさい", "i", "small"),
    ("新しい", "あたらしい", "i", "new"), ("古い", "ふるい", "i", "old (things)"),
    ("暑い", "あつい", "i", "hot (weather)"), ("寒い", "さむい", "i", "cold (weather)"),
    ("涼しい", "すずしい", "i", "cool"), ("暖かい", "あたたかい", "i", "warm"),
    ("楽しい", "たのしい", "i", "fun"), ("難しい", "むずかしい", "i", "difficult"),
    ("優しい", "やさしい", "i", "kind"), ("忙しい", "いそがしい", "i", "busy"),
    ("面白い", "おもしろい", "i", "interesting"), ("つまらない", "つまらない", "i", "boring"),
    ("美味しい", "おいしい", "i", "delicious"), ("早い", "はやい", "i", "early"),
    ("遅い", "おそい", "i", "late, slow"), ("近い", "ちかい", "i", "near"),
    ("遠い", "とおい", "i", "far"), ("長い", "ながい", "i", "long"),
    ("短い", "みじかい", "i", "short"), ("強い", "つよい", "i", "strong"),
    ("弱い", "よわい", "i", "weak"), ("多い", "おおい", "i", "many"),
    ("少ない", "すくない", "i", "few"), ("いい", "いい", "i", "good"),
    ("かっこいい", "かっこいい", "i", "cool, good-looking"), ("悪い", "わるい", "i", "bad"),
    ("痛い", "いたい", "i", "painful"), ("怖い", "こわい", "i", "scary"),
    ("嬉しい", "うれしい", "i", "happy"), ("悲しい", "かなしい", "i", "sad"),
    ("寂しい", "さびしい", "i", "lonely"), ("眠い", "ねむい", "i", "sleepy"),
    ("若い", "わかい", "i", "young"), ("明るい", "あかるい", "i", "bright"),
    ("暗い", "くらい", "i", "dark"), ("重い", "おもい", "i", "heavy"),
    ("軽い", "かるい", "i", "light"), ("広い", "ひろい", "i", "spacious"),
    ("狭い", "せまい", "i", "cramped"), ("甘い", "あまい", "i", "sweet"),
    ("辛い", "からい", "i", "spicy"), ("汚い", "きたない", "i", "dirty"),
    ("恥ずかしい", "はずかしい", "i", "embarrassing"), ("危ない", "あぶない", "i", "dangerous"),
    ("可愛い", "かわいい", "i", "cute"), ("赤い", "あかい", "i", "red"),
    # na-adjectives
    ("静か", "しずか", "na", "quiet"), ("元気", "げんき", "na", "well, lively"),
    ("綺麗", "きれい", "na", "pretty, clean"), ("有名", "ゆうめい", "na", "famous"),
    ("便利", "べんり", "na", "convenient"), ("不便", "ふべん", "na", "inconvenient"),
    ("好き", "すき", "na", "liked"), ("嫌い", "きらい", "na", "disliked"),
    ("上手", "じょうず", "na", "skilful"), ("下手", "へた", "na", "unskilful"),
    ("暇", "ひま", "na", "free (time)"), ("大切", "たいせつ", "na", "important"),
    ("大丈夫", "だいじょうぶ", "na", "all right"), ("簡単", "かんたん", "na", "easy"),
    ("親切", "しんせつ", "na", "kind"), ("賑やか", "にぎやか", "na", "lively"),
    ("大変", "たいへん", "na", "tough"), ("必要", "ひつよう", "na", "necessary"),
    ("安全", "あんぜん", "na", "safe"), ("危険", "きけん", "na", "dangerous"),
    ("自由", "じゆう", "na", "free"), ("丁寧", "ていねい", "na", "polite"),
    ("真面目", "まじめ", "na", "serious"), ("素敵", "すてき", "na", "lovely"),
    ("残念", "ざんねん", "na", "a shame"), ("特別", "とくべつ", "na", "special"),
    ("複雑", "ふくざつ", "na", "complicated"), ("楽", "らく", "na", "easy, comfortable"),
]

WORDS = [Word(r[0], r[1], r[2], r[3], r[4] if len(r) > 4 else frozenset()) for r in _RAW]
