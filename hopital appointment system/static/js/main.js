/**
 * Hospital Appointment System - Main Client-Side JavaScript
 */

// CSRF helper for AJAX requests
function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

async function fetchWithCsrf(url, options = {}) {
  const headers = options.headers || {};
  if (!headers['X-CSRFToken'] && !headers['x-csrftoken']) {
    headers['X-CSRFToken'] = getCsrfToken();
  }
  options.headers = headers;
  return fetch(url, options);
}

// Toast notification system
function showToast(message, type = 'info') {
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.style.cssText = `
      position: fixed;
      bottom: 24px;
      right: 24px;
      z-index: 9999;
      display: flex;
      flex-direction: column;
      gap: 10px;
    `;
    document.body.appendChild(toastContainer);
  }

  const toast = document.createElement('div');
  const bgMap = {
    success: '#10b981',
    danger: '#ef4444',
    warning: '#f59e0b',
    info: '#0284c7'
  };

  toast.style.cssText = `
    background: ${bgMap[type] || '#0284c7'};
    color: white;
    padding: 12px 20px;
    border-radius: 8px;
    font-size: 0.9rem;
    font-weight: 500;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    display: flex;
    align-items: center;
    gap: 10px;
    animation: toastSlideIn 0.25s ease-out;
  `;
  toast.innerHTML = `<span>${message}</span>`;
  toastContainer.appendChild(toast);

  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transform = 'translateY(10px)';
    toast.style.transition = 'all 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Modal helpers
function openModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.add('show');
  }
}

function closeModal(modalId) {
  const modal = document.getElementById(modalId);
  if (modal) {
    modal.classList.remove('show');
  }
}

// Global Event Listeners Setup
document.addEventListener('DOMContentLoaded', () => {
  // Mobile sidebar toggle
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebar = document.getElementById('dashboardSidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', () => {
      sidebar.classList.toggle('open');
    });
    // Close sidebar on click outside on mobile
    document.addEventListener('click', (e) => {
      if (window.innerWidth <= 992 && !sidebar.contains(e.target) && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('open');
      }
    });
  }

  // User dropdown menu toggle
  const userMenuBtn = document.getElementById('userMenuBtn');
  const userDropdown = document.getElementById('userDropdown');
  if (userMenuBtn && userDropdown) {
    userMenuBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      userDropdown.classList.toggle('show');
    });
    document.addEventListener('click', () => {
      userDropdown.classList.remove('show');
    });
  }

  // Notification dropdown toggle & fetching
  const notifBtn = document.getElementById('notifBtn');
  const notifDropdown = document.getElementById('notifDropdown');
  if (notifBtn && notifDropdown) {
    notifBtn.addEventListener('click', async (e) => {
      e.stopPropagation();
      const isShowing = notifDropdown.classList.toggle('show');
      if (isShowing) {
        await loadNotifications();
      }
    });

    document.addEventListener('click', () => {
      notifDropdown.classList.remove('show');
    });

    const markAllReadBtn = document.getElementById('markAllReadBtn');
    if (markAllReadBtn) {
      markAllReadBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        try {
          const res = await fetchWithCsrf('/api/notifications/read-all', { method: 'POST' });
          const data = await res.json();
          if (data.success) {
            const badge = document.getElementById('notifBadge');
            if (badge) badge.style.display = 'none';
            await loadNotifications();
            showToast('All notifications marked as read', 'success');
          }
        } catch (err) {
          console.error(err);
        }
      });
    }
  }

  // Alert dismiss buttons
  document.querySelectorAll('.alert-close-btn').forEach(btn => {
    btn.addEventListener('click', function() {
      const alert = this.closest('.alert');
      if (alert) alert.remove();
    });
  });

  // Modal backdrop click close
  document.querySelectorAll('.modal-backdrop').forEach(backdrop => {
    backdrop.addEventListener('click', (e) => {
      if (e.target === backdrop) {
        backdrop.classList.remove('show');
      }
    });
  });
});

async function loadNotifications() {
  const listContainer = document.getElementById('notifList');
  if (!listContainer) return;

  try {
    const res = await fetch('/api/notifications');
    const data = await res.json();

    if (!data.notifications || data.notifications.length === 0) {
      listContainer.innerHTML = '<div style="padding: 20px; text-align: center; color: #94a3b8; font-size: 0.85rem;">No recent notifications</div>';
      return;
    }

    listContainer.innerHTML = data.notifications.map(item => `
      <div class="notif-item ${item.is_read ? '' : 'unread'}" data-id="${item.id}">
        <div class="notif-title">${item.title}</div>
        <div class="notif-desc">${item.message}</div>
        <div class="notif-time">${item.created_at}</div>
      </div>
    `).join('');

    // Update badge counter
    const badge = document.getElementById('notifBadge');
    if (badge) {
      if (data.unread_count > 0) {
        badge.textContent = data.unread_count;
        badge.style.display = 'inline-block';
      } else {
        badge.style.display = 'none';
      }
    }
  } catch (err) {
    console.error('Failed to load notifications:', err);
  }
}
