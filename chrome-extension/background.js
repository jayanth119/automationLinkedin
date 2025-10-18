// Background Service Worker

const API_BASE = 'http://13.233.129.57/';

// Listen for messages from content script or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getSessionId') {
    chrome.storage.local.get('sessionId', (result) => {
      sendResponse({ sessionId: result.sessionId });
    });
    return true;
  }

  if (request.action === 'clearSession') {
    chrome.storage.local.remove(['sessionId', 'email', 'loginTime'], () => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'setCurrentUrl') {
    chrome.storage.session.set({ currentUrl: request.url }, () => {
      sendResponse({ success: true });
    });
    return true;
  }

  if (request.action === 'getCurrentUrl') {
    chrome.storage.session.get('currentUrl', (result) => {
      sendResponse({ url: result.currentUrl || '' });
    });
    return true;
  }

  if (request.action === 'openSummarizePopup') {
    chrome.storage.session.set({
      currentUrl: request.url,
      postText: request.postText
    });
    chrome.action.openPopup();
    sendResponse({ success: true });
    return true;
  }

  if (request.action === 'getApiHealth') {
    checkApiHealth().then(status => {
      sendResponse(status);
    });
    return true;
  }
});

// Check API health
async function checkApiHealth() {
  try {
    const response = await fetch(`${API_BASE}/api/health`, {
      method: 'GET'
    });
    return {
      healthy: response.ok,
      status: response.status
    };
  } catch (error) {
    return {
      healthy: false,
      error: error.message
    };
  }
}

// Set up periodic session cleanup (every 2 hours)
chrome.alarms.create('sessionCleanup', { periodInMinutes: 120 });

chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === 'sessionCleanup') {
    chrome.storage.local.get(['loginTime'], (result) => {
      if (result.loginTime) {
        const loginTime = new Date(result.loginTime);
        const now = new Date();
        const diffHours = (now - loginTime) / (1000 * 60 * 60);
        
        // Clear session after 24 hours
        if (diffHours > 24) {
          chrome.storage.local.remove(['sessionId', 'email', 'loginTime']);
          chrome.runtime.sendMessage({
            action: 'sessionExpired'
          }).catch(() => {});
        }
      }
    });
  }
});

// Create context menu
chrome.contextMenus.removeAll(() => {
  chrome.contextMenus.create({
    id: 'summarizePost',
    title: '✨ Summarize this LinkedIn Post',
    contexts: ['page'],
    documentUrlPatterns: ['https://www.linkedin.com/*']
  });

  chrome.contextMenus.create({
    id: 'copyPostUrl',
    title: 'Copy Post URL',
    contexts: ['page'],
    documentUrlPatterns: ['https://www.linkedin.com/*']
  });
});

// Handle context menu clicks
chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === 'summarizePost') {
    chrome.storage.local.get('sessionId', (result) => {
      if (!result.sessionId) {
        chrome.action.openPopup();
        return;
      }

      chrome.tabs.sendMessage(tab.id, {
        action: 'openSummarizePopup',
        url: tab.url
      }).catch(() => {
        chrome.action.openPopup();
      });
    });
  }

  if (info.menuItemId === 'copyPostUrl') {
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      function: () => {
        navigator.clipboard.writeText(window.location.href);
      }
    });
  }
});

// Update badge count
function updateBadge() {
  chrome.storage.local.get(['sessionId'], (result) => {
    if (result.sessionId) {
      chrome.action.setBadgeText({ text: '✓' });
      chrome.action.setBadgeBackgroundColor({ color: '#28a745' });
    } else {
      chrome.action.setBadgeText({ text: '' });
    }
  });
}

// Listen for storage changes
chrome.storage.onChanged.addListener((changes, namespace) => {
  if (namespace === 'local' && changes.sessionId) {
    updateBadge();
  }
});

// Initialize badge on startup
updateBadge();

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && tab.url.includes('linkedin.com')) {
    // Inject content script if not already injected
    chrome.tabs.sendMessage(tabId, { action: 'ping' }).catch(() => {
      chrome.scripting.executeScript({
        target: { tabId: tabId },
        files: ['content.js']
      }).catch(() => {});
    });
  }
});