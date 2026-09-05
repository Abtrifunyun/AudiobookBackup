const downloadsDirInput = document.getElementById("downloads-dir");
const downloadsDirDefaultNote = document.getElementById("downloads-dir-default");
const libraryDirInput = document.getElementById("library-dir");
const libraryDirDefaultNote = document.getElementById("library-dir-default");
const saveBtn = document.getElementById("save-btn");
const resetBtn = document.getElementById("reset-btn");
const openDownloadsBtn = document.getElementById("open-downloads-btn");
const openLibraryBtn = document.getElementById("open-library-btn");
const organizeByAuthorCheckbox = document.getElementById("organize-by-author");
const darkModeCheckbox = document.getElementById("dark-mode-checkbox");
const statusEl = document.getElementById("settings-status");

function isDarkMode() {
  const explicit = document.documentElement.getAttribute("data-theme");
  if (explicit === "dark" || explicit === "light") return explicit === "dark";
  return window.matchMedia("(prefers-color-scheme: dark)").matches;
}

darkModeCheckbox.checked = isDarkMode();
darkModeCheckbox.addEventListener("change", () => {
  const theme = darkModeCheckbox.checked ? "dark" : "light";
  document.documentElement.setAttribute("data-theme", theme);
  try {
    localStorage.setItem("theme", theme);
  } catch (err) {
    console.error(err);
  }
});

function showStatus(message, isError) {
  statusEl.textContent = message;
  statusEl.className = isError ? "error" : "hint";
  statusEl.hidden = false;
}

function applySettings(data) {
  downloadsDirInput.value = data.downloads_dir;
  libraryDirInput.value = data.library_output_dir;
  downloadsDirDefaultNote.hidden = !data.downloads_dir_is_default;
  libraryDirDefaultNote.hidden = !data.library_output_dir_is_default;
  organizeByAuthorCheckbox.checked = data.organize_by_author;
}

async function loadSettings() {
  try {
    const data = await apiGet("/api/settings");
    applySettings(data);
  } catch (err) {
    showStatus(`Failed to load settings: ${err.message}`, true);
  }
}

saveBtn.addEventListener("click", async () => {
  saveBtn.disabled = true;
  saveBtn.textContent = "Saving…";
  try {
    const data = await apiPost("/api/settings", {
      downloads_dir: downloadsDirInput.value,
      library_output_dir: libraryDirInput.value,
      organize_by_author: organizeByAuthorCheckbox.checked,
    });
    applySettings(data);
    showStatus("Saved. New downloads/conversions will use these folders.", false);
  } catch (err) {
    showStatus(err.message, true);
  } finally {
    saveBtn.disabled = false;
    saveBtn.textContent = "Save";
  }
});

resetBtn.addEventListener("click", async () => {
  resetBtn.disabled = true;
  try {
    const data = await apiPost("/api/settings", {
      downloads_dir: "",
      library_output_dir: "",
      organize_by_author: true,
    });
    applySettings(data);
    showStatus("Reset to defaults.", false);
  } catch (err) {
    showStatus(err.message, true);
  } finally {
    resetBtn.disabled = false;
  }
});

openDownloadsBtn.addEventListener("click", async () => {
  openDownloadsBtn.disabled = true;
  try {
    await apiPost("/api/settings/open-downloads-folder");
  } catch (err) {
    showStatus(err.message, true);
  } finally {
    openDownloadsBtn.disabled = false;
  }
});

openLibraryBtn.addEventListener("click", async () => {
  openLibraryBtn.disabled = true;
  try {
    await apiPost("/api/settings/open-library-folder");
  } catch (err) {
    showStatus(err.message, true);
  } finally {
    openLibraryBtn.disabled = false;
  }
});

loadSettings();
