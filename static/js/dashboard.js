(async function initDashboard() {
  if (!requireAuth()) return;

  const user = await getCurrentUser();
  if (!user) return;

  document.getElementById("nav-username").textContent = user.username;
  document.getElementById("welcome-name").textContent = user.first_name || user.username;
  document.getElementById("account-email").textContent = user.email;

  const res = await apiRequest("/api/dashboard/stats/");
  if (res.ok) {
    const { data } = await res.json();
    document.getElementById("doc-count").textContent = data.documents;
    document.getElementById("chat-count").textContent = data.chat_sessions;
  }

  document.getElementById("loading").classList.add("d-none");
  document.getElementById("dashboard-content").classList.remove("d-none");
})();