#!/usr/bin/env python3
"""
output/stories/*.json を読み込み、index.html を生成する。
"""

import json
from pathlib import Path

_ROOT = Path(__file__).parent.parent
STORIES_DIR = _ROOT / "output" / "stories"
OUTPUT_HTML = _ROOT / "output" /"index.html"

TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>遠野物語</title>
<style>
  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  :root {
    --bg: #faf8f4;
    --bg-sidebar: #f0ece4;
    --border: #d8d0c0;
    --accent: #6b4c2a;
    --text: #2c2418;
    --text-muted: #9a8a78;
    --original-bg: #fff;
    --colloquial-bg: #f5f0e8;
    --sidebar-w: 220px;
    --item-active: #e8dfd0;
  }

  body {
    font-family: "Hiragino Mincho ProN", "Yu Mincho", "游明朝", Georgia, serif;
    background: var(--bg);
    color: var(--text);
    display: flex;
    height: 100vh;
    overflow: hidden;
  }

  /* ── サイドバー ── */
  #sidebar {
    width: var(--sidebar-w);
    min-width: var(--sidebar-w);
    background: var(--bg-sidebar);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  #sidebar-header {
    padding: 16px 14px 12px;
    border-bottom: 1px solid var(--border);
    font-size: 0.8rem;
    color: var(--text-muted);
    letter-spacing: 0.1em;
    flex-shrink: 0;
  }

  #sidebar-header strong {
    display: block;
    font-size: 1rem;
    color: var(--accent);
    margin-bottom: 4px;
    letter-spacing: 0.05em;
  }

  #story-list {
    overflow-y: auto;
    flex: 1;
    padding: 6px 0;
  }

  .page-group-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 14px;
    cursor: pointer;
    font-size: 0.8rem;
    font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
    letter-spacing: 0.06em;
    color: var(--text-muted);
    border-left: 3px solid transparent;
    transition: background 0.1s;
  }

  .page-group-header:hover { background: var(--item-active); }

  .page-group-header.active {
    color: var(--accent);
    border-left-color: var(--accent);
  }

  .page-group-header .chevron {
    font-size: 0.6rem;
    transition: transform 0.15s;
  }

  .page-group-header.active .chevron { transform: rotate(90deg); }

  .page-stories { display: none; }
  .page-stories.open { display: block; }

  .story-item {
    display: flex;
    align-items: baseline;
    gap: 8px;
    padding: 7px 14px 7px 22px;
    cursor: pointer;
    border-left: 3px solid transparent;
    transition: background 0.1s;
    line-height: 1.4;
  }

  .story-item:hover { background: var(--item-active); }

  .story-item.active {
    background: var(--item-active);
    border-left-color: var(--accent);
  }

  .story-item.no-colloquial { opacity: 0.45; }

  .story-num {
    font-size: 0.7rem;
    color: var(--text-muted);
    min-width: 26px;
    font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
  }

  .story-label {
    font-size: 0.9rem;
  }

  /* ── メイン ── */
  #main {
    flex: 1;
    overflow-y: auto;
    padding: 40px 48px;
    max-width: 780px;
  }

  .story-section {
    margin-bottom: 56px;
    padding-bottom: 56px;
    border-bottom: 1px solid var(--border);
    scroll-margin-top: 24px;
  }

  .story-section:last-child {
    border-bottom: none;
    margin-bottom: 0;
  }

  .story-section-header {
    margin-bottom: 32px;
    border-bottom: 1px solid var(--border);
    padding-bottom: 16px;
  }

  .story-number-label {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
    letter-spacing: 0.12em;
    margin-bottom: 4px;
  }

  .story-title-label {
    font-size: 1.6rem;
    color: var(--accent);
    letter-spacing: 0.05em;
  }

  .section {
    margin-bottom: 32px;
  }

  .section-label {
    font-size: 0.7rem;
    font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
    letter-spacing: 0.14em;
    color: var(--text-muted);
    margin-bottom: 10px;
    text-transform: uppercase;
  }

  .section-body {
    line-height: 2.1;
    font-size: 1rem;
    white-space: pre-wrap;
    padding: 20px 24px;
    border-radius: 4px;
    border: 1px solid var(--border);
  }

  .section.original .section-body { background: var(--original-bg); }
  .section.colloquial .section-body { background: var(--colloquial-bg); }

  .no-colloquial-msg {
    color: var(--text-muted);
    font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
    font-size: 0.9rem;
    padding: 16px 0;
  }

  #placeholder {
    color: var(--text-muted);
    font-family: "Hiragino Sans", "Yu Gothic", sans-serif;
    margin-top: 80px;
    font-size: 1rem;
    letter-spacing: 0.05em;
  }

  /* ── モバイル ── */
  #menu-toggle {
    display: none;
    position: fixed;
    top: 10px;
    left: 10px;
    z-index: 200;
    width: 36px;
    height: 36px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 4px;
    font-size: 1.15rem;
    cursor: pointer;
    align-items: center;
    justify-content: center;
    line-height: 1;
  }

  #sidebar-backdrop {
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.38);
    z-index: 90;
  }

  @media (max-width: 600px) {
    body { overflow: auto; }

    #menu-toggle { display: flex; }

    #sidebar {
      position: fixed;
      top: 0;
      left: 0;
      height: 100%;
      z-index: 100;
      width: min(var(--sidebar-w), 82vw);
      transform: translateX(-100%);
      transition: transform 0.22s ease;
      box-shadow: 2px 0 12px rgba(0,0,0,0.18);
    }

    #sidebar.open { transform: translateX(0); }

    #sidebar-backdrop.open { display: block; }

    #main {
      padding: 56px 16px 32px;
      max-width: 100%;
    }

    .story-title-label { font-size: 1.2rem; }

    .section-body { padding: 14px 16px; }
  }
