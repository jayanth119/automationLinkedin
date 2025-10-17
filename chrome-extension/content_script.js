// content_script.js
const data = await res.json();
if (data.ok) {
  const token = data.token;
  chrome.storage.local.set({ token, email }, () => {
    document.getElementById("ll-status").textContent =
      "Logged in successfully.";
    document.getElementById("ll-password").value = "";
  });
} else {
  document.getElementById("ll-status").textContent =
    "Login failed: " + (data.error || "unknown");
}

async function summarizeHandler() {
  const tokenRes = await new Promise((resolve) =>
    chrome.storage.local.get(["token"], resolve)
  );
  const token = tokenRes.token;
  if (!token) return alert("Please login first.");
  const post_url = getLinkedInPostURL();
  document.getElementById("ll-output").textContent = "Processing...";

  try {
    const res = await fetch(`${BACKEND}/summarize`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token, post_url }),
    });
    const data = await res.json();
    if (data.ok) {
      document.getElementById("ll-output").textContent = JSON.stringify(
        data.result,
        null,
        2
      );
    } else {
      document.getElementById("ll-output").textContent =
        "Error: " + (data.error || "unknown");
    }
  } catch (err) {
    document.getElementById("ll-output").textContent =
      "Network error: " + err.message;
  }
}

async function downloadHandler() {
  const tokenRes = await new Promise((resolve) =>
    chrome.storage.local.get(["token"], resolve)
  );
  const token = tokenRes.token;
  if (!token) return alert("Please login first.");
  const post_url = getLinkedInPostURL();

  // Download PDF through backend and open it in a new tab
  const res = await fetch(`${BACKEND}/download_pdf`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ token, post_url }),
  });
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank");
}

// Inject UI once DOM is ready
if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", createUI);
} else {
  createUI();
}
