const gridEl = document.getElementById("grid");
const lastSyncedEl = document.getElementById("last-synced");
const errorEl = document.getElementById("library-error");
const refreshBtn = document.getElementById("refresh-btn");

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

function renderBooks(books) {
  gridEl.innerHTML = "";
  if (books.length === 0) {
    gridEl.innerHTML = '<p class="empty">No books yet — click "Refresh Library" to fetch your purchases.</p>';
    return;
  }
  for (const book of books) {
    const card = document.createElement("div");
    card.className = "book-card";

    const coverSrc = book.cover_local_path ? `/covers/${book.cover_local_path}` : book.cover_url;
    const authorLine = book.authors.join(", ");
    const narratorLine = book.narrators.join(", ");

    card.innerHTML = `
      <img class="book-cover" src="${coverSrc || ""}" alt="${book.title} cover" loading="lazy">
      <div class="book-info">
        <h3>${book.title}</h3>
        ${authorLine ? `<p class="book-authors">${authorLine}</p>` : ""}
        ${narratorLine ? `<p class="book-narrators">Narrated by ${narratorLine}</p>` : ""}
        ${book.runtime_length_min ? `<p class="book-runtime">${formatRuntime(book.runtime_length_min)}</p>` : ""}
        <span class="badge badge-${book.download_status}">${book.download_status.replace("_", " ")}</span>
      </div>
    `;
    gridEl.appendChild(card);
  }
}

function setLastSynced(timestamp) {
  lastSyncedEl.textContent = timestamp ? `Last synced: ${new Date(timestamp).toLocaleString()}` : "Never synced";
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
  try {
    const data = await apiGet("/api/library");
    renderBooks(data.books);
    setLastSynced(data.last_synced_at);
  } catch (err) {
    showError(err.message);
  }
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

loadCached();
