const params = new URLSearchParams(window.location.search);
const asin = params.get("asin");

const errorEl = document.getElementById("book-error");
const verifyBtn = document.getElementById("verify-btn");

function showError(message) {
  errorEl.textContent = message;
  errorEl.hidden = false;
}

function formatRuntime(minutes) {
  if (!minutes) return "";
  const hours = Math.floor(minutes / 60);
  const mins = minutes % 60;
  return `${hours}h ${mins}m`;
}

function formatTime(seconds) {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = Math.floor(seconds % 60);
  if (h > 0) return `${h}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
  return `${m}:${String(s).padStart(2, "0")}`;
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

function renderVerifyResults(book) {
  const container = document.getElementById("verify-results");
  if (!book.verified_at) {
    container.innerHTML = '<p class="hint">Not verified yet.</p>';
    return;
  }
  const statusText = book.verified ? "✓ Verified" : "⚠ Issues found";
  const statusClass = book.verified ? "badge-downloaded" : "badge-failed";
  const facts = `
    <ul class="verify-facts">
      <li>Duration: ${book.verify_duration_seconds ? formatTime(book.verify_duration_seconds) : "unknown"}</li>
      <li>Chapters: ${book.verify_chapter_count ?? "unknown"}</li>
      <li>Cover art: ${book.verify_has_cover_art ? "present" : "missing"}</li>
    </ul>
  `;
  const issues = book.verify_issues.length
    ? `<ul class="verify-issues">${book.verify_issues.map((i) => `<li>${i}</li>`).join("")}</ul>`
    : "";
  container.innerHTML = `
    <p><span class="badge ${statusClass}">${statusText}</span>
       <span class="hint">as of ${new Date(book.verified_at).toLocaleString()}</span></p>
    ${facts}
    ${issues}
  `;
}

async function loadChapters() {
  try {
    const data = await apiGet(`/api/library/${asin}/chapters`);
    renderChapters(data.chapters);
  } catch (err) {
    console.error(err);
  }
}

function applyBook(book) {
  document.title = `Audiobook Backup — ${book.title}`;
  document.getElementById("book-title").textContent = book.title;
  const subtitleEl = document.getElementById("book-subtitle");
  subtitleEl.textContent = book.subtitle || "";
  subtitleEl.hidden = !book.subtitle;
  document.getElementById("book-authors").textContent = book.authors.join(", ");
  document.getElementById("book-narrators").textContent = book.narrators.length
    ? `Narrated by ${book.narrators.join(", ")}`
    : "";
  document.getElementById("book-runtime").textContent = formatRuntime(book.runtime_length_min);

  const cover = document.getElementById("book-cover");
  cover.src = book.cover_local_path ? `/covers/${book.cover_local_path}` : book.cover_url || "";
  cover.alt = `${book.title} cover`;

  const playerSection = document.getElementById("player-section");
  const noAudioNote = document.getElementById("no-audio-note");
  const audio = document.getElementById("audio-player");
  if (book.convert_status === "converted") {
    playerSection.hidden = false;
    noAudioNote.hidden = true;
    audio.src = `/api/library/${asin}/audio`;
    loadChapters();
  } else {
    playerSection.hidden = true;
    noAudioNote.hidden = false;
  }

  renderVerifyResults(book);
  verifyBtn.disabled = book.convert_status !== "converted";
}

async function loadBook() {
  if (!asin) {
    showError("No book specified.");
    return;
  }
  try {
    const book = await apiGet(`/api/library/${asin}`);
    applyBook(book);
  } catch (err) {
    showError(err.message);
  }
}

verifyBtn.addEventListener("click", async () => {
  verifyBtn.disabled = true;
  verifyBtn.textContent = "Verifying…";
  try {
    const book = await apiPost(`/api/library/${asin}/verify`);
    applyBook(book);
  } catch (err) {
    showError(err.message);
  } finally {
    verifyBtn.disabled = false;
    verifyBtn.textContent = "Run Verification";
  }
});

loadBook();
