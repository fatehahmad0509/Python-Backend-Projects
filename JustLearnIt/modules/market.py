"""
JustLearnIt - Market Module

Allows students to browse and purchase items using their earned gold.
Items include score/gold boosts, streak protection, cosmetic badges, and loot chests.
"""
import random
import pytz
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Request
from core.db import get_conn
from core.security import auth_required, student_required
from core.achievements import award_badge
from core.logs import log_action

_TR = pytz.timezone("Europe/Istanbul")
def _now(): return datetime.now(_TR)

router = APIRouter(prefix="/market", tags=["Market"])


@router.get("/items")
def items(user=Depends(student_required)):
    """Return all available market items sorted by price ascending."""
    with get_conn() as (conn, c):
        c.execute("SELECT id,name,description,price,item_type FROM market_items ORDER BY price ASC")
        rows = c.fetchall()
    return [{"id": r[0], "name": r[1], "description": r[2], "price": r[3], "item_type": r[4]} for r in rows]


@router.post("/buy/{item_id}")
def buy(item_id: int, user=Depends(student_required), request: Request = None):
    """
    Purchase a market item by spending gold.
    Applies the appropriate effect (boost, streak freeze, badge, or chest reward).
    Raises 404 if item not found, 400 if the student has insufficient gold.
    """
    with get_conn() as (conn, c):
        c.execute("SELECT price,name FROM market_items WHERE id=%s", (item_id,))
        item = c.fetchone()
        if not item:
            raise HTTPException(404, "Item not found")
        price, name = item

        c.execute("SELECT id,gold FROM students WHERE user_id=%s", (user["id"],))
        st = c.fetchone()
        if not st or (st[1] or 0) < price:
            raise HTTPException(400, "Insufficient gold")

        sid = st[0]
        c.execute("UPDATE students SET gold=gold-%s WHERE id=%s", (price, sid))

        expiry, mult, msg = None, 1, f"{name} activated!"

        if name == "Energy Drink":
            expiry = _now() + timedelta(hours=24)
            mult = 2
        elif name == "Energy Bomb":
            expiry = _now() + timedelta(hours=24)
            mult = 3
        elif name == "Streak Freeze":
            expiry = _now() + timedelta(days=2)
        elif name == "Gold Badge":
            expiry = _now() + timedelta(days=7)
            msg = "Your badge will shine on your profile for 1 week! ✨"
            award_badge(sid, "Gold Badge")
        elif "Chest" in name:
            chance = random.randint(1, 100)
            # Determine reward type and amount based on chest tier
            if "Silver" in name:
                amt = random.randint(50, 200) if chance <= 60 else random.randint(100, 400)
                field = "score" if chance <= 60 else "gold"
            elif "Gold" in name or "Legend" in name:
                amt = random.randint(300, 800) if chance <= 50 else random.randint(500, 1200)
                field = "score" if chance <= 50 else "gold"
            else:
                # Fallback for unknown chest types — award a moderate gold reward
                amt = random.randint(100, 300)
                field = "gold"
            c.execute(f"UPDATE students SET {field}={field}+%s WHERE id=%s", (amt, sid))
            msg = f"You got {amt} {field} from the chest!"

        if expiry:
            c.execute(
                "INSERT INTO active_boosts(student_id,item_name,expires_at,multiplier) VALUES(%s,%s,%s,%s)",
                (sid, name, expiry, mult)
            )
        conn.commit()

    log_action(user, "market_purchase", "market_item", item_id, f"{name} - {price} gold. {msg}", request)
    return {"status": "success", "message": msg}
