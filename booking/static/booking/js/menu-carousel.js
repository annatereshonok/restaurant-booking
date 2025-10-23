(() => {
  const track = document.querySelector('[data-menu-track]');
  const list  = document.querySelector('[data-menu-list]');
  const prev  = document.querySelector('[data-menu-prev]');
  const next  = document.querySelector('[data-menu-next]');
  if (!track || !list) return;

  track.addEventListener('wheel', (e) => {
    if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
      track.scrollLeft += e.deltaY;
      e.preventDefault();
    }
  }, { passive:false });

  let isDown = false, startX = 0, startLeft = 0;
  const getX = (e) => e.pageX ?? (e.touches && e.touches[0]?.pageX);
  track.addEventListener('mousedown', (e) => { isDown = true; startX = getX(e); startLeft = track.scrollLeft; });
  track.addEventListener('touchstart', (e) => { isDown = true; startX = getX(e); startLeft = track.scrollLeft; }, {passive:true});
  window.addEventListener('mousemove', (e) => { if (!isDown) return; track.scrollLeft = startLeft - (getX(e) - startX); });
  window.addEventListener('touchmove', (e) => { if (!isDown) return; track.scrollLeft = startLeft - (getX(e) - startX); }, {passive:true});
  window.addEventListener('mouseup', () => { isDown = false; });
  window.addEventListener('touchend', () => { isDown = false; });

  const step = () => Math.min(360, track.clientWidth * 0.8);
  prev?.addEventListener('click', () => track.scrollBy({left: -step(), behavior: 'smooth'}));
  next?.addEventListener('click', () => track.scrollBy({left:  step(), behavior: 'smooth'}));
})();
