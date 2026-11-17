"""Two interactive pieces that need the browser, built as Streamlit v2 components
(they run in the page itself, not an iframe, and can send values back to Python):

  reader   a passage you can tap: a word shows its reading, dictionary form and
           meaning, with a speaker button; a sentence's EN shows its translation; the
           speaker reads it out.
           Furigana can be toggled. Returns the words you tapped, so the page can
           offer to add them to your vocab.
  mic      a microphone button. Uses the browser's speech recognition (Chrome,
           Edge, Safari incl. iOS) and returns what it heard. Firefox has none; the
           button says so.

Both use the phone's own speech engines — nothing is recorded or stored here, though
Chrome does send the audio to Google to transcribe it.
"""
import hashlib, json

import streamlit as st

_COLORS = """
  --bg: #13151c; --line: #252938; --fg: #eceef5; --muted: #8d94a8;
  --accent: #8b9dff; --ok: #6fe0ab; --no: #ff8a9b;
"""

# --------------------------------------------------------------------- reader

_READER_CSS = """
.rd {%s color: var(--fg);
     font-family: 'Inter', -apple-system, 'Hiragino Sans', 'Noto Sans JP', sans-serif;}
.rd .mi {font-family: 'Material Symbols Rounded'; font-weight: 400;
     font-style: normal; font-size: 1.25em; line-height: 1; display: inline-block;
     vertical-align: -0.22em; font-feature-settings: 'liga'; text-transform: none;
     -webkit-font-smoothing: antialiased;}
.rd .bar {display: flex; gap: 0.5rem; margin-bottom: 0.6rem;}
.rd .bar button {flex: 1;}
.rd button {background: #1a1d27; color: var(--fg); border: 1px solid var(--line);
            border-radius: 12px; padding: 0.55rem 0.7rem; font-size: 0.95rem;
            cursor: pointer; font-family: inherit;}
.rd button.on {border-color: var(--accent); color: var(--accent);}
.rd .s {background: var(--bg); border: 1px solid var(--line); border-radius: 14px;
        padding: 0.7rem 0.85rem; margin-bottom: 0.5rem;}
.rd .s.playing {border-color: var(--accent);}
.rd .txt {font-size: 1.28rem; line-height: 2.15;}
.rd.es .txt {line-height: 1.75;}
.rd .w {cursor: pointer; border-radius: 6px; padding: 0 1px;}
.rd .w:hover {background: rgba(139,157,255,0.12);}
.rd .w.seen {background: rgba(139,157,255,0.18);}
.rd .w.sel {background: rgba(139,157,255,0.35);}
.rd rt {font-size: 0.5em; color: var(--muted);}
.rd .ctl {display: flex; gap: 0.4rem; justify-content: flex-end; margin-top: 0.15rem;}
.rd .ctl button {padding: 0.15rem 0.6rem; font-size: 0.8rem; border-radius: 999px;}
.rd .en {display: none; color: var(--muted); font-size: 0.95rem; line-height: 1.5;
         margin-top: 0.35rem;}
.rd .s.show .en {display: block;}
.rd .pop {background: #1d2130; border: 1px solid var(--accent); border-radius: 14px;
          padding: 0.8rem 1rem; margin: -0.2rem 0 0.6rem; display: none;}
.rd .pop .h {font-size: 1.6rem; font-weight: 600;}
.rd .pop .r {color: var(--muted); font-size: 1rem; margin-left: 0.5rem;}
.rd .pop .d {color: var(--muted); font-size: 0.85rem; margin-top: 0.1rem;}
.rd .pop .g {font-size: 1.1rem; margin-top: 0.35rem;}
.rd .pop .row {display: flex; gap: 0.5rem; margin-top: 0.6rem;}
""" % _COLORS

_SPEECH_JS = """
function voiceFor(lang) {
  const vs = speechSynthesis.getVoices();
  return vs.find(v => v.lang === lang) || vs.find(v => v.lang.startsWith(lang.slice(0, 2)));
}
function say(text, lang, rate, onend) {
  const u = new SpeechSynthesisUtterance(text);
  u.lang = lang; u.rate = rate || 0.9;
  const v = voiceFor(lang); if (v) u.voice = v;
  if (onend) u.onend = onend;
  speechSynthesis.speak(u);
}
"""

