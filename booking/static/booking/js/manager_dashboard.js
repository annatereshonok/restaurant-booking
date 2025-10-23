(function () {
  const cfg = window.MANAGER_CFG || {};
  const LOCALE = 'en-GB';

  const STATUS_LABELS_EN = {
    pending:   "Pending",
    confirmed: "Confirmed",
    seated:    "Seated",
    completed: "Completed",
    no_show:   "No-show",
    canceled:  "Canceled",
  };

  const monthLabel  = document.getElementById("monthLabel");
  const dayLabel    = document.getElementById("dayLabel");
  const dayTotals   = document.getElementById("dayTotals");
  const calGrid     = document.getElementById("calendarGrid");
  const dayList     = document.getElementById("dayList");
  const prevBtn     = document.getElementById("prevMonth");
  const nextBtn     = document.getElementById("nextMonth");
  const statusBtns  = document.querySelectorAll("button[data-status]");
  const areaFilter  = document.getElementById("areaFilter");
  const tableFilter = document.getElementById("tableFilter");
  const applyFilt   = document.getElementById("applyFilters");

  let current = new Date(); current.setDate(1);
  let daySelected = new Date();
  let activeStatus = "all";
  let monthData = [];
  let statusChoices = Object.entries(STATUS_LABELS_EN).map(([code, label]) => ({ code, label }));

  function getCSRFToken() {
    const meta = document.querySelector('meta[name="csrf-token"]');
    if (meta && meta.content) return meta.content;
    const m = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
    return m ? decodeURIComponent(m[1]) : "";
  }

  function isoLocalDate(d) {
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }
  function isSameLocalDay(a, b) {
    return a.getFullYear() === b.getFullYear()
        && a.getMonth() === b.getMonth()
        && a.getDate() === b.getDate();
  }
  function monthBounds(d) {
    const y = d.getFullYear(), m = d.getMonth();
    return { start: new Date(y, m, 1), end: new Date(y, m + 1, 0) };
  }
  function monthFmt(d) {
    return new Intl.DateTimeFormat(LOCALE, { month: 'long', year: 'numeric' }).format(d);
  }
  function dayFmt(d) {
    return new Intl.DateTimeFormat(LOCALE, { weekday: 'short', day: '2-digit', month: '2-digit' }).format(d);
  }
  function timeFmt(s) {
    return new Intl.DateTimeFormat(LOCALE, { hour: '2-digit', minute: '2-digit' }).format(new Date(s));
  }

  function statusColor(status) {
    return (cfg.STATUS_COLORS && cfg.STATUS_COLORS[status]) || "#EEE";
  }

  async function fetchMonthData() {
    const { start, end } = monthBounds(current);
    const params = new URLSearchParams({
      date_from: isoLocalDate(start),
      date_to: isoLocalDate(end),
    });
    if (activeStatus !== "all") params.append("status", activeStatus);
    if (areaFilter && areaFilter.value) params.append("area", areaFilter.value);
    if (tableFilter && tableFilter.value) params.append("table", tableFilter.value);

    const res = await fetch(`${cfg.API_LIST}?${params.toString()}`, {
      credentials: "same-origin",
      headers: { "Accept": "application/json" }
    });
    if (!res.ok) {
      console.error("Failed to load bookings:", res.status);
      monthData = [];
      return;
    }
    const data = await res.json();
    monthData = (data && data.results) ? data.results : [];
  }

  async function setStatus(id, statusCode) {
    const res = await fetch(cfg.API_SET_STATUS(id), {
      method: "POST",
      credentials: "same-origin",
      headers: {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "X-CSRFToken": getCSRFToken(),
      },
      body: JSON.stringify({ status: statusCode })
    });
    if (!res.ok) {
      const t = await res.text().catch(() => "");
      console.error("Status change failed:", res.status, t);
      alert(`Failed to set status (${res.status}).`);
      return false;
    }
    return true;
  }

  async function loadStatusChoices() {
    if (!cfg.API_STATUS_CHOICES) return;
    try {
      const r = await fetch(cfg.API_STATUS_CHOICES, { credentials: "same-origin" });
      if (r.ok) {
        const incoming = await r.json();
        statusChoices = incoming.map(x => ({
          code: x.code,
          label: STATUS_LABELS_EN[x.code] || x.label || x.code
        }));
      }
    } catch (_) {}
  }

  function setMonthLabel() { monthLabel.textContent = monthFmt(current); }
  function setDayLabel(d)   { dayLabel.textContent   = dayFmt(d); }

  function renderCalendar() {
    calGrid.innerHTML = "";
    const { start, end } = monthBounds(current);
    setMonthLabel();

    const pad = (start.getDay() + 6) % 7;
    for (let i = 0; i < pad; i++) {
      const empty = document.createElement("div");
      empty.className = "h-20";
      calGrid.appendChild(empty);
    }

    const daysInMonth = end.getDate();
    for (let d = 1; d <= daysInMonth; d++) {
      const cellDate = new Date(current.getFullYear(), current.getMonth(), d);
      const box = document.createElement("button");
      box.type = "button";
      box.className = "h-20 bg-white rounded-xl border hover:shadow flex flex-col px-2 py-1 text-left";

      const head = document.createElement("div");
      head.className = "flex items-center justify-between";

      const num = document.createElement("div");
      num.className = "text-sm font-semibold";
      num.textContent = d;

      const dots = document.createElement("div");
      dots.className = "flex gap-1";

      const items = monthData.filter(x => isSameLocalDay(new Date(x.datetime_start), cellDate));
      const seen = new Set(items.map(x => x.status));
      ["pending","confirmed","seated","completed","no_show","canceled"].forEach(s => {
        if (seen.has(s)) {
          const dot = document.createElement("span");
          dot.className = "inline-block w-2 h-2 rounded-full";
          dot.style.background = statusColor(s);
          dots.appendChild(dot);
        }
      });

      head.appendChild(num);
      head.appendChild(dots);

      const cnt = document.createElement("div");
      cnt.className = "text-[11px] opacity-70 mt-auto";
      if (items.length) cnt.textContent = `${items.length} bookings`;

      box.appendChild(head);
      box.appendChild(cnt);

      box.addEventListener("click", () => {
        daySelected = cellDate;
        setDayLabel(daySelected);
        renderDayList();
      });

      calGrid.appendChild(box);
    }
  }

  function renderDayList() {
    dayList.innerHTML = "";
    const itemsAll = monthData.filter(x => isSameLocalDay(new Date(x.datetime_start), daySelected));
    const items = (activeStatus === "all") ? itemsAll : itemsAll.filter(x => x.status === activeStatus);

    const counts = items.reduce((acc, i) => { acc[i.status] = (acc[i.status] || 0) + 1; return acc; }, {});
    dayTotals.textContent =
      `Total: ${items.length}. ` +
      `Pending: ${counts["pending"] || 0}, ` +
      `Confirmed: ${counts["confirmed"] || 0}, ` +
      `Seated: ${counts["seated"] || 0}, ` +
      `Completed: ${counts["completed"] || 0}, ` +
      `No-show: ${counts["no_show"] || 0}, ` +
      `Canceled: ${counts["canceled"] || 0}`;

    if (!items.length) {
      dayList.innerHTML = `<div class="py-6 text-center text-sm opacity-60">No bookings for this day</div>`;
      return;
    }

    items.forEach(it => {
      const row = document.createElement("div");
      row.className = "py-3 flex items-start gap-3";

      const badge = document.createElement("div");
      badge.className = "w-2 h-6 rounded";
      badge.style.background = statusColor(it.status);

      const body = document.createElement("div");
      body.className = "flex-1";

      const title = document.createElement("div");
      title.className = "font-semibold";
      title.textContent = `${timeFmt(it.datetime_start)} – ${timeFmt(it.datetime_end)} · Table ${it.table_name} · ${it.user_name || it.user_email || "guest"}`;

      const sub = document.createElement("div");
      sub.className = "text-sm opacity-75";
      sub.textContent = `Status: ${STATUS_LABELS_EN[it.status] || it.status}`;

      // Status select + Save
      const wrap = document.createElement("div");
      wrap.className = "mt-2 flex items-center gap-2";

      const sel = document.createElement("select");
      sel.className = "border rounded px-2 py-1 text-sm";
      statusChoices.forEach(sc => {
        const opt = document.createElement("option");
        opt.value = sc.code;
        opt.textContent = sc.label;
        if (sc.code === it.status) opt.selected = true;
        sel.appendChild(opt);
      });

      const saveBtn = document.createElement("button");
      saveBtn.className = "px-2 py-1 rounded bg-[#295E70] text-white text-sm";
      saveBtn.textContent = "Save";

      saveBtn.addEventListener("click", async () => {
        const id = it.id ?? it.pk;
        const ok = await setStatus(id, sel.value);
        if (ok) await reloadMonth(); // refresh calendar + list
      });

      wrap.appendChild(sel);
      wrap.appendChild(saveBtn);

      body.appendChild(title);
      body.appendChild(sub);
      body.appendChild(wrap);

      row.appendChild(badge);
      row.appendChild(body);
      dayList.appendChild(row);
    });
  }

  prevBtn.addEventListener("click", () => { current.setMonth(current.getMonth() - 1); reloadMonth(); });
  nextBtn.addEventListener("click", () => { current.setMonth(current.getMonth() + 1); reloadMonth(); });
  applyFilt.addEventListener("click", reloadMonth);

  statusBtns.forEach(b => {
    b.addEventListener("click", () => {
      statusBtns.forEach(x => x.classList.remove("ring-2", "ring-[#295E70]"));
      b.classList.add("ring-2", "ring-[#295E70]");
      activeStatus = b.dataset.status;
      reloadMonth();
    });
  });

  async function reloadMonth() {
    await fetchMonthData();
    renderCalendar();
    setDayLabel(daySelected);
    renderDayList();
  }

  (async function init() {
    await loadStatusChoices();
    setDayLabel(daySelected);
    await reloadMonth();
  })();
})();
