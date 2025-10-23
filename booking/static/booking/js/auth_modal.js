document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById('authModal');
  if (!modal) return;

  const API_REGISTER = modal.dataset.apiRegister || "/api/auth/register/";
  const API_LOGIN    = modal.dataset.apiLogin    || "/api/auth/login/";
  // опциональный URL для skip (можно задать в data-атрибуте), по умолчанию — /booking/
  const SKIP_URL     = modal.dataset.skipUrl     || "/booking/";

  const afterSuccess = () => {
    if (typeof window.afterAuthContinue === "function") {
      try { window.afterAuthContinue(); return; } catch {}
    }
    const redirect = modal.dataset.redirectOnSuccess || "";
    if (redirect) { window.location.href = redirect; return; }
    window.location.reload();
  };

  // DOM
  const errorBox  = document.getElementById('authError');
  const regForm   = document.getElementById('authRegister');
  const loginForm = document.getElementById('authLogin');
  const toggleBtn = modal.querySelector('[data-toggle-auth]');
  const closeEls  = modal.querySelectorAll('[data-auth-close]');
  const skipBtn   = modal.querySelector('[data-skip-auth]');
  const titleEl   = modal.querySelector('[data-auth-title]');

  // helpers
  const show = () => modal.classList.remove('hidden');
  const hide = () => modal.classList.add('hidden');
  const getCSRF = () => (document.cookie.match(/csrftoken=([^;]+)/) || [,''])[1];
  const showError = (m) => { if (!errorBox) return; errorBox.textContent = m || "Something went wrong"; errorBox.classList.remove('hidden'); };
  const clearError = () => { if (!errorBox) return; errorBox.classList.add('hidden'); errorBox.textContent = ""; };
  const parseErrors = (data, fallback="Request failed") => {
    if (!data) return fallback;
    if (typeof data === "string") return data;
    if (data.detail) return data.detail;
    try {
      const parts = [];
      for (const k in data) {
        const v = data[k];
        if (Array.isArray(v) && v.length) parts.push(`${k}: ${v[0]}`);
        else if (typeof v === "string") parts.push(`${k}: ${v}`);
      }
      return parts.join(" ") || fallback;
    } catch { return fallback; }
  };

  function openModal(mode="login") {
    clearError();
    if (mode === "login") {
      regForm.classList.add("hidden");
      loginForm.classList.remove("hidden");
      titleEl.textContent = "Login";
      toggleBtn.textContent = "Need an account? Register";
    } else {
      loginForm.classList.add("hidden");
      regForm.classList.remove("hidden");
      titleEl.textContent = "Register";
      toggleBtn.textContent = "Already have an account? Login";
    }
    show();
  }

  document.addEventListener('click', (e) => {
    const btn = e.target.closest('[data-auth-open]');
    if (!btn) return;
    e.preventDefault();
    openModal(btn.dataset.authOpen === 'register' ? 'register' : 'login');
  });

  closeEls.forEach(c => c.addEventListener('click', (e) => { e.preventDefault(); hide(); }));

  skipBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    hide();
    if (typeof window.onAuthSkip === "function") {
      window.onAuthSkip();
    } else {
      window.location.href = SKIP_URL;
    }
  });

  toggleBtn?.addEventListener('click', (e) => {
    e.preventDefault(); clearError();
    const loginVisible = !loginForm.classList.contains('hidden');
    if (loginVisible) {
      loginForm.classList.add('hidden'); regForm.classList.remove('hidden');
      titleEl.textContent = "Register";  toggleBtn.textContent = "Already have an account? Login";
    } else {
      regForm.classList.add('hidden'); loginForm.classList.remove('hidden');
      titleEl.textContent = "Login";     toggleBtn.textContent = "Need an account? Register";
    }
  });

  regForm?.addEventListener('submit', async (e) => {
    e.preventDefault(); clearError();
    const fd = new FormData(regForm);
    const name = (fd.get('name') || "").toString().trim();
    const email = (fd.get('email') || "").toString().trim();
    const password = (fd.get('password') || "").toString();

    try {
      const r = await fetch(API_REGISTER, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type":"application/json", "X-CSRFToken": getCSRF() },
        body: JSON.stringify({ name, email, password })
      });
      const d = await r.json().catch(()=> ({}));
      if (!r.ok) throw new Error(parseErrors(d, "Registration failed"));

      try {
        const rl = await fetch(API_LOGIN, {
          method: "POST",
          credentials: "include",
          headers: { "Content-Type":"application/json", "X-CSRFToken": getCSRF() },
          body: JSON.stringify({ email, password })
        });
        if (rl.ok) { hide(); afterSuccess(); return; }
      } catch {}

      hide(); afterSuccess();
    } catch (err) {
      showError(err.message || "Registration failed");
    }
  });

  loginForm?.addEventListener('submit', async (e) => {
    e.preventDefault(); clearError();
    const fd = new FormData(loginForm);
    const email = (fd.get('email') || "").toString().trim();
    const password = (fd.get('password') || "").toString();
    try {
      const r = await fetch(API_LOGIN, {
        method: "POST",
        credentials: "include",
        headers: { "Content-Type":"application/json", "X-CSRFToken": getCSRF() },
        body: JSON.stringify({ email, password })
      });
      const data = await r.json().catch(()=> ({}));
      if (!r.ok) throw new Error(parseErrors(data, "Login failed"));
      hide(); afterSuccess();
    } catch (err) {
      showError(err.message || "Login failed");
    }
  });

  window.openAuthModal = openModal;
});
