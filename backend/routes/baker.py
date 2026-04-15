from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection

router = APIRouter()

class BakerProfile(BaseModel):
    user_id: int
    shop_name: str
    city: str
    address: str


@router.post("/create")
def create_baker(profile: BakerProfile):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO baker_profiles (user_id, shop_name, city, address)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """,
        (profile.user_id, profile.shop_name, profile.city, profile.address)
    )

    baker_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "baker profile created", "baker_id": baker_id}