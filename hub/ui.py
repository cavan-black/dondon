"""Look and feel shared by every page, and spoken Japanese and Spanish.

SPEECH comes from the phone's own text-to-speech (the Web Speech API), not audio
files. iOS and Android both ship Japanese voices, so every word, sentence and tutor
reply can be heard without publishing anyone's recordings — the reason the deck audio
was pulled from this repo does not apply to audio the phone synthesises itself.
"""
import html, json, os

import streamlit as st


MARK = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    "assets", "mark.svg")

STYLE = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Bricolage+Grotesque:opsz,wght@12..96,600..800&family=Zen+Kaku+Gothic+New:wght@400;500;700&display=swap');

  :root {
    --bg: #0b0c11;
    --surface: #13151c;
    --raised: #1a1d27;
    --line: #252938;
    --track: #222636;
    --fg: #eceef5;
    --muted: #8d94a8;
    --ok: #3ecf8e;
    --no: #f0566e;
    --warn: #f2c76b;
    --accent: #8b9dff;
    --accent-soft: rgba(139,157,255,0.14);
    --ok-soft: rgba(62,207,142,0.14);
    --accent-2: #b39bff;
    --spark: #ff9466;
    --spark-soft: rgba(255,148,102,0.14);
    /* chart fills: the two brand hues, a step deeper so they sit in a dark panel */
    --viz-1: #7183f2; --viz-2: #e36f3a;
    --display: 'Bricolage Grotesque', 'Inter', 'Zen Kaku Gothic New', sans-serif;
    --ease: cubic-bezier(0.22, 0.8, 0.22, 1);
    /* one hue, three steps: how well a word is held */
    --seq-1: #414a8a; --seq-2: #6a79d6; --seq-3: #aab6ff;
    --r-lg: 20px; --r-md: 14px;
  }

  #MainMenu, footer {visibility: hidden;}
  header[data-testid="stHeader"] {background: rgba(11,12,17,0.82);
                                  backdrop-filter: blur(14px);}
  .stApp {background: var(--bg);}
  /* Set on the root and inherited — a blanket [class*="st-"] rule would also override
     the icon font and print icon names ("_arrow_right") instead of the icons. */
  html, body, .stApp {font-family: 'Inter', -apple-system, BlinkMacSystemFont,
                              'Segoe UI', 'Zen Kaku Gothic New', 'Hiragino Sans',
                              'Noto Sans JP', sans-serif;}
  .block-container {padding-top: 3.4rem; padding-bottom: 5rem; max-width: 560px;}

  div[data-testid="stProgress"] > div > div {background: var(--track); height: 4px;}
  div[data-testid="stProgress"] > div > div > div {background: var(--accent); height: 4px;}

  .meta {display: flex; justify-content: space-between; align-items: baseline;
         font-size: 0.72rem; color: var(--muted); letter-spacing: 0.08em;
         text-transform: uppercase; font-weight: 600; margin: 1.1rem 0 0.45rem;}
  .meta .right {text-transform: none; letter-spacing: 0; font-weight: 500;}

  .card {background: var(--surface); border: 1px solid var(--line);
         border-radius: var(--r-lg); padding: 2.0rem 1.2rem; margin: 0.6rem 0 1.0rem;
         box-shadow: 0 1px 2px rgba(0,0,0,0.4), 0 8px 24px rgba(0,0,0,0.22);}
  .card.tight {padding: 1.1rem 1.1rem;}
  .word {font-size: clamp(2.6rem, 14vw, 4.2rem); line-height: 1.45; text-align: center;
         color: var(--fg); font-weight: 500; letter-spacing: 0.01em;}
  .word.small {font-size: clamp(2rem, 10vw, 3rem);}
  .word ruby rt {font-size: 0.36em; opacity: 0.7; font-weight: 400;}
  .reading {font-size: 1.2rem; text-align: center; color: var(--muted);
            margin-top: 0.4rem; font-weight: 400;}
  .meaning {font-size: 1.35rem; text-align: center; color: var(--fg); font-weight: 600;
            margin-top: 0.8rem; line-height: 1.4;}
  .target {text-align: center; margin-top: 1.1rem;}
  .target .jp {font-size: 1.6rem; color: var(--accent); font-weight: 600;}
  .target .en {font-size: 0.9rem; color: var(--muted); margin-top: 0.1rem;}
  .rule {height: 1px; background: var(--line); margin: 1.4rem 0 1.1rem;}
  .sent {font-size: 1.22rem; line-height: 2.0; text-align: center; color: var(--fg);
         opacity: 0.92;}
  .sent ruby rt {font-size: 0.42em; opacity: 0.65;}
  .sent-en {font-size: 0.92rem; text-align: center; color: var(--muted);
            margin-top: 0.5rem; line-height: 1.5;}
  .verdict {font-size: 1.05rem; font-weight: 600; text-align: center; margin: 0.2rem 0;}
  .verdict.ok {color: #6fe0ab;} .verdict.no {color: #ff8a9b;} .verdict.mid {color: #f2c76b;}
  .answer {font-size: 1.8rem; text-align: center; color: var(--fg); margin-top: 0.3rem;}
  .why {font-size: 0.92rem; color: var(--muted); line-height: 1.55; margin-top: 0.8rem;}
  .chip {display: inline-block; font-size: 0.75rem; color: var(--muted);
         border: 1px solid var(--line); border-radius: 999px; padding: 0.1rem 0.6rem;
         margin: 0 0.25rem 0.25rem 0;}
  .chip.on {color: var(--fg); border-color: rgba(139,157,255,0.55);
            background: var(--accent-soft);}
  .chip.done {color: var(--fg); border-color: rgba(62,207,142,0.45);
              background: var(--ok-soft);}

  .big {font-family: var(--display); font-size: 2.2rem; font-weight: 700; color: var(--fg); line-height: 1.1;}
  .stat {text-align: center;}
  .stat .lbl {font-size: 0.72rem; color: var(--muted); text-transform: uppercase;
              letter-spacing: 0.06em;}

  /* ---- panels: the flat building block of Today and Progress ---- */
  .panel {background: var(--surface); border: 1px solid var(--line);
          border-radius: var(--r-lg); padding: 1.1rem 1.1rem; margin: 0 0 0.7rem;}
  .panel .h {font-family: var(--display); font-size: 0.98rem; font-weight: 700; color: var(--fg);
             letter-spacing: -0.01em;}
  .panel .note {font-size: 0.82rem; color: var(--muted); line-height: 1.5;
                margin-top: 0.3rem;}

  .bar {height: 6px; border-radius: 999px; background: var(--track); overflow: hidden;}
  .bar > i {display: block; height: 100%; border-radius: 999px;
            background: var(--accent);}
  .bar.ok > i {background: var(--ok);}
  .bar.thin {height: 4px;}

  @property --p {syntax: '<percentage>'; inherits: false; initial-value: 0%;}
  .ring {flex: none; border-radius: 50%; display: grid; place-items: center;
         position: relative;
         background: conic-gradient(var(--accent) 0%, var(--accent-2) var(--p),
                                    var(--track) var(--p));
         animation: sweep 1.2s var(--ease) 0.1s both;}
  .ring::before {content: ""; position: absolute; inset: 9px; border-radius: 50%;
                 background: var(--surface);}
  .ring > div {position: relative; text-align: center; line-height: 1.1;}
  .ring .v {font-family: var(--display); font-size: 1.7rem; font-weight: 800; color: var(--fg);
            font-variant-numeric: tabular-nums; letter-spacing: -0.02em;}
  .ring .l {font-size: 0.68rem; color: var(--muted); text-transform: uppercase;
            letter-spacing: 0.08em; font-weight: 600; margin-top: 0.2rem;}

  /* ---- Today: the hero ---- */
  .hero {display: flex; gap: 1.1rem; align-items: center;}
  .hero .side {flex: 1; min-width: 0;}
  .eyebrow {font-size: 0.72rem; color: var(--muted); text-transform: uppercase;
                  letter-spacing: 0.08em; font-weight: 600;}
  .hero .title {font-family: var(--display); font-size: 1.3rem; font-weight: 800; color: var(--fg);
                letter-spacing: -0.02em; margin: 0.15rem 0 0.55rem; line-height: 1.2;}
  .hero .under {display: flex; justify-content: space-between; gap: 0.5rem;
                font-size: 0.78rem; color: var(--muted); margin-top: 0.4rem;}
  .week {display: flex; gap: 0.35rem; margin-top: 1.0rem; padding-top: 0.9rem;
         border-top: 1px solid var(--line);}
  .week .d {flex: 1; text-align: center; font-size: 0.66rem; color: var(--muted);
            font-weight: 600; letter-spacing: 0.04em;}
  .week .d i {display: block; height: 6px; border-radius: 999px; margin-bottom: 0.35rem;
              background: var(--track);}
  .week .d.on i {background: var(--accent);}
  .week .d.now {color: var(--fg);}
  .week .streak {flex: none; align-self: center; font-size: 0.8rem; font-weight: 700;
                 color: var(--fg); padding-left: 0.5rem; white-space: nowrap;}

  /* ---- the daily plan: one row per step, the whole row is the link ---- */
  .task {display: flex; align-items: center; gap: 0.8rem;
         background: var(--surface); border: 1px solid var(--line);
         border-radius: var(--r-md); padding: 0.8rem 0.9rem; margin: 0;}
  .task .ico {flex: none; width: 2.4rem; height: 2.4rem; border-radius: 12px;
              display: grid; place-items: center; font-size: 1.15rem;
              background: var(--raised); border: 1px solid var(--line);}
  .task .body {flex: 1; min-width: 0;}
  .task .name {font-weight: 650; color: var(--fg); font-size: 0.98rem;}
  .task .sub {font-size: 0.8rem; color: var(--muted); margin: 0.1rem 0 0.45rem;
              white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
  .task .state {flex: none; font-size: 0.82rem; color: var(--muted); white-space: nowrap;
                font-variant-numeric: tabular-nums; text-align: right;}
  .task .chev {flex: none; color: var(--muted); font-size: 1.2rem; line-height: 1;
               transition: transform 0.2s var(--ease), color 0.2s;}
  .task {transition: border-color 0.2s, transform 0.12s var(--ease);}
  [class*="st-key-go_"]:hover .task {border-color: #3a4054;}
  [class*="st-key-go_"]:hover .chev {transform: translateX(3px); color: var(--fg);}
  [class*="st-key-go_"]:active .task {transform: scale(0.99);}
  .task.next {border-color: rgba(139,157,255,0.6); background:
              linear-gradient(0deg, var(--accent-soft), var(--accent-soft)), var(--surface);}
  .task.next .ico {background: var(--accent); border-color: transparent;}
  .task.done .name {color: var(--muted);}
  .task.done .ico {color: #6fe0ab; font-weight: 700;}
  .task.done .state {color: #6fe0ab; font-weight: 600;}
  [class*="st-key-go_"] {position: relative; gap: 0 !important; margin-bottom: 0.45rem;}
  [class*="st-key-go_"] div[data-testid="stElementContainer"]:has(a)
      {position: absolute; inset: 0; opacity: 0; z-index: 2; margin: 0;
       width: 100% !important;}
  [class*="st-key-go_"] div[data-testid="stElementContainer"]:has(a) *
      {height: 100%; width: 100% !important; max-width: none;}
  [class*="st-key-go_"]:active .task {border-color: var(--accent);}

  /* ---- stat tiles ---- */
  .tiles {display: grid; grid-template-columns: repeat(3, 1fr); gap: 0.5rem;
          margin-bottom: 0.7rem;}
  .tiles.two {grid-template-columns: repeat(2, 1fr);}
  .tile {background: var(--surface); border: 1px solid var(--line);
         border-radius: var(--r-md); padding: 0.8rem 0.85rem; min-width: 0;}
  .tile .v {font-family: var(--display); font-size: 1.45rem; font-weight: 800; color: var(--fg); line-height: 1.15;
            font-variant-numeric: tabular-nums; letter-spacing: -0.02em;}
  .tile .l {font-size: 0.66rem; color: var(--muted); text-transform: uppercase;
            letter-spacing: 0.07em; font-weight: 600; margin-top: 0.2rem;}
  .tile .s {font-size: 0.76rem; color: var(--muted); margin-top: 0.25rem;}

  /* ---- Progress: requirement rows, the level path, charts ---- */
  .req {margin-top: 0.85rem;}
  .req .top {display: flex; justify-content: space-between; align-items: baseline;
             font-size: 0.86rem; color: var(--fg); margin-bottom: 0.35rem; gap: 0.5rem;}
  .req .top span:last-child {color: var(--muted); font-variant-numeric: tabular-nums;
                             white-space: nowrap; font-size: 0.8rem;}
  .req .tag {font-size: 0.64rem; font-weight: 700; color: #2a1206;
             background: var(--spark); border-radius: 999px; padding: 0.05rem 0.45rem;
             margin-left: 0.4rem; letter-spacing: 0.03em; text-transform: uppercase;}

  .path {position: relative; margin-top: 0.9rem;}
  .path .step {display: flex; gap: 0.8rem; position: relative; padding-bottom: 1.0rem;}
  .path .step:last-child {padding-bottom: 0;}
  .path .step::before {content: ""; position: absolute; left: 0.68rem; top: 1.5rem;
                       bottom: 0; width: 2px; background: var(--track);}
  .path .step:last-child::before {display: none;}
  .path .step.done::before {background: var(--ok);}
  .path .dot {flex: none; width: 1.45rem; height: 1.45rem; border-radius: 50%;
              display: grid; place-items: center; font-size: 0.72rem; font-weight: 700;
              border: 2px solid var(--track); color: var(--muted); background: var(--bg);
              position: relative; z-index: 1; box-sizing: border-box;}
  .path .done .dot {background: var(--ok); border-color: var(--ok); color: #062014;}
  .path .here .dot {border-color: var(--accent); color: var(--accent);
                    box-shadow: 0 0 0 4px var(--accent-soft);}
  .path .name {font-weight: 650; color: var(--fg); font-size: 0.95rem;}
  .path .step.todo .name {color: var(--muted);}
  .path .can {font-size: 0.82rem; color: var(--muted); margin-top: 0.1rem;}
  .path .needs {font-size: 0.74rem; color: var(--muted); margin-top: 0.2rem;
                font-variant-numeric: tabular-nums;}
  .path .flag {font-size: 0.64rem; font-weight: 700; color: var(--accent);
               border: 1px solid rgba(139,157,255,0.5); border-radius: 999px;
               padding: 0.05rem 0.45rem; margin-left: 0.4rem; letter-spacing: 0.03em;
               text-transform: uppercase; white-space: nowrap;}

  .cols {display: flex; align-items: flex-end; gap: 2px; height: 104px;
         margin-top: 0.9rem; border-bottom: 1px solid var(--line);}
  .cols .c {flex: 1; height: 100%; display: flex; flex-direction: column;
            justify-content: flex-end; align-items: center; min-width: 0;}
  .cols .c i {display: block; width: 100%; max-width: 22px; background: var(--viz-1);
              border-radius: 4px 4px 0 0;}
  .cols .c i.b {background: var(--viz-2); border-radius: 4px 4px 0 0;}
  .cols .c i.b + i {border-radius: 0; margin-top: 2px;}
  .cols .c:hover i {filter: brightness(1.2);}
  .cols .c .n {font-size: 0.62rem; color: var(--muted); margin-bottom: 0.15rem;
               font-variant-numeric: tabular-nums;}
  .axis {display: flex; gap: 2px; margin-top: 0.3rem;}
  .axis span {flex: 1; text-align: center; font-size: 0.62rem; color: var(--muted);
              min-width: 0; overflow: hidden;}
  .axis span.now {color: var(--fg); font-weight: 700;}

  .row {display: flex; align-items: center; gap: 0.7rem; margin-top: 0.7rem;}
  .row .k {flex: none; width: 4.4rem; font-size: 0.84rem; color: var(--fg);}
  .row .bar {flex: 1;}
  .row .n {flex: none; width: 8.2rem; text-align: right; font-size: 0.76rem;
           color: var(--muted); font-variant-numeric: tabular-nums; white-space: nowrap;}

  .stack {display: flex; gap: 2px; height: 8px; border-radius: 999px; overflow: hidden;
          background: var(--track); margin-top: 0.4rem;}
  .stack i {display: block; height: 100%;}
  .legend {display: flex; flex-wrap: wrap; gap: 0.2rem 0.9rem; margin-top: 0.7rem;
           font-size: 0.74rem; color: var(--muted);}
  .legend b {display: inline-block; width: 8px; height: 8px; border-radius: 2px;
             margin-right: 0.35rem;}

  .stage {display: flex; align-items: center; gap: 0.7rem; padding: 0.55rem 0;
          border-top: 1px solid var(--line);}
  .stage.first {border-top: 0; margin-top: 0.4rem;}
  .stage .no {flex: none; width: 1.5rem; height: 1.5rem; border-radius: 50%;
              display: grid; place-items: center; font-size: 0.7rem; font-weight: 700;
              background: var(--track); color: var(--muted);}
  .stage.done .no {background: var(--ok); color: #062014;}
  .stage.current .no {background: var(--accent); color: #0b1020;}
  .stage .body {flex: 1; min-width: 0;}
  .stage .name {font-size: 0.88rem; color: var(--fg); font-weight: 550;}
  .stage.locked .name {color: var(--muted);}
  .stage .n {flex: none; font-size: 0.78rem; color: var(--muted);
             font-variant-numeric: tabular-nums;}
  .stage .bar {margin-top: 0.35rem;}


  /* ---- the brand lockup: two beats, the second bigger. どん、どん。 ---- */
  .brand {display: flex; align-items: center; gap: 0.6rem; justify-content: center;}
  .brand .mark {position: relative; flex: none; width: 2.5rem; height: 2.5rem;
                border-radius: 0.68rem; background: var(--raised);
                border: 1px solid var(--line);}
  .brand .mark i {position: absolute; border-radius: 50%;
                  animation: beat 0.6s var(--ease) both;}
  .brand .mark i:nth-child(1) {width: 30%; height: 30%; left: 20%; top: 49%;
                               background: var(--accent); animation-delay: 0.15s;}
  .brand .mark i:nth-child(2) {width: 41%; height: 41%; left: 45%; top: 19%;
                               background: var(--spark); animation-delay: 0.4s;}
  .brand .wm {font-family: var(--display); font-weight: 800; font-size: 1.9rem;
              letter-spacing: -0.04em; color: var(--fg); line-height: 1;}
  .brand .jp {font-size: 0.8rem; color: var(--muted); letter-spacing: 0.12em;
              align-self: flex-end; padding-bottom: 0.2rem;}
  .brand.big .mark {width: 3.4rem; height: 3.4rem; border-radius: 0.95rem;}
  .brand.big .wm {font-size: 2.7rem;}
  .hello {display: flex; justify-content: space-between; align-items: baseline;
          gap: 0.6rem; margin: 0.2rem 0 0.7rem; animation: rise 0.5s var(--ease) both;}
  .hello .hi {font-family: var(--display); font-weight: 800; font-size: 1.45rem;
              letter-spacing: -0.02em; color: var(--fg); line-height: 1.2;}
  .hello .on {font-size: 0.78rem; color: var(--muted); white-space: nowrap;}

  /* ---- the forecast: one line per level, the bar is how long it takes ---- */
  .eta {display: flex; align-items: baseline; gap: 0.5rem; flex-wrap: wrap;
        margin-top: 0.5rem;}
  .eta .when {font-family: var(--display); font-weight: 800; font-size: 1.7rem;
              letter-spacing: -0.02em; color: var(--fg); line-height: 1.15;}
  .eta .in {font-size: 0.86rem; color: var(--spark); font-weight: 600;}
  .fc {display: flex; align-items: center; gap: 0.7rem; margin-top: 0.7rem;}
  .fc .k {flex: none; width: 7.4rem; font-size: 0.84rem; color: var(--fg);
          white-space: nowrap; overflow: hidden; text-overflow: ellipsis;}
  .fc.held .k, .fc.held .n {color: var(--muted);}
  .fc .bar {flex: 1;}
  .fc.pick .bar > i {background: var(--spark);}
  .fc.pick .k {font-weight: 700;}
  .fc .n {flex: none; width: 5.2rem; text-align: right; font-size: 0.78rem;
          color: var(--fg); font-variant-numeric: tabular-nums; white-space: nowrap;}

  /* ---- motion: things arrive once, in order, then hold still ---- */
  @keyframes rise {from {opacity: 0; transform: translateY(12px);}}
  @keyframes pop {from {opacity: 0; transform: scale(0.97);}}
  @keyframes grow {from {transform: scaleX(0);}}
  @keyframes growy {from {transform: scaleY(0);}}
  @keyframes sweep {from {--p: 0%;}}
  @keyframes beat {0% {opacity: 0; transform: scale(0.2);}
                   60% {opacity: 1; transform: scale(1.18);} 100% {transform: scale(1);}}
  @keyframes halo {0%, 100% {box-shadow: 0 0 0 0 rgba(139,157,255,0.45);}
                   60% {box-shadow: 0 0 0 7px rgba(139,157,255,0);}}
  @keyframes glow {0%, 100% {box-shadow: 0 0 0 0 rgba(139,157,255,0);}
                   50% {box-shadow: 0 0 22px 0 rgba(139,157,255,0.16);}}
  @keyframes flame {0%, 100% {transform: scale(1) rotate(-2deg);}
                    50% {transform: scale(1.12) rotate(3deg);}}

  .panel, .task, .tiles .tile, .meta {animation: rise 0.55s var(--ease) both;}
  .card {animation: pop 0.28s var(--ease) both;}
  .verdict {animation: pop 0.25s var(--ease) both;}
  .bar > i, .stack i {transform-origin: left center;
                      animation: grow 0.9s var(--ease) 0.25s both;}
  .cols .c i {transform-origin: center bottom; animation: growy 0.7s var(--ease) both;}
  .week .d i {transform-origin: left center; animation: grow 0.5s var(--ease) both;}
  .path .step {animation: rise 0.5s var(--ease) both;}
  .path .here .dot {animation: halo 2.4s ease-out 1s infinite;}
  .task.next {animation: rise 0.55s var(--ease) both, glow 3.2s ease-in-out 1.2s infinite;}
  .week .streak .mi {animation: flame 1.8s ease-in-out infinite;}
  .stMain .block-container {animation: pop 0.3s var(--ease) both;}
  div[data-testid="stVerticalBlock"] > :nth-child(2) :is(.panel, .task, .tiles, .meta) {animation-delay: 90ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(3) :is(.panel, .task, .tiles, .meta) {animation-delay: 135ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(4) :is(.panel, .task, .tiles, .meta) {animation-delay: 180ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(5) :is(.panel, .task, .tiles, .meta) {animation-delay: 225ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(6) :is(.panel, .task, .tiles, .meta) {animation-delay: 270ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(7) :is(.panel, .task, .tiles, .meta) {animation-delay: 315ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(8) :is(.panel, .task, .tiles, .meta) {animation-delay: 360ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(9) :is(.panel, .task, .tiles, .meta) {animation-delay: 405ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(10) :is(.panel, .task, .tiles, .meta) {animation-delay: 450ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(11) :is(.panel, .task, .tiles, .meta) {animation-delay: 495ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(12) :is(.panel, .task, .tiles, .meta) {animation-delay: 540ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(13) :is(.panel, .task, .tiles, .meta) {animation-delay: 585ms;}
  div[data-testid="stVerticalBlock"] > :nth-child(14) :is(.panel, .task, .tiles, .meta) {animation-delay: 630ms;}
  .tiles .tile:nth-child(1) {animation-delay: 50ms;}
  .tiles .tile:nth-child(2) {animation-delay: 100ms;}
  .tiles .tile:nth-child(3) {animation-delay: 150ms;}
  .tiles .tile:nth-child(4) {animation-delay: 200ms;}
  .tiles .tile:nth-child(5) {animation-delay: 250ms;}
  .tiles .tile:nth-child(6) {animation-delay: 300ms;}
  .cols .c:nth-child(1) i {animation-delay: 185ms;}
  .cols .c:nth-child(2) i {animation-delay: 220ms;}
  .cols .c:nth-child(3) i {animation-delay: 255ms;}
  .cols .c:nth-child(4) i {animation-delay: 290ms;}
  .cols .c:nth-child(5) i {animation-delay: 325ms;}
  .cols .c:nth-child(6) i {animation-delay: 360ms;}
  .cols .c:nth-child(7) i {animation-delay: 395ms;}
  .cols .c:nth-child(8) i {animation-delay: 430ms;}
  .cols .c:nth-child(9) i {animation-delay: 465ms;}
  .cols .c:nth-child(10) i {animation-delay: 500ms;}
  .cols .c:nth-child(11) i {animation-delay: 535ms;}
  .cols .c:nth-child(12) i {animation-delay: 570ms;}
  .cols .c:nth-child(13) i {animation-delay: 605ms;}
  .cols .c:nth-child(14) i {animation-delay: 640ms;}
  .path .step:nth-child(1) {animation-delay: 220ms;}
  .path .step:nth-child(2) {animation-delay: 290ms;}
  .path .step:nth-child(3) {animation-delay: 360ms;}
  .path .step:nth-child(4) {animation-delay: 430ms;}
  .path .step:nth-child(5) {animation-delay: 500ms;}
  .path .step:nth-child(6) {animation-delay: 570ms;}
  .week .d:nth-child(1) i {animation-delay: 350ms;}
  .week .d:nth-child(2) i {animation-delay: 400ms;}
  .week .d:nth-child(3) i {animation-delay: 450ms;}
  .week .d:nth-child(4) i {animation-delay: 500ms;}
  .week .d:nth-child(5) i {animation-delay: 550ms;}
  .week .d:nth-child(6) i {animation-delay: 600ms;}
  .week .d:nth-child(7) i {animation-delay: 650ms;}
  @media (prefers-reduced-motion: reduce) {
    *, *::before, *::after {animation: none !important; transition: none !important;}
  }

  /* ---- icons: Material Symbols Rounded, the set Streamlit's own widgets use ---- */
  .mi {font-family: 'Material Symbols Rounded'; font-weight: 400; font-style: normal;
       font-size: 1.25em; line-height: 1; letter-spacing: normal; text-transform: none;
       display: inline-block; white-space: nowrap; direction: ltr; vertical-align: -0.22em;
       -webkit-font-feature-settings: 'liga'; font-feature-settings: 'liga';
       -webkit-font-smoothing: antialiased; user-select: none;
       font-variation-settings: 'FILL' 0, 'wght' 400, 'GRAD' 0, 'opsz' 24;}
  .mi.fill {font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;}
  .task .ico .mi {font-size: 1.35rem; vertical-align: 0; color: var(--fg);}
  .task.next .ico .mi {color: #0b1020;}
  .task.done .ico .mi {color: #6fe0ab;}
  .week .streak .mi {color: var(--spark); font-size: 1.15rem;}
  .word .mi {font-size: 1em; color: var(--accent);}

  /* ---- controls ---- */
  .stButton > button, .stFormSubmitButton > button {
      height: 3.3rem; font-size: 1.0rem; font-weight: 600; border-radius: 14px;
      border: 1px solid var(--line); background: var(--raised); color: var(--fg);
      transition: transform 0.12s var(--ease), filter 0.15s, border-color 0.15s;}
  .stButton > button:active, .stFormSubmitButton > button:active {transform: scale(0.98);}
  .stButton > button:hover {border-color: #3a4054; color: var(--fg);}
  .stButton > button:focus {box-shadow: none; color: var(--fg);}
  .stButton > button[data-testid^="stBaseButton-primary"],
  .stFormSubmitButton > button[data-testid^="stBaseButton-primary"] {
      background: linear-gradient(135deg, var(--accent), var(--accent-2));
      border-color: transparent; color: #0b1020; font-weight: 700;
      box-shadow: 0 6px 20px rgba(139,157,255,0.22);}
  .stButton > button[data-testid^="stBaseButton-primary"]:hover,
  .stButton > button[data-testid^="stBaseButton-primary"]:focus,
  .stFormSubmitButton > button[data-testid^="stBaseButton-primary"]:hover {
      color: #0b1020; filter: brightness(1.06);}
  .stTextInput input {font-size: 1.4rem; height: 3.2rem; text-align: center;}
  div[data-testid="InputInstructions"] {display: none;}

  /* left/right grading pairs: wrap them in st.container(key="graders") */
  .st-key-graders div[data-testid="stColumn"]:nth-of-type(1) .stButton > button
    {background: rgba(240,86,110,0.12); border-color: rgba(240,86,110,0.4); color: #ff8a9b;}
  .st-key-graders div[data-testid="stColumn"]:nth-of-type(2) .stButton > button
    {background: rgba(62,207,142,0.12); border-color: rgba(62,207,142,0.4); color: #6fe0ab;}

  div[data-testid="stMetricValue"] {font-size: 1.6rem;}
</style>
"""


def setup():
    st.markdown(STYLE, unsafe_allow_html=True)
    st.logo(MARK, size="large")


def esc(s):
    return html.escape(s or "")


def icon(name, fill=False):
    """A Material Symbols icon as HTML, by its name (fonts.google.com/icons). In a
    Streamlit label — a button, a caption, a page link — write :material/name:
    instead; this is for the HTML the pages build themselves."""
    return f'<span class="mi{" fill" if fill else ""}" aria-hidden="true">{name}</span>'


def card(inner, tight=False):
    st.markdown(f'<div class="card{" tight" if tight else ""}">{inner}</div>',
                unsafe_allow_html=True)


def ruby(written, kana):
    """Whole-word furigana. Fine-grained per-kanji ruby needs a dictionary; whole-word
    is honest and enough to read it."""
    if not kana or written == kana:
        return esc(written)
    return f"<ruby>{esc(written)}<rt>{esc(kana)}</rt></ruby>"

# ------------------------------------------------------------ dashboard pieces
# bar() and ring() return HTML so a page can compose several into one panel.

def pct(frac):
    return f"{round(100 * min(max(frac, 0.0), 1.0))}%"


def bar(frac, cls=""):
    return f'<div class="bar {cls}"><i style="width:{pct(frac)}"></i></div>'


def ring(frac, value, label, size="6.6rem"):
    """A progress ring that sweeps round to `frac`: `value` in the middle, `label`
    under it."""
    return (f'<div class="ring" style="width:{size};height:{size};--p:{pct(frac)}">'
            f'<div><div class="v">{esc(str(value))}</div>'
            f'<div class="l">{esc(label)}</div></div></div>')


def brand(big=False):
    """The lockup: the mark (two beats, rising), the name, and the name in kana."""
    return (f'<div class="brand{" big" if big else ""}"><span class="mark"><i></i><i></i>'
            f'</span><span class="wm">dondon</span><span class="jp">どんどん</span></div>')


def tiles(items, two=False):
    """A grid of stat tiles from (value, label) or (value, label, small print)."""
    cells = "".join(
        f'<div class="tile"><div class="v">{esc(str(it[0]))}</div>'
        f'<div class="l">{esc(it[1])}</div>'
        + (f'<div class="s">{esc(it[2])}</div>' if len(it) > 2 and it[2] else "")
        + "</div>" for it in items)
    st.markdown(f'<div class="tiles{" two" if two else ""}">{cells}</div>',
                unsafe_allow_html=True)


def section(left, right=""):
    st.markdown(f'<div class="meta"><span>{esc(left)}</span>'
                f'<span class="right">{esc(right)}</span></div>', unsafe_allow_html=True)


def panel(inner):
    st.markdown(f'<div class="panel">{inner}</div>', unsafe_allow_html=True)


_icon = icon


def task(key, icon, name, sub, state, page, frac=None, done=False, nxt=False):
    """One step of the daily plan. The whole row opens `page`: an invisible page
    link is laid over it, which keeps the session (a plain <a> would reload it)."""
    cls = "done" if done else "next" if nxt else ""
    meter = bar(frac, "thin ok" if done else "thin") if frac is not None else ""
    with st.container(key=f"go_{key}"):
        st.markdown(
            f'<div class="task {cls}"><div class="ico">{_icon("check" if done else icon)}</div>'
            f'<div class="body"><div class="name">{esc(name)}</div>'
            f'<div class="sub">{esc(sub)}</div>{meter}</div>'
            f'<div class="state">{esc(state)}</div><div class="chev">›</div></div>',
            unsafe_allow_html=True)
        st.page_link(page, label=name)


def speak(text, lang="ja-JP", label="", rate=0.9, icon="volume_up"):
    """A button that reads `text` aloud with the device's own voice for `lang`."""
    payload = json.dumps(text)
    # An iframe can't see the page's fonts, so it fetches the two icons it may show.
    st.iframe(f"""
      <link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Material+Symbols+Rounded:opsz,wght,FILL,GRAD@24,400,0,0&icon_names=slow_motion_video,volume_up&display=block">
      <style>html,body{{margin:0;overflow:hidden;background:transparent}}
        button{{display:flex;align-items:center;justify-content:center;gap:6px}}
        .mi{{font-family:'Material Symbols Rounded';font-size:20px;line-height:1;
             font-feature-settings:'liga';-webkit-font-smoothing:antialiased}}</style>
      <button id="b" style="width:100%;height:40px;border-radius:12px;
        border:1px solid #252938;background:#13151c;color:#eceef5;font-size:15px;
        font-family:Inter,-apple-system,sans-serif;font-weight:500;cursor:pointer"
        ><span class="mi">{icon}</span>{html.escape(label)}</button>
      <script>
        document.getElementById('b').onclick = () => {{
          const u = new SpeechSynthesisUtterance({payload});
          u.lang = '{lang}'; u.rate = {rate};
          const v = speechSynthesis.getVoices().find(v => v.lang.startsWith('{lang[:2]}'));
          if (v) u.voice = v;
          speechSynthesis.cancel(); speechSynthesis.speak(u);
        }};
      </script>""", height=46)


def focus_input():
    """Put the cursor back in the answer box after each drill, so you can keep typing.
    (iOS only opens the keyboard on a real tap, so there it just saves aiming.)"""
    st.iframe("""<script>
      const inp = window.parent.document.querySelectorAll('input[type="text"]');
      if (inp.length) inp[inp.length - 1].focus();
    </script>""", height=1)
