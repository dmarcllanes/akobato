from fasthtml.common import *


def landing_page() -> FT:
    return Div(
        # Fixed particle canvas
        Canvas(id="particle-canvas"),
        # Scanlines overlay
        Div(cls="scanlines-overlay"),

        # ── Hero ──────────────────────────────────────────────────────────────
        Section(
            Div("⬤ INSERT COIN TO PLAY ⬤", cls="insert-coin"),
            H1("AKOBATO", data_text="AKOBATO", cls="lp-hero-title"),
            P(
                Span(id="typewriter-text"),
                Span("_", cls="cursor-blink"),
                cls="lp-hero-typewriter",
            ),
            Div(
                Span("ROUND TIME", cls="lp-timer-label"),
                Span("60", id="hero-timer", cls="lp-hero-timer"),
                Span("SECONDS", cls="lp-timer-label"),
                cls="lp-timer-wrap",
            ),
            A("⚔ ENTER THE ARENA", href="/auth/login", cls="lp-cta-btn"),
            P("FREE DAILY MATCH  ·  NO CREDIT CARD", cls="lp-hero-sub"),
            cls="lp-hero",
        ),

        Div(cls="lp-divider"),

        # ── How It Works ──────────────────────────────────────────────────────
        Section(
            Div(
                P("// HOW_IT_WORKS.EXE", cls="lp-section-tag reveal"),
                H2("Three rounds. One survivor.", cls="lp-section-title reveal"),
                P(
                    "A polarizing news prompt drops. You type your hottest take. "
                    "The AI judge burns the loser.",
                    cls="lp-section-desc reveal",
                ),
                Div(
                    Div(
                        Span("01", cls="lp-card-step"),
                        Span("📰", cls="lp-card-icon"),
                        H3("THE DROP"),
                        P("A live news headline becomes the battlefield. No prep. "
                          "No Google. Just raw opinion."),
                        cls="lp-arcade-card reveal",
                    ),
                    Div(
                        Span("02", cls="lp-card-step"),
                        Span("⏱", cls="lp-card-icon"),
                        H3("THE CLASH"),
                        P("60 seconds. One opponent. Type your argument before "
                          "the clock murders your chances."),
                        cls="lp-arcade-card reveal",
                        style="transition-delay:0.1s",
                    ),
                    Div(
                        Span("03", cls="lp-card-step"),
                        Span("⚖", cls="lp-card-icon"),
                        H3("THE VERDICT"),
                        P("The AI Judge reads both arguments, picks a winner, "
                          "and publicly roasts whoever lost."),
                        cls="lp-arcade-card reveal",
                        style="transition-delay:0.2s",
                    ),
                    cls="lp-cards-row",
                ),
                cls="lp-section-inner",
            ),
            cls="lp-section",
        ),

        Div(cls="lp-divider"),

        # ── Anti-Cheat ────────────────────────────────────────────────────────
        Section(
            Div(
                P("// ANTI_CHEAT.SYS", cls="lp-section-tag reveal"),
                H2(
                    "Sound Like a Robot? ",
                    Span("You Lose.", style="color:var(--lp-pink)"),
                    cls="lp-section-title reveal",
                ),
                P(
                    "Copy-paste from ChatGPT and the judge will humiliate you. "
                    "Generic buzzwords, corporate fluff, 'let's delve' — instant losses.",
                    cls="lp-section-desc reveal",
                ),
                Div(
                    Div(
                        Div(
                            Span(cls="lp-dot lp-dot-r"),
                            Span(cls="lp-dot lp-dot-y"),
                            Span(cls="lp-dot lp-dot-g"),
                            Span("akobato_judge.exe — AI VERDICT OUTPUT",
                                 cls="lp-terminal-label"),
                            cls="lp-terminal-bar",
                        ),
                        Div(
                            Div(
                                Span("judge@akobato:~$", cls="lp-t-prompt"),
                                " analyze_debate --match=7f3a2b1c",
                            ),
                            Div("\u00a0"),
                            Div(
                                Span("►", cls="lp-t-prompt"),
                                " Scanning arguments...",
                            ),
                            Div(
                                Span("►", cls="lp-t-prompt"),
                                " Detecting AI slop... ",
                                Span("ALERT: Player 2", style="color:var(--lp-pink)"),
                            ),
                            Div("\u00a0"),
                            Div("WINNER: Player 1 🏆", cls="lp-t-verdict"),
                            Div("\u00a0"),
                            Div(id="terminal-roast", cls="lp-t-roast"),
                            cls="lp-terminal-body",
                        ),
                        cls="lp-terminal-wrap reveal",
                    ),
                    cls="lp-section-inner",
                ),
            ),
            cls="lp-section lp-section-alt",
        ),

        Div(cls="lp-divider"),

        # ── Economy ───────────────────────────────────────────────────────────
        Section(
            Div(
                P("// TOKEN_ECONOMY.DAT", cls="lp-section-tag reveal"),
                H2("1 Free Riot Per Day.", cls="lp-section-title reveal"),
                P(
                    "Everyone gets one free match daily. Need to settle more grudges? "
                    "Grab a token bundle and go unlimited.",
                    cls="lp-section-desc reveal",
                ),
                Div(
                    Div(
                        Span("🎮", cls="lp-token-emoji"),
                        Div("DAILY FREE",    cls="lp-token-name"),
                        Div("1",             cls="lp-token-count"),
                        Div("match per day, always", cls="lp-token-price"),
                        cls="lp-token-card reveal",
                    ),
                    Div(
                        Span("🟡", cls="lp-token-emoji"),
                        Div("STARTER PACK",  cls="lp-token-name"),
                        Div("5",             cls="lp-token-count"),
                        Div("tokens — $2.99", cls="lp-token-price"),
                        cls="lp-token-card reveal",
                        style="transition-delay:0.1s",
                    ),
                    Div(
                        Span("🟠", cls="lp-token-emoji"),
                        Div("GRUDGE MASTER", cls="lp-token-name"),
                        Div("15",            cls="lp-token-count"),
                        Div("tokens — $7.99", cls="lp-token-price"),
                        cls="lp-token-card reveal",
                        style="transition-delay:0.2s",
                    ),
                    Div(
                        Span("🔴", cls="lp-token-emoji"),
                        Div("ROAST LEGEND",  cls="lp-token-name"),
                        Div("50",            cls="lp-token-count"),
                        Div("tokens — $19.99", cls="lp-token-price"),
                        cls="lp-token-card reveal",
                        style="transition-delay:0.3s",
                    ),
                    cls="lp-token-grid",
                ),
                Div(
                    Span("🪙 FIRST MATCH IS ALWAYS FREE", cls="lp-free-badge"),
                    Br(),
                    A("GET STARTED →", href="/auth/login", cls="lp-cta-btn",
                      style="margin-top:24px; display:inline-block;"),
                    style="text-align:center",
                ),
                cls="lp-section-inner",
            ),
            cls="lp-section",
        ),

        # ── Footer ticker ─────────────────────────────────────────────────────
        Div(
            Div(id="lp-ticker", cls="lp-ticker-track"),
            cls="lp-ticker-wrap",
        ),

        # ── Install banner ────────────────────────────────────────────────────
        Div(
            P("Install Akobato for instant access"),
            Button("INSTALL",  cls="lp-install-btn",  id="install-btn"),
            Button("✕",        cls="lp-dismiss-btn",  id="dismiss-btn"),
            id="install-banner",
        ),

        Script(src="/static/js/landing.js"),
    )
