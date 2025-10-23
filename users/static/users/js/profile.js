// ===== Helpers =====
function getCookie(name) {
  let value = `; ${document.cookie}`;
  let parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(";").shift();
}
const csrftoken = getCookie("csrftoken");
const $ = (s) => document.querySelector(s);

const CANCEL_TPL = document.body?.dataset?.cancelTemplate || "/api/me/bookings/0/cancel";

function buildCancelUrl(id) {
  const path = CANCEL_TPL.replace(/\/0\/cancel\/?$/, `/${id}/cancel`);
  return new URL(path, window.location.origin).toString();
}

// ===== Badges / Cards =====
function statusBadge(s) {
  const map = {
    pending:   "bg-[#F2BB3A]/30 text-[#1b1f23]",   // жёлтый полупрозрачный, тёмный текст
    confirmed: "bg-[#025C6C]/10 text-[#025C6C]",   // headings 10% + headings текст
    seated:    "bg-[#025C6C]/10 text-[#025C6C]",   // как confirmed
    canceled:  "bg-[#F02D2F]/15 text-[#F02D2F]",   // красный мягкий фон + красный текст
    completed: "bg-[#000000]/10 text-[#000000]",   // тёмный 10% + тёмный текст
    no_show:   "bg-[#000000]/10 text-[#000000]",
  };
  return `<span class="chip ${map[s] || "bg-dark/10"}">${String(s || "").toUpperCase()}</span>`;
}

function bookingCard(b) {
  const d = new Date(b.datetime_start);
  const start = d.toLocaleString(undefined, {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  });
  const end = new Date(b.datetime_end).toLocaleTimeString(undefined, {
    hour: "2-digit", minute: "2-digit"
  });

  const canCancel = ["pending", "confirmed"].includes((b.status || "").trim().toLowerCase());
  const tableArea = b.table_area || "";
  const tableName = b.table_name || (b.table ? `#${b.table}` : "");
  const cancelUrl = buildCancelUrl(b.id); // как мы добавили ранее

  return `
    <div class="bg-white rounded-2xl shadow px-4 py-4">
      <!-- горизонтальный контейнер: контент слева, действия справа -->
      <div class="flex items-center gap-4">
        <!-- слева: «аватар» гостей + основной контент -->
        <div class="flex items-center gap-4 flex-1 min-w-0">
          <div class="w-12 h-12 rounded-xl bg-peach flex items-center justify-center font-black text-headings shrink-0">
            ${b.guests}
          </div>
          <div class="min-w-0">
            <div class="font-bold text-dark truncate">${start} — ${end}</div>
            <div class="text-sm text-dark/70 truncate">
              Table: ${tableName}${tableArea ? ` (${tableArea})` : ""} · Guests: ${b.guests}
            </div>
            <div class="mt-1">${statusBadge(b.status)}</div>
          </div>
        </div>

        <!-- справа: действия; фиксированная ширина, ровное выравнивание -->
        <div class="flex items-center gap-2 shrink-0">
          <a class="px-3 py-2 rounded-xl border hover:bg-peach/60" href="/api/me/bookings/${b.id}/ical">.ics</a>

          <button
            class="px-3 py-2 rounded-xl text-white hover:opacity-90 disabled:opacity-40"
            style="${canCancel ? 'background:#F02D2F;border:none;' : 'background:#9aa0a6;border:none;'}"
            data-cancel="${b.id}"
            data-cancel-url="${cancelUrl}"
            ${canCancel ? "" : "disabled"}
            >
            Cancel
          </button>
        </div>
      </div>
    </div>`;
}

// ===== Tabs =====
const STATUS_META = [
  { key: "pending",   label: "Waiting for confirmation" },
  { key: "confirmed", label: "Confirmed" },
  { key: "seated",    label: "Seated" },
  { key: "completed", label: "Completed" },
  { key: "canceled",  label: "Canceled" },
  { key: "no_show",   label: "No show" },
];

function renderTabsNav(counts) {
  const nav = $("#resTabsNav");
  nav.innerHTML = STATUS_META.map(({ key, label }) => {
    const c = counts?.[key] ?? 0;
    return `
      <button type="button"
              role="tab"
              data-tab="${key}"
              class="px-3 py-1.5 rounded-full border border-[#295E70]/20 text-[#295E70] hover:bg-white/70
                     data-[active=true]:bg-[#F2BB3A] data-[active=true]:text-[#1b1f23] data-[active=true]:border-transparent">
        <span>${label}</span>
        <span class="ml-2 text-xs bg-[#F2BB3A] text-[#1b1f23] rounded-full px-2 py-0.5 align-middle">${c}</span>
      </button>`;
  }).join("");
}

function renderTabsPanes(byStatus) {
  const panes = $("#resTabsPanes");
  panes.innerHTML = STATUS_META.map(({ key, label }) => {
    const list = byStatus?.[key] || [];
    const content = list.length
      ? list.map(bookingCard).join("")
      : `<div class="bg-white rounded-2xl shadow p-6 text-dark/70">No reservations</div>`;
    return `
      <div role="tabpanel" data-pane="${key}" class="hidden">
        <h4 class="text-[#295E70] font-bold mb-2">${label}</h4>
        <div class="grid gap-3">${content}</div>
      </div>`;
  }).join("");
}

