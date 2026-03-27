from fasthtml.common import *
from datetime import datetime, timezone, timedelta


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

        # ── Match history ─────────────────────────────────────────────────────
        match_history_section(),

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


# ── Match history ──────────────────────────────────────────────────────────────

def match_history_section() -> FT:
    """Section shell with filter tabs — body loaded via HTMX."""
    _TABS = [("recent", "RECENT"), ("weekly", "WEEKLY"), ("all", "ALL")]
    tab_els = [
        Button(
            label,
            type="button",
            cls=f"mh-tab{'  mh-tab--active' if key == 'recent' else ''}",
            id=f"mh-tab-{key}",
            hx_get=f"/profile/matches?filter={key}",
            hx_target="#mh-body",
            hx_swap="innerHTML",
            onclick=f"setMhTab('{key}')",
        )
        for key, label in _TABS
    ]
    return Div(
        Div(
            Span("// MATCH_HISTORY", cls="prof-sys-label"),
            Div(*tab_els, cls="mh-tabs"),
            cls="mh-header",
        ),
        Div(
            Div(
                Span(cls="wt-dot"), Span(cls="wt-dot"), Span(cls="wt-dot"),
                cls="wt-dots",
                style="justify-content:center; margin:1.25rem 0;",
            ),
            id="mh-body",
            hx_get="/profile/matches?filter=recent",
            hx_trigger="load",
            hx_target="#mh-body",
            hx_swap="innerHTML",
        ),
        Script("""
(function(){
  window.setMhTab = function(key) {
    document.querySelectorAll('.mh-tab').forEach(function(t){
      t.classList.toggle('mh-tab--active', t.id === 'mh-tab-' + key);
    });
  };
})();
"""),
        cls="mh-section",
    )


def match_history_fragment(rows: list, username: str, filter_name: str) -> FT:
    """HTMX-returned fragment with match rows."""
    if not rows:
        msg = "No matches this week." if filter_name == "weekly" else "No matches yet."
        return Div(
            Span("📭", style="font-size:1.5rem; display:block; margin-bottom:.5rem;"),
            Div(msg, style="font-size:.82rem; color:var(--brand-muted); font-weight:600;"),
            style="text-align:center; padding:1.5rem 0;",
        )
    return Div(*[_match_row(r, username) for r in rows])


def _match_row(r: dict, username: str) -> FT:
    is_p1    = r.get("player1") == username
    opp_name = r.get("player2") if is_p1 else r.get("player1")
    opp_display = r.get("opp_alias") or opp_name or "?"

    winner = r.get("winner", "")
    # verdicts table stores "Player 1", "Player 2", or "Tie"
    if winner == "Tie":
        result, result_cls, score_str, score_cls = "TIE",  "mh-result--tie",  "+1", "mh-score--tie"
    elif (winner == "Player 1" and is_p1) or (winner == "Player 2" and not is_p1):
        result, result_cls, score_str, score_cls = "WIN",  "mh-result--win",  "+3", "mh-score--win"
    else:
        result, result_cls, score_str, score_cls = "LOSS", "mh-result--loss", "+0", "mh-score--loss"

    prompt = r.get("prompt", "")
    prompt_short = (prompt[:55] + "…") if len(prompt) > 55 else prompt

    orig = r.get("hp1_score") if is_p1 else r.get("hp2_score")
    orig_el = (
        Span(f"⚡{orig}", cls="mh-orig")
        if orig else ()
    )

    return Div(
        Span(result, cls=f"mh-result {result_cls}"),
        Div(
            Div(
                Span("vs ", cls="mh-vs"),
                Span(opp_display, cls="mh-opponent"),
                orig_el,
                cls="mh-row-top",
            ),
            Div(prompt_short, cls="mh-prompt"),
            cls="mh-row-info",
        ),
        Div(
            Div(score_str, cls=f"mh-score {score_cls}"),
            Div(_fmt_date(r.get("created_at", "")), cls="mh-date"),
            cls="mh-row-right",
        ),
        cls="mh-row",
    )


def _fmt_date(created_at: str) -> str:
    if not created_at:
        return ""
    try:
        s = created_at.replace("Z", "+00:00")
        dt = datetime.fromisoformat(s)
        now = datetime.now(timezone.utc)
        diff = now - dt
        if diff < timedelta(minutes=1):
            return "just now"
        if diff < timedelta(hours=1):
            return f"{int(diff.total_seconds() / 60)}m ago"
        if diff < timedelta(days=1):
            return f"{int(diff.total_seconds() / 3600)}h ago"
        if diff < timedelta(days=7):
            return f"{diff.days}d ago"
        return dt.strftime("%b %d")
    except Exception:
        return ""
