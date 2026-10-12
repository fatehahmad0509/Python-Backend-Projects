from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import database as db
import asyncio
import json
import os
import base64

try:
    from pywebpush import webpush, WebPushException
    PUSH_AVAILABLE = True
except ImportError:
    PUSH_AVAILABLE = False
    print("[Warning] pywebpush not installed — push notifications disabled.")

app = FastAPI(title="MessageLMS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

db.init_db()

# ── VAPID Auto-Setup ───────────────────────────────────────────────────────

def _generate_vapid_keys() -> tuple[str, str]:
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives import serialization

    key = ec.generate_private_key(ec.SECP256R1(), default_backend())

    d = key.private_numbers().private_value
    priv_b64 = base64.urlsafe_b64encode(d.to_bytes(32, "big")).rstrip(b"=").decode()

    pub_bytes = key.public_key().public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint,
    )
    pub_b64 = base64.urlsafe_b64encode(pub_bytes).rstrip(b"=").decode()

    return pub_b64, priv_b64


def _load_or_create_vapid() -> tuple[str, str]:
    env_pub  = os.environ.get("VAPID_PUBLIC_KEY", "").strip()
    env_priv = os.environ.get("VAPID_PRIVATE_KEY", "").strip()
    if env_pub and env_priv:
        print("[VAPID] Using keys from environment variables.")
        return env_pub, env_priv

    db_pub  = db.get_setting("vapid_public_key")
    db_priv = db.get_setting("vapid_private_key")
    if db_pub and db_priv:
        print("[VAPID] Loaded existing keys from database.")
        return db_pub, db_priv

    print("[VAPID] No keys found — generating new VAPID key pair…")
    pub_b64, priv_b64 = _generate_vapid_keys()
    db.set_setting("vapid_public_key",  pub_b64)
    db.set_setting("vapid_private_key", priv_b64)
    print("[VAPID] Keys saved to database. Push notifications are ready.")
    return pub_b64, priv_b64


VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY = _load_or_create_vapid()
VAPID_MAILTO = os.environ.get("VAPID_MAILTO", "mailto:admin@messagelms.com")

# ── Connection Tracking ────────────────────────────────────────────────────
connections: dict[int, list[WebSocket]] = {}
ws_nicks: dict[int, str] = {}
ws_rooms: dict[int, int] = {}


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return FileResponse("index.html")


@app.get("/config")
def config():
    return {"vapid_public_key": VAPID_PUBLIC_KEY}


@app.get("/rooms")
def rooms():
    return db.get_rooms()


@app.get("/active-users")
def active_users():
    online_set   = set(ws_nicks.values())
    online_list  = sorted(online_set)
    all_users    = db.get_all_usernames()
    offline_list = sorted([u for u in all_users if u not in online_set])
    return {"count": len(online_list), "users": online_list, "offline": offline_list}


@app.post("/users")
def register_user(data: dict):
    username = data.get("username", "").strip()
    if not username:
        return {"ok": False, "error": "İsim boş olamaz"}
    try:
        db.create_user(username)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/rooms")
def create_room(data: dict):
    name = data.get("name", "").strip()
    if not name:
        return {"ok": False, "error": "Room name cannot be empty"}
    db.create_room(name)
    return {"ok": True}


@app.get("/messages/{room_id}")
def messages(room_id: int):
    try:
        return db.get_messages(room_id)
    except Exception as e:
        import traceback
        return {"error": str(e), "detail": traceback.format_exc()}


@app.delete("/messages/{message_id}")
async def delete_message(message_id: int, data: dict):
    nick = data.get("nick", "").strip()
    if not nick:
        return {"ok": False, "error": "Nick gerekli"}
    deleted = db.delete_message(message_id, nick)
    if not deleted:
        return {"ok": False, "error": "Mesaj bulunamadı veya yetkiniz yok"}

    # Odadaki herkese bildir
    room_id = db.get_message_room(message_id) or _find_room_of_ws(nick)
    if room_id:
        payload = json.dumps({"type": "delete", "msg_id": message_id})
        for conn in connections.get(room_id, []):
            try: await conn.send_text(payload)
            except Exception: pass
    return {"ok": True}


@app.patch("/messages/{message_id}")
async def edit_message(message_id: int, data: dict):
    nick     = data.get("nick", "").strip()
    new_text = data.get("text", "").strip()
    if not nick or not new_text:
        return {"ok": False, "error": "Nick ve metin gerekli"}
    updated = db.edit_message(message_id, nick, new_text)
    if not updated:
        return {"ok": False, "error": "Mesaj bulunamadı veya yetkiniz yok"}

    room_id = db.get_message_room(message_id) or _find_room_of_ws(nick)
    if room_id:
        payload = json.dumps({"type": "edit", "msg_id": message_id, "text": new_text})
        for conn in connections.get(room_id, []):
            try: await conn.send_text(payload)
            except Exception: pass
    return {"ok": True}


def _find_room_of_ws(nick: str) -> int | None:
    """O an bağlı olan nick'in bulunduğu room_id'yi döner."""
    for ws_id, n in ws_nicks.items():
        if n == nick:
            return ws_rooms.get(ws_id)
    return None



