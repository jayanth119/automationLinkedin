// Popup Script

const API_BASE = 'http://localhost:8000';

// DOM Elements
const emailInput = document.getElementById('email');
const passwordInput = document.getElementById('password');
const loginBtn = document.getElementById('login-btn');
const logoutBtn = document.getElementById('logout-btn');
const loginSection = document.getElementById('login-section');
const loggedInSection = document.getElementById('logged-in-section');
const userEmailSpan = document.getElementById('user-email');
const messageContainer = document.getElementById('message-container');
const postUrlInput = document.getElementById('post-url');
const formatSelect = document.getElementById('format');
const summarizeBtn = document.getElementById('summarize-btn');
const downloadSection = document.getElementById('download-section');
const downloadLink = document.getElementById('download-link');
const summarizeText = document.getElementById('summarize-text');

// Show Message
function showMessage(message, type = 'info') {
  const msgEl = document.createElement('div');
  msgEl.className = `message ${type}`;
  msgEl.textContent = message;
  msgEl.style.animation = 'slideIn 0.3s ease';
  messageContainer.innerHTML = '';
  messageContainer.appendChild(msgEl);
  
  if (type !== 'error') {
    setTimeout(() => msgEl.remove(), 4000);
  }
}

// Get Current Tab URL
async function getCurrentTabUrl() {
  try {
    // First try to get from session storage
    const result = await chrome.storage.session.get('currentUrl');
    if (result.currentUrl) {
      chrome.storage.session.remove('currentUrl');
      return result.currentUrl;
    }

    // Fallback to active tab
    const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
    return tabs[0]?.url || '';
  } catch (error) {
    console.error('Error getting tab URL:', error);
    return '';
  }
}

// Check API Health
async function checkApiHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    return response.ok;
  } catch (error) {
    return false;
  }
}

// Initialize
async function init() {
  // Check API health
  const apiHealthy = await checkApiHealth();
  if (!apiHealthy) {
    showMessage('⚠️ Backend server not responding. Make sure it\'s running on port 8000', 'error');
  }

  // Fetch current tab URL
  const currentUrl = await getCurrentTabUrl();
  if (currentUrl.includes('linkedin.com')) {
    postUrlInput.value = currentUrl;
  }

  // Check if already logged in
  const session = await chrome.storage.local.get(['sessionId', 'email']);
  if (session.sessionId) {
    showLoggedInView(session.email);
    await verifySession(session.sessionId);
  }

  // Restore email if saved
  const savedEmail = await chrome.storage.local.get('savedEmail');
  if (savedEmail.savedEmail) {
    emailInput.value = savedEmail.savedEmail;
  }
}

// Verify Session with Backend
async function verifySession(sessionId) {
  try {
    const response = await fetch(`${API_BASE}/api/verify-session`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: sessionId })
    });

    if (!response.ok) {
      // Session expired
      await chrome.storage.local.remove(['sessionId', 'email', 'loginTime']);
      showLoggedOutView();
      showMessage('Session expired. Please login again', 'error');
    }
  } catch (error) {
    console.error('Session verification error:', error);
  }
}

// Login Handler
loginBtn.addEventListener('click', async () => {
  const email = emailInput.value.trim();
  const password = passwordInput.value.trim();

  if (!email || !password) {
    showMessage('Please enter both email and password', 'error');
    return;
  }

  // Validate email format
  if (!email.match(/^[^\s@]+@[^\s@]+\.[^\s@]+$/)) {
    showMessage('Please enter a valid email address', 'error');
    return;
  }

  loginBtn.disabled = true;
  summarizeText.innerHTML = '<span class="loading"></span>Logging in...';

  try {
    const response = await fetch(`${API_BASE}/api/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Login failed');
    }

    // Store session
    await chrome.storage.local.set({
      sessionId: data.session_id,
      email: data.email,
      loginTime: new Date().toISOString(),
      savedEmail: email
    });

    showMessage('✓ Login successful!', 'success');
    showLoggedInView(data.email);

    // Update badge
    chrome.action.setBadgeText({ text: '✓' });
    chrome.action.setBadgeBackgroundColor({ color: '#28a745' });
  } catch (error) {
    showMessage(`Login failed: ${error.message}`, 'error');
  } finally {
    loginBtn.disabled = false;
    summarizeText.innerHTML = 'Summarize';
  }
});

// Logout Handler
logoutBtn.addEventListener('click', async () => {
  const session = await chrome.storage.local.get('sessionId');
  
  if (session.sessionId) {
    try {
      await fetch(`${API_BASE}/api/logout`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ session_id: session.sessionId })
      });
    } catch (error) {
      console.error('Logout error:', error);
    }
  }

  // Clear storage
  await chrome.storage.local.remove(['sessionId', 'email', 'loginTime']);
  showLoggedOutView();
  showMessage('Logged out successfully', 'success');

  // Clear badge
  chrome.action.setBadgeText({ text: '' });
});

// Summarize Handler
summarizeBtn.addEventListener('click', async () => {
  const url = postUrlInput.value.trim();
  const format = formatSelect.value;
  const session = await chrome.storage.local.get('sessionId');

  if (!url) {
    showMessage('Please enter a post URL', 'error');
    return;
  }

  if (!url.includes('linkedin.com')) {
    showMessage('Please enter a valid LinkedIn URL', 'error');
    return;
  }

  if (!session.sessionId) {
    showMessage('Session expired. Please login again', 'error');
    showLoggedOutView();
    return;
  }

  summarizeBtn.disabled = true;
  summarizeText.innerHTML = '<span class="loading"></span>Processing...';
  downloadSection.style.display = 'none';

  try {
    const response = await fetch(`${API_BASE}/api/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        session_id: session.sessionId,
        url: url,
        format: format
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.error || 'Summarization failed');
    }

    showMessage('✓ Summary generated successfully!', 'success');
    
    // Show download link
    const downloadUrl = `${API_BASE}${data.download_link}`;
    downloadLink.href = downloadUrl;
    downloadLink.download = `summary_${data.file_id}.${format}`;
    downloadLink.textContent = `⬇️ Download ${format.toUpperCase()}`;
    downloadSection.style.display = 'block';

    // Copy URL to clipboard
    postUrlInput.value = '';

  } catch (error) {
    showMessage(`Error: ${error.message}`, 'error');
  } finally {
    summarizeBtn.disabled = false;
    summarizeText.innerHTML = 'Summarize';
  }
});

// Allow Enter key to summarize
postUrlInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !summarizeBtn.disabled) {
    summarizeBtn.click();
  }
});

// Allow Enter key to login
passwordInput.addEventListener('keypress', (e) => {
  if (e.key === 'Enter' && !loginBtn.disabled) {
    loginBtn.click();
  }
});

// Show Logged In View
function showLoggedInView(email) {
  loginSection.style.display = 'none';
  loggedInSection.style.display = 'block';
  userEmailSpan.textContent = email;
  postUrlInput.focus();
}

// Show Logged Out View
function showLoggedOutView() {
  loginSection.style.display = 'block';
  loggedInSection.style.display = 'none';
  passwordInput.value = '';
  postUrlInput.value = '';
  downloadSection.style.display = 'none';
  emailInput.focus();
}

// Initialize
init();

// Listen for session expiration
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'sessionExpired') {
    showMessage('Session expired. Please login again', 'error');
    showLoggedOutView();
    chrome.storage.local.remove(['sessionId', 'email', 'loginTime']);
  }
});