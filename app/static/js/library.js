const listEl = document.getElementById("list");
const lastSyncedEl = document.getElementById("last-synced");
const errorEl = document.getElementById("library-error");
const refreshBtn = document.getElementById("refresh-btn");
const issuesBtn = document.getElementById("issues-btn");
const issuesPanel = document.getElementById("issues-panel");
const issuesList = document.getElementById("issues-list");
const issuesCloseBtn = document.getElementById("issues-close-btn");

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function hideError() {
  errorEl.hidden = true;
}

function formatRuntime(minutes) {
  if (!minutes) return "";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

const IN_PROGRESS_DOWNLOAD_STATUSES = ["queued", "downloading"];
const IN_PROGRESS_CONVERT_STATUSES = ["queued", "converting"];

function downloadButtonLabel(status) {
  if (status === "downloaded") return "Downloaded ✓";
  if (status === "queued") return "Queued…";
  if (status === "downloading") return "Downloading…";
  if (status === "failed") return "Retry Download";
  return "Download";
}

function convertButtonLabel(status) {
  if (status === "converted") return "Converted ✓";
  if (status === "queued") return "Queued…";
  if (status === "converting") return "Converting…";
  if (status === "failed") return "Retry Convert";
  return "Convert";
}

function formatFileSize(bytes) {
  if (!bytes) return "";
  const mb = bytes / (1024 * 1024);
  return mb >= 1024 ? `${(mb / 1024).toFixed(2)} GB` : `${mb.toFixed(1)} MB`;
}

function statusBadge(label, status) {
  return `<span class="badge badge-${status}">${label}: ${status.replace("_", " ")}</span>`;
}

function renderBooks(books) {
  listEl.innerHTML = "";
  if (books.length === 0) {
    listEl.innerHTML = '<p class="empty">No books yet — click "Refresh Library" to fetch your purchases.</p>';
    return;
  }
  for (const book of books) {
    const row = document.createElement("div");
    row.className = "book-row";

    const coverSrc = book.cover_local_path ? `/covers/${book.cover_local_path}` : book.cover_url;
    const authorLine = book.authors.join(", ");
    const narratorLine = book.narrators.length ? `Narrated by ${book.narrators.join(", ")}` : "";
    const metaParts = [authorLine, narratorLine, formatRuntime(book.runtime_length_min), formatFileSize(book.file_size_bytes)]
      .filter(Boolean)
      .join(" · ");
    const downloadBusy = IN_PROGRESS_DOWNLOAD_STATUSES.includes(book.download_status) || book.download_status === "downloaded";
    const convertBusy =
      book.download_status !== "downloaded" ||
      IN_PROGRESS_CONVERT_STATUSES.includes(book.convert_status) ||
      book.convert_status === "converted";
    const errorMessage = book.convert_error || book.download_error;

    row.innerHTML = `
      <img class="book-row-cover" src="${coverSrc || ""}" alt="${book.title} cover" loading="lazy">
      <div class="book-row-info">
        <h3><a href="/book.html?asin=${book.asin}">${book.title}</a></h3>
        ${metaParts ? `<p class="book-row-meta">${metaParts}</p>` : ""}
        ${errorMessage ? `<p class="error download-error">${errorMessage}</p>` : ""}
      </div>
      <div class="book-row-statuses">
        ${statusBadge("Download", book.download_status)}
        ${statusBadge("Convert", book.convert_status)}
      </div>
      <button class="download-btn" data-asin="${book.asin}" ${downloadBusy ? "disabled" : ""}>${downloadButtonLabel(book.download_status)}</button>
      <button class="download-btn convert-btn" data-asin="${book.asin}" ${convertBusy ? "disabled" : ""}>${convertButtonLabel(book.convert_status)}</button>
    `;
    listEl.appendChild(row);
  }
}

function setLastSynced(timestamp) {
  lastSyncedEl.textContent = timestamp ? `Last synced: ${new Date(timestamp).toLocaleString()}` : "Never synced";
}

let pollTimer = null;

function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(refreshFromCache, 2000);
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer);
    pollTimer = null;
  }
}

async function refreshFromCache() {
  try {
    const data = await apiGet("/api/library");
    renderBooks(data.books);
    setLastSynced(data.last_synced_at);
    const anyInProgress = data.books.some(
      (b) =>
        IN_PROGRESS_DOWNLOAD_STATUSES.includes(b.download_status) ||
        IN_PROGRESS_CONVERT_STATUSES.includes(b.convert_status)
    );
    if (anyInProgress) {
      startPolling();
    } else {
      stopPolling();
    }
  } catch (err) {
    showError(err.message);
  }
}

async function loadCached() {
  try {
    const status = await apiGet("/api/auth/status");
    if (!status.authenticated) {
      window.location.href = "/";
      return;
    }
  } catch (err) {
    console.error(err);
  }
  await refreshFromCache();
}

refreshBtn.addEventListener("click", async () => {
  hideError();
  refreshBtn.disabled = true;
  refreshBtn.textContent = "Syncing…";
  try {
    const data = await apiPost("/api/library/sync");
    renderBooks(data.books);
    setLastSynced(data.last_synced_at);
  } catch (err) {
    showError(err.message);
  } finally {
    refreshBtn.disabled = false;
    refreshBtn.textContent = "Refresh Library";
  }
});

listEl.addEventListener("click", async (e) => {
  const btn = e.target.closest(".download-btn");
  if (!btn || btn.disabled) return;
  const isConvert = btn.classList.contains("convert-btn");
  const action = isConvert ? "convert" : "download";
  hideError();
  const asin = btn.dataset.asin;
  btn.disabled = true;
  btn.textContent = "Starting…";
  try {
    await apiPost(`/api/library/${asin}/${action}`);
    await refreshFromCache();
  } catch (err) {
    showError(err.message);
    btn.disabled = false;
    btn.textContent = isConvert ? "Convert" : "Download";
  }
});

function renderIssues(errors) {
  if (errors.length === 0) {
    issuesList.innerHTML = '<p class="empty">No issues logged.</p>';
    return;
  }
  issuesList.innerHTML = errors
    .map(
      (e) => `
        <details class="issue">
          <summary>${new Date(e.occurred_at).toLocaleString()} — ${e.source}: ${e.message}</summary>
          <pre class="issue-traceback">${e.traceback ? e.traceback.replace(/</g, "&lt;") : "(no traceback)"}</pre>
        </details>
      `
    )
    .join("");
}

async function loadIssues() {
  try {
    const data = await apiGet("/api/errors");
    issuesBtn.textContent = data.errors.length ? `Issues (${data.errors.length})` : "Issues";
    renderIssues(data.errors);
  } catch (err) {
    issuesList.innerHTML = `<p class="error">Failed to load issues: ${err.message}</p>`;
  }
}

issuesBtn.addEventListener("click", async () => {
  issuesPanel.hidden = !issuesPanel.hidden;
  if (!issuesPanel.hidden) {
    await loadIssues();
  }
});

issuesCloseBtn.addEventListener("click", () => {
  issuesPanel.hidden = true;
});

loadCached();
loadIssues();
