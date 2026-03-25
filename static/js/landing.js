/* ================================================================
   Akobato — Landing Page JavaScript
   Particle canvas · Glitch · Typewriter · 3D tilt · PWA install
   ================================================================ */

/* ── Particle Canvas ─────────────────────────────────────────── */
(function initParticles() {
  const canvas = document.getElementById('particle-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  let W, H, particles = [], mouse = { x: -9999, y: -9999 };
  const COUNT  = 80;
  const MAX_DIST = 130;
  const CYAN = '5,217,232';
  const PINK = '255,42,109';

  function resize() {
    W = canvas.width  = window.innerWidth;
    H = canvas.height = window.innerHeight;
  }
  resize();
  window.addEventListener('resize', resize);

  window.addEventListener('mousemove', e => {
    mouse.x = e.clientX;
    mouse.y = e.clientY;
  });

  function rand(min, max) { return Math.random() * (max - min) + min; }

  function createParticle() {
    return {
      x:  rand(0, W),
      y:  rand(0, H),
      vx: rand(-0.3, 0.3),
      vy: rand(-0.3, 0.3),
      r:  rand(1, 2.5),
      color: Math.random() > 0.5 ? CYAN : PINK,
      opacity: rand(0.3, 0.8),
    };
  }

  for (let i = 0; i < COUNT; i++) particles.push(createParticle());

  function draw() {
    ctx.clearRect(0, 0, W, H);

    // faint neon grid
    ctx.strokeStyle = 'rgba(5,217,232,0.03)';
    ctx.lineWidth = 1;
    const step = 60;
    for (let x = 0; x < W; x += step) {
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, H); ctx.stroke();
    }
    for (let y = 0; y < H; y += step) {
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(W, y); ctx.stroke();
    }

    // connect & draw
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];

      // mouse repulsion
      const dx = p.x - mouse.x, dy = p.y - mouse.y;
      const dm = Math.sqrt(dx * dx + dy * dy);
      if (dm < 120) {
        const force = (120 - dm) / 120;
        p.vx += (dx / dm) * force * 0.4;
        p.vy += (dy / dm) * force * 0.4;
      }

      // friction & move
      p.vx *= 0.98;
      p.vy *= 0.98;
      p.x += p.vx;
      p.y += p.vy;

      // wrap
      if (p.x < 0) p.x = W; if (p.x > W) p.x = 0;
      if (p.y < 0) p.y = H; if (p.y > H) p.y = 0;

      // dot
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(${p.color},${p.opacity})`;
      ctx.fill();

      // connect nearby
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j];
        const ex = p.x - q.x, ey = p.y - q.y;
        const ed = Math.sqrt(ex * ex + ey * ey);
        if (ed < MAX_DIST) {
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          const alpha = (1 - ed / MAX_DIST) * 0.25;
          ctx.strokeStyle = `rgba(${p.color},${alpha})`;
          ctx.lineWidth = 0.8;
          ctx.stroke();
        }
      }
    }

    requestAnimationFrame(draw);
  }
  draw();
})();


/* ── Typewriter ──────────────────────────────────────────────── */
(function initTypewriter() {
  const el = document.getElementById('typewriter-text');
  if (!el) return;

  const phrases = [
    '60 Seconds. 1 Hot Take.',
    'Real-Time 1v1 Debate.',
    'The AI Judge Has No Mercy.',
    'Write Like a Human. Win Big.',
    'No ChatGPT. No Excuses.',
  ];

  let pi = 0, ci = 0, deleting = false, pause = 0;

  function tick() {
    const phrase = phrases[pi];
    if (pause > 0) { pause--; setTimeout(tick, 50); return; }

    if (!deleting) {
      el.textContent = phrase.slice(0, ++ci);
      if (ci === phrase.length) { pause = 40; deleting = true; }
      setTimeout(tick, 60);
    } else {
      el.textContent = phrase.slice(0, --ci);
      if (ci === 0) { deleting = false; pi = (pi + 1) % phrases.length; pause = 8; }
      setTimeout(tick, 30);
    }
  }
  setTimeout(tick, 800);
})();


/* ── Hero Countdown ──────────────────────────────────────────── */
(function initHeroTimer() {
  const el = document.getElementById('hero-timer');
  if (!el) return;
  let t = 60;
  setInterval(() => {
    t--;
    if (t < 0) t = 60;
    el.textContent = t < 10 ? '0' + t : t;
    el.className = 'hero-timer' + (t <= 10 ? ' danger' : '');
  }, 1000);
})();


/* ── 3D Card Tilt ────────────────────────────────────────────── */
(function initCardTilt() {
  document.querySelectorAll('.arcade-card').forEach(card => {
    card.addEventListener('mousemove', e => {
      const rect = card.getBoundingClientRect();
      const cx   = rect.left + rect.width  / 2;
      const cy   = rect.top  + rect.height / 2;
      const rx   = ((e.clientY - cy) / (rect.height / 2)) * -10;
      const ry   = ((e.clientX - cx) / (rect.width  / 2)) *  10;
      card.style.transform = `perspective(600px) rotateX(${rx}deg) rotateY(${ry}deg) translateZ(6px)`;
    });
    card.addEventListener('mouseleave', () => {
      card.style.transform = 'perspective(600px) rotateX(0) rotateY(0) translateZ(0)';
    });
  });
})();


/* ── Terminal Roast Typer ────────────────────────────────────── */
(function initTerminalRoast() {
  const el = document.getElementById('terminal-roast');
  if (!el) return;

  const roasts = [
    '"Your argument reads like a LinkedIn post written by a malfunctioning algorithm. Your opponent said \'Nah fam\' and somehow won. Respect the 60 seconds next time."',
    '"Congratulations — you discovered every buzzword in existence and strung them together. \'Synergistic paradigm shift\' lost to someone who typed \'bro just think about it\'."',
    '"The AI judge fell asleep twice reading your submission. Your opponent\'s three words were more convincing than your five paragraphs of corporate fluff."',
  ];

  let ri = 0;

  function typeRoast() {
    el.textContent = '';
    const roast = roasts[ri % roasts.length];
    let ci = 0;
    el.classList.add('t-typing');

    const t = setInterval(() => {
      el.textContent = roast.slice(0, ++ci);
      if (ci === roast.length) {
        clearInterval(t);
        el.classList.remove('t-typing');
        ri++;
        setTimeout(typeRoast, 5000);
      }
    }, 22);
  }

  // start when terminal scrolls into view
  const observer = new IntersectionObserver(entries => {
    if (entries[0].isIntersecting) {
      observer.disconnect();
      setTimeout(typeRoast, 500);
    }
  }, { threshold: 0.3 });

  observer.observe(el.closest('.terminal-wrap') || el);
})();


/* ── Footer Ticker ───────────────────────────────────────────── */
(function initTicker() {
  const track = document.getElementById('ticker');
  if (!track) return;

  const items = [
    '⚔ REAL-TIME DEBATES', '🔥 AI JUDGE', '⏱ 60 SECONDS',
    '📰 LIVE NEWS PROMPTS', '🏆 HALL OF FAME', '🚫 NO AI SLOP',
    '🎮 FREE DAILY MATCH', '🤖 ROAST OR BE ROASTED',
  ];

  const html = items.map(i =>
    `<span>${i}</span><span class="sep">◆</span>`
  ).join('');

  // duplicate for seamless loop
  track.innerHTML = html + html;
})();


/* ── Scroll Reveal ───────────────────────────────────────────── */
(function initReveal() {
  const observer = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (e.isIntersecting) e.target.classList.add('visible');
    });
  }, { threshold: 0.12 });

  document.querySelectorAll('.reveal').forEach(el => observer.observe(el));
})();


/* ── PWA Install ─────────────────────────────────────────────── */
(function initPWA() {
  // Register service worker
  if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    });
  }

  let deferredPrompt = null;
  const banner    = document.getElementById('install-banner');
  const installBtn = document.getElementById('install-btn');
  const dismissBtn = document.getElementById('dismiss-btn');

  window.addEventListener('beforeinstallprompt', e => {
    e.preventDefault();
    deferredPrompt = e;
    setTimeout(() => banner && banner.classList.add('show'), 3000);
  });

  installBtn && installBtn.addEventListener('click', async () => {
    if (!deferredPrompt) return;
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') banner.classList.remove('show');
    deferredPrompt = null;
  });

  dismissBtn && dismissBtn.addEventListener('click', () => {
    banner && banner.classList.remove('show');
    deferredPrompt = null;
  });

  window.addEventListener('appinstalled', () => {
    banner && banner.classList.remove('show');
  });
})();
