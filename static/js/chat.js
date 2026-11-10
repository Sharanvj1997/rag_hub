const CHAT_API = "/api/chat";
const DOCS_LIST_API = "/api/documents/list/";

let currentSessionId = null;
let selectedDocIds = [];      // empty = search all documents
let readyDocuments = [];
let isStreaming = false;



const byId = (id) => document.getElementById(id);

// ---------- UI helpers ----------

function closeSidebar() {
  const el = byId("chat-side");
  if (el && el.classList.contains("show")) {
    bootstrap.Offcanvas.getOrCreateInstance(el).hide();
  }
}

function scrollToBottom() {
  const box = byId("messages");
  box.scrollTop = box.scrollHeight;
}

function setHeader(title) {
  byId("chat-title").textContent = title || "New chat";
}

function setBusy(busy) {
  byId("send-btn").disabled = busy;
  byId("send-btn").textContent = busy ? "..." : "Send";
  byId("message-input").disabled = busy;
  if (!busy) byId("message-input").focus();
}

function showEmptyState() {
  byId("messages").innerHTML = `
    <div class="empty-state h-100 d-flex flex-column justify-content-center align-items-center text-center text-muted">
      <h5>Ask anything about your documents</h5>
      <p class="mb-0">Use the Documents menu above to choose which files to search,<br>or leave it on "All documents".</p>
    </div>`;
}

function setSources(el, titles) {
  el.innerHTML = "";
  el.className = "src-list";
  (titles || []).forEach((t) => {
    const chip = document.createElement("span");
    chip.className = "src-chip";
    chip.textContent = t;
    el.appendChild(chip);
  });
}

function titlesFromChunks(chunks) {
  if (!chunks) return [];
  return [...new Set(chunks.map((c) => c.title).filter(Boolean))];
}

function appendMessage(role, text, sources = []) {
  const box = byId("messages");
  const empty = box.querySelector(".empty-state");
  if (empty) empty.remove();

  const row = document.createElement("div");
  row.className = `d-flex mb-3 ${role === "user" ? "justify-content-end" : "justify-content-start"}`;

  const col = document.createElement("div");
  col.style.maxWidth = "75%";

  const bubble = document.createElement("div");
  bubble.className = `p-3 rounded-3 ${role === "user" ? "bg-primary text-white" : "bg-white border"}`;
  bubble.style.whiteSpace = "pre-wrap";
  bubble.textContent = text; // textContent so model output can't inject HTML

  const sourceLine = document.createElement("div");
  sourceLine.className = "small text-muted mt-1";
  setSources(sourceLine, sources);

  col.append(bubble, sourceLine);
  row.appendChild(col);
  box.appendChild(row);
  scrollToBottom();

  return { bubble, sourceLine };
}

// ---------- Document picker ----------

function updateScopeLabel() {
  const label = byId("scope-label");
  if (selectedDocIds.length === 0) {
    label.textContent = "All documents";
  } else if (selectedDocIds.length === 1) {
    const doc = readyDocuments.find((d) => d.id === selectedDocIds[0]);
    label.textContent = doc ? doc.title : "1 document";
  } else {
    label.textContent = `${selectedDocIds.length} documents`;
  }
}

function renderDocPicker() {
  const menu = byId("doc-menu-items");
  menu.innerHTML = "";

  if (readyDocuments.length === 0) {
    menu.innerHTML = `<p class="text-muted small mb-0">No processed documents yet. Upload one on the Documents page.</p>`;
  }

  readyDocuments.forEach((doc) => {
    const label = document.createElement("label");
    label.className = "d-flex align-items-start gap-2 mb-2";

    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "form-check-input mt-1";
    checkbox.checked = selectedDocIds.includes(doc.id);
    checkbox.addEventListener("change", () => onDocToggle(doc.id, checkbox.checked));

    const name = document.createElement("span");
    name.className = "small";
    name.textContent = doc.title;

    label.append(checkbox, name);
    menu.appendChild(label);
  });

  updateScopeLabel();
}

async function saveScope() {
  if (!currentSessionId) return; // no chat yet: the selection is sent when the chat is created
  await apiRequest(`${CHAT_API}/sessions/${currentSessionId}/`, {
    method: "PATCH",
    body: JSON.stringify({ document_ids: selectedDocIds }),
  });
}

async function onDocToggle(docId, checked) {
  selectedDocIds = checked
    ? [...new Set([...selectedDocIds, docId])]
    : selectedDocIds.filter((id) => id !== docId);
  updateScopeLabel();
  await saveScope();
}

async function loadDocuments() {
  const res = await apiRequest(DOCS_LIST_API);
  if (!res.ok) return;
  const { data } = await res.json();
  readyDocuments = data.filter((d) => d.status === "ready");
  renderDocPicker();
}

// ---------- Sessions ----------

