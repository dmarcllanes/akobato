import os
import secrets
import time
from dotenv import load_dotenv
from fasthtml.common import *
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.staticfiles import StaticFiles
from starlette.responses import FileResponse

load_dotenv()

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR  = os.path.join(BASE_DIR, "static")
_raw_key   = os.getenv("SESSION_SECRET", "")
SESSION_KEY = _raw_key if _raw_key and "change_this" not in _raw_key else secrets.token_hex(32)


# ── Supabase (optional) ───────────────────────────────────────────────────────
def _init_supabase():
    url = os.getenv("SUPABASE_URL", "")
    key = os.getenv("SUPABASE_KEY", "")
    if not url or not key or "your_" in url:
        return None
    try:
        from supabase import create_client
        return create_client(url, key)
    except Exception:
        return None


# ── Shared game state ─────────────────────────────────────────────────────────
class GameState:
    def __init__(self):
        self.matches: dict        = {}    # match_id -> MatchState
        self.player_matches: dict = {}    # username -> match_id
        self.waiting: tuple | None = None # (username, match_id)
        self.rooms: dict          = {}    # room_code -> match_id  (private rooms)
        self.db = _init_supabase()


game_state = GameState()

# ── FastHTML app ──────────────────────────────────────────────────────────────
_CSS_VERSION = str(int(time.time()))

app, rt = fast_app(
    pico=True,
    hdrs=(Link(rel="stylesheet", href=f"/static/css/custom.css?v={_CSS_VERSION}"),),
    middleware=[
        Middleware(
            SessionMiddleware,
            secret_key=SESSION_KEY,
            https_only=False,
            max_age=60 * 60 * 24 * 30,   # 30 days
            same_site="lax",
        ),
    ],
    live=False,
)

# Mount static files explicitly with an absolute path
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Service worker must be served from root scope
@app.route("/sw.js")
async def sw(request):
    return FileResponse(
        os.path.join(STATIC_DIR, "js", "sw.js"),
        media_type="application/javascript",
        headers={"Service-Worker-Allowed": "/", "Cache-Control": "no-cache"},
    )

# ── Routes ────────────────────────────────────────────────────────────────────
from routes.auth          import setup_auth_routes
from routes.dashboard     import setup_dashboard_routes
from routes.game          import setup_game_routes
from routes.leaderboard   import setup_leaderboard_routes
from routes.profile       import setup_profile_routes
from routes.roast         import setup_roast_routes
from routes.ws            import setup_ws_routes
from services.news_fetcher import warmup_prompt_pool

setup_auth_routes(rt, game_state)
setup_dashboard_routes(rt, game_state)
setup_game_routes(rt, game_state)
setup_leaderboard_routes(rt, game_state)
setup_profile_routes(rt, game_state)
setup_roast_routes(rt, game_state)
setup_ws_routes(app, game_state)


@app.on_event("startup")
async def _startup():
    import asyncio
    # Pre-fetch 2 prompts per category so match joins are instant
    asyncio.create_task(warmup_prompt_pool(count_per_category=2))

# ── Run ───────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 7860))
    serve(host="0.0.0.0", port=port)
