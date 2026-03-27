from fasthtml.common import *


def login_page(error: str = "") -> FT:
    return Div(
        # Particle canvas
        Canvas(id="login-canvas"),
        # Scanlines
        Div(cls="login-scanlines"),

        Div(
            # Auth-required label
            Div("// AUTHENTICATION REQUIRED", cls="login-sys-label"),

            # Card with corner brackets
            Div(
                # Corner brackets (decorative)
                Div(cls="login-corner tl"),
                Div(cls="login-corner tr"),
                Div(cls="login-corner bl"),
                Div(cls="login-corner br"),

                # Logo
                Div(
                    Img(src="/static/img/logo.svg", height="44", alt="Akobato"),
                    cls="login-logo",
                ),

                # Blinking player tag
                Div("▶ PLAYER 1 READY", cls="login-player-tag"),

                H2("Enter the Arena", cls="login-title"),
                P(
                    "Sign in with Google to claim your place in the debate.",
                    cls="login-sub",
                ),

                # Error
                P(f"⚠ {error}", cls="login-error") if error else "",

                # Google button
                A(
                    Span(
                        # Official Google "G" logo colours
                        NotStr("""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="20" height="20">
  <path fill="#EA4335" d="M24 9.5c3.14 0 5.95 1.08 8.17 2.86l6.08-6.08C34.5 3.04 29.54 1 24 1 14.82 1 7.07 6.48 3.73 14.22l7.08 5.51C12.56 13.49 17.83 9.5 24 9.5z"/>
  <path fill="#4285F4" d="M46.52 24.5c0-1.64-.15-3.22-.43-4.75H24v9h12.7c-.55 2.96-2.2 5.47-4.68 7.16l7.19 5.59C43.44 37.27 46.52 31.33 46.52 24.5z"/>
  <path fill="#FBBC05" d="M10.81 28.27A14.6 14.6 0 0 1 9.5 24c0-1.49.26-2.93.71-4.27l-7.08-5.51A23.93 23.93 0 0 0 0 24c0 3.87.93 7.53 2.57 10.76l8.24-6.49z"/>
  <path fill="#34A853" d="M24 47c5.54 0 10.19-1.84 13.59-4.99l-7.19-5.59c-1.89 1.27-4.3 2.02-6.4 2.02-6.17 0-11.44-4-13.19-9.17l-8.24 6.49C7.07 41.52 14.82 47 24 47z"/>
  <path fill="none" d="M0 0h48v48H0z"/>
</svg>"""),
                        cls="login-google-icon",
                    ),
                    Span("Sign in with Google", cls="login-google-text"),
                    href="/auth/login",
                    cls="login-google-btn",
                ),

                # Stat bar
                Div(
                    Div(
                        Span("FREE", cls="login-stat-val"),
                        Span("DAILY MATCH", cls="login-stat-lbl"),
                    ),
                    Div(cls="login-stat-sep"),
                    Div(
                        Span("AI", cls="login-stat-val"),
                        Span("JUDGE", cls="login-stat-lbl"),
                    ),
                    Div(cls="login-stat-sep"),
                    Div(
                        Span("60s", cls="login-stat-val"),
                        Span("PER ROUND", cls="login-stat-lbl"),
                    ),
                    cls="login-stats",
                ),

                Div(cls="login-divider"),

                P(
                    "Play fair. Argue harder. Accept the AI Judge's roasts gracefully.",
                    cls="login-fine-print",
                ),

                A("← Back to home", href="/", cls="login-back"),

                cls="login-card",
            ),

            cls="login-wrap",
        ),

        # ── Sound effects ─────────────────────────────────────────────────────
        Script("""
(function(){
  // Boot sound once — plays when user first touches the login card
  var booted = false;
  function tryBoot() {
    if (booted || !window.SFX) return;
    booted = true;
    SFX.boot();
  }
  var card = document.querySelector('.login-card');
  if (card) {
    card.addEventListener('mouseenter', tryBoot, { once: true });
    card.addEventListener('touchstart', tryBoot, { passive: true, once: true });
  }
  document.addEventListener('touchstart', tryBoot, { passive: true, once: true });
})();
"""),

        Script("""
(function(){
  // Mini particle canvas for login bg
  const c = document.getElementById('login-canvas');
  if(!c) return;
  const ctx = c.getContext('2d');
  let W, H, pts = [];
  function resize(){ W=c.width=window.innerWidth; H=c.height=window.innerHeight; }
  resize();
  window.addEventListener('resize', resize);
  for(let i=0;i<50;i++) pts.push({
    x:Math.random()*1e4%window.innerWidth,
    y:Math.random()*1e4%window.innerHeight,
    vx:(Math.random()-.5)*.25, vy:(Math.random()-.5)*.25,
    r:Math.random()*1.8+.6,
    col: Math.random()>.5 ? '5,217,232' : '255,42,109'
  });
  function draw(){
    ctx.clearRect(0,0,W,H);
    // grid
    ctx.strokeStyle='rgba(5,217,232,0.03)'; ctx.lineWidth=1;
    for(let x=0;x<W;x+=60){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,H);ctx.stroke();}
    for(let y=0;y<H;y+=60){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(W,y);ctx.stroke();}
    pts.forEach(p=>{
      p.x+=p.vx; p.y+=p.vy;
      if(p.x<0)p.x=W; if(p.x>W)p.x=0;
      if(p.y<0)p.y=H; if(p.y>H)p.y=0;
      ctx.beginPath();ctx.arc(p.x,p.y,p.r,0,Math.PI*2);
      ctx.fillStyle=`rgba(${p.col},0.5)`;ctx.fill();
    });
    requestAnimationFrame(draw);
  }
  draw();
})();
"""),
    )
