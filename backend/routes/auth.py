from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

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

    # check email first
    cur.execute("SELECT id FROM users WHERE email = %s", (user.email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return {"error": "email already exists"}

    # hash after validation
    hashed_password = pwd_context.hash(user.password)

    cur.execute(
        """
        INSERT INTO users (name, email, phone, password, role)
        VALUES (%s, %s, %s, %s, %s)
        RETURNING id;
        """,
        (user.name, user.email, user.phone, hashed_password, user.role)
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