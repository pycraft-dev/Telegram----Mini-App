/**
 * HTTP-запросы к backend (тот же origin, что и Mini App).
 * @param {string} path
 * @param {RequestInit} [options]
 * @returns {Promise<any>}
 */
export async function apiFetch(path, options = {}) {
  const base = window.location.origin;
  const url = `${base}${path}`;
  const res = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  const text = await res.text();
  let data = null;
  try {
    data = text ? JSON.parse(text) : null;
  } catch {
    data = { detail: text || "Некорректный ответ сервера" };
  }
  if (!res.ok) {
    const err = new Error(`HTTP_${res.status}`);
    err.status = res.status;
    err.data = data;
    throw err;
  }
  return data;
}

/**
 * Повторяет запрос при сетевых ошибках.
 * @param {() => Promise<any>} fn
 * @param {number} retries
 */
export async function withRetry(fn, retries = 2) {
  let lastErr = null;
  for (let i = 0; i <= retries; i += 1) {
    try {
      return await fn();
    } catch (e) {
      lastErr = e;
      if (e && typeof e === "object" && "status" in e) {
        throw e;
      }
      await new Promise((r) => setTimeout(r, 400 * (i + 1)));
    }
  }
  throw lastErr;
}