_READER_JS = _SPEECH_JS + """
const PUNCT_AFTER = /^[.,;:!?)\\]»…%、。！？」』）]/;
const OPEN_BEFORE = /[¿¡(«\\[「『（]$/;
const KANJI = /[\\u3400-\\u9fff々]/;

function esc(s) {
  return (s || '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
}

export default function (component) {
  const { data, parentElement, setStateValue } = component;
  let root = parentElement.querySelector('.rd');
  if (!root) {
    root = document.createElement('div');
    parentElement.appendChild(root);
  }
  if (root.dataset.sig === data.sig) return;
  root.dataset.sig = data.sig;
  root.className = 'rd ' + data.lang.slice(0, 2);
  const ja = data.lang.startsWith('ja');
  let furi = !!data.furigana;
  const tapped = [];

  function tokenHtml(t, si, ti) {
    let inner = esc(t.t);
    if (ja && furi && t.r && KANJI.test(t.t)) inner = `<ruby>${inner}<rt>${esc(t.r)}</rt></ruby>`;
    if (!t.g) return inner;
    return `<span class="w" data-s="${si}" data-t="${ti}">${inner}</span>`;
  }
  function sentenceHtml(s, si) {
    let out = '';
    s.tokens.forEach((t, ti) => {
      if (!ja && out && !PUNCT_AFTER.test(t.t) && !OPEN_BEFORE.test(s.tokens[ti - 1].t))
        out += ' ';
      out += tokenHtml(t, si, ti);
    });
    return out;
  }
  function plain(s) {
    let out = '';
    s.tokens.forEach((t, ti) => {
      if (!ja && out && !PUNCT_AFTER.test(t.t) && !OPEN_BEFORE.test(s.tokens[ti - 1].t))
        out += ' ';
      out += t.t;
    });
    return out;
  }

  function render() {
    const bar = `<div class="bar">
        <button class="all"><span class="mi">volume_up</span> Read it all</button>
        ${ja ? `<button class="fu ${furi ? 'on' : ''}">ふりがな</button>` : ''}
        <button class="ens">EN all</button></div>`;
    const body = data.sentences.map((s, si) => `
      <div class="s" data-i="${si}">
        <div class="txt">${sentenceHtml(s, si)}</div>
        <div class="en">${esc(s.en)}</div>
        <div class="ctl"><button class="say" data-i="${si}"><span class="mi">volume_up</span></button>
          <button class="tr" data-i="${si}">EN</button></div>
      </div>`).join('');
    root.innerHTML = bar + body + '<div class="pop"></div>';
    tapped.forEach(k => {
      const [si, ti] = k.split(':');
      const el = root.querySelector(`.w[data-s="${si}"][data-t="${ti}"]`);
      if (el) el.classList.add('seen');
    });
  }
  render();

  function closePop() {
    const pop = root.querySelector('.pop');
    pop.style.display = 'none';
    root.querySelectorAll('.w.sel').forEach(e => e.classList.remove('sel'));
  }

  root.onclick = (e) => {
    const w = e.target.closest('.w');
    const b = e.target.closest('button');
    if (b && b.classList.contains('all')) {
      speechSynthesis.cancel();
      const ss = root.querySelectorAll('.s');
      let i = 0;
      const next = () => {
        ss.forEach(x => x.classList.remove('playing'));
        if (i >= data.sentences.length) return;
        ss[i].classList.add('playing');
        say(plain(data.sentences[i]), data.lang, data.rate, next);
        i++;
      };
      next();
      return;
    }
    if (b && b.classList.contains('fu')) { furi = !furi; render(); return; }
    if (b && b.classList.contains('ens')) {
      const all = [...root.querySelectorAll('.s')];
      const show = !all.every(s => s.classList.contains('show'));
      all.forEach(s => s.classList.toggle('show', show));
      return;
    }
    if (b && b.classList.contains('say')) {
      speechSynthesis.cancel();
      say(plain(data.sentences[+b.dataset.i]), data.lang, data.rate);
      return;
    }
    if (b && b.classList.contains('tr')) {
      root.querySelector(`.s[data-i="${b.dataset.i}"]`).classList.toggle('show');
      return;
    }
    if (b && b.classList.contains('popsay')) {
      speechSynthesis.cancel(); say(b.dataset.say, data.lang, 0.8); return;
    }
    if (b && b.classList.contains('popx')) { closePop(); return; }
    if (!w) { if (!e.target.closest('.pop')) closePop(); return; }

    const si = +w.dataset.s, ti = +w.dataset.t;
    const t = data.sentences[si].tokens[ti];
    closePop();
    w.classList.add('sel', 'seen');
    const pop = root.querySelector('.pop');
    const reading = ja && t.r && t.r !== t.t ? `<span class="r">${esc(t.r)}</span>` : '';
    const dict = t.d && t.d !== t.t ? `<div class="d">dictionary form: ${esc(t.d)}</div>` : '';
    pop.innerHTML = `<div><span class="h">${esc(t.t)}</span>${reading}</div>${dict}
      <div class="g">${esc(t.g)}</div>
      <div class="row"><button class="popsay" data-say="${esc(t.r || t.t)}"><span class="mi">volume_up</span></button>
      <button class="popx">Close</button></div>`;
    // Opens in the flow under its sentence, so it never covers the page below.
    w.closest('.s').insertAdjacentElement('afterend', pop);
    pop.style.display = 'block';
    say(t.r || t.t, data.lang, 0.8);

    const k = si + ':' + ti;
    if (!tapped.includes(k)) {
      tapped.push(k);
      setStateValue('tapped', tapped.slice());
    }
  };
}
"""

_SPECS = {}


