/**
 * Hodophile — Premium AI Travel Planner
 * Complete JavaScript — Interactions, Animations, Theme
 */

/* ── Theme Management ── */
const ThemeManager = {
  key: 'hodophile_theme',
  current: 'dark',

  init() {
    const saved = localStorage.getItem(this.key) || 'dark';
    this.apply(saved);
    const btn = document.getElementById('themeBtn');
    if (btn) btn.textContent = saved === 'dark' ? '☀' : '🌙';
  },

  apply(theme) {
    this.current = theme;
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem(this.key, theme);
  },

  toggle() {
    const next = this.current === 'dark' ? 'light' : 'dark';
    this.apply(next);
    const btn = document.getElementById('themeBtn');
    if (btn) {
      btn.textContent = next === 'dark' ? '☀' : '🌙';
      btn.style.transform = 'rotate(360deg)';
      setTimeout(() => { btn.style.transform = ''; }, 400);
    }
  }
};

/* ── Ripple Effect ── */
function addRipple(el) {
  el.addEventListener('click', function(e) {
    const rect = this.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;
    const ripple = document.createElement('span');
    ripple.className = 'ripple';
    ripple.style.cssText = `width:${size}px;height:${size}px;left:${x}px;top:${y}px;`;
    this.appendChild(ripple);
    ripple.addEventListener('animationend', () => ripple.remove());
  });
}

/* ── Scroll Reveal ── */
const RevealObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      RevealObserver.unobserve(entry.target);
    }
  });
}, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

/* ── Hero Canvas (Particle Constellation) ── */
function initHeroCanvas() {
  const canvas = document.getElementById('heroCanvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let W, H, pts = [];

  function resize() {
    W = canvas.width  = canvas.offsetWidth;
    H = canvas.height = canvas.offsetHeight || window.innerHeight;
    if (pts.length === 0) init();
  }

  function init() {
    pts = [];
    for (let i = 0; i < 90; i++) {
      pts.push({
        x: Math.random() * W, y: Math.random() * H,
        vx: (Math.random() - 0.5) * 0.35,
        vy: (Math.random() - 0.5) * 0.35,
        r: Math.random() * 2 + 0.5,
        opacity: Math.random() * 0.4 + 0.1
      });
    }
  }

  function draw() {
    ctx.clearRect(0, 0, W, H);
    const isLight = document.documentElement.getAttribute('data-theme') === 'light';
    const ptColor = isLight ? 'rgba(108,99,255,0.3)' : 'rgba(108,99,255,0.5)';
    const lineColor = isLight ? 'rgba(108,99,255,0.06)' : 'rgba(155,150,255,0.08)';

    pts.forEach(p => {
      p.x += p.vx; p.y += p.vy;
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;
      ctx.globalAlpha = p.opacity;
      ctx.fillStyle = ptColor;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    });

    for (let i = 0; i < pts.length; i++) {
      for (let j = i + 1; j < pts.length; j++) {
        const d = Math.hypot(pts[i].x - pts[j].x, pts[i].y - pts[j].y);
        if (d < 130) {
          ctx.globalAlpha = (1 - d / 130) * (isLight ? 0.07 : 0.1);
          ctx.strokeStyle = lineColor;
          ctx.lineWidth = 0.5;
          ctx.beginPath();
          ctx.moveTo(pts[i].x, pts[i].y);
          ctx.lineTo(pts[j].x, pts[j].y);
          ctx.stroke();
        }
      }
    }
    ctx.globalAlpha = 1;
    requestAnimationFrame(draw);
  }

  window.addEventListener('resize', resize);
  resize();
  draw();
}

/* ── AI Tip Rotator ── */
function initAiTipRotator() {
  const tipEl = document.getElementById('aiTip');
  if (!tipEl) return;
  const tips = [
    'Hi! Ask me anything ✈',
    'Plan a trip? 🗺️',
    'Budget advice? 💰',
    'Hidden gems? 💎',
    'Weather tips? 🌤',
    'Packing list? 🎒'
  ];
  let idx = 0;
  tipEl.style.transition = 'opacity 0.3s ease';
  setInterval(() => {
    tipEl.style.opacity = '0';
    setTimeout(() => {
      idx = (idx + 1) % tips.length;
      tipEl.textContent = tips[idx];
      tipEl.style.opacity = '1';
    }, 300);
  }, 4000);
}

/* ── Nav Mobile Toggle ── */
function initNavToggle() {
  const toggle = document.getElementById('navToggle');
  const links  = document.getElementById('navLinks');
  if (!toggle || !links) return;
  toggle.addEventListener('click', () => {
    links.classList.toggle('open');
    toggle.textContent = links.classList.contains('open') ? '✕' : '☰';
  });
  // Close on outside click
  document.addEventListener('click', (e) => {
    if (!e.target.closest('.nav')) {
      links.classList.remove('open');
      toggle.textContent = '☰';
    }
  });
}

/* ── Auto-dismiss Flash ── */
function initFlashDismiss() {
  const container = document.getElementById('flashContainer');
  if (!container) return;
  setTimeout(() => {
    container.style.transition = 'opacity 0.5s ease';
    container.style.opacity = '0';
    setTimeout(() => container.remove(), 500);
  }, 4000);
}

/* ── Smooth Scroll for anchor links ── */
function initSmoothScroll() {
  document.querySelectorAll('a[href^="#"]').forEach(a => {
    a.addEventListener('click', (e) => {
      const target = document.querySelector(a.getAttribute('href'));
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
      }
    });
  });
}

