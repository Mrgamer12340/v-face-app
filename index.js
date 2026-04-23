/* ═══════════════════════════════════════════════════
   MAIN.JS — Complete Site Functionality
   Features:
   1. Smooth Scroll + Active Nav Links
   2. Mobile Hamburger Menu
   3. Scroll Reveal Animations
   4. Counter Animation (Stats)
   5. Sticky Nav Shadow on Scroll
   6. Back to Top Button
   7. Form Validation
   8. Typewriter Effect (Hero)
═══════════════════════════════════════════════════ */

document.addEventListener('DOMContentLoaded', () => {

  /* ─────────────────────────────────────────
     1. STICKY NAV SHADOW ON SCROLL
  ───────────────────────────────────────── */
  const nav = document.querySelector('nav');

  window.addEventListener('scroll', () => {
    if (window.scrollY > 20) {
      nav.style.boxShadow = '0 4px 32px rgba(45, 122, 106, 0.12)';
      nav.style.borderBottomColor = 'rgba(91, 193, 172, 0.25)';
    } else {
      nav.style.boxShadow = '0 1px 0 rgba(91,193,172,0.12), 0 4px 24px rgba(45,122,106,0.06)';
      nav.style.borderBottomColor = 'rgba(255,255,255,0.8)';
    }
  }, { passive: true });


  /* ─────────────────────────────────────────
     2. SMOOTH SCROLL + ACTIVE NAV LINKS
  ───────────────────────────────────────── */
  const navLinks = document.querySelectorAll('.nav-links a[href^="#"]');
  const sections = document.querySelectorAll('section[id]');

  // Smooth scroll
  navLinks.forEach(link => {
    link.addEventListener('click', e => {
      e.preventDefault();
      const target = document.querySelector(link.getAttribute('href'));
      if (!target) return;
      const offset = 80;
      const top = target.getBoundingClientRect().top + window.scrollY - offset;
      window.scrollTo({ top, behavior: 'smooth' });

      // Close mobile menu if open
      navMenu.classList.remove('open');
      hamburger.classList.remove('open');
      document.body.style.overflow = '';
    });
  });

  // Active nav link on scroll
  const observerNav = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        navLinks.forEach(link => {
          link.classList.remove('active');
          if (link.getAttribute('href') === `#${entry.target.id}`) {
            link.classList.add('active');
          }
        });
      }
    });
  }, { rootMargin: '-40% 0px -55% 0px' });

  sections.forEach(sec => observerNav.observe(sec));

  // Active nav styles (injected once)
  const navStyle = document.createElement('style');
  navStyle.textContent = `
    .nav-links a.active {
      color: var(--cyan) !important;
      font-weight: 600 !important;
    }
    .nav-links a.active::after {
      content: '';
      display: block;
      width: 100%;
      height: 2px;
      background: var(--cyan-mid, #5bc1ac);
      border-radius: 2px;
      margin-top: 2px;
    }
  `;
  document.head.appendChild(navStyle);


  /* ─────────────────────────────────────────
     3. MOBILE HAMBURGER MENU
  ───────────────────────────────────────── */

  // Create hamburger button
  const hamburger = document.createElement('button');
  hamburger.className = 'hamburger';
  hamburger.setAttribute('aria-label', 'Toggle menu');
  hamburger.innerHTML = `
    <span></span>
    <span></span>
    <span></span>
  `;
  nav.appendChild(hamburger);

  // Create mobile menu overlay
  const navMenu = document.createElement('div');
  navMenu.className = 'mobile-nav';
  navMenu.innerHTML = `
    <ul>
      ${Array.from(navLinks).map(l =>
        `<li><a href="${l.getAttribute('href')}">${l.textContent}</a></li>`
      ).join('')}
    </ul>
  `;
  document.body.appendChild(navMenu);

  hamburger.addEventListener('click', () => {
    const isOpen = navMenu.classList.toggle('open');
    hamburger.classList.toggle('open');
    document.body.style.overflow = isOpen ? 'hidden' : '';
  });

  // Close on outside click
  document.addEventListener('click', e => {
    if (!nav.contains(e.target) && !navMenu.contains(e.target)) {
      navMenu.classList.remove('open');
      hamburger.classList.remove('open');
      document.body.style.overflow = '';
    }
  });

  // Hamburger + Mobile Nav styles
  const mobileStyle = document.createElement('style');
  mobileStyle.textContent = `
    .hamburger {
      display: none;
      flex-direction: column;
      gap: 5px;
      background: transparent;
      border: none;
      cursor: pointer;
      padding: 6px;
      z-index: 200;
    }
    .hamburger span {
      display: block;
      width: 24px;
      height: 2px;
      background: var(--cyan, #2d7a6a);
      border-radius: 2px;
      transition: all 0.3s ease;
      transform-origin: center;
    }
    .hamburger.open span:nth-child(1) { transform: translateY(7px) rotate(45deg); }
    .hamburger.open span:nth-child(2) { opacity: 0; transform: scaleX(0); }
    .hamburger.open span:nth-child(3) { transform: translateY(-7px) rotate(-45deg); }

    .mobile-nav {
      position: fixed;
      top: 68px;
      left: 0; right: 0;
      background: rgba(232, 246, 243, 0.96);
      backdrop-filter: blur(24px);
      -webkit-backdrop-filter: blur(24px);
      border-bottom: 1px solid rgba(91,193,172,0.2);
      padding: 1.5rem 5%;
      z-index: 99;
      transform: translateY(-110%);
      opacity: 0;
      transition: transform 0.35s cubic-bezier(0.4,0,0.2,1), opacity 0.3s ease;
      box-shadow: 0 8px 32px rgba(45,122,106,0.12);
    }
    .mobile-nav.open {
      transform: translateY(0);
      opacity: 1;
    }
    .mobile-nav ul {
      list-style: none;
      display: flex;
      flex-direction: column;
      gap: 0;
    }
    .mobile-nav ul a {
      display: block;
      padding: 14px 0;
      color: var(--text-muted, rgba(18,65,55,0.55));
      text-decoration: none;
      font-size: 0.9rem;
      font-weight: 500;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(91,193,172,0.1);
      transition: color 0.2s;
    }
    .mobile-nav ul li:last-child a { border-bottom: none; }
    .mobile-nav ul a:hover { color: var(--cyan, #2d7a6a); }

    @media (max-width: 768px) {
      .hamburger { display: flex; }
      nav .nav-links { display: none !important; }
      nav .nav-cta { display: none; }
    }
  `;
  document.head.appendChild(mobileStyle);


  /* ─────────────────────────────────────────
     4. SCROLL REVEAL ANIMATIONS
  ───────────────────────────────────────── */
  const revealEls = document.querySelectorAll('.reveal');

  const revealObserver = new IntersectionObserver(entries => {
    entries.forEach((entry, i) => {
      if (entry.isIntersecting) {
        // stagger delay based on sibling index
        const siblings = Array.from(entry.target.parentElement?.children || []);
        const idx = siblings.indexOf(entry.target);
        const delay = Math.min(idx * 80, 400);
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, delay);
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: '0px 0px -40px 0px' });

  revealEls.forEach(el => revealObserver.observe(el));


  /* ─────────────────────────────────────────
     5. COUNTER ANIMATION (STATS)
  ───────────────────────────────────────── */
  const statNumbers = document.querySelectorAll('.stat-number');

  function animateCounter(el) {
    // Parse the raw text — handles "98%", "10K+", "4.9★", "150+"
    const raw = el.textContent.trim();
    const match = raw.match(/([\d.]+)/);
    if (!match) return;

    const target   = parseFloat(match[1]);
    const isFloat  = match[1].includes('.');
    const prefix   = raw.slice(0, raw.indexOf(match[1]));
    const suffix   = raw.slice(raw.indexOf(match[1]) + match[1].length);
    const duration = 1800;
    const start    = performance.now();

    function step(now) {
      const elapsed  = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const ease     = 1 - Math.pow(1 - progress, 3);
      const current  = isFloat
        ? (ease * target).toFixed(1)
        : Math.floor(ease * target);

      el.textContent = `${prefix}${current}${suffix}`;
      if (progress < 1) requestAnimationFrame(step);
    }

    requestAnimationFrame(step);
  }

  const counterObserver = new IntersectionObserver(entries => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        animateCounter(entry.target);
        counterObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.5 });

  statNumbers.forEach(el => counterObserver.observe(el));


  /* ─────────────────────────────────────────
     6. BACK TO TOP BUTTON
  ───────────────────────────────────────── */
  const btt = document.createElement('button');
  btt.className = 'back-to-top';
  btt.setAttribute('aria-label', 'Back to top');
  btt.innerHTML = `
    <svg width="18" height="18" viewBox="0 0 18 18" fill="none">
      <path d="M9 14V4M4 9l5-5 5 5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>
  `;
  document.body.appendChild(btt);

  const bttStyle = document.createElement('style');
  bttStyle.textContent = `
    .back-to-top {
      position: fixed;
      bottom: 2rem;
      right: 2rem;
      width: 46px; height: 46px;
      border-radius: 50%;
      background: rgba(255,255,255,0.75);
      backdrop-filter: blur(16px);
      -webkit-backdrop-filter: blur(16px);
      border: 1px solid rgba(91,193,172,0.4);
      color: var(--cyan, #2d7a6a);
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 20px rgba(45,122,106,0.15), inset 0 1px 0 white;
      opacity: 0;
      transform: translateY(16px) scale(0.9);
      transition: opacity 0.3s ease, transform 0.3s ease, box-shadow 0.25s ease;
      z-index: 999;
      pointer-events: none;
    }
    .back-to-top.visible {
      opacity: 1;
      transform: translateY(0) scale(1);
      pointer-events: all;
    }
    .back-to-top:hover {
      background: rgba(255,255,255,0.95);
      box-shadow: 0 8px 28px rgba(45,122,106,0.22), inset 0 1px 0 white;
      transform: translateY(-2px) scale(1.05);
    }
    .back-to-top:active { transform: scale(0.96); }
  `;
  document.head.appendChild(bttStyle);

  window.addEventListener('scroll', () => {
    btt.classList.toggle('visible', window.scrollY > 400);
  }, { passive: true });

  btt.addEventListener('click', () => {
    window.scrollTo({ top: 0, behavior: 'smooth' });
  });


  /* ─────────────────────────────────────────
     7. FORM VALIDATION
     Targets any form on the page with
     class="validate-form"
     Supports: required, email, tel, minlength
  ───────────────────────────────────────── */
  const forms = document.querySelectorAll('.validate-form');

  // Inject form styles
  const formStyle = document.createElement('style');
  formStyle.textContent = `
    .field-wrap { position: relative; margin-bottom: 1.2rem; }
    .field-wrap input,
    .field-wrap textarea {
      width: 100%;
      padding: 12px 16px;
      background: rgba(255,255,255,0.65);
      backdrop-filter: blur(12px);
      border: 1px solid rgba(91,193,172,0.3);
      border-radius: 10px;
      font-family: var(--font-body, 'DM Sans', sans-serif);
      font-size: 0.9rem;
      color: var(--text, #0d2b24);
      transition: border-color 0.25s, box-shadow 0.25s;
      outline: none;
      box-shadow: inset 0 1px 0 rgba(255,255,255,0.8);
    }
    .field-wrap input:focus,
    .field-wrap textarea:focus {
      border-color: rgba(91,193,172,0.6);
      box-shadow: 0 0 0 3px rgba(91,193,172,0.12), inset 0 1px 0 rgba(255,255,255,0.8);
    }
    .field-wrap input.error,
    .field-wrap textarea.error {
      border-color: rgba(220,60,60,0.5);
      box-shadow: 0 0 0 3px rgba(220,60,60,0.08);
    }
    .field-wrap input.valid,
    .field-wrap textarea.valid {
      border-color: rgba(45,122,106,0.5);
    }
    .field-error {
      display: none;
      font-size: 0.76rem;
      color: #c23b3b;
      margin-top: 5px;
      padding-left: 4px;
    }
    .field-wrap.show-error .field-error { display: block; }

    .form-success {
      text-align: center;
      padding: 2rem;
      font-family: var(--font-head, 'Oxanium', sans-serif);
      color: var(--cyan, #2d7a6a);
      font-size: 1rem;
      font-weight: 600;
      animation: fade-up 0.5s ease both;
    }
    .form-success svg { margin-bottom: 0.75rem; display: block; margin-left: auto; margin-right: auto; }

    .btn-submit-loading {
      opacity: 0.7;
      pointer-events: none;
      cursor: not-allowed;
    }
  `;
  document.head.appendChild(formStyle);

  function validateField(input) {
    const wrap  = input.closest('.field-wrap');
    const error = wrap?.querySelector('.field-error');
    const val   = input.value.trim();
    let msg = '';

    if (input.hasAttribute('required') && !val) {
      msg = 'Ye field zaruri hai.';
    } else if (input.type === 'email' && val && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(val)) {
      msg = 'Sahi email daalein.';
    } else if (input.type === 'tel' && val && !/^[\d\s\+\-\(\)]{7,15}$/.test(val)) {
      msg = 'Sahi phone number daalein.';
    } else if (input.hasAttribute('minlength') && val.length < +input.getAttribute('minlength')) {
      msg = `Kam az kam ${input.getAttribute('minlength')} characters chahiye.`;
    }

    if (wrap) {
      wrap.classList.toggle('show-error', !!msg);
      input.classList.toggle('error', !!msg);
      input.classList.toggle('valid', !msg && !!val);
      if (error) error.textContent = msg;
    }
    return !msg;
  }

  forms.forEach(form => {
    const inputs = form.querySelectorAll('input, textarea');

    // Wrap inputs in .field-wrap if not already
    inputs.forEach(input => {
      if (!input.closest('.field-wrap')) {
        const wrap = document.createElement('div');
        wrap.className = 'field-wrap';
        input.parentNode.insertBefore(wrap, input);
        wrap.appendChild(input);

        const errSpan = document.createElement('span');
        errSpan.className = 'field-error';
        wrap.appendChild(errSpan);
      }
    });

    // Live validation on blur
    inputs.forEach(input => {
      input.addEventListener('blur', () => validateField(input));
      input.addEventListener('input', () => {
        if (input.classList.contains('error')) validateField(input);
      });
    });

    form.addEventListener('submit', e => {
      e.preventDefault();
      let valid = true;
      inputs.forEach(input => { if (!validateField(input)) valid = false; });

      if (!valid) return;

      const submitBtn = form.querySelector('[type="submit"]');
      if (submitBtn) {
        submitBtn.classList.add('btn-submit-loading');
        submitBtn.textContent = 'Bhej raha hai...';
      }

      // Simulate async submit (replace with real API call)
      setTimeout(() => {
        form.innerHTML = `
          <div class="form-success">
            <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
              <circle cx="24" cy="24" r="22" stroke="#5bc1ac" stroke-width="2" fill="rgba(91,193,172,0.1)"/>
              <path d="M14 24l7 7 13-13" stroke="#5bc1ac" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
            </svg>
            Shukriya! Apka paigham mil gaya. Jald hi rabta karenge.
          </div>
        `;
      }, 1200);
    });
  });


  /* ─────────────────────────────────────────
     8. TYPEWRITER EFFECT (HERO)
     Targets element with id="typewriter"
     or class="typewriter"
     Add data-words='["word1","word2"]' attribute
  ───────────────────────────────────────── */
  const typeEl = document.querySelector('#typewriter, .typewriter');

  if (typeEl) {
    let words = ['Intelligent', 'Accurate', 'Powerful'];
    try {
      const attr = typeEl.getAttribute('data-words');
      if (attr) words = JSON.parse(attr);
    } catch(e) {}

    let wordIdx  = 0;
    let charIdx  = 0;
    let deleting = false;
    let paused   = false;

    // Cursor style
    const cursorStyle = document.createElement('style');
    cursorStyle.textContent = `
      .typewriter-cursor {
        display: inline-block;
        width: 3px;
        height: 1em;
        background: var(--cyan-mid, #5bc1ac);
        margin-left: 3px;
        vertical-align: text-bottom;
        border-radius: 2px;
        animation: blink-cursor 0.9s step-end infinite;
      }
      @keyframes blink-cursor {
        0%, 100% { opacity: 1; }
        50%       { opacity: 0; }
      }
    `;
    document.head.appendChild(cursorStyle);

    // Wrap text + add cursor span
    const originalText = typeEl.innerHTML;
    const textNode = document.createElement('span');
    textNode.className = 'typewriter-text';
    const cursor   = document.createElement('span');
    cursor.className = 'typewriter-cursor';

    typeEl.innerHTML = '';
    typeEl.appendChild(textNode);
    typeEl.appendChild(cursor);

    function type() {
      if (paused) return;
      const word = words[wordIdx];

      if (!deleting) {
        textNode.textContent = word.slice(0, ++charIdx);
        if (charIdx === word.length) {
          paused = true;
          setTimeout(() => { paused = false; deleting = true; requestAnimationFrame(loop); }, 1800);
          return;
        }
      } else {
        textNode.textContent = word.slice(0, --charIdx);
        if (charIdx === 0) {
          deleting = false;
          wordIdx  = (wordIdx + 1) % words.length;
          paused   = true;
          setTimeout(() => { paused = false; requestAnimationFrame(loop); }, 400);
          return;
        }
      }
      requestAnimationFrame(loop);
    }

    let lastTime = 0;
    function loop(timestamp) {
      const speed = deleting ? 60 : 100;
      if (timestamp - lastTime >= speed) {
        lastTime = timestamp;
        type();
      } else {
        requestAnimationFrame(loop);
      }
    }

    // Start after a short delay
    setTimeout(() => requestAnimationFrame(loop), 800);
  }

}); // end DOMContentLoaded
