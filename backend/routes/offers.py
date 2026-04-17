from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection

router = APIRouter()

class OfferCreate(BaseModel):
    cake_id: int
    baker_id: int
    price: int
    delivery_days: int
    message: str | None = None


@router.post("/create")
def create_offer(offer: OfferCreate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO offers (cake_id, baker_id, price, delivery_days, message)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            offer.cake_id,
            offer.baker_id,
            offer.price,
            offer.delivery_days,
            offer.message
        )
    )

    offer_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "offer submitted",
        "offer_id": offer_id
    }


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


@router.post("/select/{offer_id}")
def select_offer(offer_id: int):
    conn = get_connection()
    cur = conn.cursor()

    # 1. get offer details
    cur.execute(
        "SELECT cake_id, baker_id, price, delivery_days, status FROM offers WHERE id = %s",
        (offer_id,)
    )
    offer = cur.fetchone()

    if not offer:
        return {"error": "offer not found"}

    cake_id, baker_id, price, delivery_days, status = offer

    # 2. prevent selecting already processed offer
    if status != "pending":
        return {"error": "offer already processed"}

    # 3. prevent duplicate order for same cake
    cur.execute(
        "SELECT id FROM orders WHERE cake_id = %s",
        (cake_id,)
    )
    existing_order = cur.fetchone()

    if existing_order:
        return {"error": "order already exists for this cake"}

    # 4. accept this offer
    cur.execute(
        "UPDATE offers SET status = 'accepted' WHERE id = %s",
        (offer_id,)
    )

    # 5. reject all other offers
    cur.execute(
        "UPDATE offers SET status = 'rejected' WHERE cake_id = %s AND id != %s",
        (cake_id, offer_id)
    )

    # 6. create order (with proper delivery date)
    cur.execute(
        """
        INSERT INTO orders (cake_id, baker_id, final_price, delivery_date)
        VALUES (%s, %s, %s, CURRENT_DATE + (%s * INTERVAL '1 day'))
        RETURNING id;
        """,
        (cake_id, baker_id, price, delivery_days)
    )

    order_id = cur.fetchone()[0]

    # 7. update cake request status
    cur.execute(
        "UPDATE cake_requests SET status = 'completed' WHERE id = %s",
        (cake_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "offer selected",
        "order_id": order_id
    }