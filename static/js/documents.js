const DOCS_API = "/api/documents";

async function fetchDocuments() {
  const res = await apiRequest(`${DOCS_API}/list/`);   // <-- fixed: matches your urls.py
  if (!res.ok) return [];
  const data = await res.json();
  return data.data;
}

async function uploadDocument(file) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("title", file.name);

  const access = localStorage.getItem("access_token");

  const res = await fetch(`${DOCS_API}/upload/`, {
    method: "POST",
    headers: { Authorization: `Bearer ${access}` },
    body: formData,
  });

  return { ok: res.ok, data: await res.json() };
}

async function deleteDocument(id) {
  const res = await apiRequest(`${DOCS_API}/${id}/delete/`, { method: "DELETE" });
  return res.ok;
}

// Turns DRF's error shape into a readable sentence instead of raw JSON.
function formatErrors(data) {
  if (data.errors) {
    // e.g. { file: ["Unsupported file type '.docx'. Allowed types: .pdf, .txt, .md"] }
    const messages = [];
    for (const field in data.errors) {
      const fieldErrors = data.errors[field];
      messages.push(...(Array.isArray(fieldErrors) ? fieldErrors : [fieldErrors]));
    }
    return messages.join(" ");
  }
  return data.message || data.detail || "Something went wrong. Please try again.";
}

function showAlert(elementId, message, type = "danger") {
  const box = document.getElementById(elementId);
  box.className = `alert alert-${type}`;
  box.textContent = message;
  box.classList.remove("d-none");

  if (type === "success") {
    setTimeout(() => box.classList.add("d-none"), 3000);
  }
}

function hideAlert(elementId) {
  document.getElementById(elementId).classList.add("d-none");
}

function renderDocuments(documents) {
  const list = document.getElementById("documents-list");
  list.innerHTML = "";

  if (documents.length === 0) {
    list.innerHTML = `<p class="text-muted">No documents uploaded yet. Upload one above to get started.</p>`;
    return;
  }

  const statusColors = {
    pending: "secondary",
    processing: "info",
    ready: "success",
    failed: "danger",
  };

  documents.forEach((doc) => {
    const row = document.createElement("div");
    row.className = "card p-3 mb-2 d-flex flex-row justify-content-between align-items-center";
    row.innerHTML = `
      <div>
        <strong>${doc.title}</strong>
        <span class="badge bg-${statusColors[doc.status] || "secondary"} ms-2">${doc.status}</span>
        <div class="text-muted small">${(doc.size_bytes / 1024).toFixed(1)} KB · ${doc.file_type}</div>
        ${doc.status === "failed" && doc.error_message ? `<div class="text-danger small">${doc.error_message}</div>` : ""}
      </div>
      <button class="btn btn-outline-danger btn-sm" data-id="${doc.id}">Delete</button>
    `;
    row.querySelector("button").addEventListener("click", async (e) => {
      const id = e.target.dataset.id;
      if (confirm(`Delete "${doc.title}"? This can't be undone.`)) {
        const ok = await deleteDocument(id);
        if (ok) {
          showAlert("upload-status", "Document deleted.", "success");
          await loadDocuments();
        } else {
          showAlert("upload-status", "Failed to delete document. Please try again.", "danger");
        }
      }
    });
    list.appendChild(row);
  });
}

async function loadDocuments() {
  const listEl = document.getElementById("documents-list");
  listEl.innerHTML = `<p class="text-muted">Loading documents...</p>`;
  const docs = await fetchDocuments();
  renderDocuments(docs);
}

(async function initDocumentsPage() {
  if (!requireAuth()) return;

  await loadDocuments();

  const form = document.getElementById("upload-form");
  const uploadBtn = form.querySelector("button[type=submit]");

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const fileInput = document.getElementById("file-input");
    const file = fileInput.files[0];
    if (!file) return;

    hideAlert("upload-status");
    uploadBtn.disabled = true;
    uploadBtn.textContent = "Uploading...";

    const { ok, data } = await uploadDocument(file);

    uploadBtn.disabled = false;
    uploadBtn.textContent = "Upload";

    if (ok) {
      fileInput.value = "";
      showAlert("upload-status", `"${data.data.title}" uploaded successfully.`, "success");
      await loadDocuments();
    } else {
      showAlert("upload-status", formatErrors(data), "danger");
    }
  });
})();