</style>
</head>
<body>

<button id="menu-toggle" aria-label="メニュー">&#9776;</button>
<div id="sidebar-backdrop"></div>

<nav id="sidebar">
  <div id="sidebar-header">
    <strong>遠野物語</strong>
    柳田國男
  </div>
  <div id="story-list"></div>
</nav>

<main id="main">
  <div id="placeholder">← ページを選んでください</div>
  <div id="story-view" hidden></div>
</main>

<script>
const STORIES = __STORIES_JSON__;
const PAGE_SIZE = 20;

const list      = document.getElementById('story-list');
const placeholder = document.getElementById('placeholder');
const storyView = document.getElementById('story-view');
const mainEl    = document.getElementById('main');

// モバイル用サイドバー開閉
const menuToggle = document.getElementById('menu-toggle');
const sidebar    = document.getElementById('sidebar');
const backdrop   = document.getElementById('sidebar-backdrop');

function openSidebar()  { sidebar.classList.add('open');    backdrop.classList.add('open'); }
function closeSidebar() { sidebar.classList.remove('open'); backdrop.classList.remove('open'); }

menuToggle.addEventListener('click', () =>
  sidebar.classList.contains('open') ? closeSidebar() : openSidebar()
);
backdrop.addEventListener('click', closeSidebar);

// ── ページグループ構築 ──────────────────────────────────────────

const pages = [];
for (let i = 0; i < STORIES.length; i += PAGE_SIZE) {
  pages.push(STORIES.slice(i, i + PAGE_SIZE));
}

let currentPageIdx = -1;
let activeItem = null;
const pageGroupEls = []; // { headerEl, storiesEl }[]

