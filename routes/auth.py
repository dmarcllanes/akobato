import os
import secrets
import hashlib
import base64
import urllib.parse

from fasthtml.common import *
from starlette.requests import Request
from starlette.responses import RedirectResponse

from routes.profile import generate_alias


def _pkce_pair() -> tuple[str, str]:
    verifier = secrets.token_urlsafe(64)
    digest   = hashlib.sha256(verifier.encode()).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode()
    return verifier, challenge


def setup_auth_routes(rt, game_state):
    BASE_URL = os.getenv("APP_BASE_URL", "http://localhost:5001")

    # ── Initiate Google OAuth ─────────────────────────────────────────────────

    @rt("/auth/login")
    def get(req: Request):
        supabase_url = os.getenv("SUPABASE_URL", "").rstrip("/")
        if not supabase_url or "your_" in supabase_url:
            return RedirectResponse(
                "/login?error=SUPABASE_URL+is+not+configured+in+.env",
                status_code=302,
            )

        verifier, challenge = _pkce_pair()
        req.session["pkce_verifier"] = verifier

        callback = urllib.parse.quote(f"{BASE_URL}/auth/callback", safe="")
        auth_url = (
            f"{supabase_url}/auth/v1/authorize"
            f"?provider=google"
            f"&redirect_to={callback}"
            f"&code_challenge={challenge}"
            f"&code_challenge_method=S256"
            f"&prompt=select_account"
        )
        return RedirectResponse(auth_url, status_code=302)

    # ── OAuth callback — server-side code exchange ────────────────────────────

    @rt("/auth/callback")
    async def get(req: Request, code: str = ""):
        """
        Supabase redirects here with ?code=... after Google auth.
        We exchange the code + PKCE verifier for a session, then redirect.
        """
        db = game_state.db

        if not code:
            return RedirectResponse("/login?error=no_code", status_code=302)

        if not db:
            # Supabase not configured — dev bypass
            req.session["username"] = "dev_user"
            return RedirectResponse("/dashboard", status_code=302)

        try:
            verifier = req.session.pop("pkce_verifier", "")

            result = db.auth.exchange_code_for_session({
                "auth_code": code,
                "code_verifier": verifier,
            })

            user = result.user
            meta = user.user_metadata or {}
            raw_name = (
                meta.get("full_name")
                or meta.get("name")
                or user.email.split("@")[0]
            )
            username = raw_name.replace(" ", "_")[:20]

            req.session["username"] = username
            req.session["user_id"]  = str(user.id)

            # Upsert player row so stats persist across sessions
            try:
                db.table("players").upsert(
                    {"username": username, "score": 0},
                    on_conflict="username",
                ).execute()
            except Exception:
                pass

            # Ensure alias exists — generate one on first login, reuse on return
            try:
                row = db.table("players").select("alias").eq("username", username).single().execute()
                saved_alias = (row.data or {}).get("alias")
                if saved_alias:
                    req.session["alias"] = saved_alias
                else:
                    new_alias = generate_alias(username)
                    db.table("players").update({"alias": new_alias}).eq("username", username).execute()
                    req.session["alias"] = new_alias
            except Exception:
                pass

            return RedirectResponse("/dashboard", status_code=302)

        except Exception as e:
            # Surface the error as a query param so user knows what happened
            msg = urllib.parse.quote(str(e)[:120], safe="")
            return RedirectResponse(f"/login?error={msg}", status_code=302)

    # ── Logout ────────────────────────────────────────────────────────────────

    @rt("/auth/logout", methods=["POST"])
    def post(req: Request):
        req.session.clear()
        return RedirectResponse("/", status_code=302)