def _component(name, **spec):
    """Register on first use per Streamlit runtime, not at import: a module stays
    imported across runtimes (tests, server restarts in one process), but the
    component registry doesn't."""
    _SPECS[name] = spec

    def mount(**kw):
        try:
            return _mounters[name](**kw)
        except (KeyError, ValueError) as exc:
            if isinstance(exc, ValueError) and "not registered" not in str(exc):
                raise
            _mounters[name] = st.components.v2.component(name, **_SPECS[name])
            return _mounters[name](**kw)
    return mount


_mounters = {}
_reader = _component("dondon_reader", css=_READER_CSS, js=_READER_JS)


def _sig(obj):
    return hashlib.sha1(json.dumps(obj, sort_keys=True, ensure_ascii=False)
                        .encode()).hexdigest()[:16]


def reader(passage, lang, furigana=True, rate=0.9, key="reader"):
    """Render a passage ({"sentences": [{"tokens": [{t, r, d, g}], "en"}]}).
    Returns the tapped tokens as a list of (sentence index, token index)."""
    data = {"sentences": passage["sentences"], "lang": lang, "furigana": furigana,
            "rate": rate}
    data["sig"] = _sig(data)
    res = _reader(key=key, data=data, default={"tapped": []},
                  on_tapped_change=lambda: None)
    out = []
    for k in (res.get("tapped") or []):
        si, ti = k.split(":")
        out.append((int(si), int(ti)))
    return out


# ------------------------------------------------------------------------ mic

_MIC_CSS = """
.mic {%s font-family: 'Inter', -apple-system, sans-serif; color: var(--fg);}
.mic .mi {font-family: 'Material Symbols Rounded'; font-weight: 400;
     font-style: normal; font-size: 1.25em; line-height: 1; display: inline-block;
     vertical-align: -0.22em; font-feature-settings: 'liga'; text-transform: none;
     -webkit-font-smoothing: antialiased;}
.mic button {width: 100%%; height: 3.6rem; border-radius: 14px; font-size: 1.1rem;
             font-weight: 600; cursor: pointer; font-family: inherit;
             background: rgba(139,157,255,0.12); border: 1px solid rgba(139,157,255,0.5);
             color: var(--accent);}
.mic button.live {background: rgba(240,86,110,0.15); border-color: rgba(240,86,110,0.6);
                  color: var(--no);}
.mic .live-text {min-height: 1.4rem; text-align: center; color: var(--muted);
                 margin-top: 0.45rem; font-size: 1rem;}
""" % _COLORS

_MIC_JS = """
export default function (component) {
  const { data, parentElement, setTriggerValue } = component;
  let root = parentElement.querySelector('.mic');
  if (!root) {
    root = document.createElement('div');
    root.className = 'mic';
    parentElement.appendChild(root);
  }
  if (root.dataset.sig === data.sig) return;
  root.dataset.sig = data.sig;
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    root.innerHTML = `<div class="live-text">This browser has no speech recognition —
      open the app in Chrome or Safari to practise speaking.</div>`;
    return;
  }
  const idle = `<span class="mi">mic</span> ${data.label}`;
  root.innerHTML = `<button>${idle}</button><div class="live-text"></div>`;
  const btn = root.querySelector('button'), live = root.querySelector('.live-text');
  let rec = null;
  btn.onclick = () => {
    if (rec) { rec.stop(); return; }
    speechSynthesis.cancel();
    rec = new SR();
    rec.lang = data.lang; rec.interimResults = true; rec.maxAlternatives = 3;
    rec.continuous = false;
    let finalText = '', alts = [];
    rec.onresult = (e) => {
      let interim = '';
      for (let i = e.resultIndex; i < e.results.length; i++) {
        const r = e.results[i];
        if (r.isFinal) {
          finalText += r[0].transcript;
          alts = [...r].map(a => a.transcript);
        } else interim += r[0].transcript;
      }
      live.textContent = finalText + interim;
    };
    rec.onerror = (e) => {
      live.textContent = e.error === 'not-allowed' || e.error === 'service-not-allowed'
        ? 'Microphone blocked — allow it for this site in the browser settings.'
        : e.error === 'no-speech' ? "Didn't hear anything — try again." : 'Error: ' + e.error;
    };
    rec.onend = () => {
      rec = null;
      btn.classList.remove('live'); btn.innerHTML = idle;
      if (finalText) setTriggerValue('heard', {text: finalText, alts: alts, at: Date.now()});
    };
    btn.classList.add('live'); btn.innerHTML = '<span class="mi">graphic_eq</span> Listening… tap to stop';
    live.textContent = '';
    rec.start();
  };
}
"""

_mic = _component("dondon_mic", css=_MIC_CSS, js=_MIC_JS)


def mic(lang, label="Say it", key="mic"):
    """A microphone button. Returns {"text", "alts"} on the run right after you
    finish speaking, else None."""
    data = {"lang": lang, "label": label}
    data["sig"] = _sig({**data, "key": key})
    res = _mic(key=key, data=data, on_heard_change=lambda: None)
    return res.get("heard")
