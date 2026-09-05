const errorEl = document.getElementById("player-error");
const fileListEl = document.getElementById("file-list");
const refreshFilesBtn = document.getElementById("refresh-files-btn");
const playerArea = document.getElementById("player-area");
const verifyBtn = document.getElementById("verify-btn");
const closePlayerBtn = document.getElementById("close-player-btn");

let books = [];
let currentPath = null;

closePlayerBtn.addEventListener("click", () => {
  window.close();
});

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function hideError() {
  errorEl.hidden = true;
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
}

function renderFileList() {
  if (books.length === 0) {
    fileListEl.innerHTML =
      '<p class="hint">No converted M4B files found yet. Convert a book from the library first, or check the converted folder in Settings.</p>';
    return;
  }
  fileListEl.innerHTML = books
    .map(
      (b, i) => `
        <div class="chapter-row" data-index="${i}">
          <span class="chapter-title">${b.title}</span>
          <span class="hint">${b.artist || ""}</span>
          <span class="chapter-time hint">${b.duration_seconds ? formatTime(b.duration_seconds) : ""}</span>
        </div>
      `
    )
    .join("");

  fileListEl.querySelectorAll(".chapter-row").forEach((row) => {
    row.addEventListener("click", () => loadPlayer(books[Number(row.dataset.index)]));
  });
}

async function loadFiles() {
  try {
    const data = await apiGet("/api/player/books");
    books = data.books;
    renderFileList();
  } catch (err) {
    showError(err.message);
  }
}

function renderChapters(chapters) {
  const container = document.getElementById("chapters-list");
  if (chapters.length === 0) {
    container.innerHTML = '<p class="hint">No chapters found.</p>';
    return;
  }
  container.innerHTML = chapters
    .map(
      (ch, i) => `
        <div class="chapter-row" data-start="${ch.start_seconds}">
          <span class="chapter-index">${i + 1}.</span>
          <span class="chapter-title">${ch.title || "Untitled"}</span>
          <span class="chapter-time hint">${formatTime(ch.start_seconds)}</span>
        </div>
      `
    )
    .join("");

  container.querySelectorAll(".chapter-row").forEach((row) => {
    row.addEventListener("click", () => {
      const audio = document.getElementById("audio-player");
      audio.currentTime = parseFloat(row.dataset.start);
      audio.play();
    });
  });
}

async function loadChapters(path) {
  try {
    const data = await apiGet(`/api/player/chapters?path=${encodeURIComponent(path)}`);
    renderChapters(data.chapters);
  } catch (err) {
    console.error(err);
  }
}

function renderVerifyResults(result) {
  const container = document.getElementById("verify-results");
  const statusText = result.valid ? "✓ Verified" : "⚠ Issues found";
  const statusClass = result.valid ? "badge-downloaded" : "badge-failed";
  const facts = `
    <ul class="verify-facts">
      <li>Duration: ${result.duration_seconds ? formatTime(result.duration_seconds) : "unknown"}</li>
      <li>Chapters: ${result.chapter_count}</li>
      <li>Cover art: ${result.has_cover_art ? "present" : "missing"}</li>
    </ul>
  `;
  const issues = result.issues.length
    ? `<ul class="verify-issues">${result.issues.map((i) => `<li>${i}</li>`).join("")}</ul>`
    : "";
  container.innerHTML = `<p><span class="badge ${statusClass}">${statusText}</span></p>${facts}${issues}`;
}

function loadPlayer(book) {
  hideError();
  currentPath = book.path;
  playerArea.hidden = false;

  document.getElementById("book-title").textContent = book.title;
  document.getElementById("book-authors").textContent = book.artist || "";
  document.getElementById("book-narrators").textContent = book.composer ? `Narrated by ${book.composer}` : "";

  const cover = document.getElementById("book-cover");
  cover.src = `/api/player/cover?path=${encodeURIComponent(book.path)}`;
  cover.onerror = () => {
    cover.onerror = null;
    cover.removeAttribute("src");
  };

  const audio = document.getElementById("audio-player");
  audio.src = `/api/player/audio?path=${encodeURIComponent(book.path)}`;

  document.getElementById("verify-results").innerHTML = '<p class="hint">Not verified yet.</p>';
  loadChapters(book.path);

  playerArea.scrollIntoView({ behavior: "smooth" });
}

refreshFilesBtn.addEventListener("click", async () => {
  refreshFilesBtn.disabled = true;
  await loadFiles();
  refreshFilesBtn.disabled = false;
});

verifyBtn.addEventListener("click", async () => {
  if (!currentPath) return;
  verifyBtn.disabled = true;
  verifyBtn.textContent = "Verifying…";
  try {
    const result = await apiPost(`/api/player/verify?path=${encodeURIComponent(currentPath)}`);
    renderVerifyResults(result);
  } catch (err) {
    showError(err.message);
  } finally {
    verifyBtn.disabled = false;
    verifyBtn.textContent = "Run Verification";
  }
});

loadFiles();
