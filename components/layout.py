from fasthtml.common import *


def layout(
    *content,
    title: str = "Akobato ⚔️",
    user: str | None = None,
    alias: str | None = None,
    tokens: int | None = None,
    full_width: bool = False,
    extra_css: str | None = None,
    body_cls: str = "",
):
    """
    Base page shell.
    - user       : logged-in username (real, used for avatar/routes)
    - alias      : display name shown in nav (falls back to user)
    - full_width : skips the .container wrapper on <main> (landing page)
    - extra_css  : path to an additional stylesheet
    - body_cls   : extra class(es) on <body>
    """
    display = alias or user
    if user:
        nav_user = A(
            Div(
                Img(src=f"/avatar/{user}", width="24", height="24",
                    alt=display, style="display:block;border-radius:50%;image-rendering:pixelated"),
                cls="nav-avatar",
            ),
            Span(display, cls="nav-username"),
            href="/profile",
            cls="nav-user",
        )
        nav_action = Form(
            Button(
                Span("⏻", cls="btn-signout-icon"),
                Span("Sign out", cls="btn-signout-text"),
                type="submit",
                cls="btn-signout",
            ),
            action="/auth/logout",
            method="post",
        )
        nav_right = Div(
            A("Dashboard",    href="/dashboard",   cls="nav-link"),
            A("Hall of Fame", href="/leaderboard", cls="nav-link"),
            A("Burn Board",   href="/roast",       cls="nav-link"),
            A("Profile",      href="/profile",     cls="nav-link"),
            nav_user,
            nav_action,
            cls="nav-right",
        )
        mobile_menu = Div(
            A("Dashboard",    href="/dashboard",   cls="nav-link"),
            A("Hall of Fame", href="/leaderboard", cls="nav-link"),
            A("Burn Board",   href="/roast",       cls="nav-link"),
            A("Profile",      href="/profile",     cls="nav-link"),
            nav_action,
            cls="nav-mobile-menu",
            id="nav-mobile-menu",
        )
        # Bottom sticky energy bar (only when tokens are known)
        _tok = tokens if tokens is not None else 5

        bottom_bar = Div(
            Div(
                # Left — energy status
                Div(
                    Span("⚡", cls="bbar-icon"),
                    Div(
                        Div(
                            Span("ENERGY", cls="bbar-label"),
                            Span(f"{_tok} / 5", cls="bbar-count"),
                            cls="bbar-row",
                        ),
                        Div(
                            *[Span(cls=f"bbar-pip {'bbar-pip--on' if i < _tok else ''}") for i in range(5)],
                            cls="bbar-pips",
                        ),
                        cls="bbar-info",
                    ),
                    cls="bbar-left",
                ),
                # Divider
                Span(cls="bbar-divider"),
                # Right — add energy button
                A(
                    Span("＋", cls="bbar-add-icon"),
                    Span("ADD ENERGY", cls="bbar-add-label"),
                    href="/play",
                    cls="bbar-add-btn",
                ),
                cls="bbar-inner",
            ),
            cls=f"bottom-bar {'bottom-bar--empty' if _tok == 0 else ''}",
        ) if tokens is not None else ()
    else:
        nav_right = Div(
            A("Hall of Fame", href="/leaderboard", cls="nav-link"),
            A("Burn Board",   href="/roast",       cls="nav-link"),
            A("Sign in", href="/login", cls="nav-signin"),
            cls="nav-right",
        )
        mobile_menu = Div(
            A("Hall of Fame", href="/leaderboard", cls="nav-link"),
            A("Burn Board",   href="/roast",       cls="nav-link"),
            A("Sign in", href="/login", cls="nav-signin nav-signin--mobile"),
            cls="nav-mobile-menu",
            id="nav-mobile-menu",
        )
        bottom_bar = ()

    extra = (Link(rel="stylesheet", href=extra_css),) if extra_css else ()

    pwa_tags = (
        Link(rel="icon", href="/static/img/favicon.svg", type="image/svg+xml"),
        Link(rel="manifest", href="/static/manifest.json"),
        Meta(name="theme-color", content="#05D9E8"),
        Meta(name="apple-mobile-web-app-capable", content="yes"),
        Meta(name="apple-mobile-web-app-status-bar-style", content="black-translucent"),
        Meta(name="apple-mobile-web-app-title", content="Akobato"),
        Link(rel="apple-touch-icon", href="/static/img/icon.svg"),
        Script("""
if('serviceWorker' in navigator){
  window.addEventListener('load',()=>navigator.serviceWorker.register('/sw.js').catch(()=>{}));
}
"""),
    )

    return (
        Title(title),
        *pwa_tags,
        *extra,
        # ── Top progress bar (shown on every HTMX request) ────────────────
        Div(id="htmx-progress"),
        # ── Page-load overlay (fades out once DOM is ready) ───────────────
        Div(
            Div(cls="page-loader-ring"),
            Span("LOADING", cls="page-loader-text"),
            id="page-loader",
        ),
        Script("""
(function(){
  // Dismiss page-load overlay
  var loader = document.getElementById('page-loader');
  if(loader){
    window.addEventListener('load', function(){
      loader.classList.add('hidden');
      setTimeout(function(){ loader.style.display='none'; }, 450);
    });
  }

  // HTMX top progress bar
  var bar = document.getElementById('htmx-progress');
  if(bar){
    document.addEventListener('htmx:beforeRequest', function(){ bar.classList.add('htmx-loading'); });
    document.addEventListener('htmx:afterRequest',  function(){ bar.classList.remove('htmx-loading'); });
  }
})();
"""),
        Header(
            Nav(
                A(
                    Img(src="/static/img/logo.svg", height="32", alt="Akobato",
                        style="display:block"),
                    href="/" if not user else "/dashboard",
                    cls="brand",
                ),
                nav_right,
                Button(
                    Span(cls="ham-line"),
                    Span(cls="ham-line"),
                    Span(cls="ham-line"),
                    cls="nav-hamburger",
                    id="nav-hamburger",
                    aria_label="Toggle menu",
                    type="button",
                ),
                cls="container nav-bar",
            ),
            mobile_menu,
            cls="site-header",
        ),
        Script("""
(function(){
  var btn  = document.getElementById('nav-hamburger');
  var menu = document.getElementById('nav-mobile-menu');
  if(btn && menu){
    btn.addEventListener('click', function(){
      var open = menu.classList.toggle('nav-mobile-menu--open');
      btn.classList.toggle('nav-hamburger--open', open);
    });
    document.addEventListener('click', function(e){
      if(!btn.contains(e.target) && !menu.contains(e.target)){
        menu.classList.remove('nav-mobile-menu--open');
        btn.classList.remove('nav-hamburger--open');
      }
    });
  }
})();
"""),
        Main(*content, cls=("has-bottom-bar" if user else "") if full_width else f"container {'has-bottom-bar' if user else ''}".strip()),
        *([] if user else [Footer(
            P("© 2026 Akobato. Silence the chat.", cls="text-center"),
            cls="site-footer container",
        )]),
        bottom_bar,
    )
