document.addEventListener("DOMContentLoaded", () => {
  if (!document.querySelector("[data-reserve]")) return;

  const BOOKING_URL = "/booking/";
  const API_ME = "/api/auth/me/";
  const AUTHED_FLAG = document.body?.dataset?.authenticated === "1";

  async function checkMeOnce() {
    try {
      const r = await fetch(API_ME, { credentials: "include" });
      if (!r.ok) return null;
      const d = await r.json().catch(()=>null);
      return (d && (d.id || d.email)) ? d : null;
    } catch { return null; }
  }

  function goBooking() { window.location.href = BOOKING_URL; }
  function openLogin() {
    if (typeof window.openAuthModal === "function") {
      window.openAuthModal("login");
    } else {
      goBooking();
    }
  }

  document.addEventListener("click", async (e) => {
    const btn = e.target.closest("[data-reserve]");
    if (!btn) return;
    e.preventDefault();

    if (AUTHED_FLAG) { goBooking(); return; }

    const me = await checkMeOnce();
    if (me) { goBooking(); return; }

    openLogin();
  });
});
