// static/js/auth.js
// Shared authentication utilities: register, login, logout, token refresh,
// route guarding, and an authenticated fetch wrapper.
// Include this file BEFORE any page-specific script (e.g. dashboard.js).

const API_BASE = "/api/accounts";


// ---------------------------------------------------------------------
// Register
// ---------------------------------------------------------------------
async function registerUser(formData) {
  const res = await fetch(`${API_BASE}/register/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(formData),
  });
  return { ok: res.ok, data: await res.json() };
}


// ---------------------------------------------------------------------
// Login
// ---------------------------------------------------------------------
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


// ---------------------------------------------------------------------
// Logout
// ---------------------------------------------------------------------
async function logoutUser() {
  console.log("Logging out user...");
  const refresh = localStorage.getItem("refresh_token");
  const access = localStorage.getItem("access_token");

  try {
    await fetch(`${API_BASE}/logout/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${access}`,
      },
      body: JSON.stringify({ refresh }),
    });
  } catch (err) {
    // Even if the blacklist request fails (e.g. network issue),
    // still clear local tokens so the user is logged out client-side.
    console.error("Logout request failed:", err);
  }

  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
  localStorage.removeItem("user");
  window.location.href = "/login/";
}


// ---------------------------------------------------------------------
// Refresh access token using the stored refresh token
// ---------------------------------------------------------------------
async function refreshAccessToken() {
  const refresh = localStorage.getItem("refresh_token");
  if (!refresh) {
    window.location.href = "/login/";
    return null;
  }

  try {
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

    // present because SIMPLE_JWT ROTATE_REFRESH_TOKENS=True
    if (data.refresh) {
      localStorage.setItem("refresh_token", data.refresh);
    }

    return data.access;
  } catch (err) {
    console.error("Token refresh failed:", err);
    localStorage.clear();
    window.location.href = "/login/";
    return null;
  }
}


// ---------------------------------------------------------------------
// Route guard: call at the top of every protected page's init script
// ---------------------------------------------------------------------
function requireAuth() {
  const access = localStorage.getItem("access_token");
  if (!access) {
    window.location.href = "/login/";
    return false;
  }
  return true;
}


// ---------------------------------------------------------------------
// Authenticated fetch wrapper.
// Attaches the access token, and if the server responds 401,
// attempts a single silent refresh + retry before giving up.
// ---------------------------------------------------------------------
async function apiRequest(url, options = {}) {
  const access = localStorage.getItem("access_token");

  const doFetch = (token) =>
    fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(options.headers || {}),
        Authorization: `Bearer ${token}`,
      },
    });

  let res = await doFetch(access);

  if (res.status === 401) {
    const newAccess = await refreshAccessToken();
    if (!newAccess) return res; // refreshAccessToken already redirected to /login/
    res = await doFetch(newAccess);
  }

  return res;
}


// ---------------------------------------------------------------------
// Convenience helper: fetch the current logged-in user
// ---------------------------------------------------------------------
async function getCurrentUser() {
  const res = await apiRequest(`${API_BASE}/me/`);
  if (!res.ok) return null;
  return await res.json();
}


// ---------------------------------------------------------------------
// Convenience helper: read cached user from localStorage (no API call)
// Useful for instant UI paint before getCurrentUser() resolves.
// ---------------------------------------------------------------------
function getCachedUser() {
  const raw = localStorage.getItem("user");
  return raw ? JSON.parse(raw) : null;
}