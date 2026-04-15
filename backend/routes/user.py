from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection

router = APIRouter()

class User(BaseModel):
    name: str
    email: str
    phone: str
    role: str  # 'user' or 'baker'


@router.post("/create")
def create_user(user: User):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (name, email, phone, role)
        VALUES (%s, %s, %s, %s)
        RETURNING id;
        """,
        (user.name, user.email, user.phone, user.role)
    )

    user_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {"message": "user created", "user_id": user_id}