async function loadSessions() {
  const res = await apiRequest(`${CHAT_API}/sessions/`);
  if (!res.ok) return [];
  const { data } = await res.json();

  const list = byId("session-list");
  list.innerHTML = "";

  if (data.length === 0) {
    list.innerHTML = `<p class="text-muted small p-3 mb-0">No chats yet.</p>`;
    return data;
  }

  data.forEach((s) => {
    const isActive = s.id === currentSessionId;

    const item = document.createElement("div");
    item.className = `list-group-item list-group-item-action d-flex justify-content-between align-items-center ${isActive ? "active" : ""}`;
    item.style.cursor = "pointer";
    item.addEventListener("click", () => {
      closeSidebar();
      selectSession(s.id);
    });

    const title = document.createElement("span");
    title.className = "text-truncate";
    title.textContent = s.title;

    const del = document.createElement("button");
    del.className = `btn btn-sm ms-2 ${isActive ? "btn-outline-light" : "btn-outline-danger"}`;
    del.innerHTML = "&times;";
    del.title = "Delete chat";
    del.addEventListener("click", (e) => {
      e.stopPropagation();
      deleteSession(s.id);
    });

    item.append(title, del);
    list.appendChild(item);
  });

  return data;
}

async function createSession() {
  if (isStreaming) return null;

  const res = await apiRequest(`${CHAT_API}/sessions/create/`, {
    method: "POST",
    body: JSON.stringify({ document_ids: selectedDocIds }),
  });
  if (!res.ok) return null;

  const { data } = await res.json();
  currentSessionId = data.id;
  setHeader(data.title);
  showEmptyState();
  await loadSessions();
  return data.id;
}

async function selectSession(id) {
  if (isStreaming || id === currentSessionId) return;

  const res = await apiRequest(`${CHAT_API}/sessions/${id}/messages/`);
  if (!res.ok) return;
  const body = await res.json();

  currentSessionId = id;
  selectedDocIds = body.session.document_ids;
  renderDocPicker();
  setHeader(body.session.title);

  byId("messages").innerHTML = "";
  if (body.data.length === 0) showEmptyState();
  body.data.forEach((m) => appendMessage(m.role, m.content, titlesFromChunks(m.source_chunks)));

  await loadSessions();
}

async function deleteSession(id) {
  if (isStreaming) return;
  if (!confirm("Delete this chat? This can't be undone.")) return;

  const res = await apiRequest(`${CHAT_API}/sessions/${id}/`, { method: "DELETE" });
  if (!res.ok) return;

  if (id === currentSessionId) {
    currentSessionId = null;
    setHeader("New chat");
    showEmptyState();
  }
  await loadSessions();
}

// ---------- Sending + streaming ----------

async function sendMessage(text) {
  if (isStreaming) return;

  if (!currentSessionId) {
    const id = await createSession();
    if (!id) return;
  }

  isStreaming = true;
  setBusy(true);

  appendMessage("user", text);
  const { bubble, sourceLine } = appendMessage("assistant", "Thinking...");
  let firstToken = true;

  // EventSource can't send an Authorization header, so the token goes in the URL.
  // getCurrentUser() first forces a silent refresh if the access token expired.
  await getCurrentUser();
  const token = localStorage.getItem("access_token");

  const url =
    `${CHAT_API}/sessions/${currentSessionId}/stream/` +
    `?message=${encodeURIComponent(text)}&token=${encodeURIComponent(token)}`;

  const source = new EventSource(url);

  const finish = async () => {
    source.close(); // otherwise EventSource auto-reconnects and re-sends the message
    isStreaming = false;
    setBusy(false);
    const sessions = await loadSessions();
    const current = sessions.find((s) => s.id === currentSessionId);
    if (current) setHeader(current.title);
  };

  source.onmessage = (event) => {
    if (event.data === "[DONE]") {
      finish();
      return;
    }

    const payload = JSON.parse(event.data);

    if (payload.error) {
      bubble.textContent = `Error: ${payload.error}`;
      finish();
      return;
    }

    if (payload.sources) {
      setSources(sourceLine, payload.sources);
      return;
    }

    if (firstToken) {
      bubble.textContent = "";
      firstToken = false;
    }
    bubble.textContent += payload.token;
    scrollToBottom();
  };

  source.onerror = () => {
    if (firstToken) {
      bubble.textContent = "Connection error. Check that Ollama is running and try again.";
    }
    finish();
  };
}

// ---------- Init ----------

(async function initChatPage() {
  if (!requireAuth()) return;

  const cached = getCachedUser();
  if (cached) byId("nav-username").textContent = cached.username;

  showEmptyState();
  await Promise.all([loadSessions(), loadDocuments()]);

  byId("new-chat-btn").addEventListener("click", async () => {
    closeSidebar();
    selectedDocIds = [];
    renderDocPicker();
    await createSession();
  });

  byId("clear-docs").addEventListener("click", async (e) => {
    e.preventDefault();
    selectedDocIds = [];
    renderDocPicker();
    await saveScope();
  });

  byId("chat-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const input = byId("message-input");
    const text = input.value.trim();
    if (!text) return;
    input.value = "";
    await sendMessage(text);
  });
})();