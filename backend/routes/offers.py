from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from db.database import get_connection
from utils.auth import get_current_user

router = APIRouter()


class OfferCreate(BaseModel):
    cake_id: int
    price: int
    delivery_days: int
    message: str | None = None


# 🍰 CREATE OFFER (SECURED)
@router.post("/create")
def create_offer(offer: OfferCreate, current_user=Depends(get_current_user)):

    # 🔐 role check
    if current_user["role"] != "baker":
        raise HTTPException(status_code=403, detail="only bakers can create offers")

    user_id = current_user["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    # 🔎 get baker_id from user_id
    cur.execute(
        "SELECT id FROM baker_profiles WHERE user_id = %s",
        (user_id,)
    )
    baker = cur.fetchone()

    if not baker:
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="baker profile not found")

    baker_id = baker[0]

    # 🚫 prevent duplicate offer
    cur.execute(
        "SELECT id FROM offers WHERE cake_id = %s AND baker_id = %s",
        (offer.cake_id, baker_id)
    )
    if cur.fetchone():
        cur.close()
        conn.close()
        raise HTTPException(status_code=400, detail="offer already exists")

    # 🧁 insert
    cur.execute(
        """
        INSERT INTO offers (cake_id, baker_id, price, delivery_days, message)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (offer.cake_id, baker_id, offer.price, offer.delivery_days, offer.message)
    )

    offer_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "offer submitted 🔥", "offer_id": offer_id}


# 📦 GET OFFERS (optional: can keep public or restrict later)
@router.get("/cake/{cake_id}")
def get_offers(cake_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT 
            o.id,
            o.price,
            o.delivery_days,
            o.message,
            b.shop_name,
            b.rating
        FROM offers o
        JOIN baker_profiles b ON o.baker_id = b.id
        WHERE o.cake_id = %s
        ORDER BY o.price ASC;
        """,
        (cake_id,)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    offers = []
    for row in rows:
        offers.append({
            "offer_id": row[0],
            "price": row[1],
            "delivery_days": row[2],
            "message": row[3],
            "baker_name": row[4],
            "rating": row[5]
        })

    return {"offers": offers}


# 🎯 SELECT OFFER (SECURED FINAL BOSS)
@router.post("/select/{offer_id}")
def select_offer(offer_id: int, current_user=Depends(get_current_user)):

    if current_user["role"] != "user":
        raise HTTPException(status_code=403, detail="only users can select offers")

    user_id = current_user["user_id"]

    conn = get_connection()
    cur = conn.cursor()

    # 1. get offer
    cur.execute(
        "SELECT cake_id, baker_id, price, delivery_days, status FROM offers WHERE id = %s",
        (offer_id,)
    )
    offer = cur.fetchone()

    if not offer:
        raise HTTPException(status_code=404, detail="offer not found")

    cake_id, baker_id, price, delivery_days, status = offer

    # 2. check cake ownership
    cur.execute(
        "SELECT user_id FROM cake_requests WHERE id = %s",
        (cake_id,)
    )
    cake = cur.fetchone()

    if not cake or cake[0] != user_id:
        raise HTTPException(status_code=403, detail="not your cake request")

    # 3. prevent re-selection
    if status != "pending":
        raise HTTPException(status_code=400, detail="offer already processed")

    # 4. prevent duplicate order
    cur.execute(
        "SELECT id FROM orders WHERE cake_id = %s",
        (cake_id,)
    )
    if cur.fetchone():
        raise HTTPException(status_code=400, detail="order already exists")

    # 5. accept offer
    cur.execute(
        "UPDATE offers SET status = 'accepted' WHERE id = %s",
        (offer_id,)
    )

    # 6. reject others
    cur.execute(
        "UPDATE offers SET status = 'rejected' WHERE cake_id = %s AND id != %s",
        (cake_id, offer_id)
    )

    # 7. create order
    cur.execute(
        """
        INSERT INTO orders (cake_id, baker_id, final_price, delivery_date)
        VALUES (%s, %s, %s, CURRENT_DATE + (%s * INTERVAL '1 day'))
        RETURNING id;
        """,
        (cake_id, baker_id, price, delivery_days)
    )

    order_id = cur.fetchone()[0]

    # 8. update cake status
    cur.execute(
        "UPDATE cake_requests SET status = 'completed' WHERE id = %s",
        (cake_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "offer selected", "order_id": order_id}