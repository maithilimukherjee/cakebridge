from fastapi import APIRouter
from pydantic import BaseModel
from db.database import get_connection
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
SECRET_KEY = "m12200123080"
ALGORITHM = "HS256"

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
    hashed_password = pwd_context.hash(user.password[:72])

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
    
class LoginRequest(BaseModel):
    email: str
    password: str
    
@router.post("/login")
def login(user: LoginRequest):
    conn = get_connection()
    cur = conn.cursor()

    # 1. get user from DB
    cur.execute(
        "SELECT id, password, role FROM users WHERE email = %s",
        (user.email,)
    )
    db_user = cur.fetchone()

    if not db_user:
        cur.close()
        conn.close()
        return {"error": "invalid credentials"}

    user_id, hashed_password, role = db_user

    # 2. verify password
    if not pwd_context.verify(user.password, hashed_password):
        cur.close()
        conn.close()
        return {"error": "invalid credentials"}

    # 3. create JWT token
    payload = {
        "user_id": user_id,
        "role": role,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

    cur.close()
    conn.close()

    return {
        "message": "login successful",
        "token": token
    }