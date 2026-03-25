from fasthtml.common import *


def profile_page(username: str, alias: str, stats: dict, saved: bool = False, error: str = "") -> FT:
    wins   = stats.get("wins",   0)
    losses = stats.get("losses", 0)
    ties   = stats.get("ties",   0)
    score  = stats.get("score",  0)

    _ERROR_MSGS = {
        "db":      "⚠ Could not save — make sure the alias column exists in your database (run 06_alias.sql).",
        "invalid": "⚠ Invalid alias. Use 2–24 characters: letters, numbers, #, _, - only.",
    }

    saved_banner = Div(
        "✔ Alias updated successfully",
        cls="prof-saved-banner",
    ) if saved else ()

    error_banner = Div(
        _ERROR_MSGS.get(error, "⚠ Something went wrong."),
        cls="prof-error-banner",
    ) if error else ()

    return Div(

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            Div("// IDENTITY_SETTINGS.EXE", cls="prof-sys-label"),
            H1("Your Profile", cls="prof-title"),
            P("Customize your alias to stay anonymous in the arena.", cls="prof-sub"),
            cls="prof-header",
        ),

        saved_banner,
        error_banner,

        # ── Identity card ─────────────────────────────────────────────────────
        Div(
            # Avatar
            Div(
                Img(
                    src=f"/avatar/{username}",
                    width="80", height="80",
                    alt=username,
                    style="display:block;border-radius:50%;image-rendering:pixelated",
                ),
                cls="prof-avatar-wrap",
            ),

            # Info
            Div(
                Div(
                    Span("ALIAS", cls="prof-field-label"),
                    Span(alias, cls="prof-alias-display"),
                    cls="prof-alias-row",
                ),
                Div(
                    Span("REAL ID", cls="prof-field-label"),
                    Span(username, cls="prof-username-display"),
                    cls="prof-alias-row",
                ),
                P("Your alias is shown everywhere in the game. Your real identity stays hidden.", cls="prof-identity-note"),
                cls="prof-identity-info",
            ),

            cls="prof-identity-card",
        ),

        # ── Edit alias form ───────────────────────────────────────────────────
        Div(
            Span("// SET_ALIAS", cls="prof-sys-label"),
            Form(
                Div(
                    Label("New alias", for_="alias-input", cls="prof-input-label"),
                    Div(
                        Input(
                            id="alias-input",
                            name="alias",
                            type="text",
                            value=alias,
                            placeholder="e.g. ShadowFox#4291",
                            maxlength="24",
                            autocomplete="off",
                            cls="prof-input",
                        ),
                        Button("SAVE", type="submit", cls="prof-save-btn"),
                        cls="prof-input-row",
                    ),
                    P("2–24 characters. Letters, numbers, #, _, - only.", cls="prof-input-hint"),
                    cls="prof-input-group",
                ),
                action="/profile/update-alias",
                method="post",
            ),
            cls="prof-edit-section",
        ),

        # ── Stats summary ─────────────────────────────────────────────────────
        Div(
            Span("// COMBAT_RECORD", cls="prof-sys-label"),
            Div(
                _pstat("🏅", "SCORE",  score),
                _pstat("🏆", "WINS",   wins),
                _pstat("💀", "LOSSES", losses),
                _pstat("🤝", "TIES",   ties),
                cls="prof-stats",
            ),
            cls="prof-stats-section",
        ),

        A("← Back to dashboard", href="/dashboard", cls="prof-back"),

        cls="prof-page",
    )


def _pstat(icon: str, label: str, value) -> FT:
    return Div(
        Span(icon, cls="prof-stat-icon"),
        Div(str(value), cls="prof-stat-value"),
        Div(label, cls="prof-stat-label"),
        cls="prof-stat-card",
    )
