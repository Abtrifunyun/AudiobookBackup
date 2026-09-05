async function apiGet(path) {
  const response = await fetch(path);
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `GET ${path} failed: ${response.status}`);
  }
  return response.json();
}

async function apiPost(path, body) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const detail = await response.json().catch(() => ({}));
    throw new Error(detail.detail || `POST ${path} failed: ${response.status}`);
  }
  return response.json();
}

function openPlayer() {
  if (window.pywebview && window.pywebview.api && window.pywebview.api.open_player_window) {
    window.pywebview.api.open_player_window();
  } else {
    // Dev-mode fallback when running in a plain browser instead of the packaged app.
    window.open("/player.html", "_blank");
  }
}
