import { apiFetch, withRetry } from "./api.js";

const tg = window.Telegram?.WebApp;

function qs(name) {
  const u = new URL(window.location.href);
  return u.searchParams.get(name);
}

function showError(text) {
  const el = document.getElementById("error");
  el.textContent = text;
  el.classList.remove("hidden");
}

function hideError() {
  const el = document.getElementById("error");
  el.textContent = "";
  el.classList.add("hidden");
}

function setLoading(isLoading) {
  const btn = document.getElementById("submit");
  btn.disabled = isLoading;
  btn.textContent = isLoading ? "Отправка…" : "Подтвердить бронь";
}

function fmtMoney(n) {
  return `${n} ₽`;
}

function fmtDt(iso) {
  const d = new Date(iso);
  return d.toLocaleString("ru-RU", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

async function loadMasterClass(id) {
  return withRetry(() => apiFetch(`/api/masterclasses/${id}`));
}

async function createBooking(payload) {
  return withRetry(() =>
    apiFetch("/api/bookings", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  );
}

async function main() {
  document.getElementById("subtitle").textContent = "Мастер-класс";

  if (tg) {
    tg.ready();
    tg.expand();
  }

  const idRaw = qs("master_class_id");
  const id = idRaw ? Number(idRaw) : NaN;
  if (!Number.isFinite(id) || id <= 0) {
    showError("Не передан master_class_id в ссылке WebApp.");
    return;
  }

  let mc;
  try {
    mc = await loadMasterClass(id);
  } catch (e) {
    const msg =
      e?.data?.detail?.toString?.() ||
      (typeof e?.data?.detail === "object" ? JSON.stringify(e.data.detail) : null) ||
      "Не удалось загрузить мастер-класс";
    showError(msg);
    return;
  }

  document.getElementById("card").classList.remove("hidden");
  document.getElementById("mcName").textContent = mc.name;
  document.getElementById("mcMeta").textContent = `${fmtDt(mc.date_time)} • ${fmtMoney(
    mc.price,
  )} • до ${mc.max_participants} чел.`;
  document.getElementById("mcDesc").textContent = mc.description || "";

  const img = document.createElement("img");
  const src =
    mc.photo_url && mc.photo_url.startsWith("http")
      ? mc.photo_url
      : `${window.location.origin}${mc.photo_url}`;
  img.alt = mc.name;
  img.src = src;
  const wrap = document.getElementById("mcPhoto");
  wrap.innerHTML = "";
  wrap.appendChild(img);

  const slot = document.getElementById("slot");
  slot.innerHTML = "";
  const opt = document.createElement("option");
  opt.value = mc.date_time;
  opt.textContent = fmtDt(mc.date_time);
  slot.appendChild(opt);
  slot.disabled = true;

  const u = tg?.initDataUnsafe?.user;
  document.getElementById("name").value = u?.first_name
    ? `${u.first_name}${u.last_name ? ` ${u.last_name}` : ""}`.trim()
    : "";
  document.getElementById("phone").value = u?.phone_number || "";

  document.getElementById("submit").addEventListener("click", async () => {
    hideError();
    document.getElementById("status").classList.add("hidden");

    const initData = tg?.initData || "";
    if (!initData) {
      showError("Нет initData. Откройте форму из Telegram (кнопка WebApp).");
      return;
    }

    const name = document.getElementById("name").value.trim();
    const phone = document.getElementById("phone").value.trim();
    if (!name || !phone) {
      showError("Заполните имя и телефон.");
      return;
    }

    setLoading(true);
    try {
      await createBooking({
        init_data: initData,
        master_class_id: id,
        name,
        phone,
      });
      document.getElementById("status").textContent = "Готово! Проверьте сообщение в чате бота.";
      document.getElementById("status").classList.remove("hidden");
      tg?.HapticFeedback?.notificationOccurred?.("success");
    } catch (e) {
      const detail = e?.data?.detail;
      const msg =
        typeof detail === "string"
          ? detail
          : Array.isArray(detail)
            ? detail.map((x) => x.msg || JSON.stringify(x)).join("; ")
            : detail
              ? JSON.stringify(detail)
              : "Не удалось создать бронь";
      showError(msg);
      tg?.HapticFeedback?.notificationOccurred?.("error");
    } finally {
      setLoading(false);
    }
  });
}

main();
