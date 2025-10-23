document.addEventListener("DOMContentLoaded", () => {
  const modal = document.getElementById("guestBookingModal");
  if (!modal) return;

  const form = document.getElementById("guestBookingForm");
  const summary = document.getElementById("gbSummary");
  const errorBox = document.getElementById("gbError");
  const closeEls = modal.querySelectorAll("[data-gb-close]");

  const gbShow = () => modal.classList.remove("hidden");
  const gbHide = () => modal.classList.add("hidden");
  const gbGetCsrf = () => (document.cookie.match(/csrftoken=([^;]+)/) || [,""])[1];

  const gbShowError = (msg) => {
    if (!errorBox) return;
    errorBox.textContent = msg || "Something went wrong";
    errorBox.classList.remove("hidden");
  };

  const gbClearError = () => {
    if (!errorBox) return;
    errorBox.classList.add("hidden");
    errorBox.textContent = "";
  };

  function openGuestBooking(details) {
    gbClearError();
    if (!form) return;

    form.reset();
    form.date.value = details.date || "";
    form.start.value = details.start || "";
    form.guests.value = details.guests || "";
    form.table_id.value = details.table_id || "";
    form.duration.value = details.duration || "";

    if (summary) {
      summary.innerHTML = `
        <div class="flex flex-wrap gap-x-4 gap-y-1">
          <div><b>Date:</b> ${details.date}</div>
          <div><b>Time:</b> ${details.start}</div>
          <div><b>Guests:</b> ${details.guests}</div>
          <div><b>Table:</b> ${details.table_name || "#" + details.table_id}</div>
        </div>
      `;
    }

    gbShow();
  }

  closeEls.forEach((btn) =>
    btn.addEventListener("click", (e) => {
      e.preventDefault();
      gbHide();
    })
  );

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    gbClearError();

    const f = e.currentTarget;

    const payload = {
      date: f.date.value,
      start: f.start.value,
      guests: parseInt(f.guests.value, 10),
      table_id: parseInt(f.table_id.value, 10),
      duration_min: parseInt(f.duration.value, 10) || 90,
      name: f.name.value.trim(),
      email: f.email.value.trim(),
      phone: f.phone.value.trim(),
      comment: f.comment.value.trim(),
    };

    if (!payload.name) return gbShowError("Please enter your name");
    if (!payload.email && !payload.phone)
      return gbShowError("Please provide email or phone");

    try {
      const r = await fetch("/api/bookings/", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-CSRFToken": gbGetCsrf(),
        },
        credentials: "include",
        body: JSON.stringify(payload),
      });

      const data = await r.json().catch(() => ({}));

      if (!r.ok) {
        const msg =
          data.detail ||
          Object.entries(data)
            .map(([k, v]) => `${k}: ${Array.isArray(v) ? v[0] : v}`)
            .join(", ") ||
          "Booking failed";
        throw new Error(msg);
      }

      gbHide();

      if (typeof window.openSuccess === "function") {
        window.openSuccess(`
          <div><b>Table:</b> ${payload.table_id}</div>
          <div><b>Date:</b> ${payload.date}</div>
          <div><b>Time:</b> ${payload.start}</div>
          <div><b>Guests:</b> ${payload.guests}</div>
          <div><b>Name:</b> ${payload.name}</div>
          <div><b>Email:</b> ${payload.email}</div>
          <div><b>Phone:</b> ${payload.phone}</div>
          <div class="mt-2 text-xs opacity-70">Status: pending confirmation</div>
        `);
      } else {
        alert("Reservation request sent successfully!");
      }

      form.reset();
    } catch (err) {
      gbShowError(err.message || "Booking failed");
    }
  });

  window.openGuestBooking = openGuestBooking;
});
