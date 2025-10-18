// Content Script - Runs on LinkedIn pages

const API_BASE = 'http://13.233.129.57/';
const POST_ATTRIBUTE = '[data-id*="urn:li:share"]';

// Listen for messages from background or popup
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'getCurrentUrl') {
    sendResponse({ url: window.location.href });
  }

  if (request.action === 'extractPostData') {
    const postData = extractLinkedInPostData();
    sendResponse(postData);
  }

  if (request.action === 'openSummarizePopup') {
    chrome.runtime.sendMessage({
      action: 'setCurrentUrl',
      url: request.url
    });
    chrome.action.openPopup();
  }
});

// Extract post data from LinkedIn page
function extractLinkedInPostData() {
  try {
    const postContainer = document.querySelector(POST_ATTRIBUTE);
    
    if (!postContainer) {
      return {
        url: window.location.href,
        postFound: false
      };
    }

    // Extract post text
    const textElement = postContainer.querySelector('[data-anonymous-user-name]');
    const postText = textElement?.innerText || '';

    // Extract images
    const images = Array.from(postContainer.querySelectorAll('img'))
      .filter(img => img.src && !img.src.includes('profile'))
      .map(img => img.src);

    // Extract video
    const videoElement = postContainer.querySelector('video');
    const hasVideo = !!videoElement;

    return {
      url: window.location.href,
      postFound: true,
      text: postText,
      imageCount: images.length,
      hasVideo: hasVideo
    };
  } catch (error) {
    console.error('Error extracting post data:', error);
    return {
      url: window.location.href,
      postFound: false,
      error: error.message
    };
  }
}

// Inject summarize button into post
function injectSummarizeButton() {
  const posts = document.querySelectorAll(POST_ATTRIBUTE);
  
  posts.forEach((post, index) => {
    // Skip if already injected
    if (post.querySelector('.summarize-btn-injected')) return;

    // Find action toolbar
    const actionToolbar = post.querySelector('[role="menubar"]') || 
                         post.querySelector('.social-details-social-counts');
    
    if (!actionToolbar) return;

    // Create button container
    const btnContainer = document.createElement('div');
    btnContainer.style.cssText = `
      display: inline-flex;
      margin-left: 10px;
      align-items: center;
    `;

    const btn = document.createElement('button');
    btn.className = 'summarize-btn-injected';
    btn.innerHTML = '✨ Summarize';
    btn.setAttribute('data-post-index', index);
    btn.setAttribute('title', 'Summarize this post with AI');

    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      e.preventDefault();
      handleSummarizeClick(post);
    });

    btn.addEventListener('mouseenter', () => {
      btn.style.transform = 'scale(1.05)';
      showTooltip(btn, 'Click to summarize this post');
    });

    btn.addEventListener('mouseleave', () => {
      btn.style.transform = 'scale(1)';
      removeTooltip();
    });

    btnContainer.appendChild(btn);
    actionToolbar.appendChild(btnContainer);
  });
}

// Handle summarize button click
function handleSummarizeClick(postElement) {
  const postUrl = window.location.href;
  const postText = postElement.innerText?.substring(0, 200) || 'LinkedIn Post';
  
  chrome.storage.local.get(['sessionId'], (result) => {
    if (!result.sessionId) {
      showNotification('Please login first via the extension popup', 'error');
      return;
    }

    showNotification('Opening summarizer...', 'info');
    chrome.runtime.sendMessage({
      action: 'openSummarizePopup',
      url: postUrl,
      postText: postText
    });
  });
}

// Show tooltip
function showTooltip(element, text) {
  const tooltip = document.createElement('div');
  tooltip.className = 'summarize-tooltip';
  tooltip.textContent = text;
  
  const rect = element.getBoundingClientRect();
  tooltip.style.left = rect.left + 'px';
  tooltip.style.top = (rect.top - 30) + 'px';
  
  document.body.appendChild(tooltip);
  tooltip.id = 'summarize-tooltip-current';
}

// Remove tooltip
function removeTooltip() {
  const tooltip = document.getElementById('summarize-tooltip-current');
  if (tooltip) tooltip.remove();
}

// Show notification
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.style.cssText = `
    position: fixed;
    top: 20px;
    right: 20px;
    padding: 16px 24px;
    background: ${type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#17a2b8'};
    color: white;
    border-radius: 8px;
    z-index: 10001;
    font-size: 14px;
    font-weight: 600;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
    animation: slideInRight 0.3s ease;
  `;
  notification.textContent = message;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.style.animation = 'slideOutRight 0.3s ease';
    setTimeout(() => notification.remove(), 300);
  }, 3000);
}

// Add slide animations
const style = document.createElement('style');
style.textContent = `
  @keyframes slideInRight {
    from {
      transform: translateX(400px);
      opacity: 0;
    }
    to {
      transform: translateX(0);
      opacity: 1;
    }
  }
  
  @keyframes slideOutRight {
    from {
      transform: translateX(0);
      opacity: 1;
    }
    to {
      transform: translateX(400px);
      opacity: 0;
    }
  }
`;
document.head.appendChild(style);

// Run on page load
function initializeExtension() {
  injectSummarizeButton();
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initializeExtension);
} else {
  initializeExtension();
}

// Re-inject when new posts are loaded (infinite scroll)
const observer = new MutationObserver((mutations) => {
  // Debounce to avoid too many injections
  clearTimeout(observer.debounceTimer);
  observer.debounceTimer = setTimeout(() => {
    injectSummarizeButton();
  }, 500);
});

observer.observe(document.body, {
  childList: true,
  subtree: true
});

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
  observer.disconnect();
});