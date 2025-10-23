(() => {
  const openBtn = document.querySelector('[data-open-nav]');
  const panel = document.querySelector('[data-nav-panel]');
  const closes = panel ? panel.querySelectorAll('[data-close-nav]') : [];

  if (!openBtn || !panel) return;
  const open = () => panel.classList.remove('hidden');
  const close = () => panel.classList.add('hidden');

  openBtn.addEventListener('click', open);
  closes.forEach(b => b.addEventListener('click', close));
})();
