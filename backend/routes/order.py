from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection

router = APIRouter()

class Order(BaseModel):
    cake_id: int
    baker_id: int
    final_price: int
    delivery_date: str
    payment_method: str  # 'cod' or 'online'


@router.post("/create")
def create_order(order: Order):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO orders (cake_id, baker_id, final_price, delivery_date, payment_method)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            order.cake_id,
            order.baker_id,
            order.final_price,
            order.delivery_date,
            order.payment_method
        )
    )

    order_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "order created", "order_id": order_id}