@app.post("/subscribe")
def subscribe(data: dict):
    try:
        nick     = data.get("nick", "").strip()
        sub      = data.get("subscription", {})
        endpoint = sub.get("endpoint", "")
        keys     = sub.get("keys", {})
        p256dh   = keys.get("p256dh", "")
        auth     = keys.get("auth", "")

        if not (nick and endpoint and p256dh and auth):
            return {"ok": False, "error": "Eksik alan"}

        db.save_subscription(nick, endpoint, p256dh, auth)
        return {"ok": True}
    except Exception as e:
        return {"ok": False, "error": str(e)}


@app.post("/unsubscribe")
def unsubscribe(data: dict):
    endpoint = data.get("endpoint", "")
    if endpoint:
        db.delete_subscription(endpoint)
    return {"ok": True}


# ── Push Notification Helper ───────────────────────────────────────────────

async def send_push_notifications(room_id: int, sender_nick: str, message: str):
    if not PUSH_AVAILABLE or not VAPID_PRIVATE_KEY or not VAPID_PUBLIC_KEY:
        return

    connected_nicks = {
        ws_nicks[id(ws)]
        for ws in connections.get(room_id, [])
        if id(ws) in ws_nicks
    }

    subs = db.get_subscriptions_to_notify(sender_nick, connected_nicks)
    if not subs:
        return

    room_name = db.get_room_name(room_id)
    body = f"{sender_nick}: {message}"
    if len(body) > 120:
        body = body[:117] + "..."

    payload = json.dumps({
        "title":     f"#{room_name}",
        "body":      body,
        "room_id":   room_id,
        "room_name": room_name,
    })

    loop = asyncio.get_running_loop()
    for sub in subs:
        try:
            await loop.run_in_executor(
                None,
                lambda s=sub: webpush(
                    subscription_info={
                        "endpoint": s["endpoint"],
                        "keys": {
                            "p256dh": s["p256dh"],
                            "auth":   s["auth"],
                        },
                    },
                    data=payload,
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims={"sub": VAPID_MAILTO},
                ),
            )
        except WebPushException as exc:
            if exc.response is not None and exc.response.status_code in (404, 410):
                db.delete_subscription(sub["endpoint"])
            else:
                print(f"[Push] WebPushException for {sub['nick']}: {exc}")
        except Exception as exc:
            print(f"[Push] Unexpected error for {sub['nick']}: {exc}")


# ── Active Users Broadcast ─────────────────────────────────────────────────

async def broadcast_active_users():
    online_set  = set(ws_nicks.values())
    online_list = sorted(online_set)
    all_users   = db.get_all_usernames()
    offline_list = sorted([u for u in all_users if u not in online_set])
    payload = json.dumps({
        "type":    "active_users",
        "count":   len(online_list),
        "users":   online_list,
        "offline": offline_list,
    })
    dead = []
    for room_conns in connections.values():
        for conn in room_conns:
            try:
                await conn.send_text(payload)
            except Exception:
                dead.append((conn,))
    for (conn,) in dead:
        for rid, room_conns in connections.items():
            if conn in room_conns:
                room_conns.remove(conn)
        ws_nicks.pop(id(conn), None)
        ws_rooms.pop(id(conn), None)


# ── WebSocket ──────────────────────────────────────────────────────────────

@app.websocket("/ws/{room_id}/{nick}")
async def ws_endpoint(room_id: int, nick: str, websocket: WebSocket):
    await websocket.accept()

    if room_id not in connections:
        connections[room_id] = []
    connections[room_id].append(websocket)
    ws_nicks[id(websocket)] = nick
    ws_rooms[id(websocket)] = room_id

    asyncio.create_task(broadcast_active_users())

    try:
        while True:
            msg = await websocket.receive_text()
            msg = msg.strip()
            if not msg:
                continue

            # ── Typing / stop_typing / read events ───────────────────────────
            try:
                parsed = json.loads(msg)
                ev = parsed.get("type", "")

                if ev in ("typing", "stop_typing"):
                    relay = json.dumps({"type": ev, "nick": nick})
                    for conn in connections.get(room_id, []):
                        if conn is not websocket:
                            try:
                                await conn.send_text(relay)
                            except Exception:
                                pass
                    continue

                if ev == "read":
                    continue  # okundu sistemi kaldırıldı

            except (json.JSONDecodeError, AttributeError):
                pass  # düz metin mesajı — devam et

            # ── Mesaj kaydet ve yayınla ───────────────────────────────────────
            from datetime import datetime
            import zoneinfo
            ts = datetime.now(zoneinfo.ZoneInfo("Europe/Istanbul")).strftime("%d.%m.%Y | %H:%M")

            msg_id = db.save_message(room_id, nick, msg)

            dead = []
            payload = json.dumps({
                "type":   "message",
                "nick":   nick,
                "text":   msg,
                "ts":     ts,
                "msg_id": msg_id,
            })
            for conn in connections[room_id]:
                try:
                    await conn.send_text(payload)
                except Exception:
                    dead.append(conn)

            for conn in dead:
                connections[room_id].remove(conn)
                ws_nicks.pop(id(conn), None)
                ws_rooms.pop(id(conn), None)

            asyncio.create_task(send_push_notifications(room_id, nick, msg))

    except WebSocketDisconnect:
        if websocket in connections.get(room_id, []):
            connections[room_id].remove(websocket)
        ws_nicks.pop(id(websocket), None)
        ws_rooms.pop(id(websocket), None)
        asyncio.create_task(broadcast_active_users())


app.mount("/", StaticFiles(directory=".", html=True), name="static")
