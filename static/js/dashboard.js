(async function initDashboard() {
  if (!requireAuth()) return;

  const user = await getCurrentUser();
  if (!user) return;

  document.getElementById("nav-username").textContent = user.username;
  document.getElementById("welcome-name").textContent = user.first_name || user.username;
  document.getElementById("account-email").textContent = user.email;

  document.getElementById("doc-count").textContent = "0";
  document.getElementById("chat-count").textContent = "0";

  document.getElementById("loading").classList.add("d-none");
  document.getElementById("dashboard-content").classList.remove("d-none");
})();