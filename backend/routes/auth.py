from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection

router = APIRouter()


class UserRegister(BaseModel):
    name: str
    email: str
    phone: str
    password: str
    role: str  # user or baker


@router.post("/register")
def register_user(user: UserRegister):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO users (name, email, phone, password, role)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (user.name, user.email, user.phone, user.password, user.role)
    )

    user_id = cur.fetchone()[0]

    conn.commit()
    cur.close()
    conn.close()

    return {
        "message": "user registered successfully",
        "user_id": user_id,
        "role": user.role
    }