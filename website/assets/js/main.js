/* eSupplyTech — site scripts */

// Active nav link
const path = window.location.pathname.replace(/\.html$/, '');
document.querySelectorAll('.nav-links a').forEach(a => {
  const href = a.getAttribute('href').replace(/\.html$/, '');
  if (href === path || (href !== '/' && path.startsWith(href))) {
    a.classList.add('active');
  }
});

// Mobile nav toggle
const navToggle = document.getElementById('navToggle');
const navLinks  = document.getElementById('navLinks');
if (navToggle && navLinks) {
  navToggle.addEventListener('click', () => {
    const open = navLinks.classList.toggle('open');
    navToggle.setAttribute('aria-expanded', String(open));
  });
  navLinks.querySelectorAll('a').forEach(a => {
    a.addEventListener('click', () => {
      navLinks.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    });
  });
  document.addEventListener('click', e => {
    if (!e.target.closest('.nav-inner')) {
      navLinks.classList.remove('open');
      navToggle.setAttribute('aria-expanded', 'false');
    }
  });
}

// FAQ accordion
document.querySelectorAll('.faq-q').forEach(btn => {
  btn.addEventListener('click', () => {
    const item = btn.closest('.faq-item');
    const isOpen = item.classList.contains('open');
    document.querySelectorAll('.faq-item.open').forEach(el => el.classList.remove('open'));
    if (!isOpen) item.classList.add('open');
  });
});

// Scroll reveal
if ('IntersectionObserver' in window) {
  const obs = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.classList.add('visible');
        obs.unobserve(e.target);
      }
    });
  }, { threshold: 0.08, rootMargin: '0px 0px -32px 0px' });
  document.querySelectorAll('.reveal').forEach(el => obs.observe(el));
} else {
  document.querySelectorAll('.reveal').forEach(el => el.classList.add('visible'));
}

// Spotlight on product cards (radial gradient follows cursor)
document.querySelectorAll('.product-card').forEach(card => {
  card.addEventListener('mousemove', e => {
    const r = card.getBoundingClientRect();
    card.style.setProperty('--mx', ((e.clientX - r.left) / r.width  * 100).toFixed(1) + '%');
    card.style.setProperty('--my', ((e.clientY - r.top)  / r.height * 100).toFixed(1) + '%');
  });
});

// Contact form via Formspree
const form = document.getElementById('contactForm');
if (form) {
  form.addEventListener('submit', async e => {
    e.preventDefault();
    const btn    = form.querySelector('[type=submit]');
    const status = document.getElementById('formStatus');
    const orig   = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Sending…';
    if (status) { status.textContent = ''; status.className = 'form-status' }
    try {
      const res = await fetch(form.action, {
        method: 'POST', body: new FormData(form),
        headers: { Accept: 'application/json' }
      });
      if (res.ok) {
        form.reset();
        if (status) {
          status.textContent = "Message sent — we'll get back to you within 24 hours.";
          status.className = 'form-status ok';
        }
        btn.textContent = 'Sent ✓';
      } else { throw new Error() }
    } catch {
      if (status) {
        status.textContent = 'Something went wrong. Email us directly at support@esupplytech.com.';
        status.className = 'form-status err';
      }
      btn.disabled = false;
      btn.textContent = orig;
    }
  });
}

// Waitlist form (TheBraid Flow)
const waitlistForm = document.getElementById('waitlistForm');
if (waitlistForm) {
  waitlistForm.addEventListener('submit', async e => {
    e.preventDefault();
    const btn    = waitlistForm.querySelector('[type=submit]');
    const status = document.getElementById('waitlistStatus');
    btn.disabled = true; btn.textContent = 'Joining…';
    try {
      const res = await fetch(waitlistForm.action, {
        method: 'POST', body: new FormData(waitlistForm),
        headers: { Accept: 'application/json' }
      });
      if (res.ok) {
        waitlistForm.reset();
        if (status) {
          status.textContent = "You're on the list! We'll email you when TheBraid Flow launches.";
          status.className = 'form-status ok';
        }
        btn.textContent = "You're in ✓";
      } else { throw new Error() }
    } catch {
      if (status) {
        status.textContent = 'Something went wrong — email us at support@esupplytech.com to join manually.';
        status.className = 'form-status err';
      }
      btn.disabled = false; btn.textContent = 'Join Waitlist';
    }
  });
}