function activateTab(key) {
  // buttons
  document.querySelectorAll('#resTabsNav [data-tab]').forEach(btn => {
    btn.dataset.active = (btn.dataset.tab === key).toString();
  });
  // panes
  document.querySelectorAll('#resTabsPanes [data-pane]').forEach(pane => {
    pane.classList.toggle('hidden', pane.dataset.pane !== key);
  });
}

function initTabsHandlers(defaultKey) {
  const nav = $("#resTabsNav");
  nav.addEventListener("click", (e) => {
    const btn = e.target.closest("[data-tab]");
    if (!btn) return;
    activateTab(btn.dataset.tab);
  });
  activateTab(defaultKey);
}

// ===== Profile loader (prefill inputs) =====
async function loadProfile() {
  const r = await fetch("/api/auth/me/", { credentials: "same-origin" });
  const data = await r.json();

  if (!data.is_authenticated) {
    window.location.href = "/login/";
    return;
  }

  if (data.avatar_url) {
    const av = document.getElementById("uiAvatar");
    if (av) av.src = data.avatar_url;
  }

  const setVal = (sel, val) => { const i = document.querySelector(sel); if (i) i.value = val ?? ""; };
  setVal('input[name="first_name"]', data.first_name);
  setVal('input[name="last_name"]', data.last_name);
  setVal('input[name="phone"]', data.phone);

  if (Object.prototype.hasOwnProperty.call(data, "favorite_dish")) {
    document.getElementById("favDishWrap")?.classList.remove("hidden");
    setVal('input[name="favorite_dish"]', data.favorite_dish);
  }
}

// ===== Bookings loader (grouped with tabs, fallback supported) =====
async function loadBookings() {
  // пробуем grouped endpoint
  let resp = await fetch("/api/me/bookings-by-status/", { credentials: "same-origin" });

  // fallback: старый список
  if (resp.status === 404) {
    const rf = await fetch("/api/me/bookings/", { credentials: "same-origin" });
    const arr = await rf.json().catch(() => []);

    renderTabsNav({ active: arr.length });
    $("#resTabsNav").innerHTML = `
      <button type="button" role="tab" data-tab="active"
              class="px-3 py-1.5 rounded-full border border-[#295E70]/20 text-[#295E70] hover:bg-white/70
                     data-[active=true]:bg-[#F2BB3A] data-[active=true]:text-[#1b1f23] data-[active=true]:border-transparent">
        <span>Active</span>
        <span class="ml-2 text-xs bg-[#F2BB3A] text-[#1b1f23] rounded-full px-2 py-0.5">${arr.length}</span>
      </button>`;
    $("#resTabsPanes").innerHTML = `
      <div role="tabpanel" data-pane="active">
        <div class="grid gap-3">
          ${arr.length ? arr.map(bookingCard).join("") :
            `<div class="bg-white rounded-2xl shadow p-6 text-dark/70">No active reservations yet.</div>`}
        </div>
      </div>`;
    initTabsHandlers("active");
    return;
  }

  if (!resp.ok) {
    $("#resTabsPanes").innerHTML =
      `<div class="bg-white rounded-2xl shadow p-6 text-[#FF0000]">Failed to load reservations</div>`;
    return;
  }

  const data = await resp.json().catch(() => ({}));
  const counts = data.counts || {};
  const by = data.by_status || {};

  renderTabsNav(counts);
  renderTabsPanes(by);

  // активируем первую вкладку с данными, если пусто — pending
  const firstWithData = STATUS_META.find(({ key }) => (by[key] || []).length > 0)?.key || "pending";
  initTabsHandlers(firstWithData);
}

// ===== Cancel action (delegated) =====
document.addEventListener("click", async (e) => {
  const btn = e.target.closest('[data-cancel]');
  if (!btn) return;
  const id = btn.dataset.cancel;
  const url = btn.dataset.cancelUrl || `/api/me/bookings/${id}/`;
  if (!confirm("Cancel this reservation?")) return;

  const r = await fetch(url, {
    method: "DELETE",
    headers: { "X-CSRFToken": csrftoken },
    credentials: "same-origin",
  });

  if (r.ok) {
    await loadBookings();
  } else {
    const data = await r.json().catch(() => ({}));
    alert(data.detail || "Failed to cancel.");
  }
});

// ===== Save profile =====
document.getElementById("profileForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  const r = await fetch("/api/auth/me/update", {
    method: "POST",
    headers: { "X-CSRFToken": csrftoken },
    body: fd,
    credentials: "same-origin",
  });
  const msg = document.getElementById("profileMsg");
  if (r.ok) {
    msg.textContent = "Profile saved ✨";
    msg.className = "text-sm text-headings";
    loadProfile();
  } else {
    const data = await r.json().catch(() => ({}));
    msg.textContent = data.detail || "Save failed";
    msg.className = "text-sm text-red";
  }
});

// ===== Init =====
loadProfile();
loadBookings();
