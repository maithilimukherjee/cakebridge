from fastapi import FastAPI
from fastapi import APIRouter
from models.schemas import CakeRequest
from db.database import get_connection
import json

router = APIRouter()

@router.post("/request")

def create_cake(request: CakeRequest):
    
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute(
        """
        INSERT INTO cake_requests
        (user_id, description, image_url, input_type,
         budget_min, budget_max, event_date, delivery_city, ai_tags)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (
            request.user_id,
            request.description,
            request.image_url,
            request.input_type,
            request.budget_min,
            request.budget_max,
            request.event_date,
            request.delivery_city,
            json.dumps(request.ai_tags) if request.ai_tags else None
        )
    )
    
    cake_id = cur.fetchone()[0]
    
    conn.commit()
    cur.close()
    conn.close()
    
    return {"message": "cake request created successfully!", "cake_id": cake_id}