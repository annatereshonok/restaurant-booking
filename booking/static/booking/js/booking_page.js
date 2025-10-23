(function () {
  function getCsrf() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }
  function normalizeNA(p) {
    if (!p || typeof p !== "string") return p;
    return p.replace(/_na(\.(svg|png|jpg|jpeg|webp))$/i, "_NA$1");
  }
  function iconTypeByCapacity(cap) {
    if (Number(cap) === 2) return "2_horiz";
    return String(cap || "4");
  }

  const layer = document.getElementById("tablesLayer");
  const reserveBtn = document.getElementById("reserveBtn");
  const mapWrap = document.getElementById("mapWrap");
  if (!layer || !mapWrap) return;

  const API_TABLES = mapWrap.dataset.apiTables;
  const API_ME = mapWrap.dataset.apiMe; // можно не задавать — тогда /me не дергаем
  const API_BOOK = mapWrap.dataset.apiBook;
  const API_AVAIL = mapWrap.dataset.apiAvailability || "/api/availability/";
  const AUTHED = mapWrap.dataset.authenticated === "1"; // ← серверный флаг

  const form = document.getElementById("searchForm");
  const fGuests = form?.elements["guests"];
  const fDate = form?.elements["date"];
  const fStart = form?.elements["start"];
  const fDuration = form?.elements["duration"];

  const successModal = document.getElementById("bookingSuccess");
  const successSummary = document.getElementById("successSummary");
  function openSuccess(html) {
    if (successModal) {
      if (successSummary) successSummary.innerHTML = html || "";
      successModal.classList.remove("hidden");
      successModal
        .querySelectorAll("[data-success-close]")
        .forEach((b) => {
          b.addEventListener("click", () =>
            successModal.classList.add("hidden")
          );
        });
    } else {
      alert("Reservation request sent!");
    }
  }

  const ICONS = {
    "1": "/static/booking/img/tables/table_type_1.svg",
    "2_horiz": "/static/booking/img/tables/table_type_2_horiz.svg",
    "2_vert": "/static/booking/img/tables/table_type_2_vert.svg",
    "4": "/static/booking/img/tables/table_type_4.svg",
    "6": "/static/booking/img/tables/table_type_6.svg",
  };
  const ICONS_NA = {
    "1": "/static/booking/img/tables/table_type_1_NA.svg",
    "2_horiz": "/static/booking/img/tables/table_type_2_horiz_NA.svg",
    "2_vert": "/static/booking/img/tables/table_type_2_vert_NA.svg",
    "4": "/static/booking/img/tables/table_type_4_NA.svg",
    "6": "/static/booking/img/tables/table_type_6_NA.svg",
  };

  const SIZES = { "1": 60, "2_horiz": 60, "2_vert": 60, "4": 60, "6": 60 };
  const HITBOX = { scaleX: 0.92, scaleY: 0.92 };
  const OFFSET = { xPct: -0.32, yPct: 0.0 };

  let selectedId = null;
  let tablesCache = [];
  const nodesById = new Map();

  function clearLayer() {
    layer.innerHTML = "";
    nodesById.clear();
  }
  function getLocalTables() {
    return Array.isArray(window.HIKARI_TABLES) ? window.HIKARI_TABLES : [];
  }
  function setHighlight(el, on) {
    el.style.boxShadow = on ? "0 0 0 4px rgba(41,94,112,1)" : "none";
    el.style.borderRadius = "6px";
  }

  function formValid() {
    const guestsOk = fGuests && Number(fGuests.value || 0) > 0;
    const dateOk = fDate && fDate.value;
    const timeOk = fStart && fStart.value;
    return Boolean(guestsOk && dateOk && timeOk && selectedId);
  }
  function updateReserveState() {
    if (reserveBtn) reserveBtn.disabled = !formValid();
  }
  ["input", "change"].forEach((ev) => {
    fGuests?.addEventListener(ev, updateReserveState);
    fDate?.addEventListener(ev, updateReserveState);
    fStart?.addEventListener(ev, updateReserveState);
    fDuration?.addEventListener(ev, updateReserveState);
  });

  // ---- Map rendering ----
  function buttonEl(table) {
    const holder = document.createElement("div");
    holder.className = "absolute -translate-x-1/2 -translate-y-1/2";
    holder.style.left = table.x + "%";
    holder.style.top = table.y + "%";

    const img = document.createElement("img");
    const srcActive = table.photo_url || ICONS[table.type] || ICONS["4"];
    const srcInactive =
      normalizeNA(table.photo_inactive_url) ||
      ICONS_NA[table.type] ||
      ICONS["4"];
    img.src = table.is_active ? srcActive : srcInactive;
    img.alt = table.name || "";
    img.className = "block select-none pointer-events-none";
    img.draggable = false;
    img.style.width = (SIZES[table.type] || 6) + "%";

    const hit = document.createElement("button");
    hit.type = "button";
    hit.title = `${table.name ?? ""} • ${table.capacity ?? ""}`;
    hit.style.position = "absolute";
    hit.style.left = "50%";
    hit.style.top = "50%";
    hit.style.transform = "translate(-50%, -50%)";
    hit.style.pointerEvents = "auto";
    hit.style.background = "transparent";
    hit.style.border = "0";
    hit.style.outline = "none";
    hit.dataset.hit = "1";
    hit.dataset.enabled = "1";

    function fitHitbox() {
      const wImg = img.clientWidth;
      const hImg = img.clientHeight;
      hit.style.width = wImg * HITBOX.scaleX + "px";
      hit.style.height = hImg * HITBOX.scaleY + "px";
      const dx = wImg * OFFSET.xPct;
      const dy = hImg * OFFSET.yPct;
      hit.style.transform = `translate(-50%, -50%) translate(${dx}px, ${dy}px)`;
    }
    img.addEventListener("load", fitHitbox);
    window.addEventListener("resize", fitHitbox);
    requestAnimationFrame(fitHitbox);

    hit.addEventListener("click", () => {
      if (hit.dataset.enabled !== "1") return;
      if (selectedId === table.id) {
        selectedId = null;
        layer
          .querySelectorAll("button[data-hit]")
          .forEach((b) => setHighlight(b, false));
      } else {
        layer
          .querySelectorAll("button[data-hit]")
          .forEach((b) => setHighlight(b, false));
        selectedId = table.id;
        setHighlight(hit, true);
      }
      updateReserveState();
    });

    holder.appendChild(img);
    holder.appendChild(hit);

    nodesById.set(table.id, { holder, img, hit, meta: table });
    return holder;
  }

  async function fetchTables() {
    if (!API_TABLES) return getLocalTables();
    try {
      const r = await fetch(API_TABLES, { credentials: "include" });
      if (!r.ok) throw new Error("api not ok");
      const data = await r.json();
      if (!Array.isArray(data) || !data.length) throw new Error("empty");
      return data.map((t) => {
        const cap = Number(t.capacity || 4);
        const nx = Number(t.x);
        const ny = Number(t.y);
        const type = t.type || iconTypeByCapacity(cap);
        return {
          id: t.id,
          name: t.name || `T-${t.id}`,
          type,
          capacity: cap,
          x: nx <= 1 ? nx * 100 : nx,
          y: ny <= 1 ? ny * 100 : ny,
          is_active: !!t.is_active,
          area_name: t.area_name || null,
          photo_url: t.photo_url || null,
          photo_inactive_url: normalizeNA(t.photo_inactive_url) || null,
        };
      });
    } catch {
      return getLocalTables();
    }
  }

  (async function init() {
    tablesCache = await fetchTables();
    clearLayer();
    tablesCache.forEach((t) => layer.appendChild(buttonEl(t)));
    if (reserveBtn) reserveBtn.disabled = true;
  })();

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();

    const guests = Number(fGuests?.value || 0);
    const date = fDate?.value || "";
    const start = fStart?.value || "";
    const duration = Number(fDuration?.value || 90);

    if (guests > 6) {
      alert(
        "Online we accept up to 6 guests. For larger groups, please call the restaurant."
      );
      return;
    }

    if (!guests || !date || !start) {
      updateReserveState();
      return;
    }

    try {
      const url = new URL(API_AVAIL, window.location.origin);
      url.searchParams.set("date", date);
      url.searchParams.set("start", start);
      url.searchParams.set("guests", String(guests));
      url.searchParams.set("duration", String(duration));

      const r = await fetch(url.toString(), { credentials: "include" });
      if (!r.ok) throw new Error("Availability failed");
      const data = await r.json();

      const availMap = new Map();
      if (Array.isArray(data.tables)) {
        data.tables.forEach((t) =>
          availMap.set(t.id, { available: !!t.available })
        );
      }

      nodesById.forEach(({ img, hit, meta }) => {
        const byCapacity = meta.capacity >= guests;
        const avail = availMap.has(meta.id)
          ? availMap.get(meta.id).available
          : true;
        const canUse = byCapacity && avail;

        const srcNormal = meta.photo_url || ICONS[meta.type] || ICONS["4"];
        const srcNA =
          normalizeNA(meta.photo_inactive_url) ||
          ICONS_NA[meta.type] ||
          srcNormal;

        img.src = canUse ? srcNormal : srcNA;

        hit.dataset.enabled = canUse ? "1" : "0";

        if (!canUse && selectedId === meta.id) {
          selectedId = null;
          setHighlight(hit, false);
        }
      });

      updateReserveState();
    } catch (err) {
      console.warn(err);
    }
  });

  async function getMe() {
    if (!API_ME) return null;
    try {
      const r = await fetch(API_ME, { credentials: "include" });
      if (!r.ok) return null;
      return await r.json();
    } catch {
      return null;
    }
  }

  async function postBooking(payload) {
    const body = {
      ...payload,
      table_id: payload.table ?? payload.table_id,
      duration_min: payload.duration ?? payload.duration_min,
    };

    const r = await fetch(API_BOOK, {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCsrf(),
      },
      body: JSON.stringify(body),
    });
    const data = await r.json().catch(() => ({}));
    if (!r.ok) {
      let msg = data.detail || "Booking failed";
      if (data && typeof data === "object") {
        for (const k in data) {
          if (Array.isArray(data[k]) && data[k][0]) {
            msg = `${k}: ${data[k][0]}`;
            break;
          }
          if (typeof data[k] === "string") {
            msg = `${k}: ${data[k]}`;
            break;
          }
        }
      }
      throw new Error(msg);
    }
    return data;
  }

  function successHTML(res, extraGuest) {
    const t = nodesById.get(selectedId)?.meta;
    const areaHtml = res?.table?.area?.name
      ? `<div><b>Area:</b> ${res.table.area.name}</div>`
      : "";
    return `
      <div><b>Table:</b> ${t?.name || res?.table?.name || "#" + (selectedId || "")}</div>
      ${areaHtml}
      <div><b>Date:</b> ${fDate.value} <b>at</b> ${fStart.value}</div>
      <div><b>Guests:</b> ${fGuests.value}</div>
      ${(res?.name || extraGuest?.name) ? `<div><b>Name:</b> ${res.name || extraGuest.name}</div>` : ""}
      ${(res?.email || extraGuest?.email) ? `<div><b>Email:</b> ${res.email || extraGuest.email}</div>` : ""}
      <div class="mt-2 text-xs opacity-70">Status: pending confirmation</div>
    `;
  }

  reserveBtn?.addEventListener("click", async () => {
  if (!selectedId || !formValid()) return;

  if (AUTHED) {
    try {
      const res = await postBooking({
        date: fDate.value,
        start: fStart.value,
        duration: Number(fDuration.value || 90),
        guests: Number(fGuests.value || 1),
        table: selectedId,
      });
      openSuccess(successHTML(res));
      nodesById.forEach(({ hit }) => setHighlight(hit, false));
      selectedId = null;
      updateReserveState();
    } catch (e) {
      alert(e.message || "Booking failed");
    }
    return;
  }

  const t = nodesById.get(selectedId)?.meta;
  const selected = {
    date: fDate.value,
    start: fStart.value,
    guests: Number(fGuests.value || 1),
    table_id: selectedId,
    duration: Number(fDuration.value || 90),
    table_name: t?.name || ("#" + selectedId),
  };

  if (typeof window.openGuestBooking === "function") {
    window.openGuestBooking(selected);
  } else {
    const gbModal = document.getElementById("guestBookingModal");
    const form = document.getElementById("guestBookingForm");
    if (gbModal && form) {
      form.reset();
      form.date.value = selected.date;
      form.start.value = selected.start;
      form.guests.value = selected.guests;
      form.table_id.value = selected.table_id;
      form.duration.value = selected.duration;
      const s = document.getElementById("gbSummary");
      if (s) {
        s.innerHTML = `
          <div class="flex flex-wrap gap-x-4 gap-y-1">
            <div><b>Date:</b> ${selected.date}</div>
            <div><b>Time:</b> ${selected.start}</div>
            <div><b>Guests:</b> ${selected.guests}</div>
            <div><b>Table:</b> ${selected.table_name}</div>
          </div>
        `;
      }
      gbModal.classList.remove("hidden");
    } else {
      alert("Contacts form is missing on the page.");
    }
  }
});
})();
