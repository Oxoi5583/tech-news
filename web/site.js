/* Progressive enhancement: reading and navigation also work without JavaScript. */
(() => {
  'use strict';
  document.documentElement.classList.add('js');
  const themeButton = document.querySelector('.theme-toggle');
  const colorPreference = window.matchMedia('(prefers-color-scheme: dark)');
  const isDark = () => document.documentElement.dataset.theme
    ? document.documentElement.dataset.theme === 'dark' : colorPreference.matches;
  const updateThemeButton = () => {
    themeButton.setAttribute('aria-pressed', String(isDark()));
    themeButton.setAttribute('aria-label', isDark() ? '切換淺色模式' : '切換深色模式');
    themeButton.title = themeButton.getAttribute('aria-label');
  };
  if (themeButton) {
    updateThemeButton();
    themeButton.addEventListener('click', () => {
      const theme = isDark() ? 'light' : 'dark';
      document.documentElement.dataset.theme = theme;
      try { localStorage.setItem('tech-news-theme', theme); } catch (_) { /* file / private mode */ }
      updateThemeButton();
    });
    colorPreference.addEventListener('change', updateThemeButton);
  }
  for (const [selector, width] of [['.site-navigation', 800], ['.article-toc', 1100]]) {
    const element = document.querySelector(selector);
    if (!element) continue;
    const media = window.matchMedia(`(max-width: ${width}px)`);
    const sync = () => { element.open = !media.matches; };
    sync();
    media.addEventListener('change', sync);
  }
  const form = document.querySelector('.archive-search');
  if (!form) return;
  const input = form.querySelector('input[type="search"]');
  const type = form.querySelector('select');
  const cards = [...document.querySelectorAll('.entry-grid > .entry-card')];
  const status = document.querySelector('.result-count');
  const empty = document.querySelector('.search-empty');
  const clear = form.querySelector('.clear-search');
  const normalize = (text) => text.normalize('NFKC').toLocaleLowerCase().trim();
  const searchable = cards.map(card => normalize(card.dataset.search));
  const params = new URLSearchParams(location.search);
  input.value = params.get('q') || '';
  if ([...type.options].some(option => option.value === params.get('type'))) type.value = params.get('type');
  function filter(updateUrl = true) {
    const words = normalize(input.value).split(/\s+/).filter(Boolean);
    let visible = 0;
    cards.forEach((card, i) => {
      const matches = (!type.value || card.dataset.type === type.value) && words.every(word => searchable[i].includes(word));
      card.hidden = !matches;
      if (matches) visible++;
    });
    status.textContent = words.length || type.value ? `找到 ${visible} 篇 · 共 ${cards.length} 篇` : `共 ${cards.length} 篇`;
    empty.hidden = visible !== 0 || cards.length === 0;
    clear.disabled = !input.value && !type.value;
    if (updateUrl) {
      const url = new URL(location.href);
      input.value.trim() ? url.searchParams.set('q', input.value.trim()) : url.searchParams.delete('q');
      type.value ? url.searchParams.set('type', type.value) : url.searchParams.delete('type');
      try { history.replaceState(null, '', url); } catch (_) { /* file: URL */ }
    }
  }
  const reset = () => { input.value = ''; type.value = ''; filter(); input.focus(); };
  form.addEventListener('submit', event => { event.preventDefault(); filter(); });
  input.addEventListener('input', () => filter());
  type.addEventListener('change', () => filter());
  clear.addEventListener('click', reset);
  empty.querySelector('button').addEventListener('click', reset);
  filter(false);
})();
