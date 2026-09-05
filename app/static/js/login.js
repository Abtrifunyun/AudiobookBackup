let sessionId = null;

const checkingEl = document.getElementById("checking");
const loginFormEl = document.getElementById("login-form");
const pasteSectionEl = document.getElementById("paste-section");
const loginErrorEl = document.getElementById("login-error");
const completeErrorEl = document.getElementById("complete-error");

function showError(el, message) {
  el.textContent = message;
  el.hidden = false;
}

function hideError(el) {
  el.hidden = true;
}

document.getElementById("open-player-btn").addEventListener("click", openPlayer);

async function init() {
  try {
    const status = await apiGet("/api/auth/status");
    if (status.authenticated) {
      window.location.href = "/library.html";
      return;
    }
  } catch (err) {
    console.error(err);
  }
  checkingEl.hidden = true;
  loginFormEl.hidden = false;
}

document.getElementById("start-login-btn").addEventListener("click", async () => {
  hideError(loginErrorEl);
  const btn = document.getElementById("start-login-btn");
  btn.disabled = true;
  btn.textContent = "Starting…";
  try {
    const locale = document.getElementById("locale").value;
    const { session_id, login_url } = await apiPost("/api/auth/login/start", { locale });
    sessionId = session_id;
    document.getElementById("audible-login-link").href = login_url;
    loginFormEl.hidden = true;
    pasteSectionEl.hidden = false;
  } catch (err) {
    showError(loginErrorEl, err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Log in with Audible";
  }
});

document.getElementById("complete-login-btn").addEventListener("click", async () => {
  hideError(completeErrorEl);
  const btn = document.getElementById("complete-login-btn");
  const url = document.getElementById("postlogin-url").value.trim();
  if (!url) {
    showError(completeErrorEl, "Paste the URL you landed on after logging in.");
    return;
  }
  btn.disabled = true;
  btn.textContent = "Verifying…";
  try {
    const result = await apiPost("/api/auth/login/complete", {
      session_id: sessionId,
      postlogin_url: url,
    });
    if (result.success) {
      window.location.href = "/library.html";
    } else {
      const hint = "Audible rejected this attempt. This session is now dead either way — " +
        "click Start Over and try again, making sure you used a wrong password on the FIRST " +
        "screen and your real password + captcha on the SECOND. Raw error: ";
      showError(completeErrorEl, hint + (result.error || "(none given)"));
    }
  } catch (err) {
    showError(completeErrorEl, err.message);
  } finally {
    btn.disabled = false;
    btn.textContent = "Complete Login";
  }
});

document.getElementById("start-over-btn").addEventListener("click", () => {
  sessionId = null;
  document.getElementById("postlogin-url").value = "";
  hideError(completeErrorEl);
  pasteSectionEl.hidden = true;
  loginFormEl.hidden = false;
});

init();
