(function () {
  // One tooltip for every chart mark that carries data-tip; the same text shows on hover and on keyboard focus.
  const tip = document.getElementById("tip");
  if (!tip) return;
  let current = null;
  const place = (x, y) => {
    const r = tip.getBoundingClientRect();
    let left = x + 14, top = y + 14;
    if (left + r.width > window.innerWidth - 8) left = Math.max(8, x - r.width - 14);
    if (top + r.height > window.innerHeight - 8) top = Math.max(8, y - r.height - 14);
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  };
  const show = (el, x, y) => {
    current = el;
    tip.textContent = el.getAttribute("data-tip");
    tip.hidden = false;
    place(x, y);
  };
  const hide = () => { current = null; tip.hidden = true; };
  document.addEventListener("pointerover", (e) => {
    const el = e.target.closest && e.target.closest("[data-tip]");
    if (el) show(el, e.clientX, e.clientY);
  });
  document.addEventListener("pointermove", (e) => { if (current) place(e.clientX, e.clientY); });
  document.addEventListener("pointerout", (e) => {
    const el = e.target.closest && e.target.closest("[data-tip]");
    if (el && el === current && !el.contains(e.relatedTarget)) hide();
  });
  document.addEventListener("focusin", (e) => {
    const el = e.target.closest && e.target.closest("[data-tip]");
    if (!el) return;
    const r = el.getBoundingClientRect();
    show(el, r.right, r.top);
  });
  document.addEventListener("focusout", hide);
  window.addEventListener("scroll", hide, { passive: true });
})();
