const API_BASE = "/api/accounts";

async function registerUser(formData) {
  const res = await fetch(`${API_BASE}/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });
  return { ok: res.ok, data: await res.json() };
}

async function loginUser(email, password) {
  const res = await fetch(`${API_BASE}/login/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const data = await res.json();

  if (res.ok) {
    localStorage.setItem("access_token", data.access);
    localStorage.setItem("refresh_token", data.refresh);
    localStorage.setItem("user", JSON.stringify(data.user));
  }

  return { ok: res.ok, data };
}

async function logoutUser() {
  const refresh = localStorage.getItem("refresh_token");
  const access = localStorage.getItem("access_token");

  await fetch(`${API_BASE}/logout/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${access}`,
    },
    body: JSON.stringify({ refresh }),
  });

  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  window.location.href = "/login/";
}

// Call this before any authenticated API request if the access token might be stale.
async function refreshAccessToken() {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) return null;

  const res = await fetch(`${API_BASE}/login/refresh/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    localStorage.clear();
    window.location.href = "/login/";
    return null;
  }

  const data = await res.json();
  localStorage.setItem("access_token", data.access);
  if (data.refresh) localStorage.setItem("refresh_token", data.refresh); // present because ROTATE_REFRESH_TOKENS=True
  return data.access;
}