/* ── Nav scroll shadow ── */
function initNavScroll() {
  const nav = document.getElementById('mainNav');
  if (!nav) return;
  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      nav.style.boxShadow = '0 4px 24px rgba(0,0,0,0.2)';
    } else {
      nav.style.boxShadow = '';
    }
  }, { passive: true });
}

/* ── Password toggle helper (called inline) ── */
function togglePassword(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.type = el.type === 'password' ? 'text' : 'password';
}

/* ── Budget bar animation on result page ── */
function animateBudgetBars() {
  const fills = document.querySelectorAll('.budget-fill');
  fills.forEach(fill => {
    const w = fill.style.width;
    fill.style.width = '0%';
    setTimeout(() => {
      fill.style.transition = 'width 1s ease';
      fill.style.width = w;
    }, 300);
  });
}

/* ── Page transition effect ── */
function initPageTransition() {
  document.querySelectorAll('a:not([target="_blank"]):not([href^="#"])').forEach(link => {
    link.addEventListener('click', (e) => {
      const href = link.getAttribute('href');
      if (!href || href.startsWith('http') || href.startsWith('mailto') || link.getAttribute('onclick')) return;
      // Allow normal navigation (Flask handles pages server-side)
    });
  });
}

/* ── Initialize everything on DOM ready ── */
document.addEventListener('DOMContentLoaded', () => {
  ThemeManager.init();

  // Theme button
  const thBtn = document.getElementById('themeBtn');
  if (thBtn) thBtn.addEventListener('click', () => ThemeManager.toggle());

  // Scroll reveal
  document.querySelectorAll('.reveal').forEach(el => RevealObserver.observe(el));

  // Ripple on all buttons
  document.querySelectorAll('.btn').forEach(addRipple);

  // Feature cards — click ripple
  document.querySelectorAll('.feature-card').forEach(addRipple);

  // Hero canvas
  initHeroCanvas();

  // AI tip
  initAiTipRotator();

  // Nav
  initNavToggle();
  initNavScroll();

  // Flash messages
  initFlashDismiss();

  // Smooth scroll
  initSmoothScroll();

  // Budget bars (result page)
  if (document.querySelector('.budget-fill')) {
    setTimeout(animateBudgetBars, 200);
  }

  // Page transition
  initPageTransition();

  // Feature card hover sound (subtle)
  document.querySelectorAll('.feature-card').forEach(card => {
    card.addEventListener('mouseenter', () => {
      card.style.transition = 'all 0.32s ease';
    });
  });

  // Gallery image lazy load fallback
  document.querySelectorAll('.gallery-img').forEach(img => {
    img.addEventListener('error', () => {
      img.parentElement.innerHTML = '<div style="width:100%;height:100%;background:var(--surface2);display:flex;align-items:center;justify-content:center;font-size:1.5rem">🏔</div>';
    });
  });

  // Auto-resize textarea on chat pages
  const chatInput = document.getElementById('chatInput');
  if (chatInput) {
    chatInput.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 120) + 'px';
    });
  }

  // Keyboard shortcut: / to focus chat input
  document.addEventListener('keydown', (e) => {
    if (e.key === '/' && document.activeElement.tagName !== 'INPUT' && document.activeElement.tagName !== 'TEXTAREA') {
      const chatIn = document.getElementById('chatInput');
      if (chatIn) { e.preventDefault(); chatIn.focus(); }
    }
  });

  console.log('✦ Hodophile initialized');
});
