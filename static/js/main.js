/* ============================
   Inventory Management System
   Main JavaScript
   ============================ */

'use strict';

// ─── Dark Mode ───
const THEME_KEY = 'ims_theme';

function applyTheme(theme) {
  document.documentElement.setAttribute('data-theme', theme);
  const icon = document.getElementById('theme-icon');
  if (icon) icon.textContent = theme === 'dark' ? '☀️' : '🌙';
}

function toggleTheme() {
  const current = document.documentElement.getAttribute('data-theme') || 'light';
  const next = current === 'dark' ? 'light' : 'dark';
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

// Apply saved theme immediately
(function () {
  const saved = localStorage.getItem(THEME_KEY) || 'light';
  applyTheme(saved);
})();

// ─── Sidebar toggle (mobile) ───
function toggleSidebar() {
  document.querySelector('.sidebar').classList.toggle('open');
}

// ─── Auto-dismiss alerts ───
function initAlertDismiss() {
  document.querySelectorAll('.alert').forEach(el => {
    setTimeout(() => {
      el.style.transition = 'opacity 0.5s';
      el.style.opacity = '0';
      setTimeout(() => el.remove(), 500);
    }, 5000);
  });
}

// ─── Mark notification read via AJAX ───
function markNotificationRead(pk, csrfToken) {
  fetch(`/notifications/${pk}/mark-read/`, {
    method: 'POST',
    headers: { 'X-CSRFToken': csrfToken, 'Content-Type': 'application/json' },
  }).then(r => r.json()).then(data => {
    if (data.status === 'ok') {
      const el = document.getElementById(`notif-${pk}`);
      if (el) el.classList.add('read');
    }
  });
}

// ─── POS / Cart ───
let cart = [];

function renderCart() {
  const cartBody = document.getElementById('cart-body');
  const cartTotal = document.getElementById('cart-total');
  const cartCount = document.getElementById('cart-count');
  const cartDataInput = document.getElementById('cart-data');
  if (!cartBody) return;

  cartBody.innerHTML = '';
  let total = 0;

  if (cart.length === 0) {
    cartBody.innerHTML = '<tr><td colspan="5" class="text-muted" style="text-align:center;padding:2rem;">Cart is empty</td></tr>';
  } else {
    cart.forEach((item, index) => {
      const lineTotal = (parseFloat(item.price) * item.quantity).toFixed(2);
      total += parseFloat(lineTotal);
      cartBody.innerHTML += `
        <tr>
          <td>${item.name}</td>
          <td>
            <input type="number" class="form-control" style="width:70px" min="1" max="${item.maxQty}"
              value="${item.quantity}" onchange="updateCartQty(${index}, this.value)">
          </td>
          <td>${parseFloat(item.price).toFixed(2)}</td>
          <td>${lineTotal}</td>
          <td><button type="button" class="btn btn-danger btn-sm" onclick="removeFromCart(${index})">✕</button></td>
        </tr>`;
    });
  }

  if (cartTotal) cartTotal.textContent = total.toFixed(2);
  if (cartCount) cartCount.textContent = cart.length;
  if (cartDataInput) cartDataInput.value = JSON.stringify(cart);
}

function addToCart(productId, name, price, maxQty) {
  const existing = cart.findIndex(i => i.product_id === productId);
  if (existing >= 0) {
    if (cart[existing].quantity < maxQty) {
      cart[existing].quantity++;
    } else {
      showToast(`Max stock reached for "${name}"`, 'warning');
      return;
    }
  } else {
    cart.push({ product_id: productId, name, price, quantity: 1, maxQty });
  }
  renderCart();
  showToast(`Added "${name}" to cart`, 'success');
}

function updateCartQty(index, qty) {
  qty = parseInt(qty);
  if (qty < 1) qty = 1;
  if (qty > cart[index].maxQty) qty = cart[index].maxQty;
  cart[index].quantity = qty;
  renderCart();
}

function removeFromCart(index) {
  cart.splice(index, 1);
  renderCart();
}

function clearCart() {
  cart = [];
  renderCart();
}

// ─── Barcode scanner lookup ───
function initBarcodeSearch() {
  const input = document.getElementById('barcode-input');
  if (!input) return;
  input.addEventListener('keydown', function (e) {
    if (e.key === 'Enter') {
      e.preventDefault();
      const barcode = this.value.trim();
      if (!barcode) return;
      fetch(`/inventory/api/barcode/?barcode=${encodeURIComponent(barcode)}`)
        .then(r => r.json())
        .then(data => {
          if (data.found) {
            addToCart(data.id, data.name, data.selling_price, data.stock_qty);
            this.value = '';
          } else {
            showToast('Product not found for barcode: ' + barcode, 'error');
          }
        });
    }
  });
}

// ─── Toast notifications ───
function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.style.cssText = 'position:fixed;bottom:1rem;right:1rem;z-index:9999;display:flex;flex-direction:column;gap:0.5rem;';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `alert alert-${type === 'error' ? 'danger' : type}`;
  toast.style.cssText = 'min-width:250px;box-shadow:0 4px 12px rgba(0,0,0,0.15);';
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = '0';
    toast.style.transition = 'opacity 0.4s';
    setTimeout(() => toast.remove(), 400);
  }, 3500);
}

// ─── Confirm dialogs ───
document.addEventListener('DOMContentLoaded', function () {
  initAlertDismiss();
  initBarcodeSearch();
  renderCart();

  // Confirm delete/void buttons
  document.querySelectorAll('[data-confirm]').forEach(btn => {
    btn.addEventListener('click', function (e) {
      if (!confirm(this.dataset.confirm)) {
        e.preventDefault();
      }
    });
  });

  // Active nav link
  const current = window.location.pathname;
  document.querySelectorAll('.nav-item a').forEach(link => {
    if (link.getAttribute('href') && current.startsWith(link.getAttribute('href')) && link.getAttribute('href') !== '/') {
      link.classList.add('active');
    }
    if (link.getAttribute('href') === '/' && current === '/') {
      link.classList.add('active');
    }
  });
});
