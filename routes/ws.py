"""
WebSocket routes — replaces all HTMX polling.

Channels:
  /ws/lobby/{username}              — waiting for opponent in versus mode
  /ws/arena/{match_id}/{username}   — waiting for AI verdict after submitting
  /ws/room/{room_code}/{username}   — host waiting for friend to join private room
"""
import asyncio
import json
from starlette.websockets import WebSocket, WebSocketDisconnect

POLL_INTERVAL = 0.1   # seconds between in-memory checks


def setup_ws_routes(app, game_state):

    async def ws_lobby(websocket: WebSocket):
        username = websocket.path_params["username"]
        await websocket.accept()
        try:
            while True:
                mid   = game_state.player_matches.get(username)
                match = game_state.matches.get(mid) if mid else None
                if match and match.status != "waiting":
                    await websocket.send_text(json.dumps({
                        "action": "redirect",
                        "url": f"/game/{mid}?player={username}",
                    }))
                    break
                await asyncio.sleep(POLL_INTERVAL)
        except WebSocketDisconnect:
            pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    async def ws_arena(websocket: WebSocket):
        match_id = websocket.path_params["match_id"]
        username = websocket.path_params["username"]
        await websocket.accept()
        try:
            while True:
                match = game_state.matches.get(match_id)
                if not match:
                    await websocket.send_text(json.dumps({"action": "error", "msg": "match_not_found"}))
                    break
                # Handle timeout: auto-submit anyone who didn't submit before timer expired
                if match.is_expired():
                    match.auto_submit_expired()
                # Drive judging forward when all args are in (also retries if AI previously failed)
                if match.status == "judging":
                    from routes.game import _maybe_judge
                    await _maybe_judge(match, game_state)
                if match.status == "complete" and match.verdict:
                    await websocket.send_text(json.dumps({
                        "action": "redirect",
                        "url": f"/game/{match_id}?player={username}",
                    }))
                    break
                await asyncio.sleep(POLL_INTERVAL)
        except WebSocketDisconnect:
            pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    async def ws_room(websocket: WebSocket):
        room_code = websocket.path_params["room_code"]
        username  = websocket.path_params["username"]
        await websocket.accept()
        try:
            while True:
                mid   = game_state.rooms.get(room_code)
                match = game_state.matches.get(mid) if mid else None
                if not match:
                    await websocket.send_text(json.dumps({"action": "error", "msg": "room_not_found"}))
                    break
                if match.status != "waiting":
                    # Brief delay so all players receive the redirect signal together
                    await asyncio.sleep(0.1)
                    await websocket.send_text(json.dumps({
                        "action": "redirect",
                        "url": f"/game/{mid}?player={username}",
                    }))
                    break
                await asyncio.sleep(POLL_INTERVAL)
        except WebSocketDisconnect:
            pass
        finally:
            try:
                await websocket.close()
            except Exception:
                pass

    app.add_websocket_route("/ws/lobby/{username}",            ws_lobby)
    app.add_websocket_route("/ws/arena/{match_id}/{username}", ws_arena)
    app.add_websocket_route("/ws/room/{room_code}/{username}", ws_room)
