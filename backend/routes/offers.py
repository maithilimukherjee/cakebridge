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