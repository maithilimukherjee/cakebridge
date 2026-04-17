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
