from fasthtml.common import *


def roast_page(best: list[dict], worst: list[dict]) -> FT:
    return Div(

        # ── Header ────────────────────────────────────────────────────────────
        Div(
            H1("🔥 The Burn Board", style="margin:0; font-size:2rem;"),
            P(
                "Anonymous arguments. Public consequences. No mercy.",
                style="color:var(--brand-muted); margin:.4rem 0 0;",
            ),
            cls="card text-center",
            style="margin-bottom:2rem; padding:2rem 1.5rem 1.5rem;",
        ),

        # ── Two-column grid ───────────────────────────────────────────────────
        Div(
            _section(
                "🏆 Hall of Flame",
                "The arguments that actually slapped.",
                best,
                variant="flame",
            ),
            _section(
                "💀 Hall of Shame",
                "These brave souls tried. They really did.",
                worst,
                variant="shame",
            ),
            style=(
                "display:grid;"
                "grid-template-columns:repeat(auto-fit,minmax(300px,1fr));"
                "gap:1.5rem;"
            ),
        ),
    )


def _section(title: str, subtitle: str, entries: list[dict], variant: str) -> FT:
    accent = "var(--brand-gold)" if variant == "flame" else "var(--brand-red)"

    if not entries:
        return Div(
            H2(title, style=f"color:{accent}; margin:0 0 .25rem;"),
            P(subtitle, style="color:var(--brand-muted); font-size:.85rem; margin:0 0 1rem;"),
            P("Nothing here yet — get debating!", style="color:var(--brand-muted); text-align:center;"),
            cls="card",
            style="padding:1.5rem;",
        )

    return Div(
        H2(title, style=f"color:{accent}; margin:0 0 .25rem;"),
        P(subtitle, style="color:var(--brand-muted); font-size:.85rem; margin:0 0 1.25rem;"),
        *[_card(e, variant) for e in entries],
        cls="card",
        style="padding:1.5rem; display:flex; flex-direction:column; gap:1rem;",
    )


def _card(entry: dict, variant: str) -> FT:
    accent  = "var(--brand-gold)" if variant == "flame" else "var(--brand-red)"
    score   = entry["score"]
    alias   = entry["alias"]
    prompt  = entry["prompt"] or ""
    arg     = entry["argument"] or ""
    reason  = entry["reasoning"] or ""
    wq      = entry.get("winning_quote", "")

    # Score bar — filled pips out of 10
    pips = Div(
        *[
            Span(
                style=(
                    f"display:inline-block;width:10px;height:10px;border-radius:2px;"
                    f"margin-right:2px;"
                    f"background:{'var(--brand-gold)' if variant=='flame' and i < score else 'var(--brand-red)' if variant=='shame' and i < score else 'rgba(255,255,255,.12)'};"
                )
            )
            for i in range(10)
        ],
        style="display:inline-flex; align-items:center; flex-wrap:wrap; gap:1px;",
    )

    # Winning quote highlighted only for flame cards
    quote_block = (
        P(
            f'"{wq}"',
            style=(
                "font-style:italic; color:var(--brand-gold);"
                "border-left:3px solid var(--brand-gold);"
                "padding-left:.75rem; margin:.5rem 0 0; font-size:.9rem;"
            ),
        )
        if variant == "flame" and wq
        else ()
    )

    # Truncate reasoning to ~200 chars so it doesn't eat the page
    reason_snippet = reason[:200].rstrip() + ("…" if len(reason) > 200 else "")

    return Div(
        # Top row: alias badge + score
        Div(
            Span(
                alias,
                style=(
                    f"font-size:.75rem; font-weight:700; letter-spacing:.05em;"
                    f"background:{accent}22; color:{accent};"
                    f"padding:.2rem .6rem; border-radius:999px; border:1px solid {accent}44;"
                ),
            ),
            Span(
                f"{score}/10",
                style=f"font-size:.8rem; font-weight:900; color:{accent};",
            ),
            style="display:flex; justify-content:space-between; align-items:center; margin-bottom:.5rem;",
        ),
        # Prompt context
        P(
            f"On: {prompt[:80]}{'…' if len(prompt) > 80 else ''}",
            style="font-size:.72rem; color:var(--brand-muted); margin:0 0 .5rem; font-style:italic;",
        ),
        # The argument
        P(
            f'"{arg[:300]}{"…" if len(arg) > 300 else ""}"',
            style=(
                "font-size:.88rem; color:var(--fg);"
                "background:rgba(255,255,255,.04);"
                "border-radius:6px; padding:.6rem .75rem; margin:0;"
            ),
        ),
        quote_block,
        # Score pips
        Div(pips, style="margin-top:.5rem;"),
        # Judge's take
        Div(
            Span("🧑‍⚖️ Judge: ", style="font-weight:700; font-size:.78rem;"),
            Span(reason_snippet, style="font-size:.78rem; color:var(--brand-muted);"),
            style=(
                "margin-top:.6rem; padding:.5rem .75rem;"
                "background:rgba(255,255,255,.03);"
                "border-radius:6px; border-left:2px solid rgba(255,255,255,.1);"
            ),
        ),
        style=(
            "padding:1rem;"
            f"border:1px solid {accent}33;"
            "border-radius:8px;"
            "background:rgba(0,0,0,.25);"
        ),
    )
