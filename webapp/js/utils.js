/**
 * Frontend Utilities: XSS Sanitization, Safe DOM helpers, Date formatting, and Telegram Haptics.
 */

export function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}

export function triggerHaptic(style = 'light') {
  try {
    const tg = window.Telegram?.WebApp;
    if (tg?.HapticFeedback) {
      if (style === 'success' || style === 'error' || style === 'warning') {
        tg.HapticFeedback.notificationOccurred(style);
      } else {
        tg.HapticFeedback.impactOccurred(style);
      }
    }
  } catch (e) {
    // Ignore if not in Telegram
  }
}

export function showToast(message, type = 'info') {
  const existing = document.getElementById('lumina-toast');
  if (existing) existing.remove();

  const toast = document.createElement('div');
  toast.id = 'lumina-toast';
  toast.style.cssText = `
    position: fixed;
    bottom: 90px;
    left: 50%;
    transform: translateX(-50%);
    background: var(--text-primary);
    color: var(--bg-surface);
    padding: 10px 18px;
    border-radius: var(--radius-full);
    font-size: 13px;
    font-weight: 600;
    box-shadow: var(--shadow-lg);
    z-index: 999;
    display: flex;
    align-items: center;
    gap: 8px;
    animation: fadeIn 150ms ease-out;
  `;
  toast.textContent = message;
  document.body.appendChild(toast);

  triggerHaptic(type === 'error' ? 'error' : 'light');

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 200ms ease-out';
    setTimeout(() => toast.remove(), 200);
  }, 2500);
}