pages.forEach((pageStories, pageIdx) => {
  const first = pageStories[0].number;
  const last  = pageStories[pageStories.length - 1].number;

  const groupEl = document.createElement('div');

  const headerEl = document.createElement('div');
  headerEl.className = 'page-group-header';
  headerEl.innerHTML =
    `<span>第${first}〜${last}話</span><span class="chevron">▶</span>`;
  headerEl.addEventListener('click', () => {
    if (currentPageIdx === pageIdx) {
      mainEl.scrollTop = 0;
    } else {
      showPage(pageIdx);
    }
  });

  const storiesEl = document.createElement('div');
  storiesEl.className = 'page-stories';

  pageStories.forEach(story => {
    const item = document.createElement('div');
    item.className = 'story-item' + (story.colloquial ? '' : ' no-colloquial');
    item.innerHTML =
      `<span class="story-num">${story.number}</span>` +
      `<span class="story-label">${story.label ?? '（無題）'}</span>`;
    item.addEventListener('click', e => {
      e.stopPropagation();
      if (activeItem) activeItem.classList.remove('active');
      activeItem = item;
      item.classList.add('active');

      if (currentPageIdx !== pageIdx) {
        showPage(pageIdx);
        requestAnimationFrame(() => jumpToStory(story.number));
      } else {
        jumpToStory(story.number);
      }
      if (window.innerWidth <= 600) closeSidebar();
    });
    storiesEl.appendChild(item);
  });

  groupEl.appendChild(headerEl);
  groupEl.appendChild(storiesEl);
  list.appendChild(groupEl);
  pageGroupEls.push({ headerEl, storiesEl });
});

// ── ページ表示 ────────────────────────────────────────────────

function showPage(pageIdx) {
  pageGroupEls.forEach(({ headerEl, storiesEl }, i) => {
    headerEl.classList.toggle('active', i === pageIdx);
    storiesEl.classList.toggle('open',  i === pageIdx);
  });

  storyView.innerHTML = '';
  pages[pageIdx].forEach(story => {
    storyView.appendChild(buildStorySection(story));
  });

  placeholder.hidden = true;
  storyView.hidden   = false;
  currentPageIdx     = pageIdx;
  mainEl.scrollTop   = 0;
}

function jumpToStory(num) {
  const el = document.getElementById(`story-${num}`);
  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function buildStorySection(story) {
  const section = document.createElement('div');
  section.className = 'story-section';
  section.id = `story-${story.number}`;

  const hdr = document.createElement('div');
  hdr.className = 'story-section-header';

  const numEl = document.createElement('div');
  numEl.className = 'story-number-label';
  numEl.textContent = `第 ${story.number} 話`;

  const titleEl = document.createElement('div');
  titleEl.className = 'story-title-label';
  titleEl.textContent = story.label ?? '';

  hdr.appendChild(numEl);
  hdr.appendChild(titleEl);
  section.appendChild(hdr);

  const origSec = document.createElement('div');
  origSec.className = 'section original';
  const origLbl = document.createElement('div');
  origLbl.className = 'section-label';
  origLbl.textContent = '原文';
  const origBody = document.createElement('div');
  origBody.className = 'section-body';
  origBody.textContent = story.original.text;
  origSec.appendChild(origLbl);
  origSec.appendChild(origBody);
  section.appendChild(origSec);

  const collSec = document.createElement('div');
  collSec.className = 'section colloquial';
  const collLbl = document.createElement('div');
  collLbl.className = 'section-label';
  collLbl.textContent = '口語訳';
  collSec.appendChild(collLbl);
  if (story.colloquial) {
    const collBody = document.createElement('div');
    collBody.className = 'section-body';
    collBody.textContent = story.colloquial.text;
    collSec.appendChild(collBody);
  } else {
    const msg = document.createElement('div');
    msg.className = 'no-colloquial-msg';
    msg.textContent = '未翻訳';
    collSec.appendChild(msg);
  }
  section.appendChild(collSec);

  return section;
}
</script>
</body>
</html>
"""


def main() -> None:
    """output/stories/*.json を読み込んで遠野物語の閲覧用 index.html を生成する。"""
    files = sorted(STORIES_DIR.glob("*.json"))
    if not files:
        print(f"JSONファイルが見つかりません: {STORIES_DIR}")
        return

    stories = [json.loads(f.read_text(encoding="utf-8")) for f in files]
    stories_json = json.dumps(stories, ensure_ascii=False)

    html = TEMPLATE.replace("__STORIES_JSON__", stories_json)
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"生成完了 ({len(stories)} 話): {OUTPUT_HTML.resolve()}")


if __name__ == "__main__":
